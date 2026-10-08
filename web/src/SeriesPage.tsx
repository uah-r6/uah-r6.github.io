import {useEffect} from 'react'
import {Link,useParams} from 'react-router-dom'
import type {Series,Team} from './publicTypes'
import {useData} from './publicData'
import {PlayerStats} from './PlayerStats'
import {teamTheme} from './theme'
import {TeamLogo} from './TeamLogo'

export function SeriesPage({teams}:{teams:Team[]}){
 const {seriesId}=useParams(),{data,error}=useData<Series>(`series/${seriesId}.json`)
 useEffect(()=>{document.title=data?`${data.team_name} vs ${data.opponent} · Series | UAH R6`:'Series | UAH R6'},[data])
 if(!data)return <section className="empty"><h1>{error?'Series not found':'Loading series…'}</h1>{error&&<><p>This series is not available.</p><Link className="button" to="/matches">Explore recorded series</Link></>}</section>
 const team=teams.find(t=>t.slug===data.team_slug)
 const anyRated=data.players.some(p=>p.rating!==null)
 return <div className="team-scope series-page" style={teamTheme(team?.primary_color||'#0058A4')}>
 <Link className="back-series" to={`/teams/${data.team_slug}/matches`}>← {data.team_name} series</Link>
 <header className="series-hero"><div className="team-heading-identity"><TeamLogo team={{slug:data.team_slug,name:data.team_name}} decorative/><div><span className="team-chip">{data.team_name}</span><div className="eyebrow">{data.season_name}</div><h1>vs {data.opponent}</h1><p>{data.date}{data.week?` · ${/^week\b/i.test(data.week)?data.week:'Week '+data.week}`:''}</p></div></div><div className="recorded-score"><span>Recorded maps</span><strong>{data.recorded_maps.wins}–{data.recorded_maps.losses}</strong><small>{data.maps.length} maps · {data.rounds} rounds</small></div></header>
 {data.demo&&<div className="demo">DEMO DATA · Synthetic maps</div>}
 <div className="series-maps series-map-summary">{data.maps.map(m=><Link to={`/matches/${m.id}`} key={m.id}><span>{m.map}</span><strong>{m.our_score}–{m.their_score}</strong><span className={`badge ${m.result.toLowerCase()}`}>{m.result==='WIN'?'W':'L'}</span><span aria-hidden="true">↗</span></Link>)}</div>
 <div className="section-title"><div><span className="eyebrow">ACROSS RECORDED MAPS</span><h2>Series Player Stats</h2></div></div>
 <p className="series-coverage-note">Series Rating uses the same frozen v3 model on combined eligible inputs. Display statistics include every recorded map each player played.</p>
 {!anyRated&&<p className="unrated-series" role="status">No eligible Series Ratings yet. Recorded performance is still shown.</p>}
 <PlayerStats players={data.players} historical showCoverage/>
 <div className="section-title"><h2>Maps</h2><Link to="/methodology/rating">How Series Rating works →</Link></div>
 <div className="match-grid">{data.maps.map(m=><Link className="match-card" key={m.id} to={`/matches/${m.id}`}><div><span className="eyebrow">MAP DETAIL</span><span className={`badge ${m.result.toLowerCase()}`}>{m.result}</span></div><h3>{m.map}</h3><div className="match-bottom"><span>Player performance & rounds</span><strong>{m.our_score} <em>:</em> {m.their_score}</strong></div></Link>)}</div>
 {data.notes&&<section className="panel series-notes"><h2>Series notes</h2><p>{data.notes}</p></section>}
 </div>
}
