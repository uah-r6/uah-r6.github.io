# Independent Ubisoft disable label constraints

Already-consumed maps only. Cached official page JSON exposes objective map totals and one-based round indexes, but `roundsStats` is an Attack/Defense aggregate, not per-round player telemetry. The primary website [enum bundle](https://static-esports.ubisoft.com/r6-website/_next/static/chunks/4112-0c4268865dc52bd7.js) explicitly defines Defuser=3. The review checks complete round identities, sides, winners, score and total disables. Where exactly one player accounts for every disable for a team, their map total constrains those round labels. This is an inference from a separate primary source, not a direct per-round actor field and not new independent replay accuracy.

| Official match / map | Team | Disable rounds | Nonzero player map totals | Constrained labels |
| --- | --- | --- | --- | --- |
| [9026](https://www.ubisoft.com/en-us/esports/rainbow-six/siege/match/9026) / Bank | 39 | [2] | njr=1 | R02 njr |
| [9026](https://www.ubisoft.com/en-us/esports/rainbow-six/siege/match/9026) / Bank | 43 | [10] | Spoit=1 | R10 Spoit |
| [7740](https://www.ubisoft.com/en-us/esports/rainbow-six/siege/match/7740) / Bank | 5 | [3] | Kds=1 | R03 Kds |
| [7740](https://www.ubisoft.com/en-us/esports/rainbow-six/siege/match/7740) / Fortress | 5 | [17] | Handyy=1 | R17 Handyy |
| [9070](https://www.ubisoft.com/en-us/esports/rainbow-six/siege/match/9070) / Bank | 9 | [1, 4] | Loira=2 | R01 Loira, R04 Loira |

Bank9026: DarkZero has one Defuser win, R02; njr has one disable and J9O zero. This is new primary evidence supporting njr and contradicting the original SiegeGG J9O label. That original label and every primary validation result remain preserved. The mandatory research control stays unresolved while the separate reviewed inference is documented. No resolver has been changed to emit njr.

SI7740: Bank has only one FaZe Defuser win, R03, and only Kds has a disable. Fortress has only one FaZe Defuser win, R17, and only Handyy has a disable. This independently supports the owners observed before explicit slot clears, despite missing global state0/component state2. It does not make slot clear alone a valid completion rule.

EWC9070: FURIA Bank Defuser wins are R01/R04; Loira has two disables and Dias zero. This agrees with the separately reviewed R01 Counter-Defusing HUD and contradicts the original Dias round label. Original outcomes are not rewritten. The official data pipeline may share underlying telemetry with other statistics sites; source independence does not prove measurement independence.

VOD limits: official Salt Lake final pTsWYqy7H2k shows Surf planting BankR02 at7080, 7088,7090,7093, then cuts to player camera by7095 before the disable HUD is visible. SI final hMJcW8s94Tk BankR03 at5900 shows postplant44.56, followed by stage/player cameras5903-5920. FortressR17 at12650 shows Mowwwgli planting;12656 postplant44.56, 12658 postplant42.55, then player cameras12661/12664/12670/12680. These samples do not visually verify kds or handyy counter-defusing. Do not infer an actor from the camera subject.

Reproduce with `.venv/Scripts/python.exe research/objective_official_disable_review.py`. Detailed source cache SHA256, enum SHA256 and objective-only projections remain ignored. 86 protected local file hashes unchanged. No target, Rating, SQLite, archive, public JSON or runtime change.
