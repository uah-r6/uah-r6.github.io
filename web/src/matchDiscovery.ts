import type {Match, Team} from './publicTypes.ts'
import {seriesGroups} from './presentation.ts'
import {resolveTeam} from './scope.ts'

export const MATCH_SORTS = ['newest', 'oldest', 'opponent'] as const
export type MatchSort = typeof MATCH_SORTS[number]
export type MatchFilters = {team:string;opponent:string;sort:MatchSort}

export function matchFilters(params:URLSearchParams, teams:Team[], scopedTeam?:string):MatchFilters {
  const sort=params.get('sort')
  return {team:scopedTeam||resolveTeam(teams,params.get('team'))?.slug||'',
    opponent:params.get('opponent')||'',
    sort:MATCH_SORTS.includes(sort as MatchSort)?sort as MatchSort:'newest'}
}

export function matchQuery(params:URLSearchParams, filters:MatchFilters, period:string, scoped=false) {
  const next=new URLSearchParams(params)
  next.set('season',period)
  if(filters.team&&!scoped)next.set('team',filters.team);else next.delete('team')
  if(filters.opponent)next.set('opponent',filters.opponent);else next.delete('opponent')
  if(filters.sort!=='newest')next.set('sort',filters.sort);else next.delete('sort')
  return next
}

export function clearMatchFilters(params:URLSearchParams, period:string, scopedTeam='') {
  return matchQuery(params,{team:scopedTeam,opponent:'',sort:'newest'},period,!!scopedTeam)
}

export function discoverSeries(matches:Match[], filters:MatchFilters) {
  const needle=filters.opponent.trim().toLocaleLowerCase()
  const groups=seriesGroups(matches.filter(m=>!filters.team||m.team_slug===filters.team))
    .filter(s=>s.maps.some(m=>m.opponent.toLocaleLowerCase().includes(needle)))
  const date=(s:typeof groups[number])=>s.maps.reduce((latest,m)=>m.date>latest?m.date:latest,'')
  return groups.sort((a,b)=>{
    const first=a.maps[0],second=b.maps[0]
    const alpha=filters.sort==='opponent'?first.opponent.localeCompare(second.opponent):0
    return alpha||(filters.sort==='oldest'?date(a).localeCompare(date(b)):date(b).localeCompare(date(a)))||a.key.localeCompare(b.key)
  })
}

export function opponentSuggestions(matches:Match[], team='') {
  return [...new Set(matches.filter(m=>!team||m.team_slug===team).map(m=>m.opponent))]
    .sort((a,b)=>a.localeCompare(b))
}
