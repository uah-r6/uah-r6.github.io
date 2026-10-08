/** Presentation assets only. Presence here never creates a team or membership. */
export const PROGRAM_LOGO='brand/uah-esports-logo.png'
export const TEAM_LOGOS:Readonly<Record<string,string>>=Object.freeze({
 blue:'brand/teams/blue.png',
 white:'brand/teams/white.png',
 grey:'brand/teams/grey.png',
 black:'brand/teams/black.png',
})
export type TeamLogoIdentity={slug:string;name:string}

export function teamLogoAsset(slug:string|null|undefined):string{
 const key=slug?.trim().toLowerCase()||''
 return Object.hasOwn(TEAM_LOGOS,key)?TEAM_LOGOS[key]:PROGRAM_LOGO
}
export function teamLogoSources(slug:string|null|undefined,base='/'):string[]{
 const prefix=base.endsWith('/')?base:base+'/'
 return [...new Set([teamLogoAsset(slug),PROGRAM_LOGO])].map(asset=>prefix+asset)
}
export function availableTeamLogo(slug:string|null|undefined,failed:readonly string[],base='/'):string|null{
 return teamLogoSources(slug,base).find(src=>!failed.includes(src))||null
}
