export const LIMITS={fileBytes:64*1024**2,submissionBytes:2*1024**3,folders:12,files:240,sessionSeconds:7200}
export class HttpError extends Error {constructor(status,message){super(message);this.status=status}}
export function requireValue(condition,message,status=400){if(!condition)throw new HttpError(status,message)}
export function safeName(value,extension=false){
 requireValue(typeof value==='string'&&value.length>0&&value.length<=160,'Invalid replay filename.')
 requireValue(!/[<>:"/\\|?*\x00-\x1f\x7f]/.test(value)&&!/[. ]$/.test(value)&&value!=='.'&&value!=='..','Unsafe replay filename.')
 requireValue(!/^(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\.|$)/i.test(value),'Reserved replay filename.')
 if(extension)requireValue(/\.rec$/i.test(value),'Only .rec replay files are accepted.')
 return value
}
function text(value,max,required=false){requireValue(typeof value==='string'&&value.length<=max&&!/[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]/.test(value),'Invalid submission text.');requireValue(!required||value.trim().length>0,'Complete the required fields.');return value.trim()}
export function validateHierarchy(maps,folders,key='folder_name',maxMaps=5){
 requireValue(Array.isArray(maps)&&maps.length>=1&&maps.length<=maxMaps,'Choose a valid logical map count.')
 const ids=new Set(folders),used=new Set()
 const result=maps.map((m,i)=>{
  requireValue(m&&m.index===i+1,`Map ${i+1} has an invalid or duplicate index.`)
  requireValue(['normal','rehost','unsure'].includes(m.type),`Map ${i+1} has an invalid type.`)
  requireValue(Array.isArray(m.segments)&&m.segments.length>0&&m.segments.length<=LIMITS.folders,`Map ${i+1} needs replay folders.`)
  requireValue(m.type!=='normal'||m.segments.length===1,`Map ${i+1} is Normal and needs exactly one folder.`)
  requireValue(m.type!=='rehost'||m.segments.length>=2,`Map ${i+1} is Rehosted and needs at least two parts.`)
  const segments=m.segments.map((s,j)=>{
   requireValue(s&&s.index===j+1,`Map ${i+1} Part ${j+1} has an invalid index.`)
   requireValue(ids.has(s[key]),`Map ${i+1} Part ${j+1} refers to an unknown folder.`)
   requireValue(!used.has(s[key]),`Map ${i+1} Part ${j+1} repeats an assigned folder.`);used.add(s[key])
   return {index:j+1,[key]:s[key]}
  })
  return {index:i+1,type:m.type,segments}
 })
 requireValue(used.size===ids.size,'Every uploaded folder must belong to exactly one logical map.')
 return result
}
export function reviewedHierarchy(maps,folders){
 const result=validateHierarchy(maps,folders.map(f=>f.id),'folder_id',12),ids=new Set()
 return result.map((m,i)=>{
  const id=maps[i].id
  requireValue(typeof id==='string'&&/^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/.test(id)&&!ids.has(id),'Invalid reviewed map identity.')
  ids.add(id);return {id,...m}
 })
}
function fileTime(value){
 if(value==null)return null
 requireValue(typeof value==='string'&&/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z$/.test(value)&&Number.isFinite(Date.parse(value))&&new Date(value).toISOString()===value,'Invalid private file timestamp.')
 return value
}
export function validateManifest(body,options){
 requireValue(body&&typeof body==='object'&&!body.website,'Submission could not be accepted.')
 const team=options.teams.find(t=>t.slug===body.team_slug),season=options.seasons.find(s=>s.slug===body.season_slug)
 requireValue(team&&season,'Choose an available UAH team and season.')
 const version=body.schema_version??1
 requireValue(version===1||version===2,'Unsupported submission schema.')
 if(version===1)requireValue(['no','yes','unsure'].includes(body.rehost),'Choose a rehost status.')
 const date=new Date(body.match_date+'T12:00:00Z')
 requireValue(/^\d{4}-\d{2}-\d{2}$/.test(body.match_date)&&Number.isFinite(date.getTime())&&date.toISOString().slice(0,10)===body.match_date,'Choose a valid match date.')
 requireValue(body.confirmed===true,'Confirm the selected team, season and replay files.')
 requireValue(Array.isArray(body.folders)&&body.folders.length>0&&body.folders.length<=LIMITS.folders,'Select 1–12 replay folders.')
 let bytes=0,count=0;const names=new Set()
 const folders=body.folders.map(f=>{
  const name=safeName(f.name);requireValue(!names.has(name.toLowerCase()),'Duplicate replay folder name.');names.add(name.toLowerCase())
  requireValue(Array.isArray(f.files)&&f.files.length>0,'A replay folder has no files.')
  const filesSeen=new Set()
  const files=f.files.map(p=>{
   const filename=safeName(p.name,true);requireValue(!filesSeen.has(filename.toLowerCase()),'Duplicate replay filename.');filesSeen.add(filename.toLowerCase())
   requireValue(Number.isSafeInteger(p.size)&&p.size>=16&&p.size<=LIMITS.fileBytes,'Each replay file must be between 16 bytes and 64 MiB.')
   requireValue(typeof p.sha256==='string'&&/^[a-f0-9]{64}$/.test(p.sha256),'Invalid replay checksum.')
   bytes+=p.size;count++;return {name:filename,size:p.size,sha256:p.sha256}
  });
  const first=fileTime(f.first_file_modified_at),last=fileTime(f.last_file_modified_at)
  requireValue((first===null&&last===null)||(first!==null&&last!==null&&first<=last),'Invalid private file timestamp range.')
  return {name,files,first_file_modified_at:first,last_file_modified_at:last}
 })
 requireValue(count<=LIMITS.files&&bytes<=LIMITS.submissionBytes,'A submission can contain at most 240 files and 2 GiB.')
 const maps=version===2?validateHierarchy(body.maps,folders.map(f=>f.name)):[]
 return {team,season,folders,maps,schema_version:version,bytes,opponent:text(body.opponent,120,true),submitter:text(body.submitter,80,true),discord:text(body.discord||'',80),notes:text(body.notes||'',2000),date:body.match_date,rehost:version===1?body.rehost:'unsure'}
}
