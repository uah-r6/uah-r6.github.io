# Prospective corrected-KOST SAL final quality seal

All 20 prospectively linked official archives have replay predictions and terminal quality decisions. Final Rating values and actor labels remain unopened. Exact model freeze and accuracy gates are unchanged.

| Official / SiegeGG | Map | Rounds | Objectives | Unresolved | Clean rows |
| --- | --- | ---: | --- | ---: | ---: |
| 8580/6178 | Lair | 14 | {'plant': 5, 'disable': 1} | 0 | 6 |
| 8581/6179 | Villa | 10 | {'plant': 4, 'disable': 1} | 1 | 0 |
| 8582/6180 | Border | 8 | {'plant': 3} | 0 | 7 |
| 8583/6253 | Clubhouse | 12 | {'plant': 3} | 0 | 5 |
| 8584/6262 | Chalet | 8 | {'plant': 2} | 0 | 10 |
| 8585/6182 | Kafe Dostoyevsky | 10 | {'plant': 1} | 0 | 6 |
| 8586/6183 | Chalet | 12 | {'plant': 1} | 0 | 6 |
| 8587/6263 | Border | 14 | {'plant': 5} | 0 | 6 |
| 8588/6264 | Border | 12 | {'plant': 4, 'disable': 1} | 1 | 0 |
| 8589/6185 | Nighthaven Labs | 11 | {'plant': 2} | 0 | 10 |
| 8590/6318 | Fortress | 12 | {'plant': 1} | 0 | 8 |
| 8591/6319 | Chalet | 10 | {'plant': 5} | 0 | 8 |
| 8592/6320 | Nighthaven Labs | 9 | {'plant': 1} | 0 | 8 |
| 8593/6321 | Nighthaven Labs | 7 | {} | 0 | 8 |
| 8594/6322 | Bank | 10 | {'plant': 4, 'disable': 2} | 0 | 5 |
| 8595/6323 | Border | 8 | {'plant': 1, 'disable': 1} | 0 | 10 |
| 8596/6324 | Lair | 10 | {'plant': 1, 'disable': 1} | 0 | 10 |
| 8597/6325 | Nighthaven Labs | 10 | {'plant': 2} | 0 | 10 |
| 8598/6326 | Border | 8 | {'plant': 1} | 0 | 8 |
| 8599/6327 | Fortress | 12 | {'plant': 1} | 0 | 10 |

Totals: {'rounds': 207, 'clean': 141, 'plant': 47, 'disable': 7, 'resolved_plant': 45, 'resolved_disable': 7}. Coverage: {'clean_rows': 141, 'clean_maps': 18, 'distinct_rosters': 10, 'objective_positive_rows': 24}; gates: {'min_clean_rows': True, 'min_clean_maps': True, 'min_distinct_rosters': True, 'min_objective_positive_rows': True}.

Exclusion issue incidences (overlapping): {'Exact K/D mismatch': 43, 'Entire map excluded: unresolved objective actor': 20}.

Both arms use the same fully objective-corrected KOST and verified objectives. Every frozen per-round feature row was independently checked against normalized rounds. Objective credits equal the verified occurrence actors; no unverified legacy credit leaks into the feature. Missing actor evidence excludes the entire map. No identity mapping uses Rating or K/D outcomes.

Eight explicit exact-UUID aliases are independently corroborated by profile histories and official rosters. Official roster GUIDs are blank: account histories support identity, not an official GUID binding. Earlier unaliased quality caches are preserved; the final cache key includes the sealed alias digest.

Prediction, quality, API and sealed target digests for all 20 archives are stored in ignored `prelabel-quality-seal.json`. The snapshot does not include the 25 unavailable later group matches or playoffs; the entire event remains reserved. Accuracy gates are unevaluated. Live v2, SQLite, private archives and public JSON remain unchanged.

Sources: [official schedule and archives](https://www.ubisoft.com/en-us/esports/rainbow-six/siege/competition/515/15020), [independent schedule](https://siege.gg/matches?competitions=187&tab=results&page=2), [independent alias registry](../v3-corrected-final-verified-aliases.json).

NEXT: commit this prospective quality checkpoint before consuming the final once. Never refit on this event or deploy automatically.
