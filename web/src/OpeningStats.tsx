import type {OpeningEngagements} from './publicTypes'
import {openingMetrics,openingValue} from './openingEngagements'
import {StatHelp} from './StatHelp'
import './openingStats.css'

export function OpeningStats({stats}:{stats?:OpeningEngagements}) {
  if(!stats)return null
  return <section className="opening-engagements" aria-label="Opening engagements">
    <h2>Opening engagements</h2>
    <p className="opening-scope">Combined Attack + Defense. Rounds without a valid player opening kill are excluded.</p>
    <div className="opening-grid">{openingMetrics.map(metric=>{
      const overall=openingValue(stats.overall,metric)
      return <article className="opening-card" key={metric.key} aria-label={metric.label}>
        <h3>{metric.label} <StatHelp label={metric.label} help={metric.help} section="advanced-stats"/></h3>
        <div className="opening-headline"><strong>{overall.percentage}</strong><span>{overall.sample} rounds</span></div>
        <dl>{(['attack','defense'] as const).map(side=>{
          const value=openingValue(stats[side],metric)
          return <div key={side}><dt>{side==='attack'?'ATK':'DEF'}</dt><dd><b>{value.percentage}</b><span>{value.sample}</span></dd></div>
        })}</dl>
      </article>
    })}</div>
    {!!stats.unknown_side.eligible_rounds&&<p className="opening-scope">{stats.unknown_side.eligible_rounds} eligible rounds have an unknown side. They remain in the combined sample.</p>}
  </section>
}
