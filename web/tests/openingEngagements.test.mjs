import test from 'node:test'
import assert from 'node:assert/strict'
import {openingMetrics,openingValue} from '../src/openingEngagements.ts'

test('all three headline labels, definitions and raw samples are explicit',()=>{
 assert.deepEqual(openingMetrics.map(m=>m.label),['Opening Kill %','Opening Kill Conversion %','Opening Death Recovery %'])
 const counts={eligible_rounds:12,opening_kills:9,opening_kill_wins:7,opening_deaths:3,opening_death_wins:1}
 assert.deepEqual(openingMetrics.map(m=>openingValue(counts,m)),[
  {percentage:'75.0%',sample:'9 / 12'}, {percentage:'77.8%',sample:'7 / 9'}, {percentage:'33.3%',sample:'1 / 3'}])
})
test('no sample is a dash; real zero success stays 0.0%; no NaN or Infinity',()=>{
 const empty={eligible_rounds:0,opening_kills:0,opening_kill_wins:0,opening_deaths:0,opening_death_wins:0}
 for(const metric of openingMetrics)assert.deepEqual(openingValue(empty,metric),{percentage:'—',sample:'0 / 0'})
 assert.equal(openingValue({...empty,eligible_rounds:2},openingMetrics[0]).percentage,'0.0%')
})
