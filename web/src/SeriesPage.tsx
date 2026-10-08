import {useEffect} from 'react'
import {Link,useParams} from 'react-router-dom'
import type {Series,Team} from './publicTypes'
import {useData} from './publicData'
import {PlayerStats} from './PlayerStats'
import {teamTheme} from './theme'
import {HeroIdentity,ScoreDisplay} from './PublicIdentity'
import {MapSummary} from './PublicMatches'
import {displayDate} from './publicView'

export function SeriesPage({teams}:{teams:Team[]}){
 const {seriesId}=useParams(),{data,error}=useData<Series>(`series/${seriesId}.json`)
 useEffect(()=>{document.title=data?`${data.team_name} vs ${data.opponent} · Series | UAH R6`:'Series | UAH R6'},[data])
 if(!data)return <section className="empty"><h1>{error?'Series not found':'Loading series…'}</h1>{error&&<><p>This series is not available.</p><Link className="button" to="/matches">Explore recorded series</Link></>}</section>
 const team=teams.find(t=>t.slug===data.team_slug)
 const anyRated=data.players.some(p=>p.rating!==null)
 return <div className="team-scope series-page" style={teamTheme(team?.primary_color||'#0058A4')}>
 <Link className="back-series" to={`/teams/${data.team_slug}/matches`}>← {data.team_name} series</Link>
 <header className="public-hero series-hero"><HeroIdentity team={{slug:data.team_slug,name:data.team_name}} eyebrow={data.team_name} title={`vs ${data.opponent}`}><div className="hero-meta"><time dateTime={data.date}>{displayDate(data.date)}</time><span>{data.season_name}</span>{data.week&&<span>{/^week\b/i.test(data.week)?data.week:'Week '+data.week}</span>}</div></HeroIdentity><div><ScoreDisplay ours={data.recorded_maps.wins} theirs={data.recorded_maps.losses}/><p className="score-support">{data.maps.length} maps · {data.rounds} rounds</p></div></header>
 {data.demo&&<div className="demo">DEMO DATA · Synthetic maps</div>}
 <div className="series-map-cards" aria-label="Recorded map results">{data.maps.map(m=><MapSummary key={m.id} map={m} teamName={data.team_name}/>)}</div>
 <div className="section-title"><div><span className="eyebrow">ACROSS RECORDED MAPS</span><h2>Series Player Stats</h2></div></div>
 <p className="series-coverage-note">Series Rating requires trusted evidence for every map and round a player played. Coverage is player-specific. All recorded performance remains visible.</p>
 {!anyRated&&<p className="unrated-series" role="status">Complete Series Ratings are unavailable for this matchup. Recorded performance is still shown.</p>}
 <PlayerStats players={data.players} historical showCoverage/>
 {data.notes&&<section className="panel series-notes"><h2>Series notes</h2><p>{data.notes}</p></section>}
 </div>
}
