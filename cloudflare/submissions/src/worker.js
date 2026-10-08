import {HttpError,LIMITS,requireValue,safeName,validateManifest,reviewedHierarchy} from './validation.js'

const now=()=>Math.floor(Date.now()/1000)
const uuid=()=>crypto.randomUUID()
const hex=bytes=>Array.from(new Uint8Array(bytes),x=>x.toString(16).padStart(2,'0')).join('')
const hash=async value=>hex(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(value)))
const secret=()=>hex(crypto.getRandomValues(new Uint8Array(32)))
const json=(data,status=200)=>Response.json(data,{status,headers:{'Cache-Control':'no-store'}})
const query=(env,sql,...args)=>env.DB.prepare(sql).bind(...args)
const first=(env,sql,...args)=>query(env,sql,...args).first()
const rows=async(env,sql,...args)=>(await query(env,sql,...args).all()).results
const run=(env,sql,...args)=>query(env,sql,...args).run()
async function body(request){
 requireValue(Number(request.headers.get('Content-Length')||0)<=128000,'Submission metadata is too large.',413)
 const reader=request.body?.getReader();requireValue(reader,'Send valid JSON.')
 const chunks=[];let size=0
 while(true){const {done,value}=await reader.read();if(done)break;size+=value.byteLength;if(size>128000){await reader.cancel();throw new HttpError(413,'Submission metadata is too large.')}chunks.push(value)}
 const bytes=new Uint8Array(size);let offset=0;for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.byteLength}
 try{return JSON.parse(new TextDecoder().decode(bytes))}catch{throw new HttpError(400,'Send valid JSON.')}
}

