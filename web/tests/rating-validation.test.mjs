import {test} from 'node:test'
import assert from 'node:assert/strict'
import {readFileSync} from 'node:fs'
import {readValidationData,validationDomain,validationMetrics} from '../src/ratingValidation.ts'

const data=JSON.parse(readFileSync(new URL('../public/methodology/rating-v3-final.json',import.meta.url),'utf8'))

test('scatter contains the frozen final cohort and reproduces its reported accuracy',()=>{
  assert.equal(readValidationData(data),data)
  assert.equal(new Set(data.points.map(p=>p.game_id)).size,11)
  assert.equal(new Set(data.points.map(p=>`${p.game_id}/${p.player}`)).size,110)
  const metrics=validationMetrics(data.points)
  assert.equal(metrics.mae.toFixed(5),'0.03036')
  assert.equal(metrics.v2_mae.toFixed(5),'0.06059')
  assert.equal((metrics.within_005*100).toFixed(2),'81.82')
  const report=readFileSync(new URL('../../research/output/v3-native-final-apac1-result.md',import.meta.url),'utf8')
  const frozen=JSON.parse(report.slice(report.indexOf('{')))
  assert.equal(metrics.rows,frozen.rows)
  assert.ok(Math.abs(metrics.mae-frozen.candidate.mae)<1e-12)
  assert.ok(Math.abs(metrics.v2_mae-frozen.baseline.mae)<1e-12)
})

test('visualization exposes only public identifiers and ratings, and points fit the chart',()=>{
  assert.deepEqual(Object.keys(data).sort(),['evaluation','event','freeze_commit','maps','metrics','points','report_url','rosters','version'])
  const {min,max,ticks}=validationDomain(data.points)
  assert.ok(ticks.length>=3)
  for(const p of data.points){
    assert.deepEqual(Object.keys(p).sort(),['game_id','map','match_id','player','prediction','target','v2_prediction'])
    for(const value of [p.target,p.prediction])assert.ok(value>=min&&value<=max)
  }
  assert.doesNotMatch(JSON.stringify(data),/data\/research\/|archive|sqlite|profile_id|C:\\|\.rec|cache/i)
})

test('missing, malformed or inconsistent chart data is refused for the summary fallback',()=>{
  assert.throws(()=>readValidationData(null))
  assert.throws(()=>readValidationData({...data,points:[]}))
  assert.throws(()=>readValidationData({...data,metrics:{...data.metrics,mae:.5}}))
  assert.throws(()=>readValidationData({...data,points:data.points.map((p,i)=>i? p:{...p,prediction:NaN})}))
  assert.throws(()=>validationMetrics([]))
})
