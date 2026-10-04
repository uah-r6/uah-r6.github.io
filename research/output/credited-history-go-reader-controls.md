# Opt-in Go history evidence controls

The new Go structural reader matches all **74 fixed cached buffers**, including every typed item byte range/raw payload, ordinal, identity/icon/alliance, header profile/team, container boundary and scalar tie. It retains null elapsed seconds and `production_authoritative=false`. No Python tracker/runtime/default reader path uses this evidence.

Six Go tests cover cumulative prefixes, tied list order, replacement/reordering refusal, unknown middle/truncation, strict ten-player five-versus-five identity, exact icon and alliance width, raw kinds2/3/10 and unsupported kill-free anchors. Three Python verifier tests reject source/identity/scalar drift, inferred seconds/authority and silent scalar sorting. Full Go tests and vet passed.477Python tests passed,1optional skipped,6subtests. Public/admin source unchanged.

## Actual input exposed an integration failure

The initial `--replay` controls on SAL8583R02 and UAHFortressR04 both returned incomplete `no_bounded_two_reference_anchor`, although their cached buffers matched. `Reader.Read()` explicitly frees its decompressed buffer at completion (`r.b=nil`). The trial incorrectly inspected that released buffer after `Read`. This is a reader-lifetime problem, not a missing replay event or new round/operator issue.

Both failed actual-input results, source/binary reservation and expected cached evidence are preserved under `data/research/credited-history-go-controls/`. Exact historical source snapshots are committed under `research/source-checkpoints/go-history-v1/` before correcting the interface; source/result hashes remain verifiable. The v1 executable remains separate and ignored. Do not rerun the old source/binary reservation against a revised source tree or replace the failures with successful results.

Next: an opt-in wrapper captures a reference to the decompressed buffer before normal reading, then inspects that reference using the final header. Leave default `Reader.Read` memory release unchanged. Build a separately named v2 diagnostic executable, reserve a new interface trial, then verify both actual inputs and cached-buffer parity. No credit attribution, time calibration, Rating formula, normalization, SQLite, archive, default parser executable or public JSON change is permitted by this prototype.

The causal mismatch stays unresolved: Aokayu raw3 has no typed kind5 actor record, and Nina/OSAdinho counters differ from the finisher-based hypothesis. Complete structural framing does not supply missing down ownership or a generic self/TK/environment policy. Further lifecycle/source/clock research and a separate migration review are required.
