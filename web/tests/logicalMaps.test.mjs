import {test} from 'node:test'
import assert from 'node:assert/strict'
import {resizeMaps,changeMapType,validateMaps,hierarchy,assignments,selectedFolders,fileTimes,timeLabel,chronological} from '../src/logicalMaps.ts'
const folder=(name,size=32,time=1791400000000)=>({name,bytes:size,files:[{name:'Game-R01.rec',size,lastModified:time}]})
const candidates=Array.from({length:13},(_,i)=>folder('F'+i))
const normal=(...names)=>names.map(name=>({type:'normal',folders:[name]}))
test('one/two normal, BO3/BO5, normal plus two/three part rehost and separate rehosts',()=>{
 for(const maps of [normal('F0'),normal('F0','F1'),normal('F0','F1','F2'),normal('F0','F1','F2','F3','F4'),[...normal('F0'),{type:'rehost',folders:['F1','F2']}],[...normal('F0'),{type:'rehost',folders:['F1','F2','F3']}],[{type:'rehost',folders:['F0','F1']},{type:'rehost',folders:['F2','F3']}],[{type:'unsure',folders:['F0','F1']}]]){
  assert.equal(validateMaps(maps,candidates).folders,maps.reduce((n,m)=>n+m.folders.length,0));assert.equal(hierarchy(maps).length,maps.length)
 }
})
test('resize preserves existing maps; map-specific validation blocks incomplete, duplicate and wrong-type assignments',()=>{
 const maps=normal('F0','F1');assert.deepEqual(resizeMaps(maps,5).slice(0,2),maps);assert.deepEqual(resizeMaps(maps,1),maps.slice(0,1));assert.throws(()=>resizeMaps(maps,6))
 for(const [maps,pattern] of [[normal(''),/Map 1/],[[{type:'rehost',folders:['F0']}],/Map 1/],[normal('F0','F0'),/Map 2.*Map 1/],[[{type:'normal',folders:['F0','F1']}],/exactly one/],[normal('unknown'),/Map 1/]])assert.throws(()=>validateMaps(maps,candidates),pattern)
 assert.equal(assignments(normal('F0')).F0,'Map 1')
})
test('normal to rehost keeps Part 1; ordered manifest and selection follow manual reorder',()=>{
 assert.deepEqual(changeMapType(normal('F0')[0],'rehost'),{type:'rehost',folders:['F0','']})
 const maps=[{type:'rehost',folders:['F2','F1','F0']}];assert.deepEqual(selectedFolders(maps,candidates).map(f=>f.name),['F2','F1','F0']);assert.deepEqual(hierarchy(maps)[0].segments.map(p=>[p.index,p.folder_name]),[[1,'F2'],[2,'F1'],[3,'F0']]);assert.deepEqual(changeMapType(maps[0],'normal'),{type:'normal',folders:['F2']})
})
test('all map limits apply to combined selection',()=>{
 assert.throws(()=>validateMaps([{type:'rehost',folders:candidates.map(f=>f.name)}],candidates),/12/)
 assert.throws(()=>validateMaps(normal('F0','F1'),[folder('F0',64*1024**2+1),folder('F1')]),/64 MiB/)
 const many=[{...folder('F0'),files:Array.from({length:241},(_,i)=>({name:`R${i}.rec`,size:32,lastModified:1}))}];assert.throws(()=>validateMaps(normal('F0'),many),/240/)
})
test('file times show valid ranges, tolerate missing/invalid timestamps and sort oldest first',()=>{
 const times=fileTimes([{lastModified:1791400000000},{lastModified:1791400600000},{lastModified:NaN},{lastModified:0}]);assert.ok(times.first_file_modified_at<times.last_file_modified_at);assert.match(timeLabel(times.first_file_modified_at,times.last_file_modified_at),/–/);assert.equal(timeLabel('bad'),'File time unavailable');assert.equal(timeLabel(null),'File time unavailable');assert.deepEqual(fileTimes([{lastModified:NaN},{lastModified:-1}]),{first_file_modified_at:null,last_file_modified_at:null});assert.deepEqual(chronological([folder('new',32,2000),folder('unknown',32,0),folder('old',32,1000)]).map(f=>f.name),['old','new','unknown'])
})
