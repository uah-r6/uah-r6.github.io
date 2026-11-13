import {useEffect} from 'react'
import {Link,useSearchParams} from 'react-router-dom'
import {useData} from './publicData'
import {teamTheme} from './theme'
import type {Index} from './publicTypes'
import './teamFirstKills.css'

type Round={number:number;side:string;result:string;player_slug:string|null;player_name:string|null;status:'recorded'|'no_kill'|'unresolved'}
type MapRow={id:string;series_id:string;season:string;opponent:string;date:string;map:string;team_slug:string;exclude_from_stats:boolean;demo:boolean;rounds:Round[]}

export function TeamFirstKills({index}:{index:Index}){
 const {data,error}=useData<{maps:MapRow[]}>('team-first-kills.json')
 const [params,setParams]=useSearchParams()
 const team=index.teams.find(t=>t.slug===params.get('team'))||index.teams[0]
 const season=params.get('season')||index.active_season||'career'
 const side=params.get('side')||'All',series=params.get('series')||'all',map=params.get('map')||'all'
 const update=(key:string,value:string)=>{const next=new URLSearchParams(params);next.set(key,value);if(key==='team'||key==='season'){next.delete('series');next.delete('map')}if(key==='series')next.delete('map');setParams(next)}
 const maps=data?.maps.filter(m=>m.team_slug===team.slug&&(season==='career'||m.season===season)&&!m.exclude_from_stats&&!m.demo)||[]
 const seriesOptions=[...new Map(maps.map(m=>[m.series_id,{id:m.series_id,label:`${m.date} · vs ${m.opponent}`}])).values()]
 const seriesMaps=series==='all'?maps:maps.filter(m=>m.series_id===series)
 const selectedMaps=map==='all'?seriesMaps:seriesMaps.filter(m=>m.id===map)
 const rows=selectedMaps.flatMap(m=>m.rounds.filter(r=>side==='All'||r.side===side))
 const counted=rows.filter(r=>r.status==='recorded'),unresolved=rows.filter(r=>r.status==='unresolved').length
 const totals=new Map<string,{name:string;total:number;attack:number;defense:number}>()
 for(const r of counted){const slug=r.player_slug!;const t=totals.get(slug)||{name:r.player_name!,total:0,attack:0,defense:0};t.total++;if(r.side==='Attack')t.attack++;if(r.side==='Defense')t.defense++;totals.set(slug,t)}
 const leaders=[...totals.entries()].sort((a,b)=>b[1].total-a[1].total||a[1].name.localeCompare(b[1].name))
 useEffect(()=>{document.title='First UAH Kill · Team rounds | UAH R6'},[])
 return <div className="team-first-kills" style={teamTheme(team.primary_color)}>
  <div className="heading"><span className="eyebrow">TEAM ROUND ANALYSIS</span><h1>First UAH Kill</h1><p>The first UAH player to eliminate an opponent in each round, even when the opponent got the opening kill.</p></div>
  <p>Based on recorded, valid opponent eliminations in selected replay rounds. Teamkills and suicides do not qualify. Maps marked no count are excluded.</p>
  <div className="first-kill-filters">
   <label>Team<select aria-label="Team" value={team.slug} onChange={e=>update('team',e.target.value)}>{index.teams.map(t=><option key={t.slug} value={t.slug}>{t.name}</option>)}</select></label>
   <label>Season<select aria-label="Season" value={season} onChange={e=>update('season',e.target.value)}>{index.seasons.map(s=><option key={s.slug} value={s.slug}>{s.name}</option>)}<option value="career">Career</option></select></label>
   <label>Side<select aria-label="Side" value={side} onChange={e=>update('side',e.target.value)}><option>All</option><option>Attack</option><option>Defense</option><option>Unknown</option></select></label>
   <label>Series<select aria-label="Series" value={seriesOptions.some(s=>s.id===series)?series:'all'} onChange={e=>update('series',e.target.value)}><option value="all">All series</option>{seriesOptions.map(s=><option key={s.id} value={s.id}>{s.label}</option>)}</select></label>
   <label>Map<select aria-label="Map" value={seriesMaps.some(m=>m.id===map)?map:'all'} onChange={e=>update('map',e.target.value)}><option value="all">All maps</option>{seriesMaps.map(m=><option key={m.id} value={m.id}>{m.map} · {m.date} vs {m.opponent}</option>)}</select></label>
  </div>
  {error&&<p role="alert">{error}</p>}
  {!data?<p>Loading round data…</p>:<>
   <div className="first-kill-summary"><div><span>Rounds</span><strong>{rows.length}</strong></div><div><span>UAH first kill recorded</span><strong>{counted.length}</strong></div><div><span>No UAH kill recorded</span><strong>{rows.filter(r=>r.status==='no_kill').length}</strong></div>{!!unresolved&&<div><span>Player unresolved</span><strong>{unresolved}</strong></div>}</div>
   <p>Player share is out of {counted.length} rounds with an identified UAH first kill{unresolved?`; ${unresolved} unresolved rounds are excluded from player shares`:''}.</p>
   <section className="first-kill-leaders"><h2>By player</h2>{leaders.length?<div className="first-kill-table-wrap"><table><thead><tr><th>Player</th><th>Rounds</th><th>Share</th><th>Attack</th><th>Defense</th></tr></thead><tbody>{leaders.map(([slug,p])=><tr key={slug}><th scope="row">{p.name}</th><td>{p.total}</td><td>{Math.round(100*p.total/counted.length)}%</td><td>{p.attack}</td><td>{p.defense}</td></tr>)}</tbody></table></div>:<p>No identified UAH first kills in this view.</p>}</section>
   <section className="first-kill-rounds"><h2>Round by round</h2>{selectedMaps.map(m=><article key={m.id} className="panel"><h3><Link to={`/matches/${m.id}`}>{m.map} vs {m.opponent}</Link> <small>{m.date}</small></h3><div className="first-kill-round-grid">{m.rounds.filter(r=>side==='All'||r.side===side).map(r=><div key={r.number}><b>R{r.number}</b><span>{r.side}</span><strong>{r.status==='recorded'?r.player_name:r.status==='unresolved'?'Player unresolved':'No UAH kill'}</strong><small>{r.result}</small></div>)}</div></article>)}{!selectedMaps.length&&<p>No counted maps in this view.</p>}</section>
  </>}
 </div>
}
