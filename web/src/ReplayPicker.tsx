import { useRef, useState, type DragEvent } from 'react'
import { FolderOpen, FolderDown, LoaderCircle, ShieldCheck } from 'lucide-react'
import { bytesLabel, groupReplayFiles, mergeReplayFolders, selectionTotals, type ReplayFolder } from './replayFiles'
import { captureDroppedRoots, pickerNotice, readDroppedReplays, readReplayHandle, type ReplayHandle } from './replayDirectories'
import { ReplayHelp } from './ReplayHelp'

type Props = { folders: ReplayFolder<File>[]; selected: string[]; onFolders(folders: ReplayFolder<File>[]): void; onSelected(names: string[]): void; onScanning(value: boolean): void }

export function ReplayPicker({ folders, selected, onFolders, onSelected, onScanning }: Props) {
  const picker = useRef<HTMLInputElement>(null), help = useRef<HTMLDetailsElement>(null)
  const locked = useRef(false), dragDepth = useRef(0), digests = useRef(new WeakMap<File, Promise<string>>())
  const [scanning, setScanning] = useState(false), [dragging, setDragging] = useState(false), [notice, setNotice] = useState(''), [needsHelp, setNeedsHelp] = useState(false)
  const totals = selectionTotals(folders.filter(folder => selected.includes(folder.name)))

  function showHelp() { if (help.current) { help.current.open = true; help.current.scrollIntoView({ block: 'nearest', behavior: 'smooth' }); help.current.querySelector('summary')?.focus() } }
  function digest(file: File) {
    let value = digests.current.get(file)
    if (!value) {
      value = file.arrayBuffer().then(bytes => crypto.subtle.digest('SHA-256', bytes)).then(hash => [...new Uint8Array(hash)].map(n => n.toString(16).padStart(2, '0')).join(''))
      digests.current.set(file, value)
    }
    return value
  }
  async function add(read: () => Promise<File[][]>) {
    if (locked.current) return
    locked.current = true; setScanning(true); onScanning(true); setNotice(''); setNeedsHelp(false)
    try {
      const batches = await read()
      let next = folders, duplicates = 0, found = 0
      for (const files of batches) {
        const incoming = groupReplayFiles(files); found += incoming.length
        const merged = await mergeReplayFolders(next, incoming, async (a, b) => a === b || await digest(a) === await digest(b))
        next = merged.folders; duplicates += merged.duplicates
      }
      if (!found) setNotice(batches.length ? 'No Rainbow Six replay files were found in that folder.' : 'Drag the MatchReplay folder or the replay folders inside it, rather than individual files.')
      else { onFolders(next); setNotice(`${next.length} replay ${next.length === 1 ? 'folder' : 'folders'} found${duplicates ? ' · Already-added folders were kept just once.' : ''}`) }
    } catch (error) { setNotice((error as Error).name === 'Error' ? (error as Error).message : pickerNotice(error as Error)); setNeedsHelp(true) }
    finally { locked.current = false; setScanning(false); onScanning(false) }
  }
  function chooseFolder() {
    if (locked.current) return
    const nativePicker = (window as Window & { showDirectoryPicker?: () => Promise<ReplayHandle> }).showDirectoryPicker
    if (!nativePicker) { picker.current?.click(); return }
    // Keep picker invocation in the user gesture; permission prompts need activation.
    void add(async () => [await readReplayHandle(await nativePicker.call(window))])
  }
  function dragEnter(event: DragEvent) {
    if (!event.dataTransfer.types.includes('Files')) return
    event.preventDefault(); dragDepth.current++; setDragging(true)
  }
  function drop(event: DragEvent) {
    event.preventDefault(); dragDepth.current = 0; setDragging(false)
    const roots = captureDroppedRoots(event.dataTransfer.items)
    void add(() => readDroppedReplays(roots))
  }
  return <section className="replay-picker" aria-labelledby="add-replays-title" aria-busy={scanning}>
    <span className="eyebrow">YOUR MATCH, YOUR CHOICE</span><h2 id="add-replays-title">Add your replays</h2>
    <p>Drag your MatchReplay folder here and we’ll find your replay folders. You don’t need to know which files are the replays.</p>
    <button type="button" className={`replay-dropzone${dragging ? ' dragging' : ''}`} disabled={scanning} onClick={chooseFolder}
      onDragEnter={dragEnter} onDragLeave={event => { event.preventDefault(); dragDepth.current = Math.max(0, dragDepth.current - 1); if (!dragDepth.current) setDragging(false) }}
      onDragOver={event => { event.preventDefault(); event.dataTransfer.dropEffect = scanning ? 'none' : 'copy' }} onDrop={drop} aria-label="Add replay folders: drag here or choose a folder" aria-describedby="replay-drop-instructions">
      {scanning ? <LoaderCircle size={32} aria-hidden="true" /> : <FolderDown size={32} aria-hidden="true" />}
      <strong>{scanning ? 'Looking for Rainbow Six replays…' : dragging ? 'Drop your replay folders here' : 'Drag replay folders here'}</strong>
      <span id="replay-drop-instructions">The whole MatchReplay folder, or one or more folders from your match</span><small>Or click to choose a folder</small>
    </button>
    <p className="replay-mobile-note">Submission is easiest from the PC where Siege is installed.</p>
    <div className="replay-picker-actions"><button className="button" type="button" disabled={scanning} onClick={chooseFolder}><FolderOpen size={16} aria-hidden="true" /> Choose MatchReplay Folder</button><button className="folder-fallback" type="button" disabled={scanning} onClick={() => picker.current?.click()}>Browse for replay folder</button></div>
    <input ref={picker} className="directory-input" aria-hidden="true" tabIndex={-1} type="file" multiple accept=".rec" {...{ webkitdirectory: '', directory: '' }} onChange={event => { const files = Array.from(event.target.files || []); event.target.value = ''; if (files.length) void add(async () => [files]) }} />
    <p className="replay-privacy"><ShieldCheck size={16} aria-hidden="true" /> We only upload the replay folders you choose. Adding a folder just looks for replays on your PC.</p>
    <div className="replay-scan-status" role="status" aria-live="polite" aria-atomic="true">{scanning ? 'Looking for Rainbow Six replays…' : notice}{needsHelp && <button type="button" className="button" onClick={showHelp}>Show me how</button>}</div>
    <ReplayHelp helpRef={help} />
    {!!folders.length && <><div className="replay-results-heading"><h3>Choose folders for this match</h3><button type="button" className="folder-fallback" disabled={scanning} onClick={() => { onFolders([]); onSelected([]); setNotice('Replay selection cleared.') }}>Clear folders</button></div>
      <p>Select all maps for this series, including any rehost segments. Nothing uploads until you review and confirm.</p>
      <div className="replay-folder-list">{folders.map((folder, i) => <label key={folder.name} className={selected.includes(folder.name) ? 'chosen' : ''}>
        <input type="checkbox" disabled={scanning} checked={selected.includes(folder.name)} onChange={event => onSelected(event.target.checked ? [...selected, folder.name] : selected.filter(name => name !== folder.name))} />
        <span><strong>Replay {i + 1}</strong><span>{new Date(folder.modified).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })}</span><small>{folder.name}</small></span>
        <span>{folder.files.length} replay files<br />{bytesLabel(folder.bytes)}</span>
      </label>)}</div><p className="replay-selection-total">{totals.folders} folders selected · {totals.files} replay files · {bytesLabel(totals.bytes)}</p></>}
  </section>
}
