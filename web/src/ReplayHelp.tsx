import { useRef, useState, type RefObject, type KeyboardEvent } from 'react'

const steamHelp = 'https://help.steampowered.com/en/faqs/view/4DBA-E6A9-1115-7852'
const ubisoftHelp = 'https://www.ubisoft.com/en-gb/help/connectivity-and-performance/article/finding-the-installation-location-for-your-ubisoft-game/000063991'

export function ReplayHelp({ helpRef }: { helpRef: RefObject<HTMLDetailsElement> }) {
  const [launcher, setLauncher] = useState(0)
  const tabs = useRef<(HTMLButtonElement | null)[]>([])
  function navigate(event: KeyboardEvent, index: number) {
    const next = event.key === 'Home' ? 0 : event.key === 'End' ? 1 : ['ArrowLeft', 'ArrowRight'].includes(event.key) ? 1 - index : null
    if (next === null) return
    event.preventDefault(); setLauncher(next); tabs.current[next]?.focus()
  }
  return <details className="replay-help" ref={helpRef}>
    <summary>Show me where to find my replays</summary>
    <p>You don’t need to find individual replay files. We’ll find them when you add your folder.</p>
    <div className="replay-help-tabs" role="tablist" aria-label="Your game launcher">
      {['Steam', 'Ubisoft Connect'].map((name, i) => <button key={name} ref={element => { tabs.current[i] = element }} type="button" role="tab" id={`replay-help-tab-${i}`} aria-controls={`replay-help-panel-${i}`} aria-selected={launcher === i} tabIndex={launcher === i ? 0 : -1} onClick={() => setLauncher(i)} onKeyDown={event => navigate(event, i)}>{name}</button>)}
    </div>
    <div role="tabpanel" id="replay-help-panel-0" aria-labelledby="replay-help-tab-0" hidden={launcher !== 0}>
      <ol className="replay-help-steps">
        <li>Open <strong>Steam</strong>.</li><li>Click <strong>Library</strong>.</li><li>Find <strong>Rainbow Six Siege</strong>.</li><li>Right-click <strong>Rainbow Six Siege</strong>.</li><li>Click <strong>Manage</strong>.</li><li>Click <strong>Browse local files</strong>.</li>
      </ol><p>File Explorer will open. Find the folder named <strong>MatchReplay</strong>.</p>
      <a href={steamHelp} target="_blank" rel="noreferrer">Steam’s folder help ↗</a>
    </div>
    <div role="tabpanel" id="replay-help-panel-1" aria-labelledby="replay-help-tab-1" hidden={launcher !== 1}>
      <ol className="replay-help-steps">
        <li>Open <strong>Ubisoft Connect</strong> and sign in.</li><li>Click <strong>Library</strong>.</li><li>Click <strong>Rainbow Six Siege</strong>.</li><li>Click <strong>Manage</strong>, then <strong>Properties</strong>.</li>
        <li>Find <strong>Installation directory</strong> and copy the location shown there.</li><li>Open <strong>File Explorer</strong> (Windows key + E). Click the address bar at the top, paste that location, and press Enter.</li>
      </ol><p>Find <strong>MatchReplay</strong> in the folder that opens. Installed Siege through Steam? Use the Steam steps instead.</p>
      <a href={ubisoftHelp} target="_blank" rel="noreferrer">Ubisoft’s installation help ↗</a>
    </div>
    <div className="replay-help-drag"><strong>Now drag your replays onto this page</strong><p>Drag the whole <strong>MatchReplay</strong> folder into the box above. Or open MatchReplay, select the folders for your match, and drag those together. You’ll choose which folders to submit next.</p></div>
    <details className="replay-path-help"><summary>Still can’t find it?</summary><p>Example Steam location on Windows:</p><code>C:\Program Files (x86)\Steam\steamapps\common\Tom Clancy's Rainbow Six Siege\MatchReplay</code><p>Your game may be on another drive or in another Steam library. Use the steps above to find your own folder. If MatchReplay is missing, check that Match Replay is enabled in Siege and that you’ve played a match.</p><a href="https://www.ubisoft.com/en-ca/help/article/000100946" target="_blank" rel="noreferrer">Ubisoft’s Match Replay help ↗</a></details>
  </details>
}
