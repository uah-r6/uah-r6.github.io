import {useEffect} from 'react'
import {Link} from 'react-router-dom'
import type {Match,Team} from './publicTypes'
import {TeamLogo} from './TeamLogo'
import {HeroIdentity,ScoreDisplay} from './PublicIdentity'
import {teamTheme} from './theme'
import {displayDate,mapRatingLabel} from './publicView'

export function SeriesCard({maps,wins,losses,team}:{maps:Match[];wins:number;losses:number;team?:Team}){
 const first=maps[0]
 return <section className="series-card" style={teamTheme(team?.primary_color||'#0058A4')}>
  <Link className="series-heading series-summary-link" to={`/series/${first.series_id}`}>
   <div className="series-card-identity"><TeamLogo team={{slug:first.team_slug,name:first.team_name}} decorative/><div><span className="team-chip">{first.team_name}</span><h2>vs {first.opponent}</h2><span className="section-aside">{displayDate(first.date)}{first.week?` · ${/^week\b/i.test(first.week)?first.week:'Week '+first.week}`:''}</span></div></div>
   <div><ScoreDisplay ours={wins} theirs={losses}/><span className="view-series">View series →</span></div>
  </Link>
  <div className="series-maps">{maps.map(m=><Link key={m.id} to={`/matches/${m.id}`}><span>{m.map}</span><strong>{m.our_score}–{m.their_score}</strong><span className={`badge ${m.result.toLowerCase()}`}>{m.result==='WIN'?'W':m.result==='LOSS'?'L':m.result}</span><span aria-hidden="true">↗</span></Link>)}</div>
 </section>
}
export function MapSummary({map,teamName}:{map:Match;teamName:string}){
 return <Link className="map-summary-card" to={`/matches/${map.id}`}>
  <div className="map-summary-top"><span className="eyebrow">MAP</span><span className={`badge ${map.result.toLowerCase()}`}>{map.result}</span></div>
  <h2>{map.map}</h2>
  <dl><div><dt>{teamName}</dt><dd>{map.our_score}</dd></div><div><dt>{map.opponent}</dt><dd>{map.their_score}</dd></div></dl>
  <div className="map-summary-bottom"><small>{mapRatingLabel(map)}</small><span>View map ↗</span></div>
 </Link>
}
export function MapHero({map,period=map.season}:{map:Match;period?:string}){
 useEffect(()=>{document.title=`${map.team_name} vs ${map.opponent} · ${map.map} | UAH R6`},[map])
 return <header className="public-hero map-hero">
  <HeroIdentity team={{slug:map.team_slug,name:map.team_name}} eyebrow={map.team_name} title={map.map}><p className="hero-opponent">vs {map.opponent}</p><div className="hero-meta"><span className={`badge ${map.result.toLowerCase()}`}>{map.result}</span><span>{period}</span><time dateTime={map.date}>{displayDate(map.date)}</time></div></HeroIdentity>
  <ScoreDisplay ours={map.our_score} theirs={map.their_score} label="Round score"/>
 </header>
}
