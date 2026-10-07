import { useEffect, useRef, useState } from 'react'
import { readValidationData, validationDomain, type ValidationData } from './ratingValidation'

export function RatingChart() {
  const [data, setData] = useState<ValidationData | null>(null)
  const [failed, setFailed] = useState(false)
  const [selected, setSelected] = useState(0)
  const svg = useRef<SVGSVGElement>(null)
  useEffect(() => {
    const controller = new AbortController()
    fetch(import.meta.env.BASE_URL + 'methodology/rating-v3-final.json', { signal: controller.signal })
      .then(r => { if (!r.ok) throw Error('Unavailable'); return r.json() })
      .then(readValidationData).then(setData)
      .catch(e => { if (e.name !== 'AbortError') setFailed(true) })
    return () => controller.abort()
  }, [])

  return <section className="panel validation-panel" aria-labelledby="validation-title">
    <span className="eyebrow">TESTED ON AN UNTOUCHED EVENT</span>
    <h3 id="validation-title">How close is Rating to SiegeGG?</h3>
    <p>The model was frozen before seeing this event’s target Ratings. Each point compares one professional player’s map performance with the public SiegeGG Rating.</p>
    <div className="validation-metrics">
      <div><strong>0.03036</strong><span>v3 mean absolute error</span></div>
      <div><strong>81.82%</strong><span>within ±0.05 Rating</span></div>
      <div><strong>110</strong><span>player-map observations</span></div>
    </div>
    {!data && <p role="status">{failed ? 'The interactive chart is unavailable. The frozen final results are summarized above.' : 'Loading validation chart…'}</p>}
    {data && (() => {
      const { min, max, ticks } = validationDomain(data.points)
      const left = 68, top = 24, size = 430
      const x = (n: number) => left + (n - min) / (max - min) * size
      const y = (n: number) => top + size - (n - min) / (max - min) * size
      const point = data.points[selected]
      const move = (index: number, focus = false) => {
        const next = (index + data.points.length) % data.points.length
        setSelected(next)
        if (focus) requestAnimationFrame(() => svg.current?.querySelector<SVGCircleElement>(`[data-point="${next}"]`)?.focus())
      }
      return <>
        <p className="chart-instructions" id="chart-instructions">Hover or tap a point. With the chart focused, use arrow keys to explore; Tab leaves the chart. The diagonal shows perfect agreement.</p>
        <div className="chart-layout">
          <svg ref={svg} viewBox="0 0 535 515" className="rating-scatter" role="group" aria-label="Public SiegeGG Rating versus siege_style_v3 prediction" aria-describedby="chart-instructions">
            <title>Frozen v3 final evaluation: 110 player-map predictions</title>
            <rect x={left} y={top} width={size} height={size} className="plot-background"/>
            {ticks.map(tick => <g key={tick} aria-hidden="true">
              <line x1={x(tick)} x2={x(tick)} y1={top} y2={top+size} className="plot-grid"/>
              <line x1={left} x2={left+size} y1={y(tick)} y2={y(tick)} className="plot-grid"/>
              <text x={x(tick)} y={top+size+24} textAnchor="middle">{tick.toFixed(1)}</text>
              <text x={left-12} y={y(tick)+4} textAnchor="end">{tick.toFixed(1)}</text>
            </g>)}
            <line x1={x(min)} y1={y(min)} x2={x(max)} y2={y(max)} className="agreement-line" aria-label="Perfect agreement: y equals x"/>
            <text x={left+size/2} y="507" textAnchor="middle">Public SiegeGG Rating</text>
            <text transform="translate(18 239) rotate(-90)" textAnchor="middle">siege_style_v3 prediction</text>
            {data.points.map((p, i) => <circle key={`${p.game_id}-${p.player}`} data-point={i}
              cx={x(p.target)} cy={y(p.prediction)} r={i === selected ? 7 : 5}
              className={`prediction-point ${i === selected ? 'selected' : ''}`} role="button"
              tabIndex={i === selected ? 0 : -1}
              aria-label={`${p.player}, ${p.map}, game ${p.game_id}: SiegeGG ${p.target.toFixed(2)}, v3 ${p.prediction.toFixed(4)}`}
              aria-pressed={i === selected} onMouseEnter={() => move(i)} onFocus={() => move(i)} onClick={() => move(i)}
              onKeyDown={e => {
                if (['ArrowRight', 'ArrowDown', 'ArrowLeft', 'ArrowUp'].includes(e.key)) {
                  e.preventDefault(); move(i + (['ArrowRight', 'ArrowDown'].includes(e.key) ? 1 : -1), true)
                } else if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); move(i) }
              }}/>) }
          </svg>
          <div className="chart-detail">
            <span className="eyebrow">SELECTED PLAYER / MAP</span>
            <div className="point-readout" aria-live="polite" aria-atomic="true">
              <h4>{point.player}</h4><p>{point.map} · Game {point.game_id}</p>
              <dl><div><dt>SiegeGG</dt><dd>{point.target.toFixed(2)}</dd></div>
                <div><dt>Our v3</dt><dd>{point.prediction.toFixed(4)}</dd></div>
                <div><dt>Difference</dt><dd>{point.prediction-point.target >= 0 ? '+' : ''}{(point.prediction-point.target).toFixed(4)}</dd></div></dl>
            </div>
            <label className="point-selector">Explore an observation
              <select value={selected} onChange={e => move(Number(e.target.value))}>
                {data.points.map((p, i) => <option key={i} value={i}>{p.player} · {p.map} · {p.game_id}</option>)}
              </select>
            </label>
            <div className="point-controls"><button type="button" onClick={() => move(selected-1)}>← Previous</button><button type="button" onClick={() => move(selected+1)}>Next →</button></div>
            <p className="chart-event">{data.event}<br/>{data.maps} maps · {data.rosters} rosters</p>
          </div>
        </div>
        <p className="validation-footnote">On these same 110 observations, v2’s mean absolute error was {data.metrics.v2_mae.toFixed(5)}. These are final-event results, not a training curve or a guarantee for every match. Rare 1v4/1v5 clutches and wider event coverage still need more independent validation.</p>
        <a className="method-source" href="https://github.com/uah-r6/uah-r6.github.io/blob/main/research/output/v3-native-final-apac1-result.md">Read the frozen final report ↗</a>
      </>
    })()}
  </section>
}
