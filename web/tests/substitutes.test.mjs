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

test('all real current participants remain roster with no fabricated substitute totals',()=>{
 const load=name=>JSON.parse(readFileSync(new URL('../public/data/'+name,import.meta.url)))
 for(const period of ['fall-2026','career'])for(const team of ['blue','white']){
  const data=load(`teams/${team}/${period}.json`)
  assert.deepEqual(data.sub_players,[])
 }
 for(const p of load('index.json').players){
  const profile=load(`players/${p.slug}/career.json`)
  assert.equal(profile.rounds,82)
  assert.deepEqual(profile.sub_teams,[])
  for(const m of profile.matches)for(const player of load(`matches/${m.id}.json`).players)
   assert.equal(player.appearance_role,'roster')
 }
})
