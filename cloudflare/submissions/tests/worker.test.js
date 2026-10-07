import {test} from 'node:test'
import assert from 'node:assert/strict'
import {readFile} from 'node:fs/promises'
import {createHash} from 'node:crypto'
import {Miniflare} from 'miniflare'
import {safeName} from '../src/validation.js'

const replay=Buffer.from('dissect\0fixture replay bytes for transfer tests')
const digest=b=>createHash('sha256').update(b).digest('hex')
const manifest=(extra={})=>({team_slug:'blue',season_slug:'fall-2026',opponent:'Fixture opponent',match_date:'2026-10-07',submitter:'TEST',discord:'',notes:'',rehost:'unsure',confirmed:true,folders:[{name:'Match-2026-10-07_12-00-00',files:[{name:'TEST-R01.rec',size:replay.length,sha256:digest(replay)}]}],...extra})

test('real Worker / D1 / R2 intake lifecycle and security',async t=>{
 const mf=new Miniflare({modules:true,modulesRules:[{type:'ESModule',include:['**/*.js']}],scriptPath:new URL('../src/worker.js',import.meta.url).pathname.replace(/^\/([A-Z]:)/,'$1'),compatibilityDate:'2026-07-30',d1Databases:['DB'],r2Buckets:['INBOX'],bindings:{PUBLIC_ORIGIN:'https://uah-r6.github.io',ADMIN_SECRET:'test-admin-only',IP_SALT:'test-salt-only',SUBMISSIONS_ENABLED:'true',STORAGE_CAP_BYTES:'9663676416',RETENTION_DAYS:'7'}})
 try{
 const db=await mf.getD1Database('DB'),bucket=await mf.getR2Bucket('INBOX')
 const schema=await readFile(new URL('../migrations/0001_inbox.sql',import.meta.url),'utf8')
 await db.batch(schema.match(/\s*CREATE TRIGGER[\s\S]+?\nEND;|[^;]+;/gi).map(sql=>db.prepare(sql)))
 const request=(path,method='GET',data,headers={})=>mf.dispatchFetch('https://test.invalid/v1'+path,{method,headers:{Origin:'https://uah-r6.github.io','CF-Connecting-IP':'192.0.2.1',...(data?{'Content-Type':'application/json'}:{}),...headers},body:data?JSON.stringify(data):undefined})
 const admin=(path,method='GET',data)=>request('/admin'+path,method,data,{Authorization:'Bearer test-admin-only'})
 const create=async data=>{const r=await request('/submissions','POST',data||manifest());const d=await r.json();assert.equal(r.status,201,JSON.stringify(d));return d}
 const upload=async(s,bytes=replay)=>{const f=s.files[0];return mf.dispatchFetch(`https://test.invalid/v1/uploads/${s.id}/files/${f.id}`,{method:'PUT',headers:{Authorization:'Bearer '+s.upload_token,'Content-Length':String(bytes.length),Origin:'https://uah-r6.github.io'},body:bytes})}
 const complete=async s=>{let d;do{const r=await request(`/uploads/${s.id}/complete`,'POST',{}, {Authorization:'Bearer '+s.upload_token});d=await r.json();assert.equal(r.status,200,JSON.stringify(d))}while(!d.received);return d}
 await t.test('CORS, no public lists, admin auth and input validation',async()=>{
  assert.equal((await request('/admin/storage')).status,401)
  assert.equal((await request('/submissions')).status,404)
  const cors=await request('/config','OPTIONS');assert.equal(cors.headers.get('Access-Control-Allow-Origin'),'https://uah-r6.github.io')
  assert.equal((await request('/config','GET',undefined,{Origin:'https://evil.invalid'})).status,403)
  for(const extra of [{team_slug:'fake'},{season_slug:'fake'},{match_date:'2026-02-31'},{website:'bot'},{confirmed:false}])assert.equal((await request('/submissions','POST',manifest(extra))).status,400)
  for(const name of ['../x.rec','C:\\x.rec','CON.rec','x.exe','x.rec.','x\0.rec'])assert.throws(()=>safeName(name,true))
 })
 let s
 await t.test('reservation, streamed R2 checksum validation, completion and private download',async()=>{
  s=await create();const before=await (await admin('/storage')).json();assert.equal(before.reserved_bytes,replay.length)
  assert.equal((await request(`/uploads/${s.id}`,'GET',undefined,{Authorization:'Bearer wrong'})).status,401)
  assert.equal((await upload(s,Buffer.alloc(replay.length))).status,400)
  const put=await upload(s);assert.equal(put.status,200,await put.text())
  assert.equal((await complete(s)).received,true)
  const stored=await(await admin('/storage')).json();assert.equal(stored.stored_bytes,replay.length);assert.equal(stored.reserved_bytes,0)
  const list=await(await admin('/submissions')).json();assert.equal(list.length,1);assert.equal(list[0].status,'pending');assert.ok(!JSON.stringify(list).includes('token_hash'))
  const download=await admin(`/submissions/${s.id}/files/${s.files[0].id}`);assert.deepEqual(Buffer.from(await download.arrayBuffer()),replay)
 })
 await t.test('reconciliation counts unknown real objects and preserves pending files',async()=>{
  await bucket.put('orphan-test',Buffer.from('orphan'))
  let r;do{r=await(await admin('/reconcile','POST',{})).json()}while(!r.complete)
  assert.equal(r.stored_bytes,replay.length+6)
  await admin('/cleanup','POST',{});assert.ok(await bucket.get('orphan-test'))
  const d=await(await admin(`/submissions/${s.id}`)).json();assert.equal(d.status,'pending')
  await bucket.delete('orphan-test')
 })
 await t.test('verified archive receipt, idempotency, seven-day retention and terminal purge',async()=>{
  await admin(`/submissions/${s.id}/review`,'POST',{})
  const receipt={map_id:'123456789abc',folder_ids:[s.files[0].folder_id],team_slug:'blue',season_slug:'fall-2026',archive_verified:false}
  assert.equal((await admin(`/submissions/${s.id}/consume`,'POST',receipt)).status,400)
  receipt.archive_verified=true
  assert.equal((await(await admin(`/submissions/${s.id}/consume`,'POST',receipt)).json()).status,'imported')
  assert.equal((await admin(`/submissions/${s.id}/consume`,'POST',receipt)).status,200)
  await admin('/cleanup','POST',{});assert.equal((await bucket.list()).objects.length,1)
  await db.prepare('UPDATE submissions SET terminal_at=1 WHERE id=?').bind(s.id).run()
  await admin('/cleanup','POST',{});assert.equal((await bucket.list()).objects.length,0)
  assert.equal((await admin(`/submissions/${s.id}/purge`,'POST',{confirm_display_id:s.display_id,delete_metadata:true})).status,200)
 })
 await t.test('concurrent reservations never exceed the cap; display IDs stay unique',async()=>{
  await db.prepare('UPDATE storage SET stored_bytes=9663676416-? WHERE id=1').bind(replay.length).run()
  const replies=await Promise.all([request('/submissions','POST',manifest()),request('/submissions','POST',manifest())])
  assert.deepEqual(replies.map(r=>r.status).sort(),[201,507])
  const accepted=await replies.find(r=>r.status===201).json();const state=await db.prepare('SELECT * FROM storage').first();assert.ok(state.stored_bytes+state.reserved_bytes<=state.cap_bytes)
  await db.prepare('UPDATE submissions SET expires_at=1 WHERE id=?').bind(accepted.id).run()
  await admin('/cleanup','POST',{})
  assert.equal((await db.prepare('SELECT reserved_bytes FROM storage').first()).reserved_bytes,0)
  await db.prepare('UPDATE storage SET stored_bytes=0').run()
  const existing=await db.prepare('SELECT * FROM submissions WHERE id=?').bind(accepted.id).first()
  await assert.rejects(db.prepare(`INSERT INTO submissions SELECT ?,display_id,team_slug,team_name,season_slug,season_name,opponent,match_date,submitter,discord,rehost,notes,status,created_at,submitted_at,terminal_at,objects_deleted_at,expires_at,token_hash,declared_bytes,reserved_bytes,actual_bytes,verify_cursor,review_reason,admin_notes,cleanup_lease_until FROM submissions WHERE id=?`).bind(crypto.randomUUID(),existing.id).run())
 })
 await t.test('expired capability, abandoned cleanup, rejection, disabled service and rate limit',async()=>{
  await db.exec('DELETE FROM rate_limits')
  const q=await create();await db.prepare('UPDATE submissions SET expires_at=1 WHERE id=?').bind(q.id).run()
  assert.equal((await upload(q)).status,410);await admin('/cleanup','POST',{});assert.equal((await db.prepare('SELECT reserved_bytes FROM storage').first()).reserved_bytes,0)
  const a=await create();await upload(a);await complete(a)
  const rejected=await(await admin(`/submissions/${a.id}/reject`,'POST',{reason:'Safe fixture rejection'})).json();assert.equal(rejected.status,'rejected')
  assert.equal((await admin(`/submissions/${a.id}/purge`,'POST',{confirm_display_id:'wrong'})).status,409)
  assert.equal((await admin(`/submissions/${a.id}/purge`,'POST',{confirm_display_id:a.display_id})).status,200)
  await admin('/settings','POST',{enabled:false});assert.equal((await request('/submissions','POST',manifest())).status,503);await admin('/settings','POST',{enabled:true})
  await db.exec('DELETE FROM rate_limits')
  for(let i=0;i<5;i++)assert.equal((await request('/submissions','POST',manifest())).status,201)
  assert.equal((await request('/submissions','POST',manifest())).status,429)
  assert.ok((await db.prepare('SELECT hash FROM rate_limits WHERE hash!=?').bind('global').first()).hash.length===64)
 })
 await t.test('full inventory batching, paginated reconciliation and maintenance serialization',async()=>{
  await db.exec('DELETE FROM rate_limits')
  const many=await create(manifest({folders:Array.from({length:12},(_,i)=>({name:'Match-'+i,files:Array.from({length:20},(_,j)=>({name:`Replay-R${String(j+1).padStart(2,'0')}.rec`,size:replay.length,sha256:digest(replay)}))}))}))
  assert.equal(many.files.length,240)
  // Simulate an R2 write that succeeded before the Worker acknowledged D1.
  const first=await db.prepare('SELECT * FROM files WHERE id=?').bind(many.files[0].id).first()
  await bucket.put(first.object_key,replay,{customMetadata:{sha256:digest(replay)}})
  for(let i=0;i<35;i++)await bucket.put('orphan-'+i,replay)
  const page=await admin('/reconcile','POST',{});assert.equal(page.status,200);assert.equal((await page.json()).complete,false)
  assert.equal((await admin('/cleanup','POST',{})).status,409)
  const simultaneous=await Promise.all([admin('/reconcile','POST',{}),admin('/reconcile','POST',{})])
  assert.ok(simultaneous.every(r=>[200,409].includes(r.status)))
  await db.prepare('UPDATE maintenance SET owner=?,expires=? WHERE id=1').bind('fixture-lock',Math.floor(Date.now()/1000)+60).run()
  assert.equal((await admin('/reconcile','POST',{})).status,409)
  await db.prepare('UPDATE maintenance SET owner=NULL,expires=0 WHERE id=1').run()
  let done;do{const r=await admin('/reconcile','POST',{});assert.equal(r.status,200);done=await r.json()}while(!done.complete)
  assert.equal(done.stored_bytes,36*replay.length)
  const recovered=await db.prepare('SELECT * FROM files WHERE id=?').bind(first.id).first();assert.equal(recovered.status,'uploaded')
  assert.equal(done.reserved_bytes,(240+5)*replay.length-replay.length)
  await bucket.delete((await bucket.list()).objects.map(o=>o.key))
  do{done=await(await admin('/reconcile','POST',{})).json()}while(!done.complete)
  assert.equal(done.stored_bytes,0)
  assert.equal((await db.prepare('SELECT status FROM files WHERE id=?').bind(first.id).first()).status,'waiting')
 })
 await t.test('checksum mismatch, missing object and mixed imported/rejected folder lifecycle',async()=>{
  await db.exec('DELETE FROM rate_limits')
  const a=await create(manifest({folders:[{name:'Segment-1',files:[{name:'Replay-R01.rec',size:replay.length,sha256:digest(replay)}]},{name:'Segment-2',files:[{name:'Replay-R02.rec',size:replay.length,sha256:digest(replay)}]}]}))
  const changed=Buffer.from(replay);changed[changed.length-1]^=1
  assert.equal((await upload(a,changed)).status,400)
  for(const file of a.files){assert.equal((await mf.dispatchFetch(`https://test.invalid/v1/uploads/${a.id}/files/${file.id}`,{method:'PUT',headers:{Authorization:'Bearer '+a.upload_token,'Content-Length':String(replay.length)},body:replay})).status,200)}
  const f=await db.prepare('SELECT * FROM files WHERE id=?').bind(a.files[0].id).first();await bucket.delete(f.object_key)
  assert.equal((await request(`/uploads/${a.id}/complete`,'POST',{}, {Authorization:'Bearer '+a.upload_token})).status,409)
  await bucket.put(f.object_key,replay,{customMetadata:{sha256:digest(replay)}});await complete(a)
  const receipt={map_id:'abcdef123456',folder_ids:[a.files[0].folder_id],team_slug:'blue',season_slug:'fall-2026',archive_verified:true}
  assert.equal((await(await admin(`/submissions/${a.id}/consume`,'POST',receipt)).json()).status,'reviewing')
  const rejected=await(await admin(`/submissions/${a.id}/reject`,'POST',{reason:'Other segment was a scrim'})).json()
  assert.equal(rejected.status,'imported');assert.deepEqual(rejected.folders.map(f=>f.disposition),['imported','rejected'])
  await admin(`/submissions/${a.id}/purge`,'POST',{confirm_display_id:a.display_id})
 })
 await t.test('concurrent archive receipts cannot claim the same folder for different maps',async()=>{
  await db.exec('DELETE FROM rate_limits')
  const s=await create();await upload(s);await complete(s)
  const receipt={folder_ids:[s.files[0].folder_id],team_slug:'blue',season_slug:'fall-2026',archive_verified:true}
  const results=await Promise.all(['111111111111','222222222222'].map(map_id=>admin(`/submissions/${s.id}/consume`,'POST',{...receipt,map_id})))
  assert.deepEqual(results.map(r=>r.status).sort(),[200,409])
  const d=await(await admin(`/submissions/${s.id}`)).json();assert.equal(d.status,'imported');assert.ok(['111111111111','222222222222'].includes(d.folders[0].map_id))
 })
 }finally{await mf.dispose()}
})
