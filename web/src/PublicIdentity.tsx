import type {ReactNode} from 'react'
import {TeamLogo} from './TeamLogo'
import type {TeamLogoIdentity} from './teamLogos'

export function HeroIdentity({team,title,eyebrow,children,level=1}:{team?:TeamLogoIdentity;title:string;eyebrow:string;children?:ReactNode;level?:1|2}){
 const Title=level===1?'h1':'h2'
 return <div className="hero-identity"><TeamLogo team={team} size="lg" decorative/><div><span className="eyebrow">{eyebrow}</span><Title>{title}</Title>{children}</div></div>
}
export function ScoreDisplay({ours,theirs,label='Recorded maps'}:{ours:number;theirs:number;label?:string}){
 return <div className="score-display" data-score={`${ours}-${theirs}`}><span>{label}</span><strong aria-label={`${ours} to ${theirs}`}><b>{ours}</b><i aria-hidden="true">–</i><b>{theirs}</b></strong></div>
}