async function options(env){return JSON.parse((await first(env,'SELECT json FROM options WHERE id=1')).json)}
async function enabled(env){return env.SUBMISSIONS_ENABLED!=='false'&&(await first(env,"SELECT value FROM settings WHERE key='enabled'"))?.value!=='false'}
async function cap(env){const limit=Number(env.STORAGE_CAP_BYTES||9663676416);requireValue(Number.isSafeInteger(limit)&&limit>0&&limit<=9663676416,'Invalid storage cap.',503);await run(env,'UPDATE storage SET cap_bytes=? WHERE id=1',limit);return limit}
async function alert(env){const s=await first(env,'SELECT * FROM storage WHERE id=1');const percent=(s.stored_bytes+s.reserved_bytes)/s.cap_bytes*100;const level=[75,85,95,100].filter(x=>percent>=x).at(-1)||0;if(level!==s.warning)await env.DB.batch([query(env,'UPDATE storage SET warning=? WHERE id=1',level),query(env,'INSERT INTO alerts(level,at) VALUES(?,?)',level,now())])}
async function storage(env){const s=await first(env,'SELECT * FROM storage WHERE id=1');s.cap_bytes=Number(env.STORAGE_CAP_BYTES||9663676416);const groups=await rows(env,'SELECT status,SUM(actual_bytes) bytes,COUNT(*) count FROM submissions GROUP BY status');return {...s,percent:100*(s.stored_bytes+s.reserved_bytes)/s.cap_bytes,pending_bytes:groups.filter(g=>['pending','reviewing'].includes(g.status)).reduce((n,g)=>n+g.bytes,0),terminal_bytes:groups.filter(g=>['imported','rejected','failed'].includes(g.status)).reduce((n,g)=>n+g.bytes,0),pending_count:groups.filter(g=>['pending','reviewing'].includes(g.status)).reduce((n,g)=>n+g.count,0),enabled:await enabled(env),thresholds:[75,85,95,100]}}
async function rate(env,request){
 requireValue(env.IP_SALT,'Submission security is not configured.',503)
 const ip=await hash(env.IP_SALT+':'+(request.headers.get('CF-Connecting-IP')||'unknown'))
 const bucket=Math.floor(now()/3600)
 for(const [key,max] of [[ip,5],['global',30]]){
  const result=await query(env,'INSERT INTO rate_limits(hash,window,count) VALUES(?,?,1) ON CONFLICT(hash,window) DO UPDATE SET count=count+1 WHERE count<? RETURNING count',key,bucket,max).all()
  requireValue(result.results.length,'Too many submissions. Please try again later.',429)
 }
}
async function create(env,request){
 requireValue(await enabled(env),'Replay submissions are temporarily unavailable.',503)
 const input=await body(request);const manifest=validateManifest(input,await options(env));await rate(env,request)
 if(env.TURNSTILE_SECRET){
  const check=await fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify',{method:'POST',body:new URLSearchParams({secret:env.TURNSTILE_SECRET,response:input.turnstile_token||''})}).then(r=>r.json())
  requireValue(check.success&&check.hostname===new URL(env.PUBLIC_ORIGIN).hostname,'Please complete the bot verification.',403)
 }
 await cap(env)
 const id=uuid(),token=secret(),display='R6-'+secret().slice(0,10).toUpperCase(),created=now()
 const commands=[query(env,`INSERT INTO submissions(id,display_id,team_slug,team_name,season_slug,season_name,opponent,match_date,submitter,discord,rehost,notes,status,created_at,expires_at,token_hash,declared_bytes,reserved_bytes,schema_version) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,'uploading',?,?,?,?,?,?)`,id,display,manifest.team.slug,manifest.team.name,manifest.season.slug,manifest.season.name,manifest.opponent,manifest.date,manifest.submitter,manifest.discord,manifest.rehost,manifest.notes,created,created+LIMITS.sessionSeconds,await hash(token),manifest.bytes,manifest.bytes,manifest.schema_version)]
 let ordinal=0;const files=[],fileValues=[],folderIds=new Map(manifest.folders.map(f=>[f.name,uuid()])),assignment=new Map()
 for(const m of manifest.maps){
  const mid=uuid();commands.push(query(env,'INSERT INTO logical_maps(id,submission_id,logical_index,submitted_type) VALUES(?,?,?,?)',mid,id,m.index,m.type))
  for(const segment of m.segments)assignment.set(segment.folder_name,{id:mid,index:m.index,part:segment.index})
 }
 const ordered=manifest.schema_version===2?manifest.maps.flatMap(m=>m.segments.map(part=>manifest.folders.find(f=>f.name===part.folder_name))):manifest.folders
 for(const [i,f] of ordered.entries()){
  const folder=folderIds.get(f.name),assigned=assignment.get(f.name)
  commands.push(query(env,'INSERT INTO folders(id,submission_id,name,ordinal,logical_map_id,segment_index,first_file_modified_at,last_file_modified_at) VALUES(?,?,?,?,?,?,?,?)',folder,id,f.name,i,assigned?.id||null,assigned?.part||null,f.first_file_modified_at,f.last_file_modified_at))
  for(const p of f.files){const fid=uuid();fileValues.push([fid,id,folder,p.name,`submissions/${id}/${folder}/${fid}.rec`,ordinal++,p.size,p.sha256]);files.push({id:fid,folder_id:folder,folder:f.name,name:p.name,size:p.size,logical_index:assigned?.index||null,segment_index:assigned?.part||null})}
 }
 // Multi-row inserts stay below D1's 100 bound parameters / 50 free-plan
 // queries per invocation. The entire manifest and reservation commit together.
 for(let i=0;i<fileValues.length;i+=12){const chunk=fileValues.slice(i,i+12);commands.push(query(env,'INSERT INTO files(id,submission_id,folder_id,name,object_key,ordinal,declared_size,sha256) VALUES '+chunk.map(()=>'(?,?,?,?,?,?,?,?)').join(','),...chunk.flat()))}
 try{
  await env.DB.batch(commands)
 }catch(error){if(String(error).includes('inbox_full'))throw new HttpError(507,'Replay inbox is full. Please try again after the administrator clears space.');if(String(error).includes('reconcile_busy'))throw new HttpError(503,'Replay inbox maintenance is in progress. Please try again shortly.');throw error}
 await alert(env)
 return json({id,display_id:display,upload_token:token,expires_at:created+LIMITS.sessionSeconds,files},201)
}
async function uploadSession(env,request,id){
 const s=await first(env,'SELECT * FROM submissions WHERE id=?',id)
 const token=request.headers.get('Authorization')?.replace(/^Bearer /,'')||''
 requireValue(s&&token&&await hash(token)===s.token_hash,'Invalid upload authorization.',401)
 requireValue(s.expires_at>now(),'Upload session expired. Start a new submission.',410)
 requireValue(s.status==='uploading'||s.status==='pending','This upload session is closed.',409)
 return s
}
async function putFile(env,request,s,fid){
 requireValue(s.status==='uploading','Submission is already received.',409)
 const f=await first(env,'SELECT * FROM files WHERE id=? AND submission_id=?',fid,s.id);requireValue(f,'Unknown replay file.',404)
 if(f.status==='uploaded')return json({uploaded:true,bytes:f.actual_size})
 requireValue(Number(request.headers.get('Content-Length'))===f.declared_size,'Replay upload size differs from its reservation.',413)
 requireValue(request.body,'Replay upload is empty.')
 const lease=uuid()
 const claim=await run(env,`UPDATE files SET status='uploading',lease=?,lease_until=? WHERE id=? AND actual_size=0 AND (status='waiting' OR lease_until<?) AND (SELECT lock_until FROM storage WHERE id=1)<=? AND (SELECT status FROM submissions WHERE id=?)='uploading'`,lease,now()+600,fid,now(),now(),s.id)
 requireValue(claim.meta.changes,'This file is already uploading, or storage maintenance is active. Retry shortly.',409)
 const reader=request.body.getReader();let size=0,prefix=[];let timer
 const stream=new ReadableStream({
  start(controller){timer=setTimeout(()=>{reader.cancel();controller.error(new Error('Replay upload timed out.'))},300000)},
  async pull(controller){try{const {done,value}=await reader.read();if(done){requireValue(size===f.declared_size,'Replay upload is incomplete.');clearTimeout(timer);controller.close();return}size+=value.byteLength;requireValue(size<=f.declared_size,'Replay exceeds its reserved size.',413);if(prefix.length<7){prefix.push(...value.subarray(0,7-prefix.length));if(prefix.length===7)requireValue(new TextDecoder().decode(new Uint8Array(prefix))==='dissect','This file is not a Siege replay.')}controller.enqueue(value)}catch(error){clearTimeout(timer);controller.error(error);await reader.cancel()}},
  cancel(){clearTimeout(timer);return reader.cancel()}
 })
 try{
  const sha=new Uint8Array(f.sha256.match(/../g).map(n=>parseInt(n,16)))
  const fixed=new FixedLengthStream(f.declared_size)
  const pump=stream.pipeTo(fixed.writable).catch(error=>error)
  await env.INBOX.put(f.object_key,fixed.readable,{sha256:sha,httpMetadata:{contentType:'application/octet-stream'},customMetadata:{sha256:f.sha256,submission:s.id},storageClass:'Standard'})
  const transfer=await pump;if(transfer instanceof Error)throw transfer
  const object=await env.INBOX.head(f.object_key);requireValue(object&&object.size===f.declared_size,'Stored replay size could not be verified.')
  const acknowledged=await run(env,"UPDATE files SET status='uploaded',actual_size=?,lease=NULL,lease_until=0 WHERE id=? AND lease=? AND (SELECT status FROM submissions WHERE id=?)='uploading'",object.size,fid,lease,s.id)
  requireValue(acknowledged.meta.changes,'Upload session closed during transfer.',409)
  return json({uploaded:true,bytes:object.size})
 }catch(error){await run(env,"UPDATE files SET status='waiting',lease=NULL,lease_until=0 WHERE id=? AND lease=?",fid,lease);throw new HttpError(400,'Replay upload failed validation or transfer. Retry this file.')}finally{clearTimeout(timer)}
}
async function complete(env,s){
 if(s.status==='pending')return json({received:true,display_id:s.display_id})
 const counts=await first(env,"SELECT COUNT(*) total,SUM(status='uploaded') uploaded FROM files WHERE submission_id=?",s.id)
 requireValue(counts.total>0&&counts.total===counts.uploaded&&s.actual_bytes===s.declared_bytes,'Not all replay files are safely uploaded.',409)
 const batch=await rows(env,'SELECT * FROM files WHERE submission_id=? AND ordinal>=? ORDER BY ordinal LIMIT 20',s.id,s.verify_cursor)
 for(const f of batch){const object=await env.INBOX.head(f.object_key);requireValue(object&&object.size===f.declared_size&&object.customMetadata?.sha256===f.sha256,'A stored replay is missing or inconsistent. Retry or cancel the submission.',409)}
 const next=s.verify_cursor+batch.length
 if(next>=counts.total){const result=await run(env,"UPDATE submissions SET status='pending',submitted_at=?,verify_cursor=? WHERE id=? AND status='uploading' AND verify_cursor=?",now(),next,s.id,s.verify_cursor);requireValue(result.meta.changes||(await first(env,'SELECT status FROM submissions WHERE id=?',s.id)).status==='pending','Upload session closed before completion.',409);return json({received:true,display_id:s.display_id})}
 await run(env,'UPDATE submissions SET verify_cursor=? WHERE id=? AND verify_cursor=?',next,s.id,s.verify_cursor)
 return json({received:false,verified:next,total:counts.total})
}
function logicalStructure(records,folders){return records.map(m=>({id:m.id,index:m.logical_index,type:m.submitted_type,segments:folders.filter(f=>f.logical_map_id===m.id).sort((a,b)=>a.segment_index-b.segment_index).map(f=>({index:f.segment_index,folder_id:f.id}))}))}
async function detail(env,id,internal=false){
 const s=await first(env,'SELECT * FROM submissions WHERE id=?',id);requireValue(s,'Submission not found.',404);delete s.token_hash
 const folders=await rows(env,'SELECT * FROM folders WHERE submission_id=? ORDER BY ordinal',id),maps=logicalStructure(await rows(env,'SELECT * FROM logical_maps WHERE submission_id=? ORDER BY logical_index',id),folders)
 const reviewed_maps=s.reviewed_structure_json?JSON.parse(s.reviewed_structure_json):maps;if(internal)s._reviewed_json=s.reviewed_structure_json;delete s.reviewed_structure_json
 return {...s,maps,reviewed_maps,folders,files:await rows(env,'SELECT * FROM files WHERE submission_id=? ORDER BY ordinal',id)}
}
function reviewedSelection(s,b){
 const maps=reviewedHierarchy(b.reviewed_maps||s.reviewed_maps||s.maps,s.folders)
 const map=maps.find(m=>m.id===b.logical_map_id)
 requireValue(map,'Choose a reviewed logical map.')
 requireValue(map.type!=='unsure','Classify this logical map before import.')
 const ids=map.segments.map(p=>p.folder_id)
 requireValue(Array.isArray(b.folder_ids)&&b.folder_ids.length===ids.length&&b.folder_ids.every((id,i)=>id===ids[i]),'Receipt folders must exactly match the selected logical map in reviewed order.')
 for(const f of s.folders.filter(f=>f.disposition==='imported')){
  const prior=s.reviewed_maps.find(m=>m.segments.some(p=>p.folder_id===f.id))
  const next=maps.find(m=>m.segments.some(p=>p.folder_id===f.id))
  requireValue(prior&&next&&JSON.stringify(prior)===JSON.stringify(next),'Previously imported logical structure cannot change.',409)
 }
 return maps
}

