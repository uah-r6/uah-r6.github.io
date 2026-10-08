import type {Match, Stats, SeriesPoint} from './publicTypes.ts'
import {leaderboardPlayers} from './scope.ts'

export function embedSeason(seasons:{slug:string}[], active:string|null, explicit:string|null):string|null {
  const requested=explicit??active
  return seasons.some(s=>s.slug===requested)?requested:null
}
export function ratingHistory(matches:Match[]):Match[] {
  return matches.map((map,ordinal)=>({map,ordinal})).filter(({map})=>map.rating_eligible!==false&&map.rating_version==='siege_style_v3'&&typeof map.rating==='number'&&Number.isFinite(map.rating))
    .sort((a,b)=>a.map.date.localeCompare(b.map.date)||b.ordinal-a.ordinal).map(({map})=>map)
}
export function seriesRatingHistory(series:SeriesPoint[]):SeriesPoint[]{
  const seen=new Set<string>()
  return series.map((point,ordinal)=>({point,ordinal})).filter(({point})=>{
    const key=JSON.stringify([point.id,point.team_slug,point.season])
    if(seen.has(key))return false
    seen.add(key)
    return point.rating_version==='siege_style_v3'&&completeSeriesRating(point)&&typeof point.rating==='number'&&Number.isFinite(point.rating)
  }).sort((a,b)=>a.point.date.localeCompare(b.point.date)||b.ordinal-a.ordinal).map(({point})=>point)
}
export function completeSeriesRating(point:Pick<SeriesPoint,'maps'|'rating_maps'|'rounds'|'rating_rounds'>):boolean{
  return point.maps>0&&point.rounds>0&&point.rating_maps===point.maps&&point.rating_rounds===point.rounds
}
export function seriesGroups(matches:Match[]) {
  const groups=new Map<string,Match[]>()
  for(const map of matches){const key=JSON.stringify([map.team_slug,map.season,map.series_id]);const maps=groups.get(key)||[];if(!maps.some(m=>m.id===map.id))maps.push(map);groups.set(key,maps)}
  return [...groups].map(([key,maps])=>({key,maps,wins:maps.filter(m=>m.result==='WIN').length,losses:maps.filter(m=>m.result==='LOSS').length}))
}
export const percent=(n:number)=>`${Math.round(n*100)}%`
export const decimal=(n:number|null)=>n===null?'—':n.toFixed(2)
export const signed=(n:number)=>`${n>=0?'+':''}${n}`
export const columns=[
  {key:'rating',label:'Rating',help:'Performance estimate on eligible maps. Coverage is shown on each player profile.',section:'rating',format:(s:Stats)=>decimal(s.rating)},
  {key:'kost',label:'KOST',help:'Percentage of rounds with a Kill, Objective, Survival or Traded death.',section:'core-stats',format:(s:Stats)=>percent(s.kost)},
  {key:'kd_diff',label:'K-D',help:'Kills and deaths, with their difference in parentheses.',section:'core-stats',format:(s:Stats)=>`${s.kills}-${s.deaths} (${signed(s.kd_diff)})`},
  {key:'entry_diff',label:'Entry',help:'Opening kills and opening deaths, with their difference in parentheses.',section:'advanced-stats',format:(s:Stats)=>`${s.opening_kills}-${s.opening_deaths} (${signed(s.entry_diff)})`},
  {key:'kpr',label:'KPR',help:'Enemy kills per round played.',section:'core-stats',size:'medium',format:(s:Stats)=>decimal(s.kpr)},
  {key:'srv',label:'SRV',help:'Percentage of rounds the player survived.',section:'core-stats',size:'wide',format:(s:Stats)=>percent(s.srv)},
  {key:'hs',label:'HS%',help:'Headshot eliminations as a percentage of final eliminations.',section:'core-stats',size:'wide',format:(s:Stats)=>percent(s.hs)},
  {key:'plants',label:'Plants',help:'Completed bomb plants.',section:'objectives',size:'wide',format:(s:Stats)=>String(s.plants)},
  {key:'clutches',label:'1vX',help:'Rounds won after becoming the last player alive against one or more opponents.',section:'advanced-stats',size:'medium',format:(s:Stats)=>String(s.clutches)},
] as const
export type StatKey=typeof columns[number]['key']
export function sortedPlayers(players:Stats[],key:StatKey,desc:boolean,alumni=false,historical=false):Stats[]{
  return leaderboardPlayers(players,alumni,historical).sort((a,b)=>{
    const x=a[key],y=b[key]
    if(x===null)return y===null?0:1
    if(y===null)return -1
    return (x-y)*(desc?-1:1)
  })
}
