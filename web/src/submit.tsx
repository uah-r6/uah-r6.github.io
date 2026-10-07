import { useEffect, useRef, useState } from 'react'
import { selectionTotals, validateSelection, bytesLabel, type ReplayFolder } from './replayFiles'
import { ReplayPicker } from './ReplayPicker'
import './submit.css'

type Choice = { slug: string; name: string }
type Config = { enabled: boolean; available: boolean; teams: Choice[]; seasons: Choice[]; turnstile_site_key: string | null }
type Session = { id: string; display_id: string; upload_token: string; expires_at: number; files: { id: string; folder: string; name: string; size: number }[] }
type Turnstile = { render(element: HTMLElement, options: Record<string, unknown>): string; reset(id: string): void; remove(id: string): void }
type BrowserWindow = Window & { turnstile?: Turnstile }

export function SubmitPage({ teams, seasons }: { teams: (Choice & { active: number })[]; seasons: Choice[] }) {
  const [config, setConfig] = useState<Config | null>(null), [url, setUrl] = useState(''), [error, setError] = useState('')
  const [team, setTeam] = useState(''), [season, setSeason] = useState(''), [opponent, setOpponent] = useState(''), [date, setDate] = useState('')
  const [submitter, setSubmitter] = useState(''), [discord, setDiscord] = useState(''), [rehost, setRehost] = useState(''), [notes, setNotes] = useState(''), [website, setWebsite] = useState('')
  const [folders, setFolders] = useState<ReplayFolder<File>[]>([]), [selected, setSelected] = useState<string[]>([])
  const [confirming, setConfirming] = useState(false), [confirmed, setConfirmed] = useState(false), [busy, setBusy] = useState(false)
  const [session, setSession] = useState<Session | null>(null), [received, setReceived] = useState(''), [progress, setProgress] = useState(0), [activity, setActivity] = useState('')
  const [botToken, setBotToken] = useState(''), [botError,setBotError]=useState('')
  const botWidget=useRef<string|null>(null)
  const [scanning, setScanning] = useState(false)
  const xhr = useRef<XMLHttpRequest | null>(null), cancelled = useRef(false), bot = useRef<HTMLDivElement>(null)
  const chosen = folders.filter(f => selected.includes(f.name)), totals = selectionTotals(chosen)
  const teamOptions = config?.teams.filter(t => teams.some(p => p.slug === t.slug && p.active)) || []
  const seasonOptions = config?.seasons.filter(s => seasons.some(p => p.slug === s.slug)) || []
  useEffect(() => {
    const controller = new AbortController()
    fetch(import.meta.env.BASE_URL + 'submissions-config.json', { signal: controller.signal, cache: 'no-store' }).then(r => r.json())
      .then(async data => { if (!data.worker_url) throw Error('Replay submissions are temporarily unavailable.'); setUrl(data.worker_url); const r = await fetch(data.worker_url + '/v1/config', { signal: controller.signal, cache: 'no-store' }); if (!r.ok) throw Error('Replay submissions are temporarily unavailable.'); setConfig(await r.json()) })
      .catch(e => { if (e.name !== 'AbortError') setError(e.message) })
    return () => { controller.abort(); xhr.current?.abort() }
  }, [])
  useEffect(() => {
    if (!config?.turnstile_site_key || !bot.current) return
    let widget: string | undefined, disposed = false
    const render = () => { if (!disposed && bot.current) {widget = (window as BrowserWindow).turnstile?.render(bot.current, { sitekey: config.turnstile_site_key, theme: 'dark', callback: (token:string)=>{setBotToken(token);setBotError('')}, 'expired-callback': () => {setBotToken('');setBotError('Verification expired. Please verify again.')}, 'error-callback': (code:string)=>{setBotToken('');setBotError('Browser verification failed. Retry, or refresh this page in your usual browser.');if(bot.current)bot.current.dataset.errorCode=code;return true}, 'timeout-callback': ()=>{setBotToken('');setBotError('Verification timed out. Please retry.')} });botWidget.current=widget||null} }
    const script = document.createElement('script'); script.src = 'https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit'; script.async = true; script.onload = render; script.onerror=()=>setBotError('Browser verification could not load. Check your connection and refresh this page.')
    if ((window as BrowserWindow).turnstile) render(); else document.head.append(script)
    return () => { disposed = true; botWidget.current=null; if (widget) (window as BrowserWindow).turnstile?.remove(widget); script.remove() }
  }, [config, confirming, received])

  async function request<T>(path: string, method = 'GET', payload?: unknown, token?: string): Promise<T> {
    const r = await fetch(url + '/v1' + path, { method, headers: { ...(payload !== undefined ? { 'Content-Type': 'application/json' } : {}), ...(token ? { Authorization: 'Bearer ' + token } : {}) }, body: payload === undefined ? undefined : JSON.stringify(payload), cache: 'no-store' })
    const data = await r.json(); if (!r.ok) throw Object.assign(Error(data.error || 'The submission could not be completed.'), {status:r.status}); return data
  }
  function review(event: React.FormEvent) { event.preventDefault(); try { validateSelection(chosen); setError(''); setConfirmed(false); setConfirming(true) } catch (e) { setError((e as Error).message) } }
  async function upload() {
    setBusy(true); setError(''); cancelled.current = false
    try {
      validateSelection(chosen)
      let current = session
      if (!current) {
        const manifest = []; let hashed = 0
        for (const folder of chosen) { const files = []; for (const file of folder.files) { if (cancelled.current) throw Error('Upload cancelled.'); setActivity(`Checking ${folder.name} · ${file.name}`); const digest = await crypto.subtle.digest('SHA-256', await file.arrayBuffer()); files.push({ name: file.name, size: file.size, sha256: [...new Uint8Array(digest)].map(n => n.toString(16).padStart(2, '0')).join('') }); hashed++; setProgress(Math.round(hashed / totals.files * 10)) } manifest.push({ name: folder.name, files }) }
        current = await request<Session>('/submissions', 'POST', { team_slug: team, season_slug: season, opponent, match_date: date, submitter, discord, rehost, notes, website, confirmed, folders: manifest, turnstile_token: botToken })
        setSession(current)
        if (cancelled.current) { await request(`/uploads/${current.id}/cancel`, 'POST', {}, current.upload_token); setSession(null); throw Error('Upload cancelled.') }
      }
      const state = await request<{ files: { id: string; status: string }[] }>(`/uploads/${current.id}`, 'GET', undefined, current.upload_token)
      const done = new Set(state.files.filter(f => f.status === 'uploaded').map(f => f.id))
      let completed = current.files.filter(f => done.has(f.id)).reduce((n, f) => n + f.size, 0)
      for (const item of current.files) {
        if (cancelled.current) throw Error('Upload cancelled.')
        if (done.has(item.id)) continue
        const file = chosen.find(f => f.name === item.folder)?.files.find(f => f.name === item.name)
        if (!file) throw Error('Keep the original replay selection while retrying an upload.')
        setActivity(`Uploading ${item.folder} · ${item.name}`)
        await new Promise<void>((resolve, reject) => {
          const upload = new XMLHttpRequest(); xhr.current = upload
          upload.open('PUT', `${url}/v1/uploads/${current!.id}/files/${item.id}`); upload.setRequestHeader('Authorization', 'Bearer ' + current!.upload_token); upload.timeout = 330000
          upload.upload.onprogress = e => setProgress(Math.min(95,10 + Math.round((completed + e.loaded) / totals.bytes * 85)))
          upload.onload = () => { if (upload.status >= 200 && upload.status < 300) resolve(); else { let message = 'Replay transfer failed. Retry to resume unfinished files.'; try { message = JSON.parse(upload.responseText).error || message } catch { /* An edge error can have an HTML body. */ } reject(Error(message)) } }
          upload.onerror = () => reject(Error('Connection interrupted. Retry to resume unfinished files.')); upload.ontimeout = () => reject(Error('Transfer timed out. Retry to resume unfinished files.')); upload.onabort = () => reject(Error('Upload cancelled.')); upload.send(file)
        })
        completed += item.size
      }
      setActivity('Verifying your stored replay files…')
      let result: { received: boolean; display_id: string }
      do { result = await request(`/uploads/${current.id}/complete`, 'POST', {}, current.upload_token); if (cancelled.current) throw Error('Upload cancelled.') } while (!result.received)
      setProgress(100); setReceived(result.display_id); setSession(null)
    } catch (e) { if ((e as Error & {status?:number}).status===410) {setSession(null);setConfirmed(false);setConfirming(false)} setError((e as Error).message) } finally { setBusy(false); xhr.current = null; setActivity('') }
  }
  async function cancel() {
    cancelled.current = true; xhr.current?.abort()
    if (session) { try { await request(`/uploads/${session.id}/cancel`, 'POST', {}, session.upload_token); setSession(null); setProgress(0) } catch (e) { if ((e as Error & {status?:number}).status===410) setSession(null); else {setError((e as Error).message);return} } }
    setConfirming(false); setConfirmed(false)
  }
  const unavailable = config && !config.enabled
  return <div className="submission-page"><div className="heading"><span className="eyebrow">PRIVATE REPLAY INBOX</span><h1>Submit Replays</h1><p>Send your UAH match replays for administrator review. No account, ZIP or direct message needed.</p></div>
    {received ? <section className="panel submission-success" role="status"><span className="eyebrow">THANK YOU</span><h2>Submission received</h2><p>Submission ID</p><strong>{received}</strong><p>Your replay files are awaiting administrator review. Submitting a replay does not automatically change published statistics.</p></section> : <>
      {error && <div className="submission-error" role="alert">{error}</div>}
      {unavailable && <div className="submission-error" role="status">Replay submissions are temporarily unavailable.</div>}
      {config?.enabled && !config.available && <div className="submission-error" role="status">The replay inbox is full or undergoing maintenance. Please try again after the administrator clears space.</div>}
      {!confirming ? <form onSubmit={review} className="panel submission-form">
        <div className="submit-form-grid"><label>UAH team<select required value={team} onChange={e => setTeam(e.target.value)}><option value="">Choose your team</option>{teamOptions.map(t => <option key={t.slug} value={t.slug}>{t.name}</option>)}</select></label><label>Season<select required value={season} onChange={e => setSeason(e.target.value)}><option value="">Choose the season</option>{seasonOptions.map(s => <option key={s.slug} value={s.slug}>{s.name}</option>)}</select></label><label>Opponent<input required maxLength={120} value={opponent} onChange={e => setOpponent(e.target.value)} /></label><label>Match date<input required type="date" value={date} onChange={e => setDate(e.target.value)} /></label><label>Your name / gamer tag<input required maxLength={80} value={submitter} onChange={e => setSubmitter(e.target.value)} /></label><label>Discord username <span>(optional)</span><input maxLength={80} value={discord} onChange={e => setDiscord(e.target.value)} placeholder="Helpful if we need to follow up" /></label></div>
        <fieldset className="rehost-choice"><legend>Was there a rehost?</legend>{[['no','No'],['yes','Yes'],['unsure','Not sure']].map(([value,label]) => <label key={value}><input required type="radio" name="rehost" checked={rehost === value} onChange={() => setRehost(value)} />{label}</label>)}</fieldset>
        <label>Notes <span>(optional)</span><textarea rows={3} maxLength={2000} value={notes} onChange={e => setNotes(e.target.value)} placeholder="For example: Map 2 rehosted at 4–4." /></label>
        <label className="submission-honeypot" aria-hidden="true">Website<input tabIndex={-1} autoComplete="off" value={website} onChange={e => setWebsite(e.target.value)} /></label>
        <ReplayPicker folders={folders} selected={selected} onFolders={setFolders} onSelected={setSelected} onScanning={setScanning} /><div ref={bot}/>{botError&&<div className="submission-error" role="alert">{botError}<button type="button" className="button" onClick={()=>{setBotError('');setBotToken('');if(botWidget.current)(window as BrowserWindow).turnstile?.reset(botWidget.current)}}>Retry verification</button></div>}<button className="button submit-primary" disabled={busy || scanning || !config?.enabled || !config.available || !totals.files || (!!config.turnstile_site_key && !botToken)} type="submit">Review submission →</button>
      </form> : <section className="panel confirmation"><span className="eyebrow">SUBMITTING FOR</span><h2>{teamOptions.find(t => t.slug === team)?.name}</h2><h3>{seasonOptions.find(s => s.slug === season)?.name}</h3><p>vs {opponent} · {date}</p><div className="confirmation-facts"><span>{totals.folders} replay folders</span><span>{totals.files} replay files</span><span>{bytesLabel(totals.bytes)}</span><span>Rehost: {rehost === 'yes' ? 'Yes' : rehost === 'no' ? 'No' : 'Not sure'}</span></div><p>Files upload privately for review. Match type, team identity and rehost reconstruction are verified by the administrator.</p><label className="submit-confirm"><input type="checkbox" checked={confirmed} disabled={busy || !!session} onChange={e => setConfirmed(e.target.checked)} />I confirm these are match replay files for the UAH team and season selected.</label>{(busy || session) && <div className="upload-progress" role="status"><label htmlFor="replay-upload-progress">{activity || 'Upload paused. Retry to resume.'} · {progress}%</label><progress id="replay-upload-progress" value={progress} max={100}/></div>}<div className="submit-actions"><button className="button submit-primary" disabled={busy || !confirmed} onClick={() => void upload()}>{busy ? 'Uploading…' : session ? 'Retry unfinished uploads' : 'Submit for Review'}</button><button className="button" onClick={() => void cancel()}>{busy || session ? 'Cancel upload' : 'Back to selection'}</button></div></section>}
    </>}</div>
}
