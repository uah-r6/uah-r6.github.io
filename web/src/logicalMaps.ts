import {validateSelection,type ReplayFile,type ReplayFolder} from './replayFiles.ts'

export type SubmittedMapType='normal'|'rehost'|'unsure'
export type MapSelection={type:SubmittedMapType;folders:string[]}
export const emptyMap=():MapSelection=>({type:'normal',folders:['']})

export function resizeMaps(maps:MapSelection[],count:number){
 if(!Number.isInteger(count)||count<1||count>5)throw Error('Choose between 1 and 5 maps.')
 return Array.from({length:count},(_,i)=>maps[i]||emptyMap())
}
export function changeMapType(map:MapSelection,type:SubmittedMapType):MapSelection{
 if(type==='normal')return {type,folders:[map.folders[0]||'']}
 return {type,folders:[...map.folders,...Array.from({length:Math.max(0,(type==='rehost'?2:1)-map.folders.length)},()=> '')]}
}
export function assignments(maps:MapSelection[]){
 const result:Record<string,string>={}
 maps.forEach((map,i)=>map.folders.forEach((name,j)=>{if(name)result[name]=`Map ${i+1}${map.type==='normal'?'':` / Part ${j+1}`}`}))
 return result
}
export function selectedFolders<T extends ReplayFile>(maps:MapSelection[],folders:ReplayFolder<T>[]){
 return maps.flatMap(map=>map.folders.map(name=>folders.find(f=>f.name===name)).filter((f):f is ReplayFolder<T>=>!!f))
}
export function validateMaps<T extends ReplayFile>(maps:MapSelection[],folders:ReplayFolder<T>[]){
 if(!maps.length||maps.length>5)throw Error('Choose between 1 and 5 maps.')
 const used=new Map<string,string>()
 maps.forEach((map,i)=>{
  if(!['normal','rehost','unsure'].includes(map.type))throw Error(`Map ${i+1} needs a map type.`)
  if(map.type==='normal'&&map.folders.length!==1)throw Error(`Map ${i+1} is Normal and needs exactly one replay folder.`)
  if(map.type==='rehost'&&map.folders.length<2)throw Error(`Map ${i+1} is Rehosted and needs at least 2 parts.`)
  if(!map.folders.length)throw Error(`Map ${i+1} needs a replay folder.`)
  map.folders.forEach((name,j)=>{
   const label=`Map ${i+1} / Part ${j+1}`
   if(!name||!folders.some(f=>f.name===name))throw Error(`${label} needs a replay folder.`)
   if(used.has(name))throw Error(`${label} uses a folder already assigned to ${used.get(name)}.`)
   used.set(name,label)
  })
 })
 return validateSelection(selectedFolders(maps,folders))
}
export function fileTimes(files:ReplayFile[]){
 const values=files.map(f=>f.lastModified).filter(n=>Number.isFinite(n)&&n>0&&n<=253402300799999)
 return {first_file_modified_at:values.length?new Date(Math.min(...values)).toISOString():null,
  last_file_modified_at:values.length?new Date(Math.max(...values)).toISOString():null}
}
export function timeLabel(first:string|null|undefined,last?:string|null){
 const a=first?new Date(first):null,b=last?new Date(last):null
 if(!a||!Number.isFinite(a.getTime()))return 'File time unavailable'
 const format=(d:Date)=>d.toLocaleString(undefined,{year:'numeric',month:'short',day:'numeric',hour:'numeric',minute:'2-digit'})
 return b&&Number.isFinite(b.getTime())&&b.getTime()-a.getTime()>=5*60000?`${format(a)} – ${format(b)}`:format(a)
}
export function chronological<T extends ReplayFile>(folders:ReplayFolder<T>[]){
 const start=(f:ReplayFolder<T>)=>fileTimes(f.files).first_file_modified_at
 return [...folders].sort((a,b)=>{
  const x=start(a),y=start(b);return (x?Date.parse(x):Infinity)-(y?Date.parse(y):Infinity)||a.name.localeCompare(b.name)
 })
}
export function hierarchy(maps:MapSelection[]){
 return maps.map((map,i)=>({index:i+1,type:map.type,segments:map.folders.map((name,j)=>({index:j+1,folder_name:name}))}))
}
