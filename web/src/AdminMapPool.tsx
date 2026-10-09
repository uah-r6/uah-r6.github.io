import {useEffect,useState} from 'react'
import './adminMapPool.css'

type Season={slug:string;name:string;active:number}
type Pool={season:string;season_name:string;configured:boolean;origin:string|null;updated_at:string|null;maps:{slug:string;name:string}[];catalog:{slug:string;name:string}[]}
type Api=<T>(path:string,method?:string,body?:unknown)=>Promise<T>

export function AdminMapPool({seasons,initialSeason,api,notify}:{seasons:Season[];initialSeason:string;api:Api;notify:(text:string,error?:boolean)=>void}) {
  const [season,setSeason]=useState(initialSeason||seasons.find(s=>s.active)?.slug||seasons[0]?.slug||'')
  const [pool,setPool]=useState<Pool|null>(null),[selected,setSelected]=useState<string[]>([])
  const [busy,setBusy]=useState(false),[error,setError]=useState('')
  const dirty=!!pool&&(selected.length!==pool.maps.length||selected.some(s=>!pool.maps.some(m=>m.slug===s)))
  useEffect(()=>{window.dispatchEvent(new CustomEvent('uah-map-pool-dirty',{detail:dirty}));return()=>{window.dispatchEvent(new CustomEvent('uah-map-pool-dirty',{detail:false}))}},[dirty])
  useEffect(()=>{if(!season&&seasons.length)setSeason(initialSeason||seasons.find(s=>s.active)?.slug||seasons[0].slug)},[season,seasons,initialSeason])
  useEffect(()=>{let current=true;setPool(null);setError('');if(season)api<Pool>(`/seasons/${season}/map-pool`).then(p=>{if(current){setPool(p);setSelected(p.maps.map(m=>m.slug))}}).catch(e=>{if(current)setError(e.message)});return()=>{current=false}},[season,api])
  useEffect(()=>{if(!dirty)return;const warn=(e:BeforeUnloadEvent)=>{e.preventDefault();e.returnValue=''};window.addEventListener('beforeunload',warn);return()=>window.removeEventListener('beforeunload',warn)},[dirty])
  const switchSeason=(slug:string)=>{if(dirty&&!window.confirm('Discard unsaved map-pool changes?'))return;setSeason(slug)}
  async function save() {
    if(!pool)return
    if(!selected.length&&!window.confirm('Save an empty competitive map pool? Public Maps will show no cards for this season. Historical matches remain available.'))return
    setBusy(true);setError('')
    try{const saved=await api<Pool>(`/seasons/${season}/map-pool`,'PUT',{map_slugs:selected,confirm_empty:!selected.length});setPool(saved);setSelected(saved.maps.map(m=>m.slug));notify(`Map pool saved for ${saved.season_name}. Local website data refreshed; publish when ready.`)}catch(e){setError((e as Error).message)}finally{setBusy(false)}
  }
  return <section className="admin-panel competitive-map-pool">
    <div className="admin-panel-head"><div><span className="eyebrow">PUBLIC MAP ANALYTICS</span><h2>Competitive Map Pool</h2><p>Choose the maps that should appear in public map analytics for this season. Historical matches are never deleted when a map is removed from the pool.</p></div></div>
    <label className="pool-season-label">Season<select aria-label="Map pool season" value={season} disabled={busy} onChange={e=>switchSeason(e.target.value)}>{!seasons.length&&<option value="">Create a season first</option>}{seasons.map(s=><option key={s.slug} value={s.slug}>{s.name}{s.active?' · active':''}</option>)}</select></label>
    {error&&<div className="admin-error" role="alert">{error}</div>}
    {pool?<><p className="pool-save-state" role="status">{selected.length} selected · {dirty?'Unsaved changes':pool.configured?'Saved configuration':'Not configured yet'}</p>
      {pool.origin==='preserved_visible_catalog_v1'&&<p className="pool-migration-note">The previous visible map list was preserved during setup. Select your season’s competitive maps and save; this list is not an official map pool.</p>}
      <fieldset disabled={busy}><legend className="pool-legend">Tracker-supported maps · alphabetical order</legend><div className="pool-checkbox-grid">{pool.catalog.map(m=><label key={m.slug}><input type="checkbox" checked={selected.includes(m.slug)} onChange={e=>setSelected(current=>e.target.checked?[...current,m.slug]:current.filter(s=>s!==m.slug))}/>{m.name}</label>)}</div></fieldset>
      <div className="pool-actions"><button className="admin-button" disabled={busy||(!dirty&&pool.configured)} onClick={()=>void save()}>{busy?'Saving…':'Save Map Pool'}</button><button className="admin-button secondary" disabled={busy||!dirty} onClick={()=>setSelected(pool.maps.map(m=>m.slug))}>Reset changes</button></div>
      {!selected.length&&<p className="pool-empty-warning">An empty pool hides all grid cards. Saving requires confirmation.</p>}
    </>:!error&&season?<p>Loading map pool…</p>:null}
  </section>
}
