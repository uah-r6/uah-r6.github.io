import test from 'node:test'
import assert from 'node:assert/strict'
import {winRate,rateLabel,siteLabel,sortSites,bestSite} from '../src/mapAnalytics.ts'
const site=(name,rounds,wins,unknown=false)=>({site:name,rounds,wins,losses:rounds-wins,unknown})
test('zero samples produce null/empty rates; numerator denominator preserved',()=>{
  assert.equal(winRate(site('',0,0)),null)
  assert.equal(rateLabel(site('',0,0)),'—')
  assert.equal(rateLabel(site('',9,7)),'77.8%')
  assert.equal(rateLabel(site('',3,3)),'100%')
})
test('best site ignores singleton and unknown; ranks rates then sample/name',()=>{
  const a=site('A',4,3),b=site('B',2,2),c=site('C',1,1),u=site('',5,5,true)
  assert.equal(bestSite([a,b,c,u]),b)
  assert.equal(bestSite([c,u]),null)
  assert.equal(bestSite([site('B',2,1),site('A',4,2)]).site,'A')
  assert.equal(bestSite([site('B',2,1),site('A',2,1)]).site,'A')
})
test('site list ranks sample first, then rate/name without mutating input',()=>{
  const values=[site('A',1,1),site('B',4,1),site('D',2,1),site('C',2,1),site('E',2,2)]
  assert.deepEqual(sortSites(values).map(s=>s.site),['B','E','C','D','A'])
  assert.equal(values[0].site,'A')
})
test('friendly site label preserves canonical raw string',()=>{
  const original=site('2F Command Center, 2F Servers',2,2)
  assert.equal(siteLabel(original),'2F Command Center / 2F Servers')
  assert.equal(original.site,'2F Command Center, 2F Servers')
  assert.equal(siteLabel(site('',2,0,true)),'Unknown site')
})
