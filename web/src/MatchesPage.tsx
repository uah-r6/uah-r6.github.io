import {useEffect} from 'react'
import {useSearchParams} from 'react-router-dom'
import type {Index,Season,Team} from './publicTypes'
import {useData} from './publicData'
import {SeriesCard} from './PublicMatches'
import {clearMatchFilters,discoverSeries,matchFilters,matchQuery,opponentSuggestions} from './matchDiscovery'
import type {MatchFilters} from './matchDiscovery'
import './discovery.css'

export function MatchDiscovery({index,season,team}:{index:Index;season:string;team?:Team}) {
  const [params,setParams]=useSearchParams()
  const filters=matchFilters(params,index.teams,team?.slug)
  const {data,error}=useData<Season>(`${team?`teams/${team.slug}/`:'seasons/'}${season}.json`)
  const ready=data?.slug===season&&(!team||data.team?.slug===team.slug)
  const period=season==='career'?'Career':index.seasons.find(s=>s.slug===season)?.name||season
  useEffect(()=>{document.title=`${team?.name||'Program'} Matches · ${period} | UAH R6`},[team,period])
  const update=(change:Partial<MatchFilters>,replace=false)=>setParams(matchQuery(params,{...filters,...change},season,!!team),{replace})
  const groups=ready?discoverSeries(data.matches,filters):[]
  const selectedTeam=index.teams.find(t=>t.slug===filters.team)
  const Title=team?'h2':'h1'
  return <section className="match-discovery">
    <div className="heading"><span className="eyebrow">NECC / MATCH HISTORY</span><Title>Matches</Title><p>Recorded series, map results and player performance.</p></div>
    <div className="discovery-controls">
      {!team&&<label>Team<select aria-label="Match team" value={filters.team} onChange={e=>update({team:e.target.value})}><option value="">All UAH Teams</option>{index.teams.map(t=><option key={t.id} value={t.slug}>{t.name}</option>)}</select></label>}
      <label className="opponent-control">Opponent<input type="search" aria-label="Opponent" list="recorded-opponents" placeholder="Search opponents…" value={filters.opponent} onChange={e=>update({opponent:e.target.value},true)}/></label>
      <datalist id="recorded-opponents">{opponentSuggestions(ready?data.matches:[],filters.team).map(name=><option value={name} key={name}/>)}</datalist>
      <label>Sort<select aria-label="Match sort" value={filters.sort} onChange={e=>update({sort:e.target.value as MatchFilters['sort']})}><option value="newest">Newest first</option><option value="oldest">Oldest first</option><option value="team">UAH Team</option><option value="opponent">Opponent</option></select></label>
      <button className="button" onClick={()=>setParams(clearMatchFilters(params,season,team?.slug))}>Clear filters</button>
    </div>
    {!ready?<div className="empty">{error||'Loading matches…'}</div>:<>
      {data.demo&&<div className="demo">DEMO DATA · Synthetic matches</div>}
      <p className="discovery-count" role="status">{groups.length} recorded series · {period}</p>
      {groups.map(s=><SeriesCard key={s.key} maps={s.maps} wins={s.wins} losses={s.losses} team={index.teams.find(t=>t.slug===s.maps[0].team_slug)}/>)}
      {!groups.length&&<div className="empty"><h3>{filters.opponent.trim()?`No recorded series match “${filters.opponent.trim()}”`:'No recorded series'} for {selectedTeam?.name||'All UAH Teams'} in {period}.</h3><p>{data.matches.length?'Try another opponent or clear filters.':'No matches have been recorded in this scope yet.'}</p><button className="button" onClick={()=>setParams(clearMatchFilters(params,season,team?.slug))}>Clear filters</button></div>}
    </>}
  </section>
}
