import {Link} from 'react-router-dom'
import type {PublicRound} from './publicTypes'

export function RoundBreakdown({rounds}:{rounds:PublicRound[]}){
 return <><div className="rounds map-rounds">{rounds.map(r=><div className={`round curated-round ${r.highlights?.length?'has-highlights':''}`} key={r.number}><b>R{r.number}</b><span>{r.side==='Attack'?'ATK':r.side==='Defense'?'DEF':r.side}</span><span className="round-site">{r.site}</span><strong className={r.result==='Win'?'positive':'negative'}>{r.result}</strong>{!!r.highlights?.length&&<div className="round-highlights">{r.highlights.map(h=><Link to={`/players/${h.player_slug}`} key={h.player_slug} className={`highlight-pill ${h.emphasis}`} aria-label={`${h.player_name}: ${h.labels.join(', ')}`}><span className="highlight-player">{h.player_name}</span><span>· {h.labels.join(' · ')}</span></Link>)}</div>}</div>)}</div><p className="highlight-note">Selected replay-verified moments only. Most rounds have no label. <Link to="/methodology/advanced-stats">About round highlights →</Link></p></>
}
