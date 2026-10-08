import {test} from 'node:test'
import assert from 'node:assert/strict'
import {readFile} from 'node:fs/promises'
import {createHash} from 'node:crypto'
import {Miniflare} from 'miniflare'
import {validateManifest,reviewedHierarchy} from '../src/validation.js'

const bytes=Buffer.from('dissect\0 logical map fixture replay')
const sha256=createHash('sha256').update(bytes).digest('hex')
const options={teams:[{slug:'blue',name:'UAH Blue'}],seasons:[{slug:'fall-2026',name:'Fall 2026'}]}
const folder=name=>({name,first_file_modified_at:'2026-10-07T19:00:00.000Z',last_file_modified_at:'2026-10-07T19:20:00.000Z',files:[{name:`${name}-R01.rec`,size:bytes.length,sha256}]})
const manifest=()=>({schema_version:2,team_slug:'blue',season_slug:'fall-2026',opponent:'TEST',match_date:'2026-10-07',submitter:'Fixture',confirmed:true,folders:['A','B','C'].map(folder),maps:[{index:1,type:'normal',segments:[{index:1,folder_name:'A'}]},{index:2,type:'rehost',segments:[{index:1,folder_name:'B'},{index:2,folder_name:'C'}]}]})

test('structured manifest rejects malformed hierarchy and applies global caps',()=>{
 const valid=manifest();assert.equal(validateManifest(valid,options).bytes,3*bytes.length)
 const mutations=[m=>m.maps=[],m=>m.maps[1].index=1,m=>m.maps[0].index=0,m=>m.maps[1].segments.pop(),m=>m.maps[1].type='normal',m=>m.maps[1].segments[0].folder_name='A',m=>m.maps[1].segments[0].folder_name='unknown',m=>m.maps[1].segments[1].index=1,m=>m.maps[0].type='fake',m=>m.maps=Array(6).fill(m.maps[0]),m=>m.folders[0].first_file_modified_at='bad',m=>m.folders[0].last_file_modified_at='2026-10-07T18:00:00.000Z',m=>m.folders[0].files[0].size=64*1024**2+1,m=>m.folders[0].files=Array.from({length:241},(_,i)=>({name:`R${i}.rec`,size:32,sha256})),m=>m.folders[0].files=Array.from({length:33},(_,i)=>({name:`R${i}.rec`,size:64*1024**2,sha256}))]
 for(const change of mutations){const m=structuredClone(valid);change(m);assert.throws(()=>validateManifest(m,options))}
 const legacy={...valid,schema_version:1,rehost:'yes'};delete legacy.maps;assert.equal(validateManifest(legacy,options).schema_version,1)
 assert.throws(()=>reviewedHierarchy([{id:crypto.randomUUID(),index:1,type:'normal',segments:[{index:1,folder_id:'unknown'}]}],[{id:crypto.randomUUID()}]))
})

