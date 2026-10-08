/** Presentation derivations from existing exports; never calculate a Rating. */
import type {Match} from './publicTypes.ts'
import {seriesGroups} from './presentation.ts'

export function recentSeries(matches:Match[],limit=4){
 return seriesGroups(matches).sort((a,b)=>b.maps[0].date.localeCompare(a.maps[0].date)).slice(0,limit)
}
export function programCounts(teams:{active:number}[],matches:Match[]){
 return {activeTeams:teams.filter(t=>t.active).length,maps:new Set(matches.map(m=>m.id)).size,series:seriesGroups(matches).length}
}
export function profileTeamIdentity(splits:{team_slug:string;team_name:string;maps:number;rounds:number}[]){
 const teams=[...new Map(splits.filter(t=>t.maps>0||t.rounds>0).map(t=>[t.team_slug,{slug:t.team_slug,name:t.team_name}])).values()]
 return {teams,team:teams.length===1?teams[0]:undefined}
}
export function displayDate(value:string){
 if(!/^\d{4}-\d{2}-\d{2}$/.test(value))return value
 const date=new Date(value+'T12:00:00Z')
 return Number.isFinite(date.getTime())?date.toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric',timeZone:'UTC'}):value
}
export function mapRatingLabel(map:Pick<Match,'rating_eligible'|'rating_version'>){
 return map.rating_eligible===true&&map.rating_version==='siege_style_v3'?'Rating eligible':'Unrated map'
}
