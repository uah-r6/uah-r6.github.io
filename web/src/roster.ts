export type RosterIdentity={id:number;username:string;aliases:string[]}
export function existingRosterIdentity<T extends RosterIdentity>(players:T[],username:string):T|undefined{
 const key=username.trim().toLowerCase()
 if(!key)return undefined
 const matches=players.filter(p=>[p.username,...p.aliases].some(a=>a.trim().toLowerCase()===key))
 return matches.length===1?matches[0]:undefined
}
