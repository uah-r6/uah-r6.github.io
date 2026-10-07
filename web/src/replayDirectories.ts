// Browser access only. Replay grouping, selection and upload rules live in replayFiles.
export type ReplayHandle = {
  kind: string
  name: string
  values?(): AsyncIterable<ReplayHandle>
  getFile?(): Promise<File>
}
export type ReplayEntry = {
  name: string
  isDirectory: boolean
  isFile: boolean
  createReader?(): { readEntries(success: (entries: ReplayEntry[]) => void, failure: (error: DOMException) => void): void }
  file?(success: (file: File) => void, failure: (error: DOMException) => void): void
}
type DroppedItem = {
  kind: string
  getAsFileSystemHandle?(): Promise<ReplayHandle | null>
  webkitGetAsEntry?(): ReplayEntry | null
}
export type DroppedRoot = { handle: Promise<ReplayHandle | null>; entry: ReplayEntry | null }

// Capture both APIs during the drop event: Chromium stops exposing items after it.
export function captureDroppedRoots(items: ArrayLike<DroppedItem>): DroppedRoot[] {
  return Array.from(items).filter(item => item.kind === 'file').map(item => {
    const entry = item.webkitGetAsEntry?.() || null
    let handle: Promise<ReplayHandle | null>
    try { handle = item.getAsFileSystemHandle?.() || Promise.resolve(null) }
    catch { handle = Promise.resolve(null) }
    // Attach rejection handling immediately, including while earlier roots are read.
    return { handle: handle.catch(() => null), entry }
  })
}

function relativeFile(file: File, prefix: string) {
  Object.defineProperty(file, 'webkitRelativePath', { value: `${prefix}/${file.name}`, configurable: true })
  return file
}

export async function readReplayHandle(root: ReplayHandle): Promise<File[]> {
  if (root.kind !== 'directory') return []
  const files: File[] = []
  async function walk(handle: ReplayHandle, prefix: string, depth: number) {
    if (depth > 16) throw Error('Choose MatchReplay or the replay folders inside it, rather than a larger folder.')
    if (!handle.values) throw Error('This browser could not read the folder. Try Browse for replay folder.')
    for await (const entry of handle.values()) {
      if (entry.kind === 'directory') await walk(entry, `${prefix}/${entry.name}`, depth + 1)
      else if (/\.rec$/i.test(entry.name) && entry.getFile) files.push(relativeFile(await entry.getFile(), prefix))
    }
  }
  await walk(root, root.name, 0)
  return files
}

export async function readReplayEntry(root: ReplayEntry): Promise<File[]> {
  if (!root.isDirectory) return []
  const files: File[] = []
  async function walk(entry: ReplayEntry, prefix: string, depth: number) {
    if (depth > 16) throw Error('Choose MatchReplay or the replay folders inside it, rather than a larger folder.')
    if (!entry.createReader) throw Error('This browser could not read the folder. Try Browse for replay folder.')
    const reader = entry.createReader()
    // readEntries is paginated (often 100 entries); one call can omit valid rounds/folders.
    for (;;) {
      const batch = await new Promise<ReplayEntry[]>((resolve, reject) => reader.readEntries(resolve, reject))
      if (!batch.length) break
      for (const child of batch) {
        if (child.isDirectory) await walk(child, `${prefix}/${child.name}`, depth + 1)
        else if (child.isFile && /\.rec$/i.test(child.name) && child.file) {
          const file = await new Promise<File>((resolve, reject) => child.file!(resolve, reject))
          files.push(relativeFile(file, prefix))
        }
      }
    }
  }
  await walk(root, root.name, 0)
  return files
}

// Batches preserve directory origins for grouping before duplicate additions merge.
export async function readDroppedReplays(roots: DroppedRoot[]): Promise<File[][]> {
  const batches: File[][] = []
  for (const root of roots) {
    const handle = await root.handle
    if (handle?.kind === 'directory') {
      try { batches.push(await readReplayHandle(handle)) }
      catch (error) { if (root.entry?.isDirectory) batches.push(await readReplayEntry(root.entry)); else throw error }
    }
    else if (root.entry?.isDirectory) batches.push(await readReplayEntry(root.entry))
  }
  return batches
}

export function pickerNotice(error: { name?: string; message?: string }) {
  // AbortError also means sensitive folder/permission refusal. Do not label it an error.
  if (error.name === 'AbortError') return 'No folder added. If your browser blocked the game folder, open it in File Explorer and drag it here, or try Browse for replay folder.'
  if (['SecurityError', 'NotAllowedError'].includes(error.name || '') || /system|sensitive|protected|permission|denied/i.test(error.message || '')) {
    return 'Your browser blocked direct access to this game folder. Open MatchReplay in File Explorer and drag it into the box above, or try Browse for replay folder.'
  }
  return 'The folder could not be opened. Try dragging it from File Explorer or use Browse for replay folder.'
}
