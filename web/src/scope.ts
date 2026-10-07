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
