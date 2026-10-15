import type {OpeningCounts} from './publicTypes'

export const openingMetrics = [
  {key:'opening_kill_pct',label:'Opening Kill %',numerator:'opening_kills',denominator:'eligible_rounds',help:'Percentage of eligible rounds where this team gets the first kill.'},
  {key:'conversion_pct',label:'Opening Kill Conversion %',numerator:'opening_kill_wins',denominator:'opening_kills',help:'Percentage of rounds won after this team gets the opening kill.'},
  {key:'recovery_pct',label:'Opening Death Recovery %',numerator:'opening_death_wins',denominator:'opening_deaths',help:'Percentage of rounds won after this team suffers the opening death.'},
] as const

export function openingValue(counts:OpeningCounts,metric:typeof openingMetrics[number]) {
  const numerator=counts[metric.numerator],denominator=counts[metric.denominator]
  return {percentage:denominator?`${(100*numerator/denominator).toFixed(1)}%`:'—',sample:`${numerator} / ${denominator}`}
}
