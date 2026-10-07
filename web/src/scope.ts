export function leaderboardPlayers<T extends {status?: string}>(players:T[], includeAlumni=false, historical=false):T[] {
  return players.filter(p=>historical || includeAlumni || p.status!=='Alumni')
}

export function selectedPeriod(seasons:{slug:string}[], active:string|null, saved:string|null):string {
  if(saved==='career'||seasons.some(s=>s.slug===saved))return saved!
  return seasons.some(s=>s.slug===active)?active!:seasons[0]?.slug||'career'
}
