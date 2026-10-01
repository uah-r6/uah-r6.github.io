# Pre-freeze Rating review - 2026-10-01

Candidate selection uses the same quality-gated 299 pre-August player-map rows and seven event-held-out folds, followed by 32 August EWC development rows (four maps). All experiments use raw standardized ridge with alpha 1. Objectives are excluded because reliable player attribution is unavailable. No reserved NA Stage2 target has been evaluated for this review. The dataset SHA-256 is `2454eb35ebe06df8d91f950b17cab8cea0a26384d9c40cbdd786f7e4f11b04de`.

| Candidate change from current eight-family raw baseline | Coefficients | Pooled fold MAE | August MAE | Conclusion |
| --- | ---: | ---: | ---: | --- |
| Current baseline | 8 | **0.03647** | **0.03453** | Retain |
| 2+ multikill round rate | 8 | 0.03944 | 0.03682 | Worsens both |
| Four multikill size buckets | 11 | 0.03651 | 0.03412 | Tiny, inconsistent gain; no training 5K |
| Separate opening kill/death | 9 | 0.03662 | 0.03442 | Essentially tied, more complex |
| 5/6/7/10-second trades | 8 | 0.03768 / 0.03731 / 0.03731 / 0.03616 | 0.03638 / 0.03514 / 0.03497 / 0.03597 | Eight-second control most consistent |
| Death-traded only | 8 | 0.03917 | 0.03625 | Loses information |
| Kill-traded only | 8 | 0.03770 | 0.04004 | Loses information |
| KOST without survival path | 8 | 0.04654 | 0.04055 | Strongly worse |
| Remove separate survival | 7 | 0.06548 | 0.06811 | Strongly worse |
| Linear clutch size weight | 8 | 0.03491 | 0.03525 | Fold and August disagree; sparse large clutches |

The baseline's seven fold MAEs, in plan order, are **0.03300, 0.03311, 0.04203, 0.04569, 0.03034, 0.03828, 0.02961**. Pooled CV RMSE is 0.04898. August RMSE is 0.04626, median absolute error 0.02248, max error 0.1338; 21.9/46.9/59.4/71.9/96.9% are within .01/.02/.03/.05/.10 respectively. Pooled baseline median absolute error was not stored in the historical CV record. The full-trained baseline has eight nonconstant coefficients; its raw-unit slopes are KPR +0.56175, teamkills -0.20333, multikills +0.22714, opening differential +0.14629, clutch +0.66888, KOST +0.50316, survival +0.49005, trade differential +0.14180. Raw/intercept and standardized coefficients are stored in the baseline experiment record.

The last clean-data expansion changed each varying raw-unit slope by at most about 0.00694, but the prior expansion changed clutch by about 0.0612. Nine teamkills and 29 clutch rounds in current training make those terms weakly estimated; one fold's teamkill coefficient can turn positive. The simpler raw model already beat operator-normalized variants on every earlier-event fold in the prior comparison, and no new operator-normalization hypothesis emerged. Operator sample counts remain sparse. Do not force normalization.

**Known limitations:** 153 of 560 observed player-map rows fail quality gates; 407 pass. The selected 299 train and 32 August rows pass exact K/D and round-count checks and alias requirements. Some replay/public kill attribution mismatches remain outside the clean set. Player objective actions remain uncredited in the clean training data because actor attribution is unresolved. Publicly objective-credited rows are underpredicted by roughly 0.038 on August. Public credits are analysis labels only, never predictors. The 32 August observations represent four maps and are correlated within maps. No source provides exact SiegeGG feature definitions or coefficients; this model is an independent approximation.

**Selection:** freeze the existing eight-family raw baseline for one final NA Stage2 evaluation, with the limitations above. No feature retuning after that test. Compare the frozen model with `collegiate_v1` on identical reserved clean rows, then prepare a deployment review without changing the live application. Freeze record must include the saved exact model, dataset/source hashes, splits, quality gates, parser hash, and repository commit.
