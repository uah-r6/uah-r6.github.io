import {useEffect} from 'react'
import {Link} from 'react-router-dom'
import type {MapAnalytics,MapAnalyticsDocument,RoundCounts,SiteCounts,Team} from './publicTypes'
import {useData} from './publicData'
import {bestSite,rateLabel,siteLabel,sortSites} from './mapAnalytics'
import {displayDate} from './publicView'
import './discovery.css'

function RoundRecord({label,counts}:{label:string;counts:RoundCounts}) {
  return <div className="map-round-stat"><span>{label}</span><strong>{rateLabel(counts)}</strong><small>{counts.rounds?`${counts.wins}–${counts.losses} · ${counts.rounds} rounds`:'No recorded rounds'}</small></div>
}
function MapNumbers({map}:{map:MapAnalytics}) {
  return <div className="map-round-grid"><RoundRecord label="Overall round win rate" counts={map}/><RoundRecord label="Attack" counts={map.attack}/><RoundRecord label="Defense" counts={map.defense}/></div>
}
function SiteSummary({label,sites}:{label:string;sites:SiteCounts[]}) {
  const site=bestSite(sites)
  return <div className="map-site-summary"><span>{label}</span>{site?<><b>{siteLabel(site)}</b><small>{rateLabel(site)} · {site.wins}–{site.losses} · {site.rounds} rounds</small></>:<small>Limited sample · no known site with 2+ rounds</small>}</div>
}
function SiteList({label,sites}:{label:string;sites:SiteCounts[]}) {
  return <section className="map-sites panel"><h3>{label}</h3>{sites.length?<ul>{sortSites(sites).map(s=><li key={s.site}><b>{siteLabel(s)}</b><span>{s.wins}–{s.losses} · {s.rounds} rounds</span><strong>{rateLabel(s)}</strong></li>)}</ul>:<p>No recorded rounds.</p>}</section>
}
export function TeamMaps({team,season,mapSlug}:{team:Team;season:string;mapSlug?:string}) {
  const {data,error}=useData<MapAnalyticsDocument>(`teams/${team.slug}/maps/${season}.json`)
  const ready=data?.team_slug===team.slug&&data.period===season
  const map=ready?data.maps.find(m=>m.slug===mapSlug):undefined
  useEffect(()=>{document.title=`${team.name} · ${mapSlug?(map?.name||'Map'):'Maps'} | UAH R6`},[team,mapSlug,map])
  const base=`/teams/${team.slug}/maps`,query=`?season=${encodeURIComponent(season)}`
  if(!ready)return <div className="empty">{error||'Loading map analytics…'}</div>
  const explanation=<p className="map-scope-note">{data.period_name} · Team-owned logical maps, including substitute appearances. Sites use recorded round labels. The catalog includes supported legacy replay maps; it is not a current competitive map pool.</p>
  if(mapSlug&&!map)return <section className="empty"><h2>Map not found</h2><Link to={base+query}>View all maps</Link></section>
  if(mapSlug&&map)return <section className="team-map-detail">
    <Link className="map-back" to={base+query}>← All maps</Link>
    <header className="map-detail-hero"><span className="eyebrow">MAP PERFORMANCE / {data.period_name.toUpperCase()}</span><h2>{map.name}</h2>{map.maps_played?<p>{map.maps_played} recorded {map.maps_played===1?'map':'maps'} · Map record <b>{map.map_wins}–{map.map_losses}</b></p>:<p>No recorded maps yet.</p>}</header>
    {explanation}
    {!!map.maps_played&&<><MapNumbers map={map}/>{!!map.unknown_side.rounds&&<p className="map-scope-note">{map.unknown_side.rounds} rounds have an unknown side and remain in overall totals.</p>}
      <div className="map-site-grid"><SiteList label="Defense sites" sites={map.sites.Defense}/><SiteList label="Attack vs sites" sites={map.sites.Attack}/>{!!map.sites.Unknown.length&&<SiteList label="Unknown side sites" sites={map.sites.Unknown}/>}</div>
      <section className="map-history"><div className="section-title"><h3>Recent matches on {map.name}</h3></div><ul>{map.matches.map(m=><li key={m.id}><Link to={`/matches/${m.id}`}><span><b>vs {m.opponent}</b><small>{displayDate(m.date)}</small></span><span><strong>{m.our_score}–{m.their_score}</strong><span className={`badge ${m.result.toLowerCase()}`}>{m.result}</span></span></Link></li>)}</ul></section>
    </>}
  </section>
  return <section className="team-maps"><div className="heading"><span className="eyebrow">TEAM / MAP PERFORMANCE</span><h2>Maps</h2><p>Map records, side performance and the sites behind each result.</p></div>{explanation}
    <div className="map-analytics-grid">{data.maps.map(m=><article className={`map-analytics-card${m.maps_played?'':' unplayed'}`} key={m.slug}>
      <h3><Link to={`${base}/${m.slug}${query}`}>{m.name}</Link></h3>
      {m.maps_played?<><p className="map-record">{m.maps_played} recorded {m.maps_played===1?'map':'maps'} · Map record <b>{m.map_wins}–{m.map_losses}</b></p><MapNumbers map={m}/><div className="map-site-summary-grid"><SiteSummary label="Best defense site · 2+ rounds" sites={m.sites.Defense}/><SiteSummary label="Best attacking site · 2+ rounds" sites={m.sites.Attack}/></div><Link className="map-detail-link" to={`${base}/${m.slug}${query}`}>View details →</Link></>:<p>No recorded maps yet.</p>}
    </article>)}</div>
  </section>
}
