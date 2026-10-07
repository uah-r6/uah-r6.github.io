import {test} from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import {embedSeason,ratingHistory,seriesGroups,sortedPlayers,columns} from '../src/presentation.ts'
const profile=JSON.parse(fs.readFileSync(new URL('../public/data/players/lgon/fall-2026.json',import.meta.url)))

test('embed independently follows active season and validates explicit overrides',()=>{
 const seasons=[{slug:'fall-2026'},{slug:'spring-2027'}]
 assert.equal(embedSeason(seasons,'fall-2026',null),'fall-2026')
 assert.equal(embedSeason(seasons,'spring-2027',null),'spring-2027')
 assert.equal(embedSeason(seasons,'spring-2027','fall-2026'),'fall-2026')
 assert.equal(embedSeason(seasons,null,null),null)
 assert.equal(embedSeason(seasons,'spring-2027','missing'),null)
})
test('trend keeps exact exported v3 values, chronology and eligibility',()=>{
 const copy=structuredClone(profile.matches),points=ratingHistory(copy)
 assert.equal(points.length,4)
 assert.deepEqual(points.map(p=>p.id),['d64d5478cdb3','076d2b6b02bc','8af0a6db6c39','9db26f1b6ca7'])
 for(const p of points)assert.equal(p.rating,profile.matches.find(m=>m.id===p.id).rating)
 assert.deepEqual(copy,profile.matches)
 assert.equal(ratingHistory([{...copy[0],rating:null}]).length,0)
 assert.equal(ratingHistory([{...copy[0],rating:0}])[0].rating,0) // valid numeric zero is not fabricated
 assert.equal(ratingHistory([{...copy[0],rating:NaN}]).length,0)
 assert.equal(ratingHistory([{...copy[0],rating_version:'collegiate_v1'}]).length,0)
 assert.equal(ratingHistory([copy[0]]).length,1)
})
test('career history combines teams and seasons without separate synthetic series',()=>{
 const maps=[{...profile.matches[0],id:'new',team_slug:'white',season:'spring-2027',date:'2027-02-01'},profile.matches.at(-1)]
 assert.deepEqual(ratingHistory(maps).map(m=>m.team_slug),['blue','white'])
})
test('series records use authoritative ID, scope and logical maps once',()=>{
 const groups=seriesGroups([...profile.matches,profile.matches[0]])
 assert.equal(groups.length,3);assert.equal(groups[0].maps.length,2)
 assert.deepEqual(groups.map(g=>[g.wins,g.losses]),[[2,0],[2,0],[2,1]])
 const map=profile.matches[0]
 assert.equal(seriesGroups([map,{...map,team_slug:'white'},{...map,season:'spring-2027'}]).length,3)
})
test('shared columns retain correct display and filter historical Alumni',()=>{
 assert.deepEqual(columns.map(c=>c.label),['Rating','KOST','K-D','Entry','KPR','SRV','HS%','Plants','1vX'])
 assert.equal(columns.find(c=>c.key==='rating').format(profile),profile.rating.toFixed(2))
 const players=[{...profile,slug:'active'},{...profile,slug:'alumni',status:'Alumni',rating:2},{...profile,slug:'unrated',rating:null}]
 assert.deepEqual(sortedPlayers(players,'rating',true).map(p=>p.slug),['active','unrated'])
 assert.equal(sortedPlayers(players,'rating',true,true).length,3)
 assert.equal(sortedPlayers(players,'rating',true,false,true).length,3)
 assert.equal(sortedPlayers(players,'rating',false,true).at(-1).slug,'unrated')
})
