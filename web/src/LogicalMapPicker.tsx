import {bytesLabel,type ReplayFolder} from './replayFiles'
import {assignments,changeMapType,chronological,fileTimes,resizeMaps,timeLabel,type MapSelection,type SubmittedMapType} from './logicalMaps'

export function MapCountControl({maps,onChange,disabled=false}:{maps:MapSelection[];onChange(maps:MapSelection[]):void;disabled?:boolean}){
 function count(value:number){
  if(value<maps.length&&maps.slice(value).some(m=>m.folders.some(Boolean))&&!window.confirm('Remove these maps and their folder assignments? Discovered folders remain available.'))return
  onChange(resizeMaps(maps,value))
 }
 return <label className="map-count-control">How many maps are you submitting?<select value={maps.length} disabled={disabled} onChange={e=>count(Number(e.target.value))}>{[1,2,3,4,5].map(n=><option key={n} value={n}>{n}</option>)}</select></label>
}

export function LogicalMapPicker({maps,folders,onChange,disabled=false}:{maps:MapSelection[];folders:ReplayFolder<File>[];onChange(maps:MapSelection[]):void;disabled?:boolean}){
 const used=assignments(maps),ordered=chronological(folders)
 const edit=(i:number,map:MapSelection)=>onChange(maps.map((m,j)=>j===i?map:m))
 function type(i:number,value:SubmittedMapType){
  if(value==='normal'&&maps[i].folders.slice(1).some(Boolean)&&!window.confirm(`Change Map ${i+1} to Normal? Keep Part 1 and release the other folder assignments.`))return
  edit(i,changeMapType(maps[i],value))
 }
 return <section className="logical-map-picker" aria-labelledby="logical-map-title">
  <h2 id="logical-map-title">Organize your maps</h2><p>Organize replay folders by map. For a rehost, add each part in the order it was played. The administrator verifies every replay before importing statistics.</p>
  {maps.map((map,i)=><section className="logical-map-card" key={i} aria-labelledby={`logical-map-${i}`}><h3 id={`logical-map-${i}`}>Map {i+1}</h3>
   <label>Map {i+1} type<select value={map.type} disabled={disabled} onChange={e=>type(i,e.target.value as SubmittedMapType)}><option value="normal">Normal</option><option value="rehost">Rehosted</option><option value="unsure">Not sure</option></select></label>
   {map.type==='unsure'&&<p>Keep the folders you believe belong together. An administrator must classify this map before import.</p>}
   {map.folders.map((name,j)=>{const folder=folders.find(f=>f.name===name),times=folder?fileTimes(folder.files):null;return <div className="logical-part" key={j}>
    <label>{map.type==='normal'?`Map ${i+1} replay folder`:`Map ${i+1} / Part ${j+1}`}<select disabled={disabled} value={name} onChange={e=>edit(i,{...map,folders:map.folders.map((f,k)=>k===j?e.target.value:f)})}><option value="">Choose a discovered folder</option>{ordered.map(f=><option key={f.name} value={f.name} disabled={!!used[f.name]&&f.name!==name}>{timeLabel(fileTimes(f.files).first_file_modified_at)} / {f.name}{used[f.name]&&f.name!==name?` (assigned to ${used[f.name]})`:''}</option>)}</select></label>
    {folder&&<div className="assigned-folder"><b>{timeLabel(times?.first_file_modified_at,times?.last_file_modified_at)}</b><small>{folder.name}</small><span>{folder.files.length} replay files / {bytesLabel(folder.bytes)}</span></div>}
    {map.type!=='normal'&&<div className="part-actions"><button className="button" type="button" disabled={disabled||j===0} aria-label={`Move Map ${i+1} Part ${j+1} up`} onClick={()=>{const next=[...map.folders];[next[j-1],next[j]]=[next[j],next[j-1]];edit(i,{...map,folders:next})}}>Move up</button><button className="button" type="button" disabled={disabled||j===map.folders.length-1} aria-label={`Move Map ${i+1} Part ${j+1} down`} onClick={()=>{const next=[...map.folders];[next[j+1],next[j]]=[next[j],next[j+1]];edit(i,{...map,folders:next})}}>Move down</button><button className="button" type="button" disabled={disabled||map.folders.length<=(map.type==='rehost'?2:1)} aria-label={`Remove Map ${i+1} Part ${j+1}`} onClick={()=>{if(name&&!window.confirm('Release this folder assignment? The discovered folder remains available.'))return;edit(i,{...map,folders:map.folders.filter((_,k)=>k!==j)})}}>Remove part</button></div>}
   </div>})}
   {map.type!=='normal'&&<button className="button" type="button" disabled={disabled||maps.reduce((n,m)=>n+m.folders.length,0)>=12} onClick={()=>edit(i,{...map,folders:[...map.folders,'']})}>+ Add {map.type==='rehost'?'rehost part':'folder'} to Map {i+1}</button>}
  </section>)}
 </section>
}

export function LogicalMapReview({maps,folders}:{maps:MapSelection[];folders:ReplayFolder<File>[]}){
 return <div className="logical-map-review">{maps.map((map,i)=><section className="logical-map-card" key={i}><h3>Map {i+1} / {map.type==='normal'?'Normal':map.type==='rehost'?'Rehosted':'Not sure — administrator review'}</h3><p>{map.folders.length} {map.type==='normal'?'replay folder':'parts'}</p>{map.folders.map((name,j)=>{const f=folders.find(f=>f.name===name)!,times=fileTimes(f.files);return <div className="assigned-folder" key={name}><b>{map.type!=='normal'&&`Part ${j+1} / `}{timeLabel(times.first_file_modified_at,times.last_file_modified_at)}</b><small>{name}</small><span>{f.files.length} replay files / {bytesLabel(f.bytes)}</span></div>})}</section>)}</div>
}
