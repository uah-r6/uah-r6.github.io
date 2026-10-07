import {test} from 'node:test'
import assert from 'node:assert/strict'
import {contrast,teamTheme} from '../src/theme.ts'
import {leaderboardPlayers,selectedPeriod} from '../src/scope.ts'

test('arbitrary team colors preserve primary and derive readable accents',()=>{
  for(const primary of ['#0058A4','#E6EDF5','#000000','#ffffff','#FDDA24','#002D72','#888888','#ff0000','#00ff00','#0000ff','#990099']){
    const css=teamTheme(primary)
    assert.equal(css['--team-primary'],primary)
    assert.ok(contrast(css['--accent'],'#17232E')>=4.5)
    const rgb=primary.slice(1).match(/.{2}/g).map(v=>parseInt(v,16))
    const muted='#'+[23,35,46].map((v,i)=>Math.round(v*.88+rgb[i]*.12).toString(16).padStart(2,'0')).join('')
    assert.ok(contrast(css['--accent'],muted)>=4.5)
    assert.ok(contrast(css['--accent'],css['--accent-ink'])>=4.5)
    assert.ok(css['--accent-muted'].startsWith('rgba('))
  }
  assert.equal(teamTheme('not a color')['--team-primary'],'#0058A4')
  assert.equal(teamTheme('#fff')['--team-primary'],'#0058A4')
})
test('Alumni filter preserves historical map participants without mutating inputs',()=>{
  const players=[{name:'Active player',status:'Active'},{name:'Former player',status:'Alumni'}]
  assert.equal(leaderboardPlayers(players).length,1)
  assert.equal(leaderboardPlayers(players,true).length,2)
  assert.equal(leaderboardPlayers(players,false,true).length,2)
  assert.equal(players.length,2)
})
test('period selector defaults to active/latest and handles saved and removed seasons',()=>{
  const seasons=[{slug:'spring-2027'},{slug:'fall-2026'}]
  assert.equal(selectedPeriod(seasons,'spring-2027',null),'spring-2027')
  assert.equal(selectedPeriod(seasons,null,null),'spring-2027')
  assert.equal(selectedPeriod(seasons,'spring-2027','career'),'career')
  assert.equal(selectedPeriod(seasons,'spring-2027','fall-2026'),'fall-2026')
  assert.equal(selectedPeriod(seasons,'spring-2027','deleted'),'spring-2027')
  assert.equal(selectedPeriod([],null,null),'career')
})
