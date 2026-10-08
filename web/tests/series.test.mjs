import {test} from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import {seriesRatingHistory,partialSeriesRating,sortedPlayers} from '../src/presentation.ts'
const load=path=>JSON.parse(fs.readFileSync(new URL('../public/data/'+path,import.meta.url)))

test('partial presentation uses actual player map and round coverage without changing values',()=>{
 const points=seriesRatingHistory(load('players/lgon/fall-2026.json').series_ratings)
 assert.deepEqual(points.map(partialSeriesRating),[true,true,false])
 const p=points[0],before=structuredClone(p)
 assert.equal(partialSeriesRating({...p,maps:1,rating_maps:1,rounds:10,rating_rounds:10}),false)
 assert.equal(partialSeriesRating({...p,maps:1,rating_maps:1,rounds:10,rating_rounds:9}),true)
 assert.deepEqual(p,before)
})

test('one chronological trusted point per series; exact exported values and map history retained',()=>{
 const profile=load('players/lgon/fall-2026.json'),points=seriesRatingHistory(profile.series_ratings)
 assert.equal(points.length,3)
 assert.deepEqual(points.map(s=>s.opponent),['Placements','University of Michigan','UCF'])
 for(const point of points){
  const series=load(`series/${point.id}.json`),player=series.players.find(p=>p.slug==='lgon')
  assert.equal(point.rating,player.rating)
  assert.equal(point.rating_maps,player.rating_maps)
  assert.equal(point.rounds,player.rounds)
 }
 assert.equal(profile.matches.length,7)
 assert.equal(profile.matches.filter(m=>m.rating!==null).length,4)
})
test('partial coverage is player-specific and weighted inputs differ from a map arithmetic mean',()=>{
 const profile=load('players/lgon/fall-2026.json'),points=seriesRatingHistory(profile.series_ratings)
 assert.deepEqual(points.map(s=>[s.rating_maps,s.maps,s.rating_rounds,s.rounds]),[[1,3,10,38],[1,2,12,24],[2,2,20,20]])
 const ucf=points.at(-1),maps=profile.matches.filter(m=>m.series_id===ucf.id)
 assert.ok(Math.abs(ucf.rating-maps.reduce((n,m)=>n+m.rating,0)/maps.length)>.01)
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
