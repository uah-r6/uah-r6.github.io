import {test} from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import {seriesRatingHistory,completeSeriesRating,sortedPlayers} from '../src/presentation.ts'
const load=path=>JSON.parse(fs.readFileSync(new URL('../public/data/'+path,import.meta.url)))

test('complete coverage requires every player-specific map and round, with nonzero participation',()=>{
 const p=load('players/lgon/fall-2026.json').series_ratings[0]
 const before=structuredClone(p)
 assert.equal(completeSeriesRating(p),true)
 for(const changed of [{rating_maps:1},{rating_rounds:19},{maps:0,rating_maps:0},{rounds:0,rating_rounds:0},{rating_maps:3},{rating_rounds:21}])assert.equal(completeSeriesRating({...p,...changed}),false)
 assert.deepEqual(p,before)
})

test('only complete series become chronological points; incomplete records and all map history remain',()=>{
 const profile=load('players/lgon/fall-2026.json'),points=seriesRatingHistory(profile.series_ratings)
 assert.equal(points.length,1)
 assert.deepEqual(points.map(s=>s.opponent),['UCF'])
 assert.equal(profile.series_ratings.length,3)
 for(const point of profile.series_ratings){
  const series=load(`series/${point.id}.json`),player=series.players.find(p=>p.slug==='lgon')
  assert.equal(point.rating,player.rating)
  assert.equal(point.rating_maps,player.rating_maps)
  assert.equal(point.rounds,player.rounds)
  assert.equal(point.rating!==null,completeSeriesRating(point))
 }
 assert.equal(profile.matches.length,7)
 assert.equal(profile.matches.filter(m=>m.rating!==null).length,4)
})

test('incomplete Series Ratings are null with exact coverage; UCF still aggregates trusted inputs',()=>{
 const profile=load('players/lgon/fall-2026.json')
 const rows=[...profile.series_ratings].reverse()
 assert.deepEqual(rows.map(s=>[s.rating_maps,s.maps,s.rating_rounds,s.rounds]),[[1,3,10,38],[1,2,12,24],[2,2,20,20]])
 assert.equal(rows[0].rating,null);assert.equal(rows[1].rating,null)
 const ucf=rows.at(-1),maps=profile.matches.filter(m=>m.series_id===ucf.id)
 assert.equal(ucf.rating,1.4156752657694631)
 assert.ok(Math.abs(ucf.rating-maps.reduce((n,m)=>n+m.rating,0)/maps.length)>.01)
})

test('stale numeric incomplete exports cannot re-enter trend controls',()=>{
 const point=load('players/lgon/fall-2026.json').series_ratings[0]
 assert.equal(seriesRatingHistory([{...point,rating_maps:1}]).length,0)
 assert.equal(seriesRatingHistory([{...point,rating_rounds:19}]).length,0)
 assert.equal(seriesRatingHistory([point,{...point,id:'next',series_id:'next',date:'2026-10-08'}]).length,2)
})

test('White complete player and substitute Series Ratings remain numeric and isolated',()=>{
 const series=load('series/ada4becd7c74.json'),profile=load('players/flex-uah/fall-2026.json')
 assert.equal(seriesRatingHistory(profile.series_ratings).length,1)
 for(const p of series.players){assert.equal(completeSeriesRating(p),true);assert.equal(typeof p.rating,'number')}
 const sub=series.players.find(p=>p.appearance_role==='sub')
 assert.ok(sub)
 assert.equal(load(`players/${sub.slug}/fall-2026.json`).series_ratings.length,0)
})

test('unrated, invalid and wrong-version series do not become fabricated zero points',()=>{
 const point=load('players/lgon/fall-2026.json').series_ratings[0]
 assert.equal(seriesRatingHistory([{...point,rating:null}]).length,0)
 assert.equal(seriesRatingHistory([{...point,rating_rounds:0,rating_maps:0,rating:0}]).length,0)
 assert.equal(seriesRatingHistory([{...point,rating:NaN}]).length,0)
 assert.equal(seriesRatingHistory([{...point,rating_version:'siege_style_v2'}]).length,0)
 assert.equal(seriesRatingHistory([]).length,0)
 assert.equal(seriesRatingHistory([point]).length,1)
 assert.equal(seriesRatingHistory([point,point]).length,1)
})
test('season/career series history handles team moves with exact data and no synthetic lines',()=>{
 const point=load('players/lgon/fall-2026.json').series_ratings[0]
 const future={...point,id:'future',series_id:'future',season:'spring-2027',date:'2027-02-01',team_slug:'white',team_name:'UAH White'}
 assert.deepEqual(seriesRatingHistory([future,point]).map(s=>s.team_slug),['blue','white'])
 assert.equal(seriesRatingHistory([point]).length,1)
})
test('Series Player Stats keep unrated and historical Alumni participants visible below rated players',()=>{
 const series=load('series/40bf93b16f97.json'),unrated={...series.players[0],slug:'sub',status:'Alumni',rating:null,rating_maps:0,rating_rounds:0}
 const sorted=sortedPlayers([...series.players,unrated],'rating',true,false,true)
 assert.equal(sorted.at(-1).slug,'sub')
 assert.equal(sorted.length,6)
})
