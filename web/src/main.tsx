import React, { useEffect, useLayoutEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { HashRouter, Link, NavLink, Route, Routes, useParams, useNavigate, useLocation } from 'react-router-dom'
import { ArrowUpRight, Crosshair, Swords, Trophy, CalendarDays } from 'lucide-react'
import './style.css'
import './brand.css'
import { teamTheme } from './theme'
import { selectedPeriod } from './scope'
import { Methodology } from './methodology'
import { SubmitPage } from './submit'

import type {Team,Stats,Match,Season,Index} from './publicTypes'
import {PlayerStats} from './PlayerStats'
import {RatingTrend} from './RatingTrend'
import {embedSeason,seriesGroups} from './presentation'
import './presentation.css'
const base = import.meta.env.BASE_URL + 'data/'
function useData<T>(path:string) {
  const [data,setData]=useState<T|null>(null), [error,setError]=useState('')
  useEffect(()=>{
    setData(null);setError('');if(!path)return
    const controller=new AbortController()
    fetch(base+path,{signal:controller.signal}).then(r=>{if(!r.ok)throw Error(`Data unavailable (${r.status})`);return r.json()}).then(setData).catch(e=>{if(e.name!=='AbortError')setError(e.message)})
    return ()=>controller.abort()
  },[path]);return {data,error}
}
const pct=(n:number)=>`${Math.round(n*100)}%`
const dec=(n:number|null,d=2)=>n===null?'—':n.toFixed(d)
const signed=(n:number)=>`${n>=0?'+':''}${n}`
const kd=(s:Stats)=>`${s.kills}-${s.deaths} (${signed(s.kd_diff)})`
const entry=(s:Stats)=>`${s.opening_kills}-${s.opening_deaths} (${signed(s.entry_diff)})`
function Loading({error}:{error:string}){return <div className="empty">{error||'Loading statistics…'}</div>}
function App(){
  const location=useLocation()
  useLayoutEffect(()=>{const name=location.pathname==='/submit'?'Submit Replays':location.pathname.startsWith('/methodology')?'Methodology':'UAH Rainbow Six Statistics';document.title=`${name} | UAH R6`},[location.pathname])
  const {data:index,error}=useData<Index>('index.json')
  const [season,setSeason]=useState('')
  useEffect(()=>{if(index){setSeason(selectedPeriod(index.seasons,index.active_season,localStorage.getItem('necc-season')))}},[index])
  useEffect(()=>{const embedded=location.pathname.startsWith('/embed/');document.documentElement.classList.toggle('embed-document',embedded);return ()=>document.documentElement.classList.remove('embed-document')},[location.pathname])
  if(!index)return <Loading error={error}/>
  if(location.pathname.startsWith('/embed/'))return <Routes><Route path="/embed/:teamSlug/player-stats" element={<EmbedStats index={index}/>}/><Route path="*" element={<NotFound compact/>}/></Routes>
  if(!season)return <Loading error={error}/>
  const change=(value:string)=>{setSeason(value);localStorage.setItem('necc-season',value)}
  return <div className="app" style={teamTheme(index.program.accent||'#0058A4')}>
    <header className="topbar"><Link className="brand" to="/"><img src={import.meta.env.BASE_URL+'brand/uah-esports-logo.png'} alt="UAH Esports"/><div><b>{index.program.short_name}</b><small>Rainbow Six Siege · NECC</small></div></Link>
      <nav aria-label="Main navigation"><NavLink end to="/">Program</NavLink><NavLink to="/players">Player Stats</NavLink><NavLink to="/matches">Matches</NavLink><NavLink to="/methodology">Methodology</NavLink><NavLink to="/submit">Submit Replays</NavLink></nav>
      {location.pathname!=='/submit'&&<label className="season-select">VIEW <select aria-label="Statistics period" value={season} onChange={e=>change(e.target.value)}>{index.seasons.map(s=><option key={s.slug} value={s.slug}>{s.name}</option>)}<option value="career">Career · all seasons</option></select></label>}
    </header>
    <main><Routes><Route path="/submit" element={<SubmitPage teams={index.teams} seasons={index.seasons}/>}/><Route path="/" element={<ProgramHome index={index} season={season}/>}/><Route path="/teams/:teamSlug/*" element={<TeamView index={index} season={season}/>}/><Route path="/players" element={<Players season={season}/>}/><Route path="/players/:slug" element={<PlayerPage season={season} teams={index.teams}/>}/><Route path="/matches" element={<Matches season={season}/>}/><Route path="/matches/:id" element={<MapPage teams={index.teams}/>}/><Route path="/methodology/*" element={<Methodology/>}/><Route path="*" element={<NotFound/>}/></Routes></main>
    <footer><span>UAH Rainbow Six Siege · NECC statistics{index.generated_at&&<Freshness value={index.generated_at}/>}</span><Link to="/methodology">Definitions & Rating coverage</Link></footer>
  </div>
}
function ProgramHome({index,season}:{index:Index;season:string}){
  return <><Heading eyebrow="THE UNIVERSITY OF ALABAMA IN HUNTSVILLE" title={index.program.name} subtitle="One program. Every team. Explore the roster, matches and performance behind each season."/>
    <div className="section-title"><h2>Our teams</h2><span className="section-aside">{season==='career'?'All seasons':index.seasons.find(s=>s.slug===season)?.name}</span></div>
    <div className="team-grid">{index.teams.map(team=><TeamCard key={team.id} team={team} season={season}/>)}</div>
    <section className="panel program-note"><span className="eyebrow">FROM THE REPLAYS</span><h2>Statistics with context</h2><p>Follow UAH’s NECC matches, organized by team and season. Player profiles show the full performance breakdown and Rating coverage.</p><Link className="button" to="/methodology">Explore the methodology</Link> <Link className="button" to="/submit">Submit match replays</Link></section></>
}
function TeamCard({team,season}:{team:Team;season:string}){
  const {data,error}=useData<Season>(`teams/${team.slug}/${season}.json`)
  return <Link className="team-card" style={teamTheme(team.primary_color)} to={`/teams/${team.slug}`}><div className="team-card-title"><span className="team-swatch"/><span className="eyebrow">{team.active?'NECC TEAM':'TEAM ARCHIVE'}</span><ArrowUpRight size={20}/></div><h2>{team.name}</h2><p>{data?.maps?`${data.maps} maps · ${data.rounds} rounds`:'No matches recorded yet'}</p><div className="team-card-facts"><span>{team.roster_count} active players</span><strong>{data?.maps?`${data.wins}-${data.maps-data.wins}`:'Ready for a new season'}</strong></div>{error&&<small>{error}</small>}</Link>
}
function TeamView({index,season}:{index:Index;season:string}){
  const navigate=useNavigate()
  const params=useParams(), team=index.teams.find(t=>t.slug===params.teamSlug||t.aliases.includes(params.teamSlug||''))
  const section=params['*']||'overview'
  if(!team)return <NotFound/>
  const prefix=`teams/${team.slug}/`
  return <div className="team-scope" style={teamTheme(team.primary_color)}><div className="context-banner"><Link to="/">UAH R6</Link><ChevronLabel/> <label className="public-team-selector">TEAM <select aria-label="Public team" value={team.slug} onChange={e=>navigate(`/teams/${e.target.value}${section==='overview'?'':'/'+section}`)}>{index.teams.map(t=><option value={t.slug} key={t.id}>{t.name}</option>)}</select></label><span>{season==='career'?'Career · all seasons':index.seasons.find(s=>s.slug===season)?.name}</span></div>
    <TeamHeader team={team} season={season}/><nav className="team-nav" aria-label="Team navigation">{['overview','roster','stats','matches'].map(p=><Link className={section===p?'active':''} key={p} to={`/teams/${team.slug}${p==='overview'?'':'/'+p}`}>{p==='stats'?'Player Stats':p[0].toUpperCase()+p.slice(1)}</Link>)}</nav>
    {section==='roster'?<TeamRoster team={team} index={index} season={season}/>:section==='stats'?<Players season={season} prefix={prefix} team={team.name}/>:section==='matches'?<Matches season={season} prefix={prefix}/>:<Overview season={season} team={team.name} prefix={prefix}/>}
  </div>
}
function ChevronLabel(){return <span aria-hidden="true">/</span>}
function TeamRoster({team,index,season}:{team:Team;index:Index;season:string}){
 const [alumni,setAlumni]=useState(false)
 const selected=index.seasons.find(s=>s.slug===season) as {start_date?:string;end_date?:string}|undefined
 const today=new Date().toLocaleDateString('en-CA')
 const cutoff=selected?.end_date&&selected.end_date<today?selected.end_date:today
 const players=index.players.filter(p=>p.memberships.some(m=>m.team_slug===team.slug&&(alumni?
   season==='career'||(!m.end_date||m.end_date>(selected?.start_date||'0001-01-01'))&&m.start_date<=(selected?.end_date||today):
   m.start_date<=cutoff&&(!m.end_date||m.end_date>cutoff)))&&(alumni||p.status==='Active'))
 return <><Heading eyebrow="TEAM ROSTER" documentTitle={`${team.name} Roster`} title={team.name} subtitle="Meet the team and explore each player’s career."/><label className="filter-toggle"><input type="checkbox" checked={alumni} onChange={e=>setAlumni(e.target.checked)}/> Include Alumni / former members</label><div className="roster-cards">{players.map(p=><Link className="panel" key={p.slug} to={`/players/${p.slug}`}><span className="eyebrow">{p.status}</span><h2>{p.name}</h2>{p.memberships.filter(m=>m.team_slug===team.slug).map(m=><p key={m.start_date}>{m.start_date==='0001-01-01'?'Joined before recorded history':m.start_date} → {m.end_date||'present'}</p>)}<span>View player ↗</span></Link>)}</div>{!players.length&&<div className="empty">No roster members recorded for this view.</div>}</>
}
function Heading({eyebrow,title,subtitle,documentTitle=title}:{eyebrow:string;title:string;subtitle:string;documentTitle?:string}){useEffect(()=>{document.title=`${documentTitle} | UAH R6`},[documentTitle]);return <div className="heading"><span className="eyebrow">{eyebrow}</span><h1>{title}</h1><p>{subtitle}</p></div>}
function StatCard({label,value,icon}:{label:string;value:string|number;icon?:React.ReactNode}){return <div className="statcard"><span>{label}{icon}</span><strong>{value}</strong></div>}
const Board=PlayerStats
function Overview({season,team,prefix="seasons/"}:{season:string;team:string;prefix?:string}){
 const {data,error}=useData<Season>(`${prefix}${season}.json`)
 if(!data)return <Loading error={error}/>
 const heading=<Heading eyebrow="COMPETITIVE INTELLIGENCE / NECC" title={`${team} · ${data.name}`} subtitle={`${team} performance across every recorded NECC map.`}/>
 if(!data.maps)return <>{heading}<EmptyTeam roster={data.roster}/></>
 return <>{heading}{data.demo&&<div className="demo">DEMO DATA · Synthetic matches for preview only</div>}<div className="cardgrid"><StatCard label="MAP RECORD" value={`${data.wins}–${data.maps-data.wins}`} icon={<Trophy size={16}/>}/><StatCard label="MAPS PLAYED" value={data.maps} icon={<Swords size={16}/>}/><StatCard label="ROUNDS WON" value={data.rounds_won} icon={<Crosshair size={16}/>}/><StatCard label="ROUND WIN RATE" value={data.rounds?pct(data.rounds_won/data.rounds):'—'} icon={<CalendarDays size={16}/>}/></div><div className="section-title"><div><span className="eyebrow">THE ROSTER</span><h2>Player Stats</h2></div><span className="section-aside">Sorted by Rating</span></div><Board players={data.players}/><div className="section-title"><div><span className="eyebrow">LATEST ACTION</span><h2>Recent maps</h2></div><Link to={prefix.startsWith("teams/")?`/teams/${prefix.split("/")[1]}/matches`:"/matches"}>View all <ArrowUpRight size={15}/></Link></div><div className="match-grid">{data.matches.slice(0,3).map(m=><MatchCard key={m.id} m={m}/>)}</div></>
}
function Players({season,prefix="seasons/",team="Program"}:{season:string;prefix?:string;team?:string}){const {data,error}=useData<Season>(`${prefix}${season}.json`);if(!data)return <Loading error={error}/>;return <><Heading eyebrow={`${team.toUpperCase()} / ${data.name.toUpperCase()}`} title="Player Stats" documentTitle={`${team} Player Stats · ${data.name}`} subtitle="Compare player performance. Select a name for the full breakdown."/>{data.maps?<Board players={data.players}/>:<EmptyTeam roster={data.roster}/>}</>}
function MatchCard({m}:{m:Match}){return <Link className="match-card" to={`/matches/${m.id}`}><div><span className="eyebrow">{m.date}</span><span className={`badge ${m.result.toLowerCase()}`}>{m.result}</span></div><h3>vs {m.opponent}</h3><div className="match-bottom"><span>{m.map}{m.rating!=null?` · Rating ${dec(m.rating)}`:''}</span><strong>{m.our_score} <em>:</em> {m.their_score}</strong></div></Link>}
function Matches({season,prefix="seasons/"}:{season:string;prefix?:string}){
 const {data,error}=useData<Season>(`${prefix}${season}.json`)
 const {data:index}=useData<Index>('index.json')
 if(!data)return <Loading error={error}/>
 return <><Heading eyebrow="NECC / MATCH HISTORY" title="Matches" documentTitle={`${data.team?.name||'Program'} Matches · ${data.name}`} subtitle="Every recorded map, organized by competitive matchup."/>{data.demo&&<div className="demo">DEMO DATA · Synthetic matches</div>}{seriesGroups(data.matches).map(({key,maps,wins,losses})=><section className="series-card" key={key} style={teamTheme(index?.teams.find(t=>t.slug===maps[0].team_slug)?.primary_color||'#0058A4')}><div className="series-heading"><div><span className="team-chip">{maps[0].team_name}</span><h2>vs {maps[0].opponent}</h2><span className="section-aside">{maps[0].date}{maps[0].week?` · ${/^week\b/i.test(maps[0].week)?maps[0].week:'Week '+maps[0].week}`:''}</span></div><div className="recorded-score"><span>Recorded maps</span><strong>{wins}–{losses}</strong></div></div><div className="series-maps">{maps.map(m=><Link key={m.id} to={`/matches/${m.id}`}><span>{m.map}</span><strong>{m.our_score}–{m.their_score}</strong><span className={`badge ${m.result.toLowerCase()}`}>{m.result==='WIN'?'W':m.result==='LOSS'?'L':m.result}</span><ArrowUpRight size={16}/></Link>)}</div></section>)}{!data.matches.length&&<EmptyTeam/>}</>
}
function DetailGrid({s}:{s:Stats}){const rows:[string,string|number][]=[['Rounds',s.rounds],['Kills',s.kills],['Deaths',s.deaths],['KD',s.kd===null?'—':dec(s.kd)],['Opening kills',s.opening_kills],['Opening deaths',s.opening_deaths],['Refrag kills',s.refrag_kills],['Deaths traded',s.deaths_traded],['Kills traded',s.kills_traded],['Untraded kills',s.untraded_kills],['Untraded deaths',s.untraded_deaths],['Pivot kills',s.pivot_kills],['Pivot deaths',s.pivot_deaths],['1vX Clutches',s.clutches],['1v1',s.clutch_1v1],['1v2',s.clutch_1v2],['1v3',s.clutch_1v3],['1v4',s.clutch_1v4],['1v5',s.clutch_1v5],['Plants',s.plants],['Disables',s.disables],['Teamkills',s.teamkills]];return <div className="detail-grid">{rows.map(([label,value])=><div key={label}><span>{label}</span><strong>{value}</strong></div>)}</div>}
function PlayerPage({season,teams}:{season:string;teams:Team[]}){const {slug}=useParams();const {data,error}=useData<Stats&{matches:Match[];memberships:{team_name:string;team_slug:string;start_date:string;end_date:string|null}[];team_splits:(Stats&{team_name:string;team_slug:string})[]}>(`players/${slug}/${season}.json`);if(!data)return <Loading error={error}/>;return <><div className="profile-head"><Heading eyebrow="NECC / PLAYER PROFILE" title={data.name} documentTitle={`${data.name} · ${season==='career'?'Career':season}`} subtitle={`${data.rounds} rounds across ${data.maps} maps`}/><span className="badge">{data.status} · {season==='career'?'Global career':'Season · all teams'}</span></div><div className="cardgrid profile-cards"><StatCard label="RATING" value={dec(data.rating)}/><StatCard label="KOST" value={pct(data.kost)}/><StatCard label="K-D" value={kd(data)}/><StatCard label="ENTRY" value={entry(data)}/><StatCard label="KPR" value={dec(data.kpr)}/><StatCard label="SURVIVAL" value={pct(data.srv)}/><StatCard label="HEADSHOTS" value={pct(data.hs)}/></div><RatingTrend matches={data.matches} teams={teams}/><div className="two-col"><section className="panel"><span className="eyebrow">COMPLETE BREAKDOWN</span><h2>Performance</h2>{data.rating_rounds!==undefined&&<p>Rating coverage: {data.rating_rounds} of {data.rounds} rounds across {data.rating_maps} of {data.maps} maps. The full performance breakdown includes every recorded map.</p>}<DetailGrid s={data}/></section><section className="panel"><span className="eyebrow">ROUND CONTEXT</span><h2>Attack / Defense</h2><div className="sides">{['Attack','Defense'].map(side=><div key={side}><h3>{side}</h3><p>{data.sides[side].rounds} rounds</p><strong>{data.sides[side].kills}–{data.sides[side].deaths}</strong><span>KPR {dec(data.sides[side].kpr)} · KD {data.sides[side].kd===null?'—':dec(data.sides[side].kd)}</span></div>)}</div><span className="eyebrow operator-label">OPERATOR USAGE</span><div className="operators">{['Attack','Defense'].map(side=><div key={side}><h3>{side}</h3>{Object.entries(data.operators[side]||{}).sort((a,b)=>b[1]-a[1]).map(([op,n])=><div className="operator" key={op}><span>{op}</span><div><i style={{width:`${100*n/Math.max(1,...Object.values(data.operators[side]))}%`}}/></div><b>{n}</b></div>)}</div>)}</div></section></div><section className="panel profile-history"><h2>Team contributions</h2><p>Your performance for each team in this view.</p>{data.team_splits.map(t=><div className="split-row" key={t.team_slug}><Link to={`/teams/${t.team_slug}/stats`}>{t.team_name} ↗</Link><span>{t.maps} maps · {t.rounds} rounds</span><strong>Rating {dec(t.rating)}</strong></div>)}<h3>Membership history</h3>{data.memberships.map(m=><p className="membership" style={teamTheme(teams.find(t=>t.slug===m.team_slug)?.primary_color||'#0058A4')} key={m.team_slug+m.start_date}><span className="team-chip">{m.team_name}</span> · {m.start_date==='0001-01-01'?'Before recorded history':m.start_date} → {m.end_date||'present'}</p>)}</section><div className="section-title"><div><span className="eyebrow">GAME LOG</span><h2>Recent maps</h2></div></div><div className="match-list">{data.matches.map(m=><MatchCard key={m.id} m={m}/>)}</div></>}
function MapPage({teams}:{teams:Team[]}){const {id}=useParams();const {data,error}=useData<Match&{players:Stats[];rounds:{number:number;side:string;result:string;site:string}[]}>(`matches/${id}.json`);if(!data)return <Loading error={error}/>;return <div className="team-scope" style={teamTheme(teams.find(t=>t.slug===data.team_slug)?.primary_color||'#0058A4')}><Heading eyebrow={`${data.team_name} / ${data.season}`} title={`${data.map} · ${data.our_score} : ${data.their_score}`} documentTitle={`${data.team_name} vs ${data.opponent} · ${data.map}`} subtitle={`vs ${data.opponent} · ${data.map} · ${data.date}`}/>{data.demo&&<div className="demo">DEMO DATA · Synthetic match</div>}<div className="section-title"><div><span className="eyebrow">YOUR TEAM</span><h2>Map performance</h2></div><span className={`badge ${data.result.toLowerCase()}`}>{data.result}</span></div><Board players={data.players} historical/><div className="section-title"><div><span className="eyebrow">ROUND BY ROUND</span><h2>Breakdown</h2></div></div><div className="rounds">{data.rounds.map(r=><div className="round" key={r.number}><b>R{r.number}</b><span>{r.side}</span><span>{r.site}</span><strong className={r.result==='Win'?'positive':'negative'}>{r.result}</strong></div>)}</div></div>}
function Freshness({value}:{value:string}){const date=new Date(value);if(!Number.isFinite(date.getTime()))return null;return <small className="freshness">Stats updated <time dateTime={value}>{date.toLocaleString(undefined,{month:'short',day:'numeric',year:'numeric',hour:'numeric',minute:'2-digit',timeZoneName:'short'})}</time></small>}
function EmptyTeam({roster=[]}:{roster?:{slug:string;name:string;status:string}[]}){return <section className="empty team-empty"><span className="eyebrow">READY FOR THE SEASON</span><h2>No matches recorded yet</h2><p>Player statistics will appear after approved replay imports.</p>{roster.length>0&&<div className="empty-roster">{roster.map(p=><Link key={p.slug} to={`/players/${p.slug}`}>{p.name}</Link>)}</div>}<Link className="button" to="/submit">Submit match replays</Link></section>}
function TeamHeader({team,season}:{team:Team;season:string}){const {data}=useData<Season>(`teams/${team.slug}/${season}.json`);return <div className="team-header"><div><span className="eyebrow">UAH R6 / {data?.name||season}</span><h2>{team.name}</h2></div><div className="team-header-facts"><span><b>{data?`${data.wins}–${data.maps-data.wins}`:'—'}</b> map record</span><span><b>{data?.rounds??'—'}</b> rounds</span><span><b>{data?.roster?.length??team.roster_count}</b> active players</span></div></div>}
function NotFound({compact=false}:{compact?:boolean}){useEffect(()=>{document.title='Page not found | UAH R6'},[]);return <div className="empty"><span className="eyebrow">404</span><h1>Page not found</h1><p>This link does not point to an available page or team.</p><Link className="button" to="/" target={compact?'_blank':undefined}>Explore UAH R6</Link></div>}
function EmbedStats({index}:{index:Index}){
 const {teamSlug}=useParams(),location=useLocation()
 const team=index.teams.find(t=>t.slug===teamSlug||t.aliases.includes(teamSlug||''))
 const period=embedSeason(index.seasons,index.active_season,new URLSearchParams(location.search).get('season'))
 const {data,error}=useData<Season>(team&&period?`teams/${team.slug}/${period}.json`:'')
 useEffect(()=>{document.title=`${team?.name||'Team'} Player Stats | UAH R6`},[team])
 if(!team||!period)return <NotFound compact/>
 return <div className="embed-page" style={teamTheme(team.primary_color)}>{data?<PlayerStats players={data.players} embed/>:<Loading error={error}/>}</div>
}
createRoot(document.getElementById('root')!).render(<React.StrictMode><HashRouter><App/></HashRouter></React.StrictMode>)
