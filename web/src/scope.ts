export function leaderboardPlayers<T extends {status?: string}>(players:T[], includeAlumni=false, historical=false):T[] {
  return players.filter(p=>historical || includeAlumni || p.status!=='Alumni')
}

export function selectedPeriod(seasons:{slug:string}[], active:string|null, saved:string|null):string {
  if(saved==='career'||seasons.some(s=>s.slug===saved))return saved!
  return seasons.some(s=>s.slug===active)?active!:seasons[0]?.slug||'career'
}

type PublicTeam = {slug:string;aliases:string[];active:number}
export function resolveTeam<T extends PublicTeam>(teams:T[], requested:string|null|undefined):T|undefined {
  return teams.find(t=>t.slug===requested||t.aliases.includes(requested||''))
}
export function leaderboardTeam<T extends PublicTeam>(teams:T[], requested:string|null):T|undefined {
  return resolveTeam(teams,requested)||resolveTeam(teams,'blue')||teams.find(t=>t.active)
}

// A deliberate choice survives navigation/refresh in this tab, not a later visit.
export function sessionPeriod(saved:string|null, now=Date.now()):string|null {
  try {const value=JSON.parse(saved||'null');return value&&typeof value.period==='string'&&typeof value.at==='number'&&now>=value.at&&now-value.at<12*60*60*1000?value.period:null}catch{return null}
}
export function playerScope(value:string|null):'roster'|'subs' {return value==='subs'?'subs':'roster'}
