import {useState} from 'react'
import {Link} from 'react-router-dom'
import {ArrowUpRight} from 'lucide-react'
import type {Stats} from './publicTypes'
import {columns,decimal,sortedPlayers} from './presentation'
import type {StatKey} from './presentation'
import {StatHelp} from './StatHelp'

export function PlayerStats({players,historical=false,embed=false}:{players:Stats[];historical?:boolean;embed?:boolean}){
 const [alumni,setAlumni]=useState(false),[sort,setSort]=useState<StatKey>('rating'),[desc,setDesc]=useState(true)
 const sorted=sortedPlayers(players,sort,desc,alumni,historical)
 const change=(key:StatKey)=>{setDesc(sort===key?!desc:true);setSort(key)}
 const playerLink=(p:Stats,i:number)=><Link className="player-link" to={`/players/${p.slug}`} target={embed?'_blank':undefined} rel={embed?'noopener':undefined}><span className="rank">{String(i+1).padStart(2,'0')}</span>{p.name}<ArrowUpRight size={14}/></Link>
 return <div className={`player-stats ${embed?'embedded-stats':''}`}>
 {!historical&&!embed&&<label className="filter-toggle"><input type="checkbox" checked={alumni} onChange={e=>setAlumni(e.target.checked)}/> Include Alumni</label>}
 <div className="table-wrap stats-desktop" role="region" aria-label="Player Stats table" tabIndex={0}><table aria-label="Player Stats"><thead><tr><th scope="col">Player</th>{columns.map(c=><th data-stat={c.key} className={'size' in c?`stat-${c.size}`:''} key={c.key} scope="col" aria-sort={sort===c.key?(desc?'descending':'ascending'):'none'}><div className="stat-column-heading"><button type="button" aria-label={c.label} onClick={()=>change(c.key)}>{c.label}<span aria-hidden="true">{sort===c.key?(desc?' ↓':' ↑'):''}</span></button><StatHelp {...c} embed={embed}/></div></th>)}</tr></thead><tbody>{sorted.map((p,i)=><tr key={p.slug}><td>{playerLink(p,i)}</td>{columns.map(c=><td key={c.key} className={`${'size' in c?`stat-${c.size}`:''} ${c.key==='rating'?'rating':c.key==='kd_diff'||c.key==='entry_diff'?(p[c.key]>0?'positive':p[c.key]<0?'negative':''):''}`} title={c.key==='rating'&&p.rating_rounds!==undefined?`Rating coverage: ${p.rating_rounds} of ${p.rounds} rounds across ${p.rating_maps} of ${p.maps??1} maps`:undefined}>{c.format(p)}</td>)}</tr>)}</tbody></table></div>
 {!embed&&<div className="stats-mobile"><label className="mobile-sort">Sort by <select aria-label="Sort mobile player stats" value={sort} onChange={e=>{setSort(e.target.value as StatKey);setDesc(true)}}>{columns.map(c=><option value={c.key} key={c.key}>{c.label}</option>)}</select><button type="button" onClick={()=>setDesc(!desc)} aria-label={desc?'Sort ascending':'Sort descending'}>{desc?'↓':'↑'}</button></label><div className="mobile-player-list">{sorted.map((p,i)=><article className="mobile-player" key={p.slug}><div className="mobile-player-heading">{playerLink(p,i)}<div className="mobile-rating"><span>Rating <StatHelp {...columns[0]}/></span><strong>{decimal(p.rating)}</strong></div></div><dl>{columns.filter(c=>['kd_diff','kost','entry_diff','kpr'].includes(c.key)).map(c=><div key={c.key}><dt>{c.label} <StatHelp {...c}/></dt><dd>{c.format(p)}</dd></div>)}</dl></article>)}</div></div>}
 {!sorted.length&&<div className="empty">No player statistics available yet.</div>}
 </div>
}
