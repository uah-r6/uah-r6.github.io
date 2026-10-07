export type ReplayFile = { name: string; size: number; lastModified: number; webkitRelativePath?: string }
export type ReplayFolder<T extends ReplayFile> = { name: string; files: T[]; bytes: number; modified: number }
export const replayLimits = { fileBytes: 64 * 1024 ** 2, submissionBytes: 2 * 1024 ** 3, folders: 12, files: 240 }

export function safeReplayName(name: string, replay = false) {
  if (!name || name.length > 160 || /[<>:"/\\|?*\x00-\x1f\x7f]/.test(name) || /[. ]$/.test(name)
    || name === '.' || name === '..' || /^(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\.|$)/i.test(name)
    || (replay && !/\.rec$/i.test(name))) throw Error('Unsafe replay filename. Choose the original MatchReplay folder.')
  return name
}

export function groupReplayFiles<T extends ReplayFile>(files: T[]): ReplayFolder<T>[] {
  const groups = new Map<string, ReplayFolder<T>>()
  const origins = new Map<string, string>()
  for (const file of files) {
    if (!/\.rec$/i.test(file.name)) continue
    safeReplayName(file.name, true)
    const path = (file.webkitRelativePath || '').split('/')
    if (path.length < 2 || path.some(p => !p || p === '..' || p === '.')) throw Error('Choose a replay directory, rather than individual files.')
    const folder = safeReplayName(path.at(-2)!)
    const origin = path.slice(0, -1).join('/')
    if (origins.has(folder.toLowerCase()) && origins.get(folder.toLowerCase()) !== origin) throw Error('Two replay folders share a name. Choose MatchReplay directly.')
    origins.set(folder.toLowerCase(), origin)
    const group = groups.get(folder) || { name: folder, files: [], bytes: 0, modified: 0 }
    if (group.files.some(f => f.name.toLowerCase() === file.name.toLowerCase())) throw Error('Replay folders contain ambiguous duplicate filenames. Choose MatchReplay directly.')
    group.files.push(file); group.bytes += file.size; group.modified = Math.max(group.modified, file.lastModified)
    groups.set(folder, group)
  }
  return [...groups.values()].sort((a, b) => b.modified - a.modified || a.name.localeCompare(b.name))
}

export function selectionTotals<T extends ReplayFile>(folders: ReplayFolder<T>[]) {
  const files = folders.flatMap(f => f.files)
  return { folders: folders.length, files: files.length, bytes: files.reduce((n, f) => n + f.size, 0) }
}

export async function mergeReplayFolders<T extends ReplayFile>(existing: ReplayFolder<T>[], incoming: ReplayFolder<T>[], sameContents: (a: T, b: T) => Promise<boolean>) {
  const groups = new Map(existing.map(folder => [folder.name.toLowerCase(), folder]))
  let duplicates = 0
  for (const folder of incoming) {
    const previous = groups.get(folder.name.toLowerCase())
    if (!previous) { groups.set(folder.name.toLowerCase(), folder); continue }
    const ordered = (files: T[]) => [...files].sort((a, b) => a.name.toLowerCase().localeCompare(b.name.toLowerCase()))
    const a = ordered(previous.files), b = ordered(folder.files)
    // A parent drop and child drop have different relative roots. Compare the complete
    // physical inventory, then content hashes, rather than trusting the folder title.
    if (a.length !== b.length || a.some((file, i) => file.name.toLowerCase() !== b[i].name.toLowerCase() || file.size !== b[i].size)) {
      throw Error('Two different replay folders have the same name. Keep them separate and submit them one at a time.')
    }
    for (let i = 0; i < a.length; i++) {
      if (!await sameContents(a[i], b[i])) throw Error('Two different replay folders have the same name. Keep them separate and submit them one at a time.')
    }
    duplicates++
  }
  return { folders: [...groups.values()].sort((a, b) => b.modified - a.modified || a.name.localeCompare(b.name)), duplicates }
}

export function validateSelection<T extends ReplayFile>(folders: ReplayFolder<T>[]) {
  const totals = selectionTotals(folders)
  if (!totals.files || totals.folders > replayLimits.folders || totals.files > replayLimits.files || totals.bytes > replayLimits.submissionBytes) {
    throw Error('Select up to 12 replay folders, 240 files and 2 GiB for one match.')
  }
  if (folders.some(f => f.files.some(p => p.size < 16 || p.size > replayLimits.fileBytes))) {
    throw Error('Replay files must be between 16 bytes and 64 MiB each.')
  }
  return totals
}

export function bytesLabel(bytes: number) {
  return bytes >= 1024 ** 3 ? `${(bytes / 1024 ** 3).toFixed(2)} GiB` : `${(bytes / 1024 ** 2).toFixed(1)} MiB`
}
