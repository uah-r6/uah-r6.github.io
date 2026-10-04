# Go reader lifetime fix: opt-in only

`ReadEventHistoryEvidence` captures a local reference to the decompressed buffer before normal `Reader.Read`, then passes it to the unchanged structural inspector with the final header. Default `Reader.Read` still releases its buffer. Operator/action-start, feedback, objective, statistics and import paths are unchanged. An inspection call on an already released reader now reports the stage limitation directly.

The separately named v2 executable matches all **six fixed cached controls across four builds**, and both **actual `.rec` controls** now match their saved structural evidence exactly:

| Actual input | Result |
| --- | --- |
| SAL8583 Clubhouse R02 | Exact parity, four finishes plus four candidate kind5 records |
| UAHFortress R04 | Exact parity, six finishes plus one candidate kind5 record |

This verifies the new explicit Go interface, not a credited-victim policy. It does not rerun a research pipeline or a model/final evaluation. The original two v1 failures, all74cached v1 results, binary and historical source snapshots remain immutable. A new source/binary/selection reservation and all eight v2 results are in ignored `data/research/credited-history-go-interface-v2/`.

Full Go tests including Y11 fixtures and eight new history tests pass; `go vet ./...` passes.477Python tests passed,1optional skipped,6subtests; subsequent changes are the opt-in Go interface and a research control runner. No web/export/runtime Python change, so the prior production builds apply. Protected SQLite/archive/public/default-binary/v2 snapshots and old studies remain unchanged.

The diagnostic is built separately:

```powershell
# From third_party/siege-dissect
& '..\..\.local-tools\go\bin\go.exe' build -o '..\..\.local-tools\bin\siege-history-inspect-v2.exe' ./cmd/history-inspect
```

It accepts `--buffer observation.json round.dump` or `--replay ROUND.rec`, returns raw bounded structure/list order/UID references, retains null elapsed seconds and `production_authoritative=false`, and never opens SQLite. `complete` means count/bounds/prefix completeness. A kill-free source without a two-reference anchor, incomplete ten-player five-versus-five identities, unknown kinds/opaque values, replacement/reordered copies and malformed bounds refuse. Generic downer/credit/cause interpretation is not provided.

Next: use the already consumed74source Go evidence and cached routed body states to audit candidate kind5/7 coverage, missing life-state entries, recovery/self/friendly/environment controls and serialization ordering. Keep every refusal and mismatch. Investigate explicit replay clock units separately; do not infer seconds from scalar magnitude or byte distance. No Rating fit, default source promotion, historical kill migration or publication.
