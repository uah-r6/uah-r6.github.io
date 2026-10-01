# Trade window experiment - 2026-10-01

Plan frozen at `1d12882`, implementation at `428bc29`. Full experiment `trade-window-20261001T215040Z` is saved in `research/experiment-log.jsonl` and ignored `data/research/experiments/trade-window-isolated-v1.json`; the record's code hash and 47 normalized-map SHA-256s are authoritative. All 8-second `deaths_traded`, `kills_traded` and KOST player-round values matched the unchanged observations (zero parity mismatches). No replay parser, live database or archived replay was modified.

The seven pre-August events supply 299 clean player-map rows / 3,215 player-rounds; August EWC supplies 32 separate development rows. The 16 historical September and 60 sealed NA September rows were excluded. Values below use the same killer-based refrag semantics and change only the timer threshold. KOST remains the cached eight-second value in every fit to isolate the trade family; a production window change would also alter KOST and needs separate consistency evaluation.

| Window | Training death / kill trades | Pooled fold MAE | August MAE | August RMSE | Median AE | Max AE | Trade slope |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 5s | 299 / 295 | 0.03768 | 0.03638 | 0.04686 | 0.03008 | 0.1356 | +0.1188 |
| 6s | 338 / 322 | 0.03731 | 0.03514 | 0.04648 | 0.02689 | 0.1356 | +0.1220 |
| 7s | 359 / 343 | 0.03731 | 0.03497 | 0.04662 | 0.02652 | 0.1354 | +0.1266 |
| **8s baseline** | **375 / 363** | **0.03647** | **0.03453** | **0.04626** | **0.02248** | **0.1338** | **+0.1418** |
| 10s | 429 / 418 | 0.03616 | 0.03597 | 0.04666 | 0.02228 | 0.1311 | +0.1504 |

| Window | Within .01 | .02 | .03 | .05 | .10 |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 5s | 18.8% | 37.5% | 50.0% | 71.9% | 96.9% |
| 6s | 25.0% | 43.8% | 56.3% | 71.9% | 96.9% |
| 7s | 25.0% | 43.8% | 59.4% | 71.9% | 96.9% |
| 8s | 21.9% | 46.9% | 59.4% | 71.9% | 96.9% |
| 10s | 15.6% | 46.9% | 59.4% | 68.8% | 96.9% |

The record contains all seven held-out event fold results, trade differential distribution, development trade counts, and coefficient drift for every shared feature. Ten seconds improves pooled fold MAE by only 0.00031 and worsens August by 0.00144. Shorter windows worsen pooled MAE by 0.00084-0.00121 and August by 0.00044-0.00185. The full-fit trade slope rises with the window. The largest shared-coefficient drift is a sparse teamkill term (up to 0.0339 at seven seconds). Whole-second timestamps also make one-second boundaries coarse. Keep eight seconds as the working research window; no evidence here warrants changing the tracker setting. Baseline pooled median AE was not recorded by the historical CV run and was not recreated via an identical fit.

NEXT: at eight seconds, compare death-traded rate, kill-traded rate, and the current differential with one fixed split/model configuration. The death and kill indicators have different player meanings. Keep all other families fixed, objectives omitted, final NA ratings sealed. Then audit how KOST overlaps with survival and trade credit before considering any combined change.
