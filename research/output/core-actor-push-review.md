# Core actor code push review — 2026-10-03

User authorized pushing the completed conservative core resolver and appropriate existing source, tests and research/status documentation. Pre-push checkpoint: `3535fa5`; branch: `main`; remote: `https://github.com/uah-r6/uah-r6.github.io.git`; prior remote checkpoint: `059f556`.

## Production scope

Core implementation commit `f534b31`: `third_party/siege-dissect/dissect/objective_actor.go`, `objective_actor_test.go`, `objective_occurrence.go`, `reader.go`; `r6stats/parser/models.py`, `siege_dissect.py`; `tests/test_verified_objective_actor_adapter.py`. Supporting reduced structured fixtures, guarded completeness/cancellation/ambiguity controls, parity scripts and documentation are included. The complete file inventory is [core-actor-push-files.txt](core-actor-push-files.txt), comparing the original remote checkpoint with the reviewed checkpoint.

The other pending commits preserve research provenance, including unsuccessful studies. Bonus-health/body1 and older-component hypotheses remain isolated research. No production allowlist, bonus actor port, kill semantics change, rating change or historical correction is included.

## Verification before push

- Python: **348 passed, one optional replay smoke test skipped, six subtests passed**.
- `go test ./...` and `go vet ./...`: pass. Includes reduced real objective completer/disable fixtures, interrupted/canceled attempts, ambiguity, objective-free and operator regressions.
- Public/admin Vite builds: pass.
- `research/objective_oce_consumed_support_verify.py`: all frozen actor/v3 sources, binaries, results and identity/support seals match; all **86 protected SQLite/archive/public files** unchanged.
- Pending history contains no changes under `web/public/data/` and no private replay/database/settings/download/cache files. Working tree was clean before this documentation addition.

## Exclusions and deployment behavior

Private SQLite, settings, raw `.rec`, replay archives, downloads, videos, derived research caches and local binaries remain ignored and excluded. No import, reparse, statistics recalculation, public export or actor correction occurred. Both failed v3 results and live v2's original MAE **0.03623** are preserved.

The existing GitHub Actions Pages workflow runs on pushes to main and builds the committed public site with unchanged JSON. This push does not publish corrected historical statistics. Next work is the credited-kill counter implementation and **read-only** UAH migration review; live historical changes require user review first.
