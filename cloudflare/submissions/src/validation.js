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
export function validateManifest(body,options){
 requireValue(body&&typeof body==='object'&&!body.website,'Submission could not be accepted.')
 const team=options.teams.find(t=>t.slug===body.team_slug),season=options.seasons.find(s=>s.slug===body.season_slug)
 requireValue(team&&season,'Choose an available UAH team and season.')
 requireValue(['no','yes','unsure'].includes(body.rehost),'Choose a rehost status.')
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
  });return {name,files}
 })
 requireValue(count<=LIMITS.files&&bytes<=LIMITS.submissionBytes,'A submission can contain at most 240 files and 2 GiB.')
 return {team,season,folders,bytes,opponent:text(body.opponent,120,true),submitter:text(body.submitter,80,true),discord:text(body.discord||'',80),notes:text(body.notes||'',2000),date:body.match_date,rehost:body.rehost}
}
