import {test} from 'node:test'
import assert from 'node:assert/strict'
import {readFileSync} from 'node:fs'
import {programCounts,recentSeries,profileTeamIdentity,displayDate,mapRatingLabel} from '../src/publicView.ts'

const load=path=>JSON.parse(readFileSync(new URL('../public/data/'+path,import.meta.url),'utf8'))
test('current program summaries and recent series derive only recorded maps without mutating exports',()=>{
 const data=load('seasons/fall-2026.json'),index=load('index.json'),before=JSON.stringify(data)
 assert.deepEqual(programCounts(index.teams,data.matches),{activeTeams:2,maps:9,series:4})
 const recent=recentSeries(data.matches)
 assert.equal(recent.length,4);assert.equal(recent[0].maps[0].team_slug,'white')
 assert.equal(recent[0].maps[0].opponent,'FSU Maroon')
 assert.deepEqual([recent[0].wins,recent[0].losses],[0,2])
 assert.deepEqual([recent[1].wins,recent[1].losses],[2,0])
 assert.equal(JSON.stringify(data),before)
})
test('zero-match future teams do not fabricate records, series, or a new team from asset presence',()=>{
 assert.deepEqual(programCounts([{active:1}],[]),{activeTeams:1,maps:0,series:0})
 assert.deepEqual(recentSeries([]),[])
 assert.equal(load('index.json').teams.length,2)
})
test('recorded series stays keyed to team, season and series with physical map duplicates removed',()=>{
 const map=load('seasons/fall-2026.json').matches[0]
 const matches=[map,map,{...map,id:'future-map',team_slug:'grey',season:'other-season'}]
 assert.deepEqual(programCounts([{active:0}],matches),{activeTeams:0,maps:2,series:2})
 assert.equal(recentSeries(matches,1).length,1)
})
test('profile identity follows actual scoped contributions rather than current membership or sub appearances',()=>{
 const blue={team_slug:'blue',team_name:'UAH Blue',maps:7,rounds:82}
 const white={team_slug:'white',team_name:'UAH White',maps:2,rounds:21}
 assert.deepEqual(profileTeamIdentity([blue]).team,{slug:'blue',name:'UAH Blue'})
 assert.equal(profileTeamIdentity([blue,white]).team,undefined)
 assert.equal(profileTeamIdentity([blue,blue,white]).teams.length,2)
 assert.deepEqual(profileTeamIdentity([{...white,maps:0,rounds:0}]),{teams:[],team:undefined})
})
test('map Rating labels require explicit trusted eligibility and never infer it from a score',()=>{
 assert.equal(mapRatingLabel({rating_eligible:true,rating_version:'siege_style_v3'}),'Rating eligible')
 for(const map of [{},{rating_eligible:false,rating_version:'siege_style_v3'},{rating_eligible:true,rating_version:'old'}])assert.equal(mapRatingLabel(map),'Unrated map')
})
test('date presentation preserves the exact exported day across viewer timezones',()=>{
 assert.equal(displayDate('2026-10-07'),'Oct 7, 2026')
 assert.equal(displayDate('unknown'),'unknown')
})
