# Public methodology presentation

The public guide uses URL-addressable sections (`/#/methodology/rating`, for example), native expandable cards, and a keyboard/touch-accessible SVG scatter. It explains production behavior; it does not calculate or modify statistics.

## Frozen Rating visualization

`web/public/methodology/rating-v3-final.json` is a projection of the already saved APAC North Stage 1 2026 final result. Its 110 player-map pairs retain the exact target, v3 prediction and original v2 prediction. Map names were joined by public match/game/player identity from the sealed pre-target rows. No fitting, evaluation, downloading or replay parsing was rerun.

The committed [final report](../research/output/v3-native-final-apac1-result.md) verifies MAE 0.03035933195958, comparison MAE 0.06058645313795608, and 81.81818181818% within ±0.05. Both models use the same 110 observations. Freeze commit: `e05dfc4`. The final event remains consumed. This asset contains only public professional player/map/game identifiers and ratings; no raw inputs, profiles, private UAH data or filesystem/cache paths.

The asset is outside `web/public/data/` so routine website-stat exports cannot erase it. The existing Vite build copies it into the static website. A failed or malformed chart response leaves the verified final summary visible. The Node tests recompute summary metrics from the projected points and compare them with the committed final report. This is a prediction comparison, not a convergence or training curve.

## Verification

Run `npm.cmd test` and `npm.cmd run build` in `web`. From the repository root, run `.venv\Scripts\python.exe scripts/verify-public-polish-ui.py` for the built site, or pass `--url https://uah-r6.github.io/` for deployment checks. This optional Playwright/Edge check covers section links, native accordion keyboard use, sorting, chart hover/tap/keyboard selection, malformed-data fallback and the public routes at four screen widths. `scripts/verify-team-ui.py` retains the broader team/season/Alumni checks.
