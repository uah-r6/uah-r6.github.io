# Consumed actor evidence comparison

The prior score diagnostic and later sole-survivor diagnostic are separate experiments. The latter never used the score candidate as input. No production resolver was replaced.

Plant intersection counts: `{('no_score', 'not_sole'): 20, ('score', 'not_sole'): 8, ('no_score', 'sole'): 4}`.

**Eight score-only plants, four liveness-only plants, zero overlap.** The net count change of minus four does not identify four lost events. All eight score candidates remain alive according to the diagnostic; multiple living teammates prevent sole-survivor attribution.

| Match/game/round | Earlier score actor (public-correct) | Alive at timer start / completion | Actor alive start/end | Close score packet: before -> after @ relative bytes | Identity |
| --- | --- | --- | --- | --- | --- |
| 3579/6707/R02 | Ape5G.WBG | 3 / 3 | [True, True] | 585 -> 685 @+432 | UID 15820655615635533352; score components [4029960473] |
| 3563/6675/R10 | kyno | 4 / 4 | [True, True] | 2430 -> 2530 @+431 | UID 17479426958970637868; score components [4027816187] |
| 4283/8686/R14 | AsK.Geekay | 2 / 2 | [True, True] | 3113 -> 3213 @+335 | UID 2908442561552310624; score components [4029286808] |
| 6157/10428/R10 | VolpsZ | 5 / 5 | [True, True] | 1650 -> 1750 @+385 | UID 10537995618141140820; score components [4029911555] |
| 6158/10563/R05 | Skeptic.TH | 5 / 5 | [True, True] | 1075 -> 1175 @+490 | UID 3364356254263955379; score components [4026991972] |
| 6277/10576/R01 | Skeptic.TH | 4 / 4 | [True, True] | 120 -> 220 @+700 | UID 10213158968193415914; score components [4027095040] |
| 6277/10576/R11 | Creedz.SECRET | 3 / 3 | [True, True] | 2518 -> 2618 @+505 | UID 6206386892904214706; score components [4027095938] |
| 6277/10576/R12 | Hungry.SECRET | 4 / 4 | [True, True] | 3565 -> 3665 @+613 | UID 10303292278741636312; score components [4027095953] |

No changed packet boundary or identity ambiguity causes these eight abstentions. All eight passed the frozen whole-roster kill/assist collision veto. DBNO, revive, gadget causes and interaction eligibility are unavailable. A positive liveness value means no earlier decoded death, not independently verified ability to plant.

## Liveness-only plants

| Match/game/round | Candidate | Earlier score rejection |
| --- | --- | --- |
| 3563/6675/R02 | Surf | counter_collision |
| 4283/8686/R01 | Yoggah.Geekay | counter_collision |
| 6157/10430/R12 | Bokzera | counter_collision |
| 6158/10563/R06 | Zaara.TH | counter_collision |

## Successful liveness disables and complete nearby defender score sequences

| Match/game/round | Candidate | Each defender score delta @ relative byte offset |
| --- | --- | --- |
| 3563/6675/R10 | Spoit | Rexen: +100@+770; Spoit: +200@+903; Canadian: +100@+1022; Ambi: +100@+1155; Surf: +100@+1288 |
| 6157/10430/R12 | kds | soulz1: +2350@+283; kds: +2450@+211; cyber: +2350@+229; vitaking: +2350@+247; handyy: +2350@+265 |
| 6158/10563/R06 | SkyZs.VP | RORICK.VP: +100@+752; p4sh4.VP: +100@+837; dan-_-.VP: +100@+970; Nayqo.VP: +100@+1103; SkyZs.VP: +100@+1236, +100@+1368 |

These disables are selected entirely by sole-survivor evidence, not by their score batches. The same common-plus-extra score pattern also occurs in unresolved multi-survivor disables; 3563/6675 R02 remains the counterexample to score-only selection. A union would expand apparent coverage, but the current analysis does not justify one.
