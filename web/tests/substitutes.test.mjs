import {test} from 'node:test'
import assert from 'node:assert/strict'
import {readFileSync} from 'node:fs'
import {sessionPeriod,selectedPeriod,playerScope} from '../src/scope.ts'

test('fresh and days-later visits default to active season, in-session Career survives refresh',()=>{
 const seasons=[{slug:'fall-2026'},{slug:'spring-2027'}],now=100000000
 for(const saved of [null,'career','malformed',JSON.stringify({period:'career',at:now-86400000}),JSON.stringify({period:'career',at:now+1})])
  assert.equal(selectedPeriod(seasons,'fall-2026',sessionPeriod(saved,now)),'fall-2026')
 const saved=JSON.stringify({period:'career',at:now-1000})
 assert.equal(selectedPeriod(seasons,'fall-2026',sessionPeriod(saved,now)),'career')
 assert.equal(selectedPeriod(seasons,'spring-2027',null),'spring-2027')
})

test('appearance query has two isolated scopes with roster as the safe default',()=>{
 for(const value of [null,'','roster','combined','invalid'])assert.equal(playerScope(value),'roster')
 assert.equal(playerScope('subs'),'subs')
 const query=new URLSearchParams('team=white&players=subs')
 assert.equal(playerScope(query.get('players')),'subs')
 assert.equal(query.get('team'),'white')
 query.delete('players')
 assert.equal(playerScope(query.get('players')),'roster')
})

test('current exported participation preserves normal and substitute separation',()=>{
 const load=name=>JSON.parse(readFileSync(new URL('../public/data/'+name,import.meta.url)))
 for(const period of ['fall-2026','career'])for(const team of ['blue','white']){
  const data=load(`teams/${team}/${period}.json`)
  assert.equal(data.players.length,team==='blue'?5:4)
  assert.equal(data.sub_players.length,team==='blue'?0:1)
  for(const player of data.players)assert.equal(player.rounds,team==='blue'?82:21)
  for(const player of data.sub_players){
   assert.equal(player.slug,'dinoted11')
   assert.equal(player.rounds,21)
   assert.equal(player.appearance_role,'sub')
  }
 }
 for(const p of load('index.json').players){
  const profile=load(`players/${p.slug}/career.json`)
  const historical=profile.matches.length>0
  assert.equal(profile.rounds,profile.matches.reduce((total,m)=>total+load(`matches/${m.id}.json`).players.find(row=>row.slug===p.slug&&row.appearance_role==='roster').rounds,0))
  if(!historical){assert.equal(profile.rating,null);assert.equal(profile.kd,null)}
  assert.equal(profile.sub_teams.length,p.slug==='dinoted11'?1:0)
  for(const m of profile.matches)
   assert.equal(load(`matches/${m.id}.json`).players.find(row=>row.slug===p.slug).appearance_role,'roster')
 }
})
