import type {Stats} from './publicTypes'
import {signed} from './presentation'

export function PlayerEntry({stats}:{stats:Stats}) {
 return <section className="panel player-entry" aria-label="Entry breakdown">
  <span className="eyebrow">OPENING DUELS</span><h2>Entry breakdown</h2>
  <p>First valid opposing kill of each round. Entry wins are opening kills; entry losses are opening deaths. Success is wins divided by opening duels, not all rounds played.</p>
  <div className="table-wrap"><table><thead><tr><th>Side</th><th>Entry W–L</th><th>Difference</th><th>Success</th><th>Opening duels</th></tr></thead><tbody>{(['Attack','Defense'] as const).map(side=>{
   const s=stats.sides[side],wins=s.opening_kills,losses=s.opening_deaths
   if(wins===undefined||losses===undefined)return <tr key={side}><th scope="row">{side}</th><td colSpan={4}>Breakdown unavailable</td></tr>
   const duels=wins+losses
   return <tr key={side}><th scope="row">{side}</th><td>{wins}–{losses}</td><td>{signed(wins-losses)}</td><td>{duels?`${Math.round(100*wins/duels)}%`:'—'}</td><td>{duels} <small>in {s.rounds} rounds</small></td></tr>
  })}</tbody></table></div>
 </section>
}
