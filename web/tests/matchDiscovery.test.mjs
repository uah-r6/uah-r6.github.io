import test from 'node:test'
import assert from 'node:assert/strict'
import {matchFilters,matchQuery,clearMatchFilters,discoverSeries,opponentSuggestions} from '../src/matchDiscovery.ts'

const teams=[{id:1,slug:'blue',name:'UAH Blue',aliases:['old-blue']},{id:2,slug:'white',name:'UAH White',aliases:[]},{id:3,slug:'future',name:'Future',aliases:[]}]
const map=(id,series,team,opponent,date)=>({id,series_id:series,team_slug:team,team_name:teams.find(t=>t.slug===team).name,opponent,date,season:'fall',result:'WIN'})
const matches=[map('b1','b','blue','UCF','2026-10-06'),map('b2','b','blue','UCF','2026-10-06'),map('w1','w','white','FSU Maroon','2026-10-07'),map('m','m','blue','University of Michigan','2026-09-30')]
const filter=(query='',scoped)=>matchFilters(new URLSearchParams(query),teams,scoped)
const ids=q=>discoverSeries(matches,filter(q)).map(s=>s.maps.map(m=>m.id))

test('global defaults all teams; invalid team/sort sanitized; aliases and future teams resolve',()=>{
  assert.deepEqual(filter(),{team:'',opponent:'',sort:'newest'})
  assert.deepEqual(filter('team=garbage&sort=random'),filter())
  assert.equal(filter('team=old-blue').team,'blue')
  assert.equal(filter('team=future').team,'future')
})
test('team/opponent combined filters preserve entire series',()=>{
  assert.deepEqual(ids(),[['w1'],['b1','b2'],['m']])
  assert.deepEqual(ids('team=blue'),[['b1','b2'],['m']])
  assert.deepEqual(ids('opponent=ucf'),[['b1','b2']])
  assert.deepEqual(ids('team=white&opponent=ucf'),[])
  assert.deepEqual(ids('opponent=%20mIcH%20'),[['m']])
  assert.deepEqual(ids('opponent=nonexistent'),[])
})
test('all useful sorts and deterministic chronological tiebreaks',()=>{
  assert.deepEqual(ids('sort=oldest'),[['m'],['b1','b2'],['w1']])
  assert.deepEqual(ids('sort=team'),[['w1'],['b1','b2'],['m']])
  assert.deepEqual(ids('sort=opponent'),[['w1'],['b1','b2'],['m']])
  assert.deepEqual(ids('team=blue&sort=oldest'),[['m'],['b1','b2']])
})
test('legacy team sorting falls back to newest while team filtering remains intact',()=>{
  assert.equal(filter('sort=team').sort,'newest')
  assert.deepEqual(ids('team=blue&sort=team&opponent=UCF'),[['b1','b2']])
  assert.deepEqual(ids('team=white&sort=team'),[['w1']])
})
test('team scope overrides hostile URL team and suggestions never leak teams',()=>{
  assert.equal(filter('team=white','blue').team,'blue')
  assert.deepEqual(discoverSeries(matches,filter('team=white','blue')).map(s=>s.maps[0].team_slug),['blue','blue'])
  assert.deepEqual(opponentSuggestions(matches,'blue'),['UCF','University of Michigan'])
  assert.deepEqual(opponentSuggestions(matches),['FSU Maroon','UCF','University of Michigan'])
})
test('share/refresh URL roundtrip; clear preserves period and unrelated context',()=>{
  const query=matchQuery(new URLSearchParams('extra=keep'),filter('team=blue&opponent=UCF&sort=oldest'),'career')
  assert.deepEqual(filter(query.toString()),filter('team=blue&opponent=UCF&sort=oldest'))
  const clear=clearMatchFilters(query,'career')
  assert.equal(clear.toString(),'extra=keep&season=career')
  assert.equal(clearMatchFilters(query,'fall','white').toString(),'extra=keep&season=fall')
  assert.equal(matchQuery(query,filter('team=white&sort=newest','blue'),'fall',true).has('team'),false)
})
test('same series id in different teams/seasons remains distinct; duplicate map IDs count once',()=>{
  const other={...matches[0],id:'other',team_slug:'white',team_name:'UAH White'}
  const prior={...matches[0],id:'prior',season:'prior'}
  const groups=discoverSeries([...matches,matches[0],other,prior],filter())
  assert.equal(groups.length,5)
  assert.equal(groups.reduce((n,g)=>n+g.maps.length,0),6)
})
