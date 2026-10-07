export type ValidationPoint = {
  player: string; map: string; match_id: number; game_id: number;
  target: number; prediction: number; v2_prediction: number
}
export type ValidationData = {
  version: string; event: string; evaluation: string; freeze_commit: string;
  report_url: string; maps: number; rosters: number;
  metrics: { rows: number; mae: number; v2_mae: number; within_005: number };
  points: ValidationPoint[]
}

export function validationMetrics(points: ValidationPoint[]) {
  const n = points.length
  if (!n) throw new Error('Empty validation data')
  return {
    rows: n,
    mae: points.reduce((sum, p) => sum + Math.abs(p.prediction - p.target), 0) / n,
    v2_mae: points.reduce((sum, p) => sum + Math.abs(p.v2_prediction - p.target), 0) / n,
    within_005: points.filter(p => Math.abs(p.prediction - p.target) <= .05).length / n,
  }
}

export function validationDomain(points: ValidationPoint[]) {
  const values = points.flatMap(p => [p.target, p.prediction])
  const min = Math.floor((Math.min(...values) - .1) * 2) / 2
  const max = Math.ceil((Math.max(...values) + .1) * 2) / 2
  const step = max - min > 3 ? 1 : .5
  const ticks: number[] = []
  for (let n = Math.ceil(min / step) * step; n <= max; n += step) ticks.push(n)
  return { min, max, ticks }
}

export function readValidationData(input: unknown): ValidationData {
  const d = input as ValidationData
  if (!d || d.version !== 'siege_style_v3' || !Array.isArray(d.points) || d.points.length !== 110
    || typeof d.event !== 'string' || d.maps !== 11 || d.rosters !== 8
    || d.points.some(p => typeof p.player !== 'string' || typeof p.map !== 'string'
      || ![p.target, p.prediction, p.v2_prediction, p.match_id, p.game_id].every(Number.isFinite))) {
    throw new Error('Invalid frozen validation data')
  }
  const metrics = validationMetrics(d.points)
  if (!d.metrics || Object.entries(metrics).some(([k, value]) => Math.abs(value - d.metrics[k as keyof typeof metrics]) > 1e-12)) {
    throw new Error('Validation summary differs from points')
  }
  return d
}
