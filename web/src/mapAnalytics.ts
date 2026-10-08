import type {RoundCounts,SiteCounts} from './publicTypes.ts'

export function winRate(counts:RoundCounts):number|null {
  return counts.rounds?counts.wins/counts.rounds:null
}
export function rateLabel(counts:RoundCounts) {
  const rate=winRate(counts)
  return rate===null?'—':`${(rate*100).toFixed(1).replace(/\.0$/,'')}%`
}
export function siteLabel(site:SiteCounts) {
  return site.unknown?'Unknown site':site.site.replace(/,\s*/g,' / ')
}
export function sortSites(sites:SiteCounts[]) {
  return [...sites].sort((a,b)=>b.rounds-a.rounds||
    (winRate(b)||0)-(winRate(a)||0)||a.site.localeCompare(b.site))
}
export function bestSite(sites:SiteCounts[]) {
  return sites.filter(s=>!s.unknown&&s.rounds>=2).sort((a,b)=>
    (winRate(b)||0)-(winRate(a)||0)||b.rounds-a.rounds||a.site.localeCompare(b.site))[0]||null
}
