import { test } from 'node:test'
import assert from 'node:assert/strict'
import { createHash } from 'node:crypto'
import { captureDroppedRoots, readDroppedReplays, readReplayHandle, readReplayEntry, pickerNotice } from '../src/replayDirectories.ts'
import { groupReplayFiles, mergeReplayFolders, selectionTotals, validateSelection } from '../src/replayFiles.ts'

const replay = (name = 'Game-R01.rec', body = 'dissect replay fixture bytes') => ({ kind: 'file', name, getFile: async () => new File([body], name, { lastModified: 100 }) })
const dir = (name, ...children) => ({ kind: 'directory', name, async *values() { yield* children } })
const match = name => dir(name, replay(), replay('Game-R02.rec'), replay('notes.txt'))
const drop = (...roots) => captureDroppedRoots(roots.map(handle => ({ kind: 'file', getAsFileSystemHandle: async () => handle })))
const groupedDrop = async (...roots) => (await readDroppedReplays(drop(...roots))).map(groupReplayFiles)
const hash = async file => createHash('sha256').update(Buffer.from(await file.arrayBuffer())).digest('hex')
const same = async (a, b) => await hash(a) === await hash(b)

test('whole MatchReplay dropped tree discovers only replay files and preserves physical folders', async () => {
  const [groups] = await groupedDrop(dir('MatchReplay', match('Map1'), match('Map2')))
  assert.deepEqual(groups.map(g => g.name), ['Map1', 'Map2'])
  assert.equal(selectionTotals(groups).files, 4)
  assert.equal(groups[0].files[0].webkitRelativePath, 'MatchReplay/Map1/Game-R01.rec')
})
test('single and multiple match folders use the same discovery and selection rules', async () => {
  const groups = (await groupedDrop(match('Map1'), match('Map2'))).flat()
  assert.deepEqual(groups.map(g => g.name), ['Map1', 'Map2'])
  assert.equal(validateSelection([groups[1]]).files, 2)
  assert.deepEqual((await groupedDrop(match('Single')))[0].map(g => g.name), ['Single'])
})
test('repeated parent/child additions are hash-deduplicated despite different relative roots', async () => {
  const [parent] = await groupedDrop(dir('MatchReplay', match('Map1')))
  const [child] = await groupedDrop(match('Map1'))
  const merged = await mergeReplayFolders(parent, child, same)
  assert.equal(merged.duplicates, 1); assert.equal(merged.folders.length, 1)
  assert.equal(merged.folders[0], parent[0])
})
test('same folder titles and same-sized different content are never silently merged', async () => {
  const [a] = await groupedDrop(match('Map1'))
  const [b] = await groupedDrop(dir('Map1', replay('Game-R01.rec', 'different replay fixture!!!!'), replay('Game-R02.rec')))
  assert.equal(a[0].files[0].size, b[0].files[0].size)
  await assert.rejects(mergeReplayFolders(a, b, same), /different replay folders/)
  await assert.rejects(mergeReplayFolders(a, [{ ...b[0], files: b[0].files.slice(0, 1) }], same), /different replay folders/)
})
test('unrelated folders and dropped individual files yield no replay folder', async () => {
  assert.deepEqual(await readReplayHandle(dir('Other', replay('notes.txt'))), [])
  assert.deepEqual(await readDroppedReplays(drop(replay())), [])
  assert.deepEqual(captureDroppedRoots([{ kind: 'string' }]), [])
})
function entry(handle, batchSize = 1) {
  if (handle.kind === 'file') return { name: handle.name, isFile: true, isDirectory: false, file: callback => { handle.getFile().then(callback) } }
  return { name: handle.name, isFile: false, isDirectory: true, createReader: () => {
    const iterator = handle.values(); let ended = false
    return { readEntries: async callback => { const batch = []; if (!ended) for (let n = 0; n < batchSize; n++) { const next = await iterator.next(); if (next.done) { ended = true; break } batch.push(entry(next.value, batchSize)) } callback(batch) } }
  } }
}
test('Chromium entry fallback drains every paginated batch, including beyond 100 entries', async () => {
  const root = dir('MatchReplay', ...Array.from({ length: 105 }, (_, i) => match(`Map${i}`)))
  const files = await readReplayEntry(entry(root, 100))
  assert.equal(groupReplayFiles(files).length, 105)
  assert.equal(files.length, 210)
})
test('read-only dropped entries never request a modern handle or its protected-folder prompt', async () => {
  let captures = 0
  const root = match('Legacy')
  const captured = captureDroppedRoots([{ kind: 'file', getAsFileSystemHandle() { captures++; return Promise.reject(new DOMException('Blocked', 'NotAllowedError')) }, webkitGetAsEntry() { captures++; return entry(root) } }])
  assert.equal(captures, 1)
  assert.equal((await readDroppedReplays(captured))[0].length, 2)
  const broken = { ...root, async *values() { throw new DOMException('Protected', 'NotAllowedError') } }
  assert.equal((await readDroppedReplays([{ handle: Promise.resolve(broken), entry: entry(root) }]))[0].length, 2)
})
test('modern handles are captured synchronously only when a read-only entry is unavailable', async () => {
  let captured = false
  const roots = captureDroppedRoots([{ kind: 'file', webkitGetAsEntry: () => null, getAsFileSystemHandle: () => { captured = true; return Promise.resolve(match('Modern-only')) } }])
  assert.equal(captured, true)
  assert.equal((await readDroppedReplays(roots))[0].length, 2)
})
test('native picker traversal and directory input produce identical selection inventories', async () => {
  const modern = groupReplayFiles(await readReplayHandle(dir('MatchReplay', match('Map1'))))
  const fallback = groupReplayFiles(modern.flatMap(g => g.files))
  assert.deepEqual(selectionTotals(modern), selectionTotals(fallback))
  assert.deepEqual(modern.map(g => g.name), fallback.map(g => g.name))
})
test('protected picker refusals are helpful and ambiguous cancellation is neutral', () => {
  assert.match(pickerNotice({ name: 'SecurityError' }), /blocked direct access.*File Explorer/)
  assert.match(pickerNotice({ name: 'AbortError' }), /^No folder added/)
  assert.doesNotMatch(pickerNotice({ name: 'AbortError' }), /error|failed|dangerous/i)
})
