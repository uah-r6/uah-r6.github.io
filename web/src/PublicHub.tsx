import {useEffect} from 'react'
import {Link} from 'react-router-dom'
import type {Index,Season,Team} from './publicTypes'
import {useData} from './publicData'
import {HeroIdentity} from './PublicIdentity'
import {SeriesCard} from './PublicMatches'
import {TeamLogo} from './TeamLogo'
import {teamTheme} from './theme'
import {programCounts,recentSeries} from './publicView'

export function ProgramHome({index,season}:{index:Index;season:string}){
 const {data,error}=useData<Season>(`seasons/${season}.json`)
 const period=season==='career'?'Career · all seasons':index.seasons.find(s=>s.slug===season)?.name||season
 const ready=data?.slug===season
 const counts=ready?programCounts(index.teams,data.matches):null
 useEffect(()=>{document.title='UAH Rainbow Six | UAH R6'},[])
 return <div className="program-home">
  <header className="public-hero program-hero"><HeroIdentity title="UAH Rainbow Six" eyebrow="THE UNIVERSITY OF ALABAMA IN HUNTSVILLE"><p className="hero-opponent">Competitive Rainbow Six Siege</p><p className="hero-meta">NECC · {period}</p></HeroIdentity><div className="hero-actions"><Link className="button primary-button" to="/players?team=blue">Explore Player Stats ↗</Link><Link className="button" to="/submit">Submit Replays</Link></div></header>
  <dl className="program-summary"><div><dt>Active teams</dt><dd>{index.teams.filter(t=>t.active).length}</dd></div><div><dt>Recorded maps</dt><dd>{counts?.maps??'—'}</dd></div><div><dt>Recorded series</dt><dd>{counts?.series??'—'}</dd></div><div><dt>Viewing</dt><dd className="period-value">{period}</dd></div></dl>
  <div className="section-title"><div><span className="eyebrow">ONE PROGRAM. EVERY TEAM.</span><h2>Meet the teams</h2></div><span className="section-aside">Choose your team</span></div>
  <div className="team-grid">{index.teams.map(team=><TeamCard key={team.id} team={team} season={season} period={period}/>)}</div>
  {ready&&!!data.matches.length&&<><div className="section-title"><h2>Latest series</h2><Link to="/matches">All matchups →</Link></div><div className="recent-series-grid">{recentSeries(data.matches,4).map(s=><SeriesCard key={s.key} maps={s.maps} wins={s.wins} losses={s.losses} team={index.teams.find(t=>t.slug===s.maps[0].team_slug)}/>)}</div></>}
  {error&&<p className="data-message">{error}</p>}
  <section className="program-note"><div><span className="eyebrow">FROM THE REPLAYS</span><h2>Every number has context.</h2><p>Explore the definitions, Rating coverage and methodology behind UAH’s recorded NECC performance.</p></div><Link className="button" to="/methodology">Read the methodology →</Link></section>
 </div>
}
function TeamCard({team,season,period}:{team:Team;season:string;period:string}){
 const {data,error}=useData<Season>(`teams/${team.slug}/${season}.json`)
 const ready=data?.team?.slug===team.slug&&data.slug===season
 const latest=ready?recentSeries(data.matches,1)[0]:undefined
 return <Link className="team-card" style={teamTheme(team.primary_color)} to={`/teams/${team.slug}`}>
  <div className="team-card-title"><span className="eyebrow">{team.active?'NECC TEAM':'TEAM ARCHIVE'}</span><span>{period}</span></div>
  <div className="team-card-identity"><TeamLogo team={team} size="lg" decorative/><div><h2>{team.name}</h2><p>{team.roster_count} active players</p></div></div>
  {ready&&data.maps>0?<dl className="team-card-record"><div><dt>Map record</dt><dd>{data.wins}–{data.maps-data.wins}</dd></div><div><dt>Maps played</dt><dd>{data.maps}</dd></div></dl>:<p className="team-card-empty">{ready?'No matches recorded for this period yet.':'Loading team record…'}</p>}
  {latest&&<div className="team-card-latest"><span>Latest recorded matchup</span><strong>vs {latest.maps[0].opponent}</strong><small>Recorded maps: {latest.wins}–{latest.losses}</small></div>}
  <div className="team-card-action">View team <span aria-hidden="true">↗</span></div>{error&&<small>{error}</small>}
 </Link>
}
export function TeamHeader({team,season}:{team:Team;season:string}){
 const {data}=useData<Season>(`teams/${team.slug}/${season}.json`)
 const ready=data?.team?.slug===team.slug&&data.slug===season
 const latest=ready?recentSeries(data.matches,1)[0]:undefined
 return <header className="public-hero team-header">
  <HeroIdentity team={team} title={team.name} eyebrow={`NECC / ${ready?data.name:season}`}><p>{ready&&!data.maps?'No matches recorded for this period yet.':'Roster, results and competitive performance.'}</p></HeroIdentity>
  <dl className="hero-facts"><div><dt>Map record</dt><dd>{ready&&data.maps?`${data.wins}–${data.maps-data.wins}`:'—'}</dd></div><div><dt>Maps</dt><dd>{ready?data.maps:'—'}</dd></div><div><dt>Rounds</dt><dd>{ready?data.rounds:'—'}</dd></div></dl>
  {latest&&<Link className="hero-footer" to={`/series/${latest.maps[0].series_id}`}><span>Latest matchup</span><strong>vs {latest.maps[0].opponent}</strong><span>Recorded maps: {latest.wins}–{latest.losses}</span><span aria-hidden="true">↗</span></Link>}
 </header>
}
