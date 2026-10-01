import React, { useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { Activity, ArrowRight, Check, ChevronRight, ClipboardList, CloudUpload, Crosshair, Database, FolderSearch, LayoutDashboard, Play, Plus, RefreshCw, Settings, ShieldCheck, Swords, Users } from 'lucide-react'
import './style.css'
import './admin.css'

type Page = 'dashboard' | 'replays' | 'roster' | 'seasons' | 'matches' | 'statistics' | 'publish' | 'settings'
type Season = { slug: string; name: string; active: number; start_date: string | null; end_date: string | null }
type Player = { id: number; slug: string; display_name: string; username: string; tracked: number; profile_bound: boolean; aliases: string[] }
type Series = { id: string; opponent: string; date: string; week: string; notes: string; season_slug: string; maps: number }
type Replay = { id: string; name: string; map?: string; timestamp?: string; match_type?: string; status: string; eligible: boolean; tracked_count?: number; rounds?: number; score?: number[]; our_team?: number | null; duplicate?: boolean }
type Preview = { preview_token: string; map: string; timestamp: string; match_type: string; game_mode: string; rounds: number; score: number[]; our_team: number | null; tracked_players: string[]; teams: { index: number; players: string[] }[]; ambiguous: string | null; duplicate: boolean; active_season: string | null; competition_if_confirmed: string }
type RehostRound = { segment: number; physical_number: number; filename: string; site: string; winner: number; physical_score: number[]; logical_score: number[]; logical_number: number | null; exclusion_reason: string | null }
type RehostPreview = Preview & { segments: { segment: number; source_name: string }[]; physical_rounds: RehostRound[] }
type MapRow = { id: string; map_name: string; match_type: string; our_score: number; their_score: number; opponent: string; date: string; series_date: string; week: string; notes: string; season_name: string; season_slug: string; series_id: string; competition: string; demo: number }
type ArchiveStatus = { status: string; message: string; rounds: number; path: string }
type KDPlayer = { player_id: number; name: string; tracked: boolean; replay_kills: number; replay_deaths: number; final_kills: number; final_deaths: number; kill_adjustment: number; death_adjustment: number; reason: string; note: string; updated_at: string | null; corrected: boolean }
type MatchDetail = MapRow & { replay_data_complete: number; manual_kd_correction: boolean; rating_eligible: boolean; kd_players: KDPlayer[]; game_mode: string; tracked_players: string[]; rounds: { number: number; site: string; result: string }[]; archive: ArchiveStatus; source_kind: 'normal' | 'rehost'; rehost: { segments: { segment: number; source_name: string }[]; mapping: { segment: number; filename: string; physical_number: number; logical_number: number | null; exclusion_reason: string | null }[]; final_scores: number[] } | null }
type Dashboard = { active_season: { slug: string; name: string } | null; roster_count: number; maps_imported: number; demo_maps: number; last_imported: { id: string; map_name: string; opponent: string; date: string; season: string } | null; last_publish: { at: string; commit: string } | null; database: { status: string; path: string; size_bytes: number } }
type SettingsData = { team_name: string; short_name: string; accent: string; replay_path: string; trade_window_seconds: number; rating_version: string; publishing_enabled: boolean; branch: string; remote_url: string; site_url: string }

let adminToken = ''
async function api<T>(path: string, method = 'GET', body?: unknown): Promise<T> {
  if (!adminToken) {
    const session = await fetch('/api/admin/session', { cache: 'no-store' }).then(response => response.json())
    adminToken = session.token
  }
  const response = await fetch(`/api/admin${path}`, {
    method,
    cache: 'no-store',
    headers: method === 'GET' ? {} : { 'Content-Type': 'application/json', 'X-R6-Admin-Token': adminToken },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  const data = await response.json()
  if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'The request could not be completed.')
  return data as T
}

const nav: { id: Page; title: string; icon: React.ReactNode }[] = [
  { id: 'dashboard', title: 'Dashboard', icon: <LayoutDashboard size={18} /> },
  { id: 'replays', title: 'Import Match', icon: <FolderSearch size={18} /> },
  { id: 'roster', title: 'Roster', icon: <Users size={18} /> },
  { id: 'seasons', title: 'Seasons', icon: <Swords size={18} /> },
  { id: 'matches', title: 'Matches', icon: <ClipboardList size={18} /> },
  { id: 'statistics', title: 'Statistics', icon: <Activity size={18} /> },
  { id: 'publish', title: 'Publish', icon: <CloudUpload size={18} /> },
  { id: 'settings', title: 'Settings', icon: <Settings size={18} /> },
]

function App() {
  const [page, setPage] = useState<Page>('dashboard')
  const [notice, setNotice] = useState<{ text: string; error: boolean } | null>(null)
  const notify = (text: string, error = false) => setNotice({ text, error })
  return <div className="admin-shell">
    <aside className="admin-sidebar">
      <div className="admin-brand"><span><Crosshair size={24} /></span><div><strong>NECC // CONTROL</strong><small>LOCAL TRACKER ADMIN</small></div></div>
      <div className="sidebar-label">WORKSPACE</div>
      <nav>{nav.map(item => <button key={item.id} className={page === item.id ? 'selected' : ''} onClick={() => { setPage(item.id); setNotice(null) }}>{item.icon}<span>{item.title}</span><ChevronRight size={15} /></button>)}</nav>
      <div className="sidebar-foot"><span className="live-dot" /> Running on this PC<br /><small>127.0.0.1 · private local API</small></div>
    </aside>
    <div className="admin-main">
      <div className="admin-topbar"><div><span className="eyebrow">LOCAL OPERATIONS</span><strong>{nav.find(item => item.id === page)?.title}</strong></div><span className="admin-local"><ShieldCheck size={15} /> Local only</span></div>
      <div className="admin-content">
        {notice && <div className={`admin-notice ${notice.error ? 'error' : 'success'}`}><span>{notice.text}</span><button onClick={() => setNotice(null)}>×</button></div>}
        {page === 'dashboard' && <DashboardPage go={setPage} />}
        {page === 'replays' && <ReplaysPage notify={notify} />}
        {page === 'roster' && <RosterPage notify={notify} />}
        {page === 'seasons' && <SeasonsPage notify={notify} />}
        {page === 'matches' && <MatchesPage notify={notify} />}
        {page === 'statistics' && <StatisticsPage notify={notify} />}
        {page === 'publish' && <PublishPage notify={notify} />}
        {page === 'settings' && <SettingsPage notify={notify} />}
      </div>
    </div>
  </div>
}

function PageHead({ label, title, description, action }: { label: string; title: string; description: string; action?: React.ReactNode }) {
  return <div className="admin-heading"><div><span className="eyebrow">{label}</span><h1>{title}</h1><p>{description}</p></div>{action}</div>
}
function Button({ children, onClick, disabled, secondary = false, type = 'button' }: { children: React.ReactNode; onClick?: () => void; disabled?: boolean; secondary?: boolean; type?: 'button' | 'submit' }) {
  return <button className={`admin-button ${secondary ? 'secondary' : ''}`} type={type} onClick={onClick} disabled={disabled}>{children}</button>
}
function ErrorBox({ message }: { message: string }) { return message ? <div className="admin-inline-error">{message}</div> : null }

function DashboardPage({ go }: { go: (page: Page) => void }) {
  const [data, setData] = useState<Dashboard | null>(null)
  const [error, setError] = useState('')
  const load = () => api<Dashboard>('/dashboard').then(setData).catch(error => setError(error.message))
  useEffect(() => { void load() }, [])
  return <><PageHead label="OVERVIEW / SYSTEM STATUS" title="Your command center" description="Everything you need to keep your NECC season current." action={<Button secondary onClick={() => void load()}><RefreshCw size={15} /> Refresh</Button>} />
    <ErrorBox message={error} />
    <div className="admin-metrics">
      <div><span>ACTIVE SEASON</span><strong>{data?.active_season?.name || 'Not set'}</strong><Swords size={21} /></div>
      <div><span>TRACKED PLAYERS</span><strong>{data?.roster_count ?? '—'}</strong><Users size={21} /></div>
      <div><span>NECC MAPS</span><strong>{data?.maps_imported ?? '—'}</strong><Crosshair size={21} /></div>
      <div><span>DATABASE</span><strong className={data?.database.status === 'ok' ? 'positive' : 'negative'}>{data?.database.status || '—'}</strong><Database size={21} /></div>
    </div>
    <div className="admin-columns">
      <section className="admin-panel"><span className="eyebrow">LATEST ACTIVITY</span><h2>Last imported map</h2>{data?.last_imported ? <div className="activity-row"><span><b>vs {data.last_imported.opponent}</b><small>{data.last_imported.map_name} · {data.last_imported.season}</small></span><em>{data.last_imported.date}</em></div> : <p className="admin-muted">No real NECC maps have been imported yet.</p>}<div className="panel-action"><Button onClick={() => go('replays')}><FolderSearch size={16} /> Review replays <ArrowRight size={15} /></Button></div></section>
      <section className="admin-panel"><span className="eyebrow">WEBSITE</span><h2>Last publish</h2>{data?.last_publish ? <div className="activity-row"><span><b>Submitted to GitHub</b><small>Commit {data.last_publish.commit}</small></span><em>{new Date(data.last_publish.at).toLocaleString()}</em></div> : <p className="admin-muted">No successful publish recorded on this PC.</p>}<div className="panel-action"><Button secondary onClick={() => go('publish')}><CloudUpload size={16} /> Open publishing</Button></div></section>
    </div>
    <div className="admin-status"><Activity size={17} /><span>Database: {data?.database.path || 'Loading…'}</span>{data?.demo_maps ? <b>{data.demo_maps} demo maps present. Clear them before a real import.</b> : <b>Real imports ready</b>}</div>
  </>
}

function ReplaysPage({ notify }: { notify: (text: string, error?: boolean) => void }) {
  const [importType, setImportType] = useState<'normal' | 'rehost'>('normal')
  const [items, setItems] = useState<Replay[]>([])
  const [seasons, setSeasons] = useState<Season[]>([])
  const [series, setSeries] = useState<Series[]>([])
  const [preview, setPreview] = useState<Preview | null>(null)
  const [selectedId, setSelectedId] = useState('')
  const [manualPath, setManualPath] = useState('')
  const [team, setTeam] = useState<number | null>(null)
  const [season, setSeason] = useState('')
  const [opponent, setOpponent] = useState('')
  const [week, setWeek] = useState('')
  const [notes, setNotes] = useState('')
  const [seriesId, setSeriesId] = useState('')
  const [confirmed, setConfirmed] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  useEffect(() => { api<Season[]>('/seasons').then(rows => { setSeasons(rows); setSeason(rows.find(row => row.active)?.slug || rows[0]?.slug || '') }).catch(error => setError(error.message)) }, [])
  useEffect(() => { if (season) api<Series[]>(`/series?season=${encodeURIComponent(season)}`).then(setSeries).catch(error => setError(error.message)); else setSeries([]) }, [season])
  async function scan() { setBusy(true); setError(''); setPreview(null); try { setItems(await api<Replay[]>('/replays')); notify('Replay scan completed.') } catch (error) { setError((error as Error).message) } finally { setBusy(false) } }
  async function review(replayId?: string, path?: string, chosenTeam?: number) { setBusy(true); setError(''); try { const result = await api<Preview>('/replays/preview', 'POST', { replay_id: replayId || null, path: path || null, team: chosenTeam ?? null }); setPreview(result); setSelectedId(replayId || ''); setTeam(result.our_team); setConfirmed(false); if (result.active_season) setSeason(result.active_season); if (result.duplicate) notify('This replay has already been imported.', true) } catch (error) { setError((error as Error).message) } finally { setBusy(false) } }
  async function importMap() { if (!preview) return; setBusy(true); setError(''); try { const result = await api<{ map_id: string; rounds: number }>('/replays/import', 'POST', { preview_token: preview.preview_token, season_slug: season, opponent, week, notes, series_id: seriesId || null, team, confirm_necc: confirmed }); notify(`Imported ${result.rounds} rounds as NECC map ${result.map_id}. Website data refreshed.`); setPreview(null); setConfirmed(false); setOpponent(''); setSeriesId(''); void scan() } catch (error) { setError((error as Error).message) } finally { setBusy(false) } }
  const selectedSeries = series.find(row => row.id === seriesId)
  if (importType === 'rehost') return <><PageHead label="REPLAY OPERATIONS" title="Import an NECC rehost" description="Choose ordered Custom Game folders, mark abandoned rounds, and confirm the competitive score." action={<Button onClick={() => void scan()} disabled={busy}><FolderSearch size={16} /> Scan replay folder</Button>} />
    <div className="import-type"><Button secondary onClick={() => setImportType('normal')}>Normal map</Button><Button onClick={() => setImportType('rehost')}>Rehosted map</Button></div>
    <ErrorBox message={error} />
    <RehostImportPanel items={items} seasons={seasons} series={series} season={season} setSeason={setSeason} setSeriesId={setSeriesId} notify={notify} afterImport={scan} />
  </>
  return <><PageHead label="REPLAY OPERATIONS" title="Import an NECC map" description="Scan replays, select one Custom Game, then explicitly confirm it was your NECC match." action={<Button onClick={() => void scan()} disabled={busy}><FolderSearch size={16} /> {busy ? 'Working…' : 'Scan replay folder'}</Button>} />
    <div className="import-type"><Button onClick={() => setImportType('normal')}>Normal map</Button><Button secondary onClick={() => setImportType('rehost')}>Rehosted map</Button></div>
    <ErrorBox message={error} />
    <div className="admin-panel admin-tip"><ShieldCheck size={22} /><div><b>Custom Game is eligibility, not proof of NECC.</b><p>Ranked, Standard and Quick Match cannot be selected. Scrims and other Custom Games stay out of your stats unless you choose and confirm them.</p></div></div>
    <section className="admin-panel"><div className="admin-panel-head"><div><span className="eyebrow">RECENT REPLAYS</span><h2>MatchReplay folder</h2></div><small>{items.length ? `${items.length} replay folders` : 'Click Scan replay folder to begin'}</small></div>
      {items.length ? <div className="replay-list">{items.map(item => <div className={`replay-item ${item.eligible ? '' : 'disabled'}`} key={item.id}><div className="replay-icon"><Play size={17} /></div><div className="replay-meta"><b>{item.map || item.name}</b><small>{item.timestamp?.slice(0, 16) || item.name} · {item.rounds ?? '—'} rounds · {item.our_team != null && item.score ? `${item.score[item.our_team]}–${item.score[1 - item.our_team]} · ` : ''}{item.tracked_count ?? '—'} roster matches</small></div><span className={`replay-status ${item.eligible ? 'eligible' : 'ineligible'}`}>{item.duplicate ? 'ALREADY IMPORTED' : item.status}</span><Button secondary disabled={!item.eligible || item.duplicate || busy} onClick={() => void review(item.id)}>Preview</Button></div>)}</div> : <p className="admin-muted">No replay scan results yet.</p>}
      <div className="manual-path"><label>Or paste a complete match folder / ZIP path<input value={manualPath} onChange={event => setManualPath(event.target.value)} placeholder="C:\...\Match-folder" /></label><Button secondary disabled={!manualPath.trim() || busy} onClick={() => void review(undefined, manualPath)}>Preview path</Button></div>
    </section>
    {preview && <section className="admin-panel preview-panel"><span className="eyebrow">IMPORT PREVIEW</span><h2>{preview.map} <span>· {preview.match_type}</span></h2><div className="preview-facts"><div><small>DATE</small><b>{preview.timestamp.slice(0, 10)}</b></div><div><small>ROUNDS</small><b>{preview.rounds}</b></div><div><small>MODE</small><b>{preview.game_mode}</b></div><div><small>SCORE</small><b>{team === null ? 'Choose team' : `${preview.score[team]} – ${preview.score[1 - team]}`}</b></div></div>
      <div className="team-choices"><b>Tracked team</b><p>{preview.tracked_players.join(', ') || 'Choose your team below.'}</p>{preview.teams.map(choice => <div key={choice.index}><span>Team {choice.index}: {choice.players.join(', ')}</span>{preview.ambiguous && <Button secondary onClick={() => void review(selectedId || undefined, selectedId ? undefined : manualPath, choice.index)}>Use team {choice.index}</Button>}</div>)}</div>
      {preview.ambiguous && <div className="admin-inline-error">{preview.ambiguous}</div>}
      {preview.duplicate && <div className="admin-inline-error">This replay has already been imported. No changes can be made.</div>}
      <div className="form-grid"><label>Season<select value={season} onChange={event => { setSeason(event.target.value); setSeriesId('') }}><option value="">Select season</option>{seasons.map(row => <option value={row.slug} key={row.slug}>{row.name}</option>)}</select></label><label>Series<select value={seriesId} onChange={event => { const id = event.target.value; setSeriesId(id); const found = series.find(row => row.id === id); if (found) { setOpponent(found.opponent); setWeek(found.week || '') } }}><option value="">New series / matchup</option>{series.map(row => <option value={row.id} key={row.id}>vs {row.opponent} · {row.date} ({row.maps} maps)</option>)}</select></label><label>Opponent name<input value={opponent} onChange={event => setOpponent(event.target.value)} placeholder="e.g. UAB" readOnly={!!selectedSeries} /></label><label>NECC week (optional)<input value={week} onChange={event => setWeek(event.target.value)} placeholder="Week 4" /></label><label className="wide">Notes (optional)<textarea value={notes} onChange={event => setNotes(event.target.value)} placeholder="Series context or match notes" rows={3} /></label></div>
      <label className="confirm-line"><input type="checkbox" checked={confirmed} onChange={event => setConfirmed(event.target.checked)} /><span>I manually selected this Custom Game and confirm it was an <b>NECC match</b>. Store it as competition = NECC.</span></label>
      <Button disabled={busy || !confirmed || !opponent.trim() || !season || team === null || preview.duplicate} onClick={() => void importMap()}><Check size={16} /> {busy ? 'Importing…' : 'Import NECC map'}</Button>
    </section>}
  </>
}

type SegmentChoice = { replay_id: string; path: string }

function RehostImportPanel({ items, seasons, series, season, setSeason, setSeriesId, notify, afterImport }: {
  items: Replay[]; seasons: Season[]; series: Series[]; season: string;
  setSeason: (value: string) => void; setSeriesId: (value: string) => void;
  notify: (text: string, error?: boolean) => void; afterImport: () => Promise<void>
}) {
  const [segments, setSegments] = useState<SegmentChoice[]>([{ replay_id: '', path: '' }, { replay_id: '', path: '' }])
  const [exclusions, setExclusions] = useState<Record<string, string>>({})
  const [preview, setPreview] = useState<RehostPreview | null>(null)
  const [dirty, setDirty] = useState(false)
  const [team, setTeam] = useState<number | null>(null)
  const [finalOur, setFinalOur] = useState('')
  const [finalTheir, setFinalTheir] = useState('')
  const [opponent, setOpponent] = useState('')
  const [week, setWeek] = useState('')
  const [notes, setNotes] = useState('')
  const [seriesId, chooseSeries] = useState('')
  const [confirmMap, setConfirmMap] = useState(false)
  const [confirmNecc, setConfirmNecc] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const key = (round: RehostRound) => `${round.segment}:${round.physical_number}`
  function updateSegment(index: number, value: SegmentChoice) {
    setSegments(current => current.map((item, at) => at === index ? value : item))
    setPreview(null); setExclusions({}); setDirty(false); setConfirmMap(false); setConfirmNecc(false)
  }
  async function review(chosenTeam?: number) {
    setBusy(true); setError('')
    try {
      const selected = segments.map(item => ({ replay_id: item.replay_id || null, path: item.replay_id ? null : item.path.trim() || null }))
      const omitted = Object.entries(exclusions).map(([id, reason]) => {
        const [segment, physical_number] = id.split(':').map(Number)
        return { segment, physical_number, reason: reason.trim() }
      })
      const result = await api<RehostPreview>('/replays/rehost/preview', 'POST', { segments: selected, exclusions: omitted, team: chosenTeam ?? team })
      setPreview(result); setTeam(result.our_team); setDirty(false); setConfirmMap(false); setConfirmNecc(false)
      if (result.active_season) setSeason(result.active_season)
      if (result.our_team !== null) { setFinalOur(String(result.score[result.our_team])); setFinalTheir(String(result.score[1 - result.our_team])) }
      if (result.duplicate) notify('One of these replay folders was already imported.', true)
    } catch (failure) { setError((failure as Error).message) } finally { setBusy(false) }
  }
  async function importMap() {
    if (!preview || dirty || team === null) return
    setBusy(true); setError('')
    try {
      const result = await api<{ map_id: string; rounds: number }>('/replays/rehost/import', 'POST', {
        preview_token: preview.preview_token, season_slug: season, opponent, week, notes,
        series_id: seriesId || null, team, confirm_necc: confirmNecc,
        confirm_folders_one_map: confirmMap, final_our_score: Number(finalOur), final_their_score: Number(finalTheir),
      })
      notify(`Imported ${result.rounds} logical rounds as NECC map ${result.map_id}.`)
      setPreview(null); setExclusions({}); setConfirmMap(false); setConfirmNecc(false)
      await afterImport()
    } catch (failure) { setError((failure as Error).message) } finally { setBusy(false) }
  }
  return <>
    <div className="admin-panel admin-tip"><ShieldCheck size={22} /><div><b>Rehost import is manual.</b><p>Select only folders from the same competitive map, put them in order, and exclude each abandoned physical round. A later Siege lobby may restart its score at 0–0.</p></div></div>
    <section className="admin-panel"><span className="eyebrow">PHYSICAL REPLAY SEGMENTS</span><h2>Choose folders in competitive order</h2>
      {segments.map((choice, index) => <div className="rehost-segment" key={index}><b>Segment {index + 1}</b>
        <select value={choice.replay_id} onChange={event => updateSegment(index, { replay_id: event.target.value, path: '' })}><option value="">Enter folder path below</option>{items.filter(item => item.eligible && !item.duplicate).map(item => <option key={item.id} value={item.id}>{item.name} · {item.map} · {item.rounds} rounds</option>)}</select>
        <input value={choice.path} disabled={!!choice.replay_id} onChange={event => updateSegment(index, { replay_id: '', path: event.target.value })} placeholder="C:\...\Match-... folder" />
        <div className="detail-actions"><Button secondary disabled={index === 0} onClick={() => { const next = [...segments]; [next[index - 1], next[index]] = [next[index], next[index - 1]]; setSegments(next); setPreview(null); setExclusions({}) }}>Move up</Button><Button secondary disabled={index === segments.length - 1} onClick={() => { const next = [...segments]; [next[index + 1], next[index]] = [next[index], next[index + 1]]; setSegments(next); setPreview(null); setExclusions({}) }}>Move down</Button><Button secondary disabled={segments.length <= 2} onClick={() => { setSegments(segments.filter((_, at) => at !== index)); setPreview(null); setExclusions({}) }}>Remove</Button></div>
      </div>)}
      <div className="detail-actions"><Button secondary onClick={() => { setSegments([...segments, { replay_id: '', path: '' }]); setPreview(null); setExclusions({}) }}><Plus size={15} /> Add segment</Button><Button disabled={busy || segments.some(item => !item.replay_id && !item.path.trim())} onClick={() => void review()}>{busy ? 'Inspecting…' : 'Preview physical rounds'}</Button></div>
    </section>
    <ErrorBox message={error} />
    {preview && <section className="admin-panel preview-panel"><span className="eyebrow">LOGICAL MAP PREVIEW</span><h2>{preview.map} · {preview.match_type}</h2><p className="admin-muted">{preview.segments.length} physical folders · {preview.physical_rounds.length} physical rounds · {preview.rounds} counting rounds. Physical scores restart within each folder; the logical score counts only selected rounds.</p>
      <div className="team-choices"><b>Tracked team</b><p>{preview.tracked_players.join(', ') || 'Choose your team below.'}</p>{preview.teams.map(choice => <div key={choice.index}><span>Team {choice.index}: {choice.players.join(', ')}</span>{preview.ambiguous && <Button secondary onClick={() => void review(choice.index)}>Use team {choice.index}</Button>}</div>)}</div>
      {preview.ambiguous && <div className="admin-inline-error">{preview.ambiguous}</div>}
      {preview.duplicate && <div className="admin-inline-error">A physical replay folder was already imported.</div>}
      {preview.segments.map(segment => <div key={segment.segment} className="rehost-round-group"><h3>Segment {segment.segment}: {segment.source_name}</h3>{preview.physical_rounds.filter(round => round.segment === segment.segment).map(round => <div className="rehost-round" key={key(round)}><label><input type="checkbox" checked={!(key(round) in exclusions)} onChange={event => { setExclusions(current => { const next = { ...current }; if (event.target.checked) delete next[key(round)]; else next[key(round)] = 'abandoned rehost round'; return next }); setDirty(true) }} /> R{String(round.physical_number).padStart(2, '0')}</label><span>{round.site} · physical {round.physical_score.join('–')}</span><strong>{key(round) in exclusions ? 'DOES NOT COUNT' : `Logical R${round.logical_number ?? '—'}`}</strong>{key(round) in exclusions && <input aria-label={`Reason segment ${round.segment} round ${round.physical_number}`} value={exclusions[key(round)]} onChange={event => { setExclusions(current => ({ ...current, [key(round)]: event.target.value })); setDirty(true) }} />}</div>)}</div>)}
      {dirty && <div className="admin-inline-error">Round choices changed. Update the preview before importing.</div>}
      <div className="detail-actions"><Button secondary disabled={busy} onClick={() => void review(team ?? undefined)}>Update preview and logical score</Button></div>
      <div className="form-grid"><label>Final UAH score<input type="number" min="0" max="30" value={finalOur} onChange={event => setFinalOur(event.target.value)} /></label><label>Final opponent score<input type="number" min="0" max="30" value={finalTheir} onChange={event => setFinalTheir(event.target.value)} /></label><label>Season<select value={season} onChange={event => { setSeason(event.target.value); chooseSeries(''); setSeriesId('') }}><option value="">Select season</option>{seasons.map(item => <option value={item.slug} key={item.slug}>{item.name}</option>)}</select></label><label>Series<select value={seriesId} onChange={event => { const id = event.target.value; chooseSeries(id); setSeriesId(id); const found = series.find(item => item.id === id); if (found) { setOpponent(found.opponent); setWeek(found.week || '') } }}><option value="">New series / matchup</option>{series.map(item => <option value={item.id} key={item.id}>vs {item.opponent} · {item.date}</option>)}</select></label><label>Opponent<input value={opponent} readOnly={!!seriesId} onChange={event => setOpponent(event.target.value)} /></label><label>NECC week<input value={week} onChange={event => setWeek(event.target.value)} /></label><label className="wide">Notes<textarea rows={3} value={notes} onChange={event => setNotes(event.target.value)} /></label></div>
      <label className="confirm-line"><input type="checkbox" checked={confirmMap} onChange={event => setConfirmMap(event.target.checked)} /><span>These ordered replay folders belong to one competitive map, and I reviewed every counted or abandoned round.</span></label>
      <label className="confirm-line"><input type="checkbox" checked={confirmNecc} onChange={event => setConfirmNecc(event.target.checked)} /><span>I confirm this Custom Game map was an NECC match.</span></label>
      <Button disabled={busy || dirty || preview.duplicate || team === null || !season || !opponent.trim() || !confirmMap || !confirmNecc || finalOur === '' || finalTheir === ''} onClick={() => void importMap()}><Check size={16} /> Import one logical NECC map</Button>
    </section>}
  </>
}

function RosterPage({ notify }: { notify: (text: string, error?: boolean) => void }) {
  const [players, setPlayers] = useState<Player[]>([])
  const [username, setUsername] = useState('')
  const [display, setDisplay] = useState('')
  const [error, setError] = useState('')
  const load = () => api<Player[]>('/roster').then(setPlayers).catch(error => setError(error.message))
  useEffect(() => { void load() }, [])
  async function add(event: React.FormEvent) { event.preventDefault(); setError(''); try { await api('/roster', 'POST', { username, display_name: display || null }); setUsername(''); setDisplay(''); notify('Player added to your roster.'); await load() } catch (error) { setError((error as Error).message) } }
  return <><PageHead label="TEAM MANAGEMENT" title="Your roster" description="Manage Ubisoft names and display names. Deactivation preserves all historical match data." /><ErrorBox message={error} />
    <form className="admin-panel add-player" onSubmit={event => void add(event)}><div><span className="eyebrow">ADD PLAYER</span><h2>Track a teammate</h2></div><label>Ubisoft username<input value={username} onChange={event => setUsername(event.target.value)} required placeholder="SiegeUsername" /></label><label>Display name (optional)<input value={display} onChange={event => setDisplay(event.target.value)} placeholder="First name or nickname" /></label><Button type="submit" disabled={!username.trim()}><Plus size={16} /> Add player</Button></form>
    <div className="admin-section-head"><h2>Players <small>{players.filter(player => player.tracked).length} active</small></h2></div>
    <div className="roster-list">{players.map(player => <RosterRow key={player.id} player={player} after={load} notify={notify} />)}{!players.length && <div className="admin-empty">Add your five Ubisoft usernames to get started.</div>}</div>
  </>
}

function RosterRow({ player, after, notify }: { player: Player; after: () => Promise<void>; notify: (text: string, error?: boolean) => void }) {
  const [name, setName] = useState(player.display_name)
  const [alias, setAlias] = useState('')
  const [error, setError] = useState('')
  async function saveName() { try { await api(`/roster/${player.id}`, 'PATCH', { display_name: name }); notify('Display name saved.'); await after() } catch (error) { setError((error as Error).message) } }
  async function addAlias() { try { await api(`/roster/${player.id}/aliases`, 'POST', { username: alias, make_current: true }); setAlias(''); notify('Ubisoft username updated; the previous alias remains available.'); await after() } catch (error) { setError((error as Error).message) } }
  async function toggle() { try { await api(`/roster/${player.id}`, 'PATCH', { tracked: !player.tracked }); notify(player.tracked ? 'Player deactivated. Historical stats remain.' : 'Player reactivated.'); await after() } catch (error) { setError((error as Error).message) } }
  return <div className={`admin-panel roster-row ${player.tracked ? '' : 'inactive'}`}><div className="roster-identity"><span className="avatar">{player.display_name.slice(0, 2).toUpperCase()}</span><div><b>{player.display_name}</b><small>@{player.username} · {player.profile_bound ? 'Profile ID linked' : 'Awaiting first replay'}</small></div><span className={`replay-status ${player.tracked ? 'eligible' : 'ineligible'}`}>{player.tracked ? 'ACTIVE' : 'INACTIVE'}</span></div><div className="roster-edit"><label>Display name<input value={name} onChange={event => setName(event.target.value)} /></label><Button secondary disabled={!name.trim() || name === player.display_name} onClick={() => void saveName()}>Save</Button><label>New Ubisoft username / alias<input value={alias} onChange={event => setAlias(event.target.value)} placeholder="NewUsername" /></label><Button secondary disabled={!alias.trim()} onClick={() => void addAlias()}>Add alias</Button></div><div className="roster-footer"><span>Known names: {player.aliases.join(' · ')}</span><button onClick={() => void toggle()}>{player.tracked ? 'Deactivate player' : 'Reactivate player'}</button></div><ErrorBox message={error} /></div>
}

function SeasonsPage({ notify }: { notify: (text: string, error?: boolean) => void }) {
  const [seasons, setSeasons] = useState<Season[]>([])
  const [name, setName] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [error, setError] = useState('')
  const load = () => api<Season[]>('/seasons').then(setSeasons).catch(error => setError(error.message))
  useEffect(() => { void load() }, [])
  async function create(event: React.FormEvent) { event.preventDefault(); try { await api('/seasons', 'POST', { name, start_date: startDate || null, end_date: endDate || null }); setName(''); setStartDate(''); setEndDate(''); notify('Season created.'); await load() } catch (error) { setError((error as Error).message) } }
  async function activate(slug: string) { try { await api(`/seasons/${slug}/activate`, 'POST', {}); notify('Active season changed.'); await load() } catch (error) { setError((error as Error).message) } }
  return <><PageHead label="SEMESTER HISTORY" title="Seasons" description="The active season is the default for new imports. Rename or date a season without changing its permanent identifier or historical maps." /><ErrorBox message={error} />
    <form className="admin-panel season-create" onSubmit={event => void create(event)}><label>New season name<input value={name} onChange={event => setName(event.target.value)} required placeholder="Fall 2026" /></label><label>Start date (optional)<input type="date" value={startDate} onChange={event => setStartDate(event.target.value)} /></label><label>End date (optional)<input type="date" value={endDate} onChange={event => setEndDate(event.target.value)} /></label><Button type="submit" disabled={!name.trim()}><Plus size={16} /> Create season</Button></form>
    <div className="season-list">{seasons.map(row => <SeasonRow key={row.slug} season={row} activate={activate} after={load} notify={notify} />)}{!seasons.length && <div className="admin-empty">Create your first NECC season to begin.</div>}</div>
  </>
}

function SeasonRow({ season, activate, after, notify }: { season: Season; activate: (slug: string) => Promise<void>; after: () => Promise<void>; notify: (text: string, error?: boolean) => void }) {
  const [editing, setEditing] = useState(false)
  const [name, setName] = useState(season.name)
  const [startDate, setStartDate] = useState(season.start_date || '')
  const [endDate, setEndDate] = useState(season.end_date || '')
  const [error, setError] = useState('')
  async function save() { try { await api(`/seasons/${season.slug}`, 'PATCH', { name, start_date: startDate || null, end_date: endDate || null }); setEditing(false); notify('Season details saved. Historical maps and links were preserved.'); await after() } catch (error) { setError((error as Error).message) } }
  return <div className="admin-panel season-row"><div className="season-summary"><div><span className="eyebrow">{season.active ? 'ACTIVE SEMESTER' : 'ARCHIVED SEMESTER'}</span><h2>{season.name}</h2><small>{season.start_date || 'No start date'} → {season.end_date || 'No end date'} · permanent ID: {season.slug}</small></div><div className="season-actions">{season.active ? <span className="replay-status eligible">ACTIVE</span> : <Button secondary onClick={() => void activate(season.slug)}>Make active</Button>}<Button secondary onClick={() => setEditing(!editing)}>{editing ? 'Cancel' : 'Edit'}</Button></div></div>{editing && <div className="form-grid"><label>Season name<input value={name} onChange={event => setName(event.target.value)} /></label><label>Start date<input type="date" value={startDate} onChange={event => setStartDate(event.target.value)} /></label><label>End date<input type="date" value={endDate} onChange={event => setEndDate(event.target.value)} /></label><div className="form-end"><Button disabled={!name.trim()} onClick={() => void save()}>Save season</Button></div></div>}<ErrorBox message={error} /></div>
}

function MatchesPage({ notify }: { notify: (text: string, error?: boolean) => void }) {
  const [matches, setMatches] = useState<MapRow[]>([])
  const [series, setSeries] = useState<Series[]>([])
  const [seasons, setSeasons] = useState<Season[]>([])
  const [filter, setFilter] = useState('')
  const [error, setError] = useState('')
  const load = async () => { try { const suffix = filter ? `?season=${encodeURIComponent(filter)}` : ''; const [mapRows, seriesRows] = await Promise.all([api<MapRow[]>(`/matches${suffix}`), api<Series[]>(`/series${suffix}`)]); setMatches(mapRows); setSeries(seriesRows) } catch (error) { setError((error as Error).message) } }
  useEffect(() => { api<Season[]>('/seasons').then(rows => { setSeasons(rows); setFilter(rows.find(row => row.active)?.slug || '') }).catch(error => setError(error.message)) }, [])
  useEffect(() => { void load() }, [filter])
  return <><PageHead label="NECC HISTORY" title="Imported matches" description="Open a map to review its rounds, edit its date or series, or remove an accidental import. Matchup details can be edited below." action={<select className="head-select" value={filter} onChange={event => setFilter(event.target.value)}><option value="">All seasons</option>{seasons.map(row => <option value={row.slug} key={row.slug}>{row.name}{row.active ? ' (active)' : ''}</option>)}</select>} /><ErrorBox message={error} />
    {series.map(group => <SeriesCard key={group.id} group={group} maps={matches.filter(map => map.series_id === group.id)} seasonSeries={series.filter(row => row.season_slug === group.season_slug)} notify={notify} after={load} />)}{!series.length && <div className="admin-empty">No real matches have been imported in this season.</div>}
  </>
}
function SeriesCard({ group, maps, seasonSeries, notify, after }: { group: Series; maps: MapRow[]; seasonSeries: Series[]; notify: (text: string, error?: boolean) => void; after: () => Promise<void> }) {
  const [editing, setEditing] = useState(false)
  const [selectedMap, setSelectedMap] = useState('')
  const [opponent, setOpponent] = useState(group.opponent)
  const [date, setDate] = useState(group.date)
  const [week, setWeek] = useState(group.week || '')
  const [notes, setNotes] = useState(group.notes || '')
  const [error, setError] = useState('')
  useEffect(() => { if (!editing) { setOpponent(group.opponent); setDate(group.date); setWeek(group.week || ''); setNotes(group.notes || '') } }, [group.opponent, group.date, group.week, group.notes, editing])
  async function save() { try { await api(`/series/${group.id}`, 'PATCH', { opponent, date, week, notes }); setEditing(false); notify('Matchup details updated. Public JSON refreshed.'); await after() } catch (error) { setError((error as Error).message) } }
  return <section className="admin-panel series-card"><div className="admin-panel-head"><div><span className="eyebrow">{group.date} / {group.season_slug}{group.week ? ` / ${group.week}` : ''}</span><h2>vs {group.opponent}</h2></div><Button secondary onClick={() => setEditing(!editing)}>{editing ? 'Cancel' : 'Edit matchup'}</Button></div><div className="series-maps">{maps.map(map => <div key={map.id}><b>{map.map_name}<small> · {map.date}</small></b><span>{map.our_score} – {map.their_score}</span><small>{map.match_type}</small><Button secondary onClick={() => setSelectedMap(selectedMap === map.id ? '' : map.id)}>{selectedMap === map.id ? 'Close' : 'Open map'}</Button></div>)}</div>{selectedMap && <MatchDetailPanel key={selectedMap} mapId={selectedMap} seasonSeries={seasonSeries} after={after} onDeleted={() => setSelectedMap('')} notify={notify} />}{editing && <div className="form-grid"><label>Opponent<input value={opponent} onChange={event => setOpponent(event.target.value)} /></label><label>Matchup date<input type="date" value={date} onChange={event => setDate(event.target.value)} /></label><label>NECC week<input value={week} onChange={event => setWeek(event.target.value)} /></label><label className="wide">Notes<textarea value={notes} onChange={event => setNotes(event.target.value)} rows={3} /></label><Button disabled={!opponent.trim() || !date} onClick={() => void save()}>Save matchup</Button></div>}<ErrorBox message={error} /></section>
}

function KDPlayerRow({ mapId, player, refresh, notify }: { mapId: string; player: KDPlayer; refresh: () => Promise<void>; notify: (text: string, error?: boolean) => void }) {
  const [kills, setKills] = useState(player.final_kills)
  const [deaths, setDeaths] = useState(player.final_deaths)
  const [reason, setReason] = useState(player.reason)
  const [note, setNote] = useState(player.note)
  const [busy, setBusy] = useState(false)
  async function save() {
    setBusy(true)
    try {
      await api(`/matches/${mapId}/kd-corrections/${player.player_id}`, 'PUT', { final_kills: kills, final_deaths: deaths, reason, note })
      notify(`${player.name} final map K/D saved. Rating is ineligible for this partial map.`)
      await refresh()
    } catch (error) { notify((error as Error).message, true) } finally { setBusy(false) }
  }
  async function remove() {
    if (!window.confirm(`Remove ${player.name}'s manual K/D correction? Replay-derived K/D will return; the map will remain marked partial.`)) return
    setBusy(true)
    try {
      await api(`/matches/${mapId}/kd-corrections/${player.player_id}`, 'DELETE', {})
      notify(`${player.name} replay-derived K/D restored.`)
      await refresh()
    } catch (error) { notify((error as Error).message, true) } finally { setBusy(false) }
  }
  return <div className="kd-correction-row"><b>{player.name}</b><span>Replay {player.replay_kills} K / {player.replay_deaths} D</span><label>Final K<input type="number" min="0" max="100" value={kills} onChange={event => setKills(Number(event.target.value))} /></label><label>Final D<input type="number" min="0" max="100" value={deaths} onChange={event => setDeaths(Number(event.target.value))} /></label><input aria-label={`${player.name} correction reason`} placeholder="Reason (required)" value={reason} onChange={event => setReason(event.target.value)} /><input aria-label={`${player.name} correction note`} placeholder="Optional note" value={note} onChange={event => setNote(event.target.value)} /><Button secondary disabled={busy || !reason.trim()} onClick={() => void save()}>{player.corrected ? 'Update' : 'Save'} final K/D</Button>{player.corrected && <button className="danger-button" disabled={busy} onClick={() => void remove()}>Remove</button>}{player.corrected && <small>Adjustment: {player.kill_adjustment >= 0 ? '+' : ''}{player.kill_adjustment} K, {player.death_adjustment >= 0 ? '+' : ''}{player.death_adjustment} D · {player.updated_at}</small>}</div>
}

function MatchDetailPanel({ mapId, seasonSeries, after, onDeleted, notify }: { mapId: string; seasonSeries: Series[]; after: () => Promise<void>; onDeleted: () => void; notify: (text: string, error?: boolean) => void }) {
  const [detail, setDetail] = useState<MatchDetail | null>(null)
  const [replayPath, setReplayPath] = useState('')
  const [segmentPaths, setSegmentPaths] = useState<string[]>([])
  const [playedOn, setPlayedOn] = useState('')
  const [groupChoice, setGroupChoice] = useState('__same__')
  const [opponent, setOpponent] = useState('')
  const [seriesDate, setSeriesDate] = useState('')
  const [week, setWeek] = useState('')
  const [notes, setNotes] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const load = () => api<MatchDetail>(`/matches/${mapId}`).then(row => { setDetail(row); setPlayedOn(row.date); setOpponent(row.opponent); setSeriesDate(row.series_date); setWeek(row.week || ''); setNotes(row.notes || ''); setGroupChoice('__same__'); setSegmentPaths(current => current.length === (row.rehost?.segments.length || 0) ? current : (row.rehost?.segments.map(() => '') || [])) }).catch(error => setError(error.message))
  useEffect(() => { void load() }, [mapId])
  async function save() {
    if (!detail) return
    setBusy(true); setError('')
    try {
      const result = await api<{ series_id: string }>(`/matches/${mapId}`, 'PATCH', { played_on: playedOn, series_id: groupChoice.startsWith('series:') ? groupChoice.slice(7) : null, make_new_series: groupChoice === '__new__' })
      if (groupChoice === '__same__' || groupChoice === '__new__') await api(`/series/${result.series_id}`, 'PATCH', { opponent, date: seriesDate, week, notes })
      notify('Map details saved. Season and player statistics refreshed.')
      if (groupChoice !== '__same__') onDeleted()
      await after()
      if (groupChoice === '__same__') await load()
    } catch (error) { setError((error as Error).message) } finally { setBusy(false) }
  }
  async function remove() {
    if (!detail || !window.confirm(`Delete this map and its archived replay? This removes the statistics and private replay archive for ${detail.map_name} vs ${detail.opponent}. Player identities remain. This cannot be undone.`)) return
    setBusy(true); setError('')
    try { await api(`/matches/${mapId}`, 'DELETE', { confirm_map_id: mapId }); notify('Map and private replay archive deleted. Statistics recalculated; player identities preserved.'); onDeleted(); await after() } catch (error) { setError((error as Error).message) } finally { setBusy(false) }
  }
  async function reparse() {
    if (!detail || (detail.source_kind === 'normal' && !replayPath.trim()) || (detail.source_kind === 'rehost' && (segmentPaths.length !== detail.rehost?.segments.length || segmentPaths.some(path => !path.trim()))) || !window.confirm(`Reparse ${detail.map_name} from the selected original replay ${detail.source_kind === 'rehost' ? 'folders' : 'folder'}? Season and matchup details will be kept.`)) return
    setBusy(true); setError('')
    try {
      const result = await api<{ message: string }>(`/matches/${mapId}/reparse`, 'POST', { path: replayPath.trim(), segment_paths: segmentPaths.map(path => path.trim()), confirm_map_id: mapId })
      notify(result.message); await load(); await after()
    } catch (error) { setError((error as Error).message) } finally { setBusy(false) }
  }
  async function verifyArchive() {
    setBusy(true); setError('')
    try {
      const status = await api<ArchiveStatus>(`/matches/${mapId}/archive`)
      setDetail(current => current ? { ...current, archive: status } : current)
      notify(`Replay archive: ${status.status}. ${status.message}`, status.status !== 'Healthy')
    } catch (error) { setError((error as Error).message) } finally { setBusy(false) }
  }
  async function backfillArchive() {
    if (!detail || (detail.source_kind === 'normal' && !replayPath.trim()) || (detail.source_kind === 'rehost' && (segmentPaths.length !== detail.rehost?.segments.length || segmentPaths.some(path => !path.trim())))) return
    setBusy(true); setError('')
    try {
      const status = await api<ArchiveStatus>(`/matches/${mapId}/archive`, 'POST', { path: replayPath.trim(), segment_paths: segmentPaths.map(path => path.trim()), confirm_map_id: mapId })
      notify(`Replay archived: ${status.rounds} rounds verified.`)
      await load()
    } catch (error) { setError((error as Error).message) } finally { setBusy(false) }
  }
  async function reparseArchived() {
    if (!detail || detail.archive.status !== 'Healthy' || !window.confirm(`Reparse ${detail.map_name} from its verified private archive? Matchup details will be kept.`)) return
    setBusy(true); setError('')
    try {
      const result = await api<{ message: string }>(`/matches/${mapId}/reparse`, 'POST', { from_archive: true, confirm_map_id: mapId })
      notify(result.message); await load(); await after()
    } catch (error) { setError((error as Error).message) } finally { setBusy(false) }
  }
  async function openArchive() {
    setBusy(true); setError('')
    try { await api(`/matches/${mapId}/archive/open`, 'POST', {}); notify('Opened private replay archive in Explorer.') }
    catch (error) { setError((error as Error).message) } finally { setBusy(false) }
  }
  if (!detail) return <div className="map-detail"><ErrorBox message={error} /><p className="admin-muted">Loading map…</p></div>
  return <div className="map-detail"><span className="eyebrow">MAP DETAIL / {detail.id}</span><h3>{detail.map_name} <span>vs {detail.opponent}</span></h3><div className="preview-facts"><div><small>RESULT</small><b>{detail.our_score} – {detail.their_score}</b></div><div><small>ROUNDS</small><b>{detail.rounds.length}</b></div><div><small>MODE</small><b>{detail.game_mode}</b></div><div><small>SEASON</small><b>{detail.season_name}</b></div></div><p className="admin-muted">Tracked players: {detail.tracked_players.join(', ') || 'None identified'}</p><section className="archive-card"><span className="eyebrow">MANUAL K/D CORRECTION</span><h4>Final map kills and deaths</h4><p className="admin-muted">Replay data: {detail.replay_data_complete ? 'COMPLETE' : 'PARTIAL'} · Manual correction: {detail.manual_kd_correction ? 'YES' : 'NO'} · Rating eligible: {detail.rating_eligible ? 'YES' : 'NO'}. Only displayed K/D changes; round-based statistics stay replay-derived.</p>{detail.kd_players.map(player => <KDPlayerRow key={`${player.player_id}:${player.updated_at}`} mapId={mapId} player={player} refresh={async () => { await load(); await after() }} notify={notify} />)}</section><div className="map-rounds">{detail.rounds.map(round => <div key={round.number}><b>R{round.number}</b><span>{round.site}</span><strong className={round.result === 'Win' ? 'positive' : 'negative'}>{round.result}</strong></div>)}</div>{detail.rehost && <div className="rehost-round-group"><h3>Physical to logical round mapping</h3>{detail.rehost.segments.map(segment => <div key={segment.segment}><b>Segment {segment.segment}: {segment.source_name}</b>{detail.rehost!.mapping.filter(item => item.segment === segment.segment).map(item => <div className="rehost-round" key={`${item.segment}:${item.physical_number}`}><span>R{String(item.physical_number).padStart(2, '0')}</span><span>{item.filename}</span><strong>{item.logical_number === null ? 'DOES NOT COUNT' : `Logical R${item.logical_number}`}</strong><span>{item.exclusion_reason || ''}</span></div>)}</div>)}</div>}<div className="archive-card"><span className="eyebrow">PRIVATE REPLAY ARCHIVE</span><h4>{detail.archive.status === 'Healthy' ? 'Archived and verified' : detail.archive.status}</h4><p className="admin-muted">{detail.archive.status === 'Healthy' ? `${detail.archive.rounds} rounds ? ${detail.archive.message}` : detail.archive.message}</p><div className="detail-actions"><Button secondary disabled={busy} onClick={() => void verifyArchive()}>Verify archive</Button><Button secondary disabled={busy || detail.archive.status === 'Missing'} onClick={() => void openArchive()}>Open archive folder</Button><Button secondary disabled={busy || detail.archive.status !== 'Healthy'} onClick={() => void reparseArchived()}><RefreshCw size={16} /> Reparse from archive</Button></div></div><div className="form-grid"><label>Map played on<input type="date" value={playedOn} onChange={event => setPlayedOn(event.target.value)} /></label><label>Series grouping<select value={groupChoice} onChange={event => setGroupChoice(event.target.value)}><option value="__same__">Keep current series</option><option value="__new__">Separate into a new series</option>{seasonSeries.filter(group => group.id !== detail.series_id).map(group => <option key={group.id} value={`series:${group.id}`}>Move to vs {group.opponent} · {group.date}</option>)}</select></label></div>{!groupChoice.startsWith('series:') && <><p className="admin-muted">Opponent, week, notes, and matchup date belong to the series. Editing them updates every map in that series.</p><div className="form-grid"><label>Opponent<input value={opponent} onChange={event => setOpponent(event.target.value)} /></label><label>Matchup date<input type="date" value={seriesDate} onChange={event => setSeriesDate(event.target.value)} /></label><label>NECC week<input value={week} onChange={event => setWeek(event.target.value)} /></label><label className="wide">Notes<textarea rows={3} value={notes} onChange={event => setNotes(event.target.value)} /></label></div></>}<div className="detail-actions"><Button disabled={busy || !playedOn || (!groupChoice.startsWith('series:') && (!opponent.trim() || !seriesDate))} onClick={() => void save()}>Save map</Button><button className="danger-button" disabled={busy} onClick={() => void remove()}>Delete this map</button></div>{detail.rehost ? <div className="form-grid"><p className="admin-muted wide">Enter every original replay folder in the same order for manual reparse or archive backfill. Archived reparse uses the verified private copies above.</p>{detail.rehost.segments.map((segment, index) => <label className="wide" key={segment.segment}>Segment {segment.segment}: {segment.source_name}<input value={segmentPaths[index] || ''} onChange={event => setSegmentPaths(current => current.map((value, at) => at === index ? event.target.value : value))} placeholder="Full MatchReplay folder path" /></label>)}<Button secondary disabled={busy || segmentPaths.length !== detail.rehost.segments.length || segmentPaths.some(path => !path.trim())} onClick={() => void reparse()}><RefreshCw size={16} /> Reparse all segments</Button>{detail.archive.status === 'Missing' && <Button secondary disabled={busy || segmentPaths.length !== detail.rehost.segments.length || segmentPaths.some(path => !path.trim())} onClick={() => void backfillArchive()}>Archive all segments</Button>}</div> : <div className="form-grid"><label className="wide">Original replay folder for reparse or archive backfill<input value={replayPath} onChange={event => setReplayPath(event.target.value)} placeholder="Full path to this map's Match-... folder" /></label><Button secondary disabled={busy || !replayPath.trim()} onClick={() => void reparse()}><RefreshCw size={16} /> Reparse this map</Button>{detail.archive.status === 'Missing' && <Button secondary disabled={busy || !replayPath.trim()} onClick={() => void backfillArchive()}>Archive this map</Button>}</div>}<ErrorBox message={error} /></div>
}

function StatisticsPage({ notify }: { notify: (text: string, error?: boolean) => void }) {
  const [dashboard, setDashboard] = useState<Dashboard | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const load = () => api<Dashboard>('/dashboard').then(setDashboard).catch(error => setError(error.message))
  useEffect(() => { void load() }, [])
  async function run(path: string) { setBusy(true); setError(''); try { const result = await api<{ message: string }>(path, 'POST', {}); notify(result.message); await load() } catch (error) { setError((error as Error).message) } finally { setBusy(false) } }
  return <><PageHead label="LOCAL STATISTICS" title="Statistics maintenance" description="Rebuild derived numbers from stored normalized matches. Stored replay records support future improvements to trades, KOST, and Rating without re-entering matches." /><ErrorBox message={error} />
    <div className="admin-columns"><section className="admin-panel"><span className="eyebrow">RECALCULATE</span><h2>Recalculate Statistics</h2><p className="admin-muted">Run the current formulas against every stored normalized map and refresh player and season aggregates.</p><div className="panel-action"><Button disabled={busy} onClick={() => void run('/recalculate')}><RefreshCw size={16} /> Recalculate Statistics</Button></div></section><section className="admin-panel"><span className="eyebrow">LOCAL EXPORT</span><h2>Regenerate Website Data</h2><p className="admin-muted">Write fresh sanitized JSON for the public site from the local database without pushing to GitHub.</p><div className="panel-action"><Button secondary disabled={busy} onClick={() => void run('/regenerate')}><Database size={16} /> Regenerate Website Data</Button></div></section></div>
    <div className="admin-status"><Database size={17} /><span>{dashboard?.database.path || 'Loading database…'}</span><b>Integrity: {dashboard?.database.status || '…'} · {dashboard?.maps_imported ?? 0} NECC maps</b></div>
  </>
}

function PublishPage({ notify }: { notify: (text: string, error?: boolean) => void }) {
  const [dashboard, setDashboard] = useState<Dashboard | null>(null)
  const [settings, setSettings] = useState<SettingsData | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  useEffect(() => { api<Dashboard>('/dashboard').then(setDashboard).catch(error => setError(error.message)); api<SettingsData>('/settings').then(setSettings).catch(error => setError(error.message)) }, [])
  async function publish() { setBusy(true); setError(''); try { const result = await api<{ status: string; message: string; detail?: string }>('/publish', 'POST', {}); notify(result.message, result.status === 'push_failed' || result.status === 'needs_git'); if (result.detail) setError(result.detail); setDashboard(await api<Dashboard>('/dashboard')) } catch (error) { setError((error as Error).message) } finally { setBusy(false) } }
  return <><PageHead label="PUBLIC WEBSITE" title="Publish statistics" description="Validate the generated public JSON, build the read-only site, commit only generated JSON, and push to GitHub Pages." /><ErrorBox message={error} />
    <section className="admin-panel publish-panel"><span className="eyebrow">GITHUB PAGES</span><h2>Publish Website</h2><p className="admin-muted">A Git or network failure cannot change valid local match and player data. Fix the issue and click Publish again to retry.</p><div className="publish-target"><span>BRANCH</span><b>{settings?.branch || 'main'}</b><span>GITHUB REPOSITORY</span><b>{settings?.remote_url || 'Existing origin remote / not set'}</b><span>PUBLIC WEBSITE</span><b>{settings?.site_url ? <a href={settings.site_url} target="_blank" rel="noreferrer">{settings.site_url}</a> : 'Not configured'}</b></div><Button disabled={busy} onClick={() => void publish()}><CloudUpload size={16} /> {busy ? 'Building and pushing…' : 'Publish Website'}</Button></section>
    <div className="admin-status"><CloudUpload size={17} /><span>Last successful publish</span><b>{dashboard?.last_publish ? `${new Date(dashboard.last_publish.at).toLocaleString()} · ${dashboard.last_publish.commit}` : 'None recorded'}</b></div>
  </>
}

function SettingsPage({ notify }: { notify: (text: string, error?: boolean) => void }) {
  const [settings, setSettings] = useState<SettingsData | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  useEffect(() => { api<SettingsData>('/settings').then(setSettings).catch(error => setError(error.message)) }, [])
  function change<K extends keyof SettingsData>(key: K, value: SettingsData[K]) { setSettings(current => current ? { ...current, [key]: value } : current) }
  async function save(event: React.FormEvent) { event.preventDefault(); if (!settings) return; setBusy(true); setError(''); try { await api('/settings', 'PUT', settings); notify('Settings saved. Public data was refreshed.') } catch (error) { setError((error as Error).message) } finally { setBusy(false) } }
  return <><PageHead label="LOCAL CONFIGURATION" title="Settings" description="Configure your team, replay folder, statistics method, and GitHub Pages destination." /><ErrorBox message={error} />
    {settings ? <form className="admin-panel settings-form" onSubmit={event => void save(event)}>
      <span className="eyebrow">TEAM IDENTITY</span>
      <div className="form-grid"><label>Team name<input required value={settings.team_name} onChange={event => change('team_name', event.target.value)} /></label><label>Short name<input required value={settings.short_name} onChange={event => change('short_name', event.target.value)} /></label><label>Accent color<input type="color" value={settings.accent} onChange={event => change('accent', event.target.value)} /></label></div>
      <span className="eyebrow">REPLAYS & METHODS</span>
      <div className="form-grid"><label className="wide">MatchReplay directory<input value={settings.replay_path} onChange={event => change('replay_path', event.target.value)} placeholder="C:\Users\YOU\Documents\My Games\Rainbow Six - Siege\MatchReplay" /><small>Leave blank to use the standard Windows location.</small></label><label>Trade window (seconds)<input type="number" min="1" max="60" value={settings.trade_window_seconds} onChange={event => change('trade_window_seconds', Number(event.target.value))} /></label><label>Active Rating version<select value={settings.rating_version} onChange={event => change('rating_version', event.target.value)}><option value="collegiate_v1">collegiate_v1</option></select><small>This V1 supports one explicit formula.</small></label></div>
      <span className="eyebrow">GITHUB PAGES</span>
      <div className="form-grid"><label>Git branch<input required value={settings.branch} onChange={event => change('branch', event.target.value)} placeholder="main" /></label><label>GitHub repository URL<input value={settings.remote_url} onChange={event => change('remote_url', event.target.value)} placeholder="https://github.com/you/r6-necc-stats.git" /><small>Optional if the local origin remote is already configured.</small></label><label className="wide">Public website URL (optional)<input type="url" value={settings.site_url} onChange={event => change('site_url', event.target.value)} placeholder="https://you.github.io/r6-necc-stats/" /></label><label className="settings-checkbox"><input type="checkbox" checked={settings.publishing_enabled} onChange={event => change('publishing_enabled', event.target.checked)} /> Enable one-click publishing</label></div>
      <Button type="submit" disabled={busy}>{busy ? 'Saving…' : 'Save settings'}</Button>
    </form> : <p className="admin-muted">Loading settings…</p>}
  </>
}

createRoot(document.getElementById('admin-root')!).render(<React.StrictMode><App /></React.StrictMode>)