test('structured Worker/D1/R2 map lifecycle, migration, retries, review and retention',async t=>{
 const mf=new Miniflare({modules:true,modulesRules:[{type:'ESModule',include:['**/*.js']}],scriptPath:new URL('../src/worker.js',import.meta.url).pathname.replace(/^\/([A-Z]:)/,'$1'),compatibilityDate:'2026-07-30',d1Databases:['DB'],r2Buckets:['INBOX'],bindings:{PUBLIC_ORIGIN:'https://uah-r6.github.io',ADMIN_SECRET:'fixture-only',IP_SALT:'fixture-only',SUBMISSIONS_ENABLED:'true',STORAGE_CAP_BYTES:'9663676416',RETENTION_DAYS:'7'}})
 try{
 const db=await mf.getD1Database('DB'),bucket=await mf.getR2Bucket('INBOX')
 const migrate=async name=>{const sql=await readFile(new URL('../migrations/'+name,import.meta.url),'utf8');await db.batch(sql.match(/\s*CREATE TRIGGER[\s\S]+?\nEND;|[^;]+;/gi).map(s=>db.prepare(s)))}
 await migrate('0001_inbox.sql')
 // An old pending submission exists before the additive migration.
 const legacyId=crypto.randomUUID()
 await db.prepare("INSERT INTO submissions(id,display_id,team_slug,team_name,season_slug,season_name,opponent,match_date,submitter,discord,rehost,notes,status,created_at,expires_at,token_hash,declared_bytes,reserved_bytes) VALUES(?,'R6-LEGACY','blue','UAH Blue','fall-2026','Fall 2026','TEST','2026-10-07','TEST','','no','','pending',1,1,'fixture',0,0)").bind(legacyId).run()
 const legacyBefore=await db.prepare('SELECT * FROM submissions WHERE id=?').bind(legacyId).first()
 await migrate('0002_logical_maps.sql')
 const legacyAfter=await db.prepare('SELECT * FROM submissions WHERE id=?').bind(legacyId).first()
 for(const [key,value] of Object.entries(legacyBefore))assert.equal(legacyAfter[key],value)
 const request=(path,method='GET',data,token)=>mf.dispatchFetch('https://fixture.invalid/v1'+path,{method,headers:{Origin:'https://uah-r6.github.io','CF-Connecting-IP':'192.0.2.1',...(data?{'Content-Type':'application/json'}:{}),...(token?{Authorization:'Bearer '+token}:{})},body:data?JSON.stringify(data):undefined})
 const admin=(path,method='GET',data)=>request('/admin'+path,method,data,'fixture-only')
 const create=async(m=manifest())=>{await db.exec('DELETE FROM rate_limits');const r=await request('/submissions','POST',m);const body=await r.json();assert.equal(r.status,201,JSON.stringify(body));return body}
 const upload=(s,f,data=bytes)=>mf.dispatchFetch(`https://fixture.invalid/v1/uploads/${s.id}/files/${f.id}`,{method:'PUT',headers:{Authorization:'Bearer '+s.upload_token,'Content-Length':String(data.length)},body:data})
 const finish=async s=>{for(const f of s.files)assert.equal((await upload(s,f)).status,200);let result;do{const r=await request(`/uploads/${s.id}/complete`,'POST',{},s.upload_token);assert.equal(r.status,200);result=await r.json()}while(!result.received);return(await admin('/submissions/'+s.id)).json()}
 const receipt=(s,map,map_id)=>({map_id,logical_map_id:map.id,reviewed_maps:s.reviewed_maps,folder_ids:map.segments.map(p=>p.folder_id),team_slug:'blue',season_slug:'fall-2026',archive_verified:true})
 let s,d,r1
 await t.test('Normal A plus Rehost B+C preserves original intent, time range and ordered private identities',async()=>{
  s=await create();assert.deepEqual(s.files.map(f=>[f.folder,f.logical_index,f.segment_index]),[['A',1,1],['B',2,1],['C',2,2]])
  assert.equal((await upload(s,s.files[0])).status,200)
  assert.equal((await upload(s,s.files[1],Buffer.alloc(bytes.length))).status,400)
  const resumed=await(await request('/uploads/'+s.id,'GET',undefined,s.upload_token)).json();assert.equal(resumed.files[0].status,'uploaded');assert.equal(resumed.files[1].status,'waiting')
  for(const f of s.files.slice(1))assert.equal((await upload(s,f)).status,200)
  assert.equal((await request(`/uploads/${s.id}/complete`,'POST',{},s.upload_token)).status,200)
  d=await(await admin('/submissions/'+s.id)).json();assert.equal(d.schema_version,2);assert.deepEqual(d.maps.map(m=>m.type),['normal','rehost']);assert.equal(d.folders[0].first_file_modified_at,'2026-10-07T19:00:00.000Z');assert.equal(d.folders[0].last_file_modified_at,'2026-10-07T19:20:00.000Z')
  assert.ok(d.files.every(f=>f.object_key.includes(s.id)&&!f.object_key.includes(f.name)));assert.ok(!JSON.stringify(d).includes('token_hash'))
  assert.equal((await admin(`/submissions/${s.id}/files/${s.files[0].id}`)).status,200)
 })
 await t.test('one map consumption stays Reviewing; wrong selection/order and unverified archive are rejected',async()=>{
  r1=receipt(d,d.maps[0],'abcdef111111')
  const bad=receipt(d,d.maps[1],'abcdef222222')
  for(const value of [{...r1,archive_verified:false},{...bad,folder_ids:[r1.folder_ids[0],bad.folder_ids[0]]},{...bad,folder_ids:bad.folder_ids.slice(0,1)},{...bad,folder_ids:[...bad.folder_ids].reverse()},{...bad,reviewed_maps:d.maps.map(m=>({...m,type:m.index===2?'unsure':m.type}))}])assert.equal((await admin(`/submissions/${s.id}/consume`,'POST',value)).status,400)
  d=await(await admin(`/submissions/${s.id}/consume`,'POST',r1)).json();assert.equal(d.status,'reviewing');assert.equal(d.terminal_at,null);assert.deepEqual(d.folders.map(f=>f.disposition),['imported',null,null])
  await db.prepare('UPDATE submissions SET created_at=1 WHERE id=?').bind(s.id).run();await admin('/cleanup','POST',{});assert.equal((await bucket.list()).objects.length,3)
 })
 await t.test('review corrections preserve original structure and freeze imported maps; exact receipts are idempotent',async()=>{
  const reviewed=structuredClone(d.maps);reviewed[1].segments.reverse();reviewed[1].segments.forEach((p,i)=>p.index=i+1)
  const invalid=structuredClone(reviewed);invalid[0].type='unsure'
  assert.equal((await admin(`/submissions/${s.id}/consume`,'POST',receipt({...d,reviewed_maps:invalid},invalid[1],'abcdef222222'))).status,409)
  const response=await admin(`/submissions/${s.id}/consume`,'POST',receipt({...d,reviewed_maps:reviewed},reviewed[1],'abcdef222222'));assert.equal(response.status,200,await response.clone().text());d=await response.json();assert.equal(d.status,'imported');assert.ok(d.terminal_at);assert.deepEqual(d.maps[1].segments.map(p=>p.folder_id),[s.files[1].folder_id,s.files[2].folder_id]);assert.deepEqual(d.reviewed_maps[1].segments.map(p=>p.folder_id),[s.files[2].folder_id,s.files[1].folder_id])
  assert.equal((await admin(`/submissions/${s.id}/consume`,'POST',r1)).status,200)
  assert.equal((await admin(`/submissions/${s.id}/consume`,'POST',{...r1,folder_ids:[s.files[1].folder_id]})).status,409)
  assert.equal((await db.prepare('SELECT COUNT(*) n FROM logical_import_receipts WHERE submission_id=?').bind(s.id).first()).n,2)
  await admin('/cleanup','POST',{});assert.equal((await bucket.list()).objects.length,3)
  await db.prepare('UPDATE submissions SET terminal_at=1 WHERE id=?').bind(s.id).run();await admin('/cleanup','POST',{});assert.equal((await bucket.list()).objects.length,0)
 })
 await t.test('selective map/folder rejection leaves other maps available; terminal mixed disposition retains seven days',async()=>{
  const a=await create(),detail=await finish(a)
  let response=await(await admin(`/submissions/${a.id}/reject`,'POST',{folder_ids:[detail.maps[1].segments[0].folder_id],reason:'Bad segment'})).json();assert.equal(response.status,'reviewing');assert.equal(response.terminal_at,null)
  response=await(await admin(`/submissions/${a.id}/consume`,'POST',receipt(detail,detail.maps[0],'abcdef333333'))).json();assert.equal(response.status,'reviewing')
  response=await(await admin(`/submissions/${a.id}/reject`,'POST',{folder_ids:[detail.maps[1].segments[1].folder_id],reason:'Remaining bad map segment'})).json();assert.equal(response.status,'imported');assert.deepEqual(response.folders.map(f=>f.disposition),['imported','rejected','rejected'])
  await admin('/cleanup','POST',{});assert.equal((await bucket.list()).objects.length,3)
  await admin(`/submissions/${a.id}/purge`,'POST',{confirm_display_id:a.display_id,delete_metadata:true});assert.equal((await bucket.list()).objects.length,0)
 })
 await t.test('simultaneous claims are atomic with no ghost receipt or partial map',async()=>{
  const a=await create(),detail=await finish(a),map=detail.maps[1]
  const responses=await Promise.all([admin(`/submissions/${a.id}/consume`,'POST',receipt(detail,map,'abcdef444444')),admin(`/submissions/${a.id}/consume`,'POST',receipt(detail,map,'abcdef555555'))])
  assert.deepEqual(responses.map(r=>r.status).sort(),[200,409])
  const folders=(await(await admin('/submissions/'+a.id)).json()).folders;assert.equal(folders[0].disposition,null);assert.equal(folders[1].map_id,folders[2].map_id)
  assert.equal((await db.prepare('SELECT COUNT(*) n FROM logical_import_receipts WHERE submission_id=?').bind(a.id).first()).n,1)
  // Force a stale revision inside a real D1 transaction: guard must roll back.
  await assert.rejects(db.batch([db.prepare("UPDATE folders SET disposition='imported',map_id='abcdef666666' WHERE id=?").bind(folders[0].id),db.prepare('INSERT INTO logical_import_receipts VALUES(?,?,?,?,?,?)').bind(a.id,'abcdef666666',detail.maps[0].id,'[]',JSON.stringify([folders[0].id]),1)]))
  assert.equal((await db.prepare('SELECT disposition FROM folders WHERE id=?').bind(folders[0].id).first()).disposition,null)
 })
 await t.test('BO5 and maximum global inventory fit D1 request batching',async()=>{
  const m=manifest();m.folders=Array.from({length:12},(_,i)=>({...folder('M'+i),files:Array.from({length:20},(_,j)=>({name:`Replay-R${j+1}.rec`,size:bytes.length,sha256}))}));let ordinal=0;m.maps=[3,3,2,2,2].map((count,i)=>({index:i+1,type:'rehost',segments:Array.from({length:count},(_,j)=>({index:j+1,folder_name:'M'+ordinal++}))}));const a=await create(m);assert.equal(a.files.length,240);assert.equal((await(await admin('/submissions/'+a.id)).json()).maps.length,5)
  assert.equal((await(await admin('/submissions/'+legacyId)).json()).schema_version,1)
 })
 }finally{await mf.dispose()}
})
