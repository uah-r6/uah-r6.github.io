import {useState} from 'react'
import {availableTeamLogo,type TeamLogoIdentity} from './teamLogos'
import './teamLogos.css'

/** Adjacent team names make the logo decorative in most page headers. */
export function TeamLogo({team,size='md',decorative=false,assetBase=import.meta.env.BASE_URL}:{team?:TeamLogoIdentity;size?:'sm'|'md'|'lg';decorative?:boolean;assetBase?:string}){
 const [failed,setFailed]=useState<string[]>([])
 const src=availableTeamLogo(team?.slug,failed,assetBase)
 const name=team?.name||'UAH R6'
 return <span className={`team-logo team-logo-${size}`} data-team-logo={team?.slug||'program'}>
  {src?<img key={src} src={src} width={1080} height={1080} decoding="async" alt={decorative?'':`${name} logo`} onError={()=>setFailed(previous=>previous.includes(src)?previous:[...previous,src])}/>:<span className="team-logo-fallback" role={decorative?undefined:'img'} aria-label={decorative?undefined:`${name} logo unavailable`} aria-hidden={decorative?true:undefined}>UAH</span>}
 </span>
}