// A durable lease serializes R2 maintenance across Worker isolates. The longer
// scan lock additionally blocks upload reservations/transfers between pages.
async function maintenance(env,work){
 const owner=uuid(),claim=await run(env,'UPDATE maintenance SET owner=?,expires=? WHERE id=1 AND expires<=?',owner,now()+600,now())
 requireValue(claim.meta.changes,'Storage maintenance is already in progress. Retry shortly.',409)
 try{return await work()}finally{await run(env,'UPDATE maintenance SET owner=NULL,expires=0 WHERE id=1 AND owner=?',owner)}
}
async function removeObjects(env,id,forced=false){
 const s=await first(env,'SELECT * FROM submissions WHERE id=?',id);requireValue(s,'Submission not found.',404)
 if(s.objects_deleted_at)return
 requireValue(!['pending','reviewing'].includes(s.status),'Pending review files cannot be cleaned up.',409)
 requireValue(!(await first(env,"SELECT id FROM files WHERE submission_id=? AND status='uploading' AND lease_until>? LIMIT 1",id,now())),'An upload is still in progress. Retry cleanup later.',409)
 const expiry=s.status==='uploading'?s.expires_at:s.terminal_at+Number(env.RETENTION_DAYS||7)*86400
 requireValue(forced||expiry<=now(),'Cloud retention has not expired.',409)
 const claim=await run(env,"UPDATE submissions SET cleanup_lease_until=?,status=CASE WHEN status='uploading' THEN 'failed' ELSE status END,terminal_at=COALESCE(terminal_at,?),expires_at=0 WHERE id=? AND objects_deleted_at IS NULL AND cleanup_lease_until<? AND NOT EXISTS(SELECT 1 FROM files WHERE submission_id=? AND status='uploading' AND lease_until>?)",now()+600,now(),id,now(),id,now())
 requireValue(claim.meta.changes,'Cleanup is already in progress.',409)
 const files=await rows(env,'SELECT object_key FROM files WHERE submission_id=?',id)
 if(files.length)await env.INBOX.delete(files.map(f=>f.object_key))
 await env.DB.batch([
  query(env,'UPDATE storage SET stored_bytes=MAX(0,stored_bytes-?),reserved_bytes=reserved_bytes-? WHERE id=1',s.actual_bytes,s.reserved_bytes),
  query(env,'UPDATE submissions SET actual_bytes=0,reserved_bytes=0,objects_deleted_at=?,cleanup_lease_until=0 WHERE id=?',now(),id),
  query(env,"UPDATE files SET status='deleted',actual_size=0 WHERE submission_id=?",id),
 ])
}
export async function cleanup(env){return maintenance(env,()=>cleanupStep(env))}
async function cleanupStep(env){
 requireValue((await first(env,'SELECT lock_until FROM storage WHERE id=1')).lock_until<=now(),'Storage reconciliation is in progress. Retry cleanup later.',409)
 const candidates=await rows(env,`SELECT id FROM submissions WHERE objects_deleted_at IS NULL AND ((status='uploading' AND expires_at<?) OR (status IN('imported','rejected','failed') AND terminal_at<?)) AND NOT EXISTS(SELECT 1 FROM files WHERE files.submission_id=submissions.id AND status='uploading' AND lease_until>?) LIMIT 4`,now(),now()-Number(env.RETENTION_DAYS||7)*86400,now())
 for(const s of candidates)await removeObjects(env,s.id)
 await run(env,'DELETE FROM rate_limits WHERE window<?',Math.floor(now()/3600)-24)
 await alert(env);return {cleaned:candidates.length}
}
async function reconcile(env){return maintenance(env,()=>reconcileStep(env))}
async function reconcileStep(env){
 const state=await first(env,'SELECT * FROM storage WHERE id=1')
 let lock=state.reconcile_lock
 if(!lock||state.lock_until<now()){
  lock=uuid();const claim=await run(env,`UPDATE storage SET reconcile_lock=?,lock_until=?,scan_cursor=NULL,scan_bytes=0 WHERE id=1 AND lock_until<=? AND NOT EXISTS(SELECT 1 FROM files WHERE status='uploading' AND lease_until>?) AND NOT EXISTS(SELECT 1 FROM submissions WHERE cleanup_lease_until>?)`,lock,now()+180,now(),now(),now())
  requireValue(claim.meta.changes,'Uploads are in progress. Reconcile after they finish.',409)
  await run(env,'DELETE FROM reconcile_seen')
 }
 const current=await first(env,'SELECT * FROM storage WHERE id=1')
 const page=await env.INBOX.list({limit:16,cursor:current.scan_cursor||undefined,include:['customMetadata']})
 const updates=[]
 for(const object of page.objects){updates.push(query(env,'INSERT INTO reconcile_seen(object_key,size) VALUES(?,?) ON CONFLICT(object_key) DO UPDATE SET size=excluded.size',object.key,object.size));updates.push(query(env,`UPDATE files SET actual_size=?,status='uploaded',lease=NULL,lease_until=0 WHERE object_key=? AND actual_size=0 AND declared_size=? AND sha256=? AND status!='deleted' AND submission_id IN(SELECT id FROM submissions WHERE status IN('uploading','failed') AND objects_deleted_at IS NULL)`,object.size,object.key,object.size,object.customMetadata?.sha256||''))}
 if(updates.length)await env.DB.batch(updates)
 const total=current.scan_bytes+page.objects.reduce((n,o)=>n+o.size,0)
 if(page.truncated){await run(env,'UPDATE storage SET scan_bytes=?,scan_cursor=?,lock_until=? WHERE id=1 AND reconcile_lock=? AND scan_cursor IS ?',total,page.cursor,now()+180,lock,current.scan_cursor);return {complete:false,scanned_bytes:total}}
 await env.DB.batch([
  query(env,"UPDATE files SET actual_size=0,status='waiting' WHERE actual_size>0 AND object_key NOT IN(SELECT object_key FROM reconcile_seen)"),
  query(env,"UPDATE submissions SET actual_bytes=(SELECT COALESCE(SUM(actual_size),0) FROM files WHERE submission_id=submissions.id),reserved_bytes=CASE WHEN status='uploading' THEN (SELECT COALESCE(SUM(declared_size),0) FROM files WHERE submission_id=submissions.id AND actual_size=0) ELSE 0 END"),
  query(env,`UPDATE storage SET stored_bytes=?,reserved_bytes=(SELECT COALESCE(SUM(reserved_bytes),0) FROM submissions),last_reconciled=?,reconcile_lock=NULL,lock_until=0,scan_cursor=NULL,scan_bytes=0 WHERE id=1 AND reconcile_lock=? AND scan_cursor IS ?`,total,now(),lock,current.scan_cursor)
 ])
 await alert(env);return {complete:true,...await storage(env)}
}
async function admin(env,request,path){
 requireValue(env.ADMIN_SECRET&&request.headers.get('Authorization')===`Bearer ${env.ADMIN_SECRET}`,'Admin authorization required.',401)
 if(path==='/storage'&&request.method==='GET')return json(await storage(env))
 if(path==='/reconcile'&&request.method==='POST')return json(await reconcile(env))
 if(path==='/cleanup'&&request.method==='POST')return json(await cleanup(env))
 if(path==='/options'&&request.method==='POST'){
  const b=await body(request);requireValue(Array.isArray(b.teams)&&Array.isArray(b.seasons)&&b.teams.length<=20&&b.seasons.length<=30,'Invalid submission choices.')
  for(const item of [...b.teams,...b.seasons])requireValue(/^[a-z0-9-]{1,80}$/.test(item.slug)&&typeof item.name==='string'&&item.name.length<=100,'Invalid team or season choice.')
  await run(env,'UPDATE options SET json=? WHERE id=1',JSON.stringify(b));return json({ok:true})
 }
 if(path==='/settings'&&request.method==='POST'){const b=await body(request);requireValue(typeof b.enabled==='boolean','Choose enabled or disabled.');await run(env,"INSERT INTO settings(key,value) VALUES('enabled',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",String(b.enabled));return json({enabled:await enabled(env)})}
 if(path==='/submissions'&&request.method==='GET'){
  const status=new URL(request.url).searchParams.get('status')||'pending'
  const result=status==='all'?await rows(env,"SELECT id FROM submissions WHERE status!='uploading' ORDER BY created_at DESC LIMIT 100"):await rows(env,"SELECT id FROM submissions WHERE status IN('pending','reviewing') ORDER BY created_at LIMIT 100")
  if(!result.length)return json([])
  const ids=result.map(s=>s.id),placeholders=ids.map(()=>'?').join(',')
  const records=await rows(env,`SELECT id,display_id,team_slug,team_name,season_slug,season_name,opponent,match_date,submitter,discord,rehost,notes,status,created_at,submitted_at,terminal_at,objects_deleted_at,actual_bytes,schema_version,reviewed_structure_json FROM submissions WHERE id IN(${placeholders}) ORDER BY created_at`,...ids)
  const folders=await rows(env,`SELECT * FROM folders WHERE submission_id IN(${placeholders})`,...ids),maps=await rows(env,`SELECT * FROM logical_maps WHERE submission_id IN(${placeholders}) ORDER BY logical_index`,...ids)
  return json(records.map(s=>{const fs=folders.filter(f=>f.submission_id===s.id),ms=logicalStructure(maps.filter(m=>m.submission_id===s.id),fs),reviewed=s.reviewed_structure_json?JSON.parse(s.reviewed_structure_json):ms;delete s.reviewed_structure_json;return {...s,folders:fs,maps:ms,reviewed_maps:reviewed}}))
 }
 const match=path.match(/^\/submissions\/([a-f0-9-]{36})(?:\/(review|reject|consume|purge|files\/([a-f0-9-]{36})))?$/)
 requireValue(match,'Admin endpoint not found.',404);const id=match[1],action=match[2]
 if(!action&&request.method==='GET')return json(await detail(env,id))
 if(action?.startsWith('files/')&&request.method==='GET'){
  const f=await first(env,"SELECT f.* FROM files f JOIN submissions s ON s.id=f.submission_id WHERE f.id=? AND f.submission_id=? AND f.status='uploaded' AND s.status IN('pending','reviewing')",match[3],id);requireValue(f,'Replay is unavailable.',404)
  const object=await env.INBOX.get(f.object_key);requireValue(object&&object.size===f.declared_size,'Stored replay is missing or inconsistent.',409)
  return new Response(object.body,{headers:{'Content-Type':'application/octet-stream','Content-Length':String(object.size),'Cache-Control':'no-store','X-Replay-SHA256':f.sha256}})
 }
 requireValue(request.method==='POST','Method not allowed.',405)
 if(action==='review'){await run(env,"UPDATE submissions SET status='reviewing' WHERE id=? AND status='pending'",id);return json(await detail(env,id))}
 const b=await body(request),s=await detail(env,id,true)
 if(action==='reject'){
  requireValue(['pending','reviewing'].includes(s.status),'This submission is already terminal.',409)
  requireValue(typeof b.reason==='string'&&b.reason.trim().length>0&&b.reason.length<=240&&typeof (b.notes||'')==='string'&&(b.notes||'').length<=2000,'Provide a rejection reason.')
  let selected=s.folders.filter(f=>!f.disposition)
  if(b.folder_ids){requireValue(Array.isArray(b.folder_ids)&&b.folder_ids.length>0&&new Set(b.folder_ids).size===b.folder_ids.length,'Choose remaining folders to reject.');selected=s.folders.filter(f=>b.folder_ids.includes(f.id));requireValue(selected.length===b.folder_ids.length&&selected.every(f=>!f.disposition),'Only unresolved owned folders can be rejected.',409)}
  await env.DB.batch([...selected.map(f=>query(env,"UPDATE folders SET disposition='rejected',reason=? WHERE id=? AND submission_id=? AND disposition IS NULL",b.reason,f.id,id)),query(env,"UPDATE submissions SET status=CASE WHEN EXISTS(SELECT 1 FROM folders WHERE submission_id=? AND disposition IS NULL) THEN 'reviewing' WHEN EXISTS(SELECT 1 FROM folders WHERE submission_id=? AND disposition='imported') THEN 'imported' ELSE 'rejected' END,terminal_at=CASE WHEN EXISTS(SELECT 1 FROM folders WHERE submission_id=? AND disposition IS NULL) THEN NULL ELSE ? END,review_reason=?,admin_notes=? WHERE id=? AND status IN('pending','reviewing')",id,id,id,now(),b.reason,b.notes||'',id)])
  return json(await detail(env,id))
 }
 if(action==='consume'){
  requireValue(['pending','reviewing','imported'].includes(s.status),'This submission cannot be imported.',409)
  requireValue(b.archive_verified===true&&/^[a-f0-9]{12}$/.test(b.map_id)&&Array.isArray(b.folder_ids)&&b.folder_ids.length>0,'Verified local archive receipt required.')
  if(s.schema_version===2){const prior=await first(env,'SELECT * FROM logical_import_receipts WHERE submission_id=? AND local_map_id=?',id,b.map_id);if(prior){requireValue(prior.logical_map_id===b.logical_map_id&&prior.folder_ids_json===JSON.stringify(b.folder_ids),'Local map receipt already belongs to another logical map.',409);return json(await detail(env,id))}}
  const reviewed=s.schema_version===2?reviewedSelection(s,b):null
  const selected=s.folders.filter(f=>b.folder_ids.includes(f.id));requireValue(selected.length===new Set(b.folder_ids).size&&selected.every(f=>!f.disposition||(f.disposition==='imported'&&f.map_id===b.map_id)),'Replay folder was already consumed or rejected.',409)
  requireValue(/^[a-z0-9-]+$/.test(b.team_slug||'')&&/^[a-z0-9-]+$/.test(b.season_slug||''),'Import context is required.')
  const evidence=reviewed?[query(env,'INSERT INTO logical_import_receipts(submission_id,local_map_id,logical_map_id,reviewed_structure_json,folder_ids_json,created_at) VALUES(?,?,?,?,?,?) ON CONFLICT(submission_id,local_map_id) DO NOTHING',id,b.map_id,b.logical_map_id,JSON.stringify(reviewed),JSON.stringify(b.folder_ids),now())]:[]
  // D1 batches are transactions. The receipt trigger aborts the entire batch
  // if a concurrent claim or review revision invalidates any selected segment.
  const revision=reviewed?[query(env,'UPDATE submissions SET reviewed_structure_json=? WHERE id=? AND reviewed_structure_json IS ?',JSON.stringify(reviewed),id,s._reviewed_json)]:[]
  let updates
  try{updates=await env.DB.batch([...revision,...selected.map(f=>query(env,"UPDATE folders SET disposition='imported',map_id=?,import_team=?,import_season=? WHERE id=? AND (disposition IS NULL OR (disposition='imported' AND map_id=?))",b.map_id,b.team_slug,b.season_slug,f.id,b.map_id)),query(env,`UPDATE submissions SET status=CASE WHEN NOT EXISTS(SELECT 1 FROM folders WHERE submission_id=? AND disposition IS NULL) THEN 'imported' ELSE 'reviewing' END,terminal_at=CASE WHEN NOT EXISTS(SELECT 1 FROM folders WHERE submission_id=? AND disposition IS NULL) THEN ? ELSE NULL END WHERE id=? AND status IN('pending','reviewing','imported') AND (SELECT COUNT(*) FROM folders WHERE disposition='imported' AND map_id=? AND id IN(${selected.map(()=>'?').join(',')}))=?`,id,id,now(),id,b.map_id,...selected.map(f=>f.id),selected.length),...evidence])}catch(error){if(String(error).includes('logical receipt conflict'))throw new HttpError(409,'Folder approval changed concurrently. Review the current cloud status.');throw error}
  updates=updates.slice(revision.length)
  requireValue(updates.slice(0,selected.length+1).every(result=>result.meta.changes),'Folder approval changed concurrently. Review the current cloud status.',409)
  return json(await detail(env,id))
 }
 if(action==='purge'){
  requireValue(b.confirm_display_id===s.display_id&&['rejected','imported','failed'].includes(s.status),'Confirm a terminal submission before removing its cloud files.',409)
  if(!s.objects_deleted_at)await maintenance(env,async()=>{requireValue((await first(env,'SELECT lock_until FROM storage WHERE id=1')).lock_until<=now(),'Reconciliation is in progress.',409);await removeObjects(env,id,true)})
  if(b.delete_metadata===true)await env.DB.batch([query(env,'DELETE FROM files WHERE submission_id=?',id),query(env,'DELETE FROM logical_import_receipts WHERE submission_id=?',id),query(env,'DELETE FROM folders WHERE submission_id=?',id),query(env,'DELETE FROM logical_maps WHERE submission_id=?',id),query(env,'DELETE FROM submissions WHERE id=?',id)])
  await alert(env);return json({ok:true})
 }
 throw new HttpError(404,'Admin endpoint not found.')
}
export default {
 async fetch(request,env){
  const origin=request.headers.get('Origin'),path=new URL(request.url).pathname
  const cors=origin===env.PUBLIC_ORIGIN?{'Access-Control-Allow-Origin':origin,'Vary':'Origin','Access-Control-Allow-Methods':'GET,POST,PUT,OPTIONS','Access-Control-Allow-Headers':'Content-Type,Authorization','Access-Control-Max-Age':'600'}:{}
  let response
  try{
   if(origin&&origin!==env.PUBLIC_ORIGIN)throw new HttpError(403,'Origin is not allowed.')
   if(request.method==='OPTIONS')response=new Response(null,{status:204})
   else if(path.startsWith('/v1/admin/'))response=await admin(env,request,path.slice(9))
   else if(path==='/v1/config'&&request.method==='GET'){const s=await storage(env);response=json({enabled:s.enabled,available:s.enabled&&s.stored_bytes+s.reserved_bytes<s.cap_bytes&&s.lock_until<=now(),limits:LIMITS,turnstile_site_key:env.TURNSTILE_SITE_KEY||null,schema_versions:[1,2],...await options(env)})}
   else if(path==='/v1/submissions'&&request.method==='POST'){requireValue(origin===env.PUBLIC_ORIGIN,'Use the public submission page.',403);response=await create(env,request)}
   else{
    const m=path.match(/^\/v1\/uploads\/([a-f0-9-]{36})(?:\/(complete|cancel|files\/([a-f0-9-]{36})))?$/);requireValue(m,'Endpoint not found.',404)
    const s=await uploadSession(env,request,m[1])
    if(!m[2]&&request.method==='GET')response=json({status:s.status,files:await rows(env,'SELECT id,status,actual_size FROM files WHERE submission_id=?',s.id)})
    else if(m[2]==='complete'&&request.method==='POST')response=await complete(env,s)
    else if(m[2]==='cancel'&&request.method==='POST'){requireValue(s.status==='uploading','Received submissions await administrator review.',409);await run(env,"UPDATE submissions SET status='failed',expires_at=0,terminal_at=0 WHERE id=?",s.id);response=json({cancelled:true})}
    else if(m[2]?.startsWith('files/')&&request.method==='PUT')response=await putFile(env,request,s,m[3])
    else throw new HttpError(405,'Method not allowed.')
   }
  }catch(error){const message=error instanceof HttpError?error.message:'The submission service could not complete this request. Please retry.';response=json({error:message},error.status||500)}
  const headers=new Headers(response.headers);for(const [k,v] of Object.entries(cors))headers.set(k,v);headers.set('X-Content-Type-Options','nosniff')
  return new Response(response.body,{status:response.status,headers})
 },
 async scheduled(_event,env,context){context.waitUntil(cleanup(env).catch(error=>{if(!(error instanceof HttpError&&error.status===409))throw error}))}
}
