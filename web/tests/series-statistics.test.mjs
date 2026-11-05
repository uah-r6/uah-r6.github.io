import {test} from 'node:test'
import assert from 'node:assert/strict'
import {ratingHistory,seriesRatingHistory,completeSeriesRating,seriesGroups} from '../src/presentation.ts'
import {discoverSeries} from '../src/matchDiscovery.ts'
import {mapRatingLabel} from '../src/publicView.ts'

const point={id:'placements',series_id:'placements',team_slug:'blue',season:'fall-2026',opponent:'Placements',date:'2026-09-23',maps:3,rounds:38,rating_maps:3,rating_rounds:38,rating:1.3,rating_version:'siege_style_v3'}
const map={...point,id:'map',map:'Border',rating_eligible:true,result:'WIN'}

test('no-count series and maps cannot become Rating trend points even with complete numeric Ratings',()=>{
 const excluded={...point,exclude_from_stats:true},excludedMap={...map,exclude_from_stats:true}
 assert.equal(completeSeriesRating(excluded),true) // Evidence validity stays independent of counting policy.
 assert.deepEqual(seriesRatingHistory([excluded]),[])
 assert.deepEqual(ratingHistory([excludedMap]),[])
 assert.equal(mapRatingLabel(excludedMap),'No count')
 assert.deepEqual(excluded,{...point,exclude_from_stats:true})
})

test('unchecking restores the exact Rating and legacy documents default to counting',()=>{
 for(const flag of [{},{exclude_from_stats:false}]){
  assert.equal(seriesRatingHistory([{...point,...flag}])[0].rating,1.3)
  assert.equal(ratingHistory([{...map,...flag}])[0].rating,1.3)
 }
})

test('no-count series remain discoverable with recorded results and exclusion metadata',()=>{
 const excluded={...map,exclude_from_stats:true}
 const groups=discoverSeries([excluded],{team:'blue',opponent:'Placements',sort:'newest'})
 assert.equal(groups.length,1)
 assert.equal(groups[0].maps[0].exclude_from_stats,true)
 assert.equal(groups[0].wins,1)
 assert.equal(seriesGroups([excluded,excluded])[0].maps.length,1)
})
