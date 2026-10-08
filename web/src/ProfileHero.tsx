import {useEffect} from 'react'
import {Link} from 'react-router-dom'
import type {Stats,Team} from './publicTypes'
import {HeroIdentity} from './PublicIdentity'
import {profileTeamIdentity} from './publicView'
import {decimal,percent,signed} from './presentation'
import {teamTheme} from './theme'

export function ProfileHero({data,teams,period,career}:{data:Stats&{team_splits:(Stats&{team_slug:string;team_name:string})[]};teams:Team[];period:string;career:boolean}){
 useEffect(()=>{document.title=`${data.name} · ${period} | UAH R6`},[data.name,period])
 const identity=profileTeamIdentity(data.team_splits)
 const theme=teams.find(t=>t.slug===identity.team?.slug)
 const partial=data.rating_rounds!==undefined&&data.rating_maps!==undefined&&(data.rating_rounds<data.rounds||data.rating_maps<data.maps)
 return <header className="public-hero profile-head" style={teamTheme(theme?.primary_color||'#0058A4')}>
  <HeroIdentity team={identity.team} title={data.name} eyebrow={identity.team?.name||'UAH RAINBOW SIX / PLAYER PROFILE'}>
   <div className="hero-meta"><span>{career?'Global career':period}</span><span>{data.status}</span></div>
   <p>{data.rounds} regular roster rounds across {data.maps} maps</p>
   {identity.teams.length>1&&<div className="profile-team-chips" aria-label="Teams in this view">{identity.teams.map(t=><Link className="team-chip" style={teamTheme(teams.find(team=>team.slug===t.slug)?.primary_color||'#0058A4')} key={t.slug} to={`/teams/${t.slug}`}>{t.name}</Link>)}</div>}
  </HeroIdentity>
  <dl className="profile-key-stats"><div><dt>Rating</dt><dd>{decimal(data.rating)}</dd><small>{data.rating===null?'Unrated':partial?'Partial Rating':'Rating'}</small></div><div><dt>K-D</dt><dd>{data.kills}–{data.deaths}</dd><small>{signed(data.kd_diff)} difference</small></div><div><dt>KOST</dt><dd>{percent(data.kost)}</dd></div><div><dt>Entry</dt><dd>{data.opening_kills}–{data.opening_deaths}</dd><small>{signed(data.entry_diff)} difference</small></div></dl>
 </header>
}
