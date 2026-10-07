import { test } from 'node:test'
import assert from 'node:assert/strict'
import { groupReplayFiles, selectionTotals, validateSelection, safeReplayName } from '../src/replayFiles.ts'

const file = (folder, name, size = 30, lastModified = 1) => ({ name, size, lastModified, webkitRelativePath: `MatchReplay/${folder}/${name}` })
test('directory scans group whole replay folders, ignore other files and sort recent first', () => {
  const groups = groupReplayFiles([file('Match-old', 'R01.rec'), file('Match-new', 'R01.rec', 40, 2), file('Match-old', 'R02.rec'), file('Match-new', 'notes.txt')])
  assert.deepEqual(groups.map(g => g.name), ['Match-new', 'Match-old'])
  assert.deepEqual(selectionTotals(groups), { folders: 2, files: 3, bytes: 100 })
  assert.deepEqual(validateSelection([groups[1]]), { folders: 1, files: 2, bytes: 60 })
})
test('individual files, unsafe paths and ambiguous folder/file names cannot enter an upload', () => {
  assert.throws(() => groupReplayFiles([{ name: 'R01.rec', size: 30, lastModified: 1 }]))
  assert.throws(() => groupReplayFiles([file('Match', 'R01.rec'), file('Match', 'r01.REC')]))
  assert.throws(() => groupReplayFiles([file('Match', 'R01.rec'), { ...file('Match', 'R02.rec'), webkitRelativePath: 'Other/Match/R02.rec' }]))
  for (const name of ['../x.rec', 'CON.rec', 'x.exe', 'C:\\x.rec']) assert.throws(() => safeReplayName(name, true))
})
test('empty, oversized and excessive selections are rejected locally', () => {
  assert.throws(() => validateSelection([]))
  assert.throws(() => validateSelection(groupReplayFiles([file('Match', 'R01.rec', 64 * 1024 ** 2 + 1)])))
  assert.throws(() => validateSelection(groupReplayFiles(Array.from({ length: 13 }, (_, i) => file('Match-' + i, 'R01.rec')))))
  assert.throws(() => validateSelection(groupReplayFiles(Array.from({ length: 241 }, (_, i) => file('Match', `R${i}.rec`)))), /240 files/)
  assert.throws(() => validateSelection(groupReplayFiles(Array.from({ length: 33 }, (_, i) => file('Match', `R${i}.rec`, 64 * 1024 ** 2)))), /2 GiB/)
})
