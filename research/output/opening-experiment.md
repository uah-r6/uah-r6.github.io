# Separate opening coefficients - 2026-10-01

Plan committed at `430cd1f`, implementation at `c1a967e`; recorded experiment `opening-20261001T195459Z`. Same dataset, 299 clean pre-August observations, seven event folds, 32 August development observations. Eight-second trades, original multikills, raw standardized ridge alpha=1, objectives excluded. Both September events excluded; final NA60 sealed.

| Model | Pooled MAE | August MAE |
| --- | ---: | ---: |
| Baseline opening differential (reused) | 0.036467 | 0.034530 |
| Separate opening kills / deaths | 0.036620 | 0.034418 |

Full-fit raw opening slopes are +0.164821 and -0.127396, versus the former constrained +/-0.146293. Fold ranges are +0.145309 to +0.190148 and -0.160221 to -0.109938. This asymmetry does not produce a robust error improvement. Retain the simpler differential for subsequent experiments. Do not stack this change with the multikill buckets based on the tiny August differences.

Most shared coefficient shifts are below 0.004; clutch changes by 0.01130 and teamkills by 0.01806. Only nine training teamkills exist (NA Stage1 five, Major two, APAC Stage1 one, EMEA Stage1 one). The teamkill fold slope ranges from -0.2736 to +0.0862. A positive fold estimate is a sparse-data warning, not evidence that teamkills should be rewarded. Twenty-nine clutches comprise twenty 1v1, five 1v2, three 1v3 and one 1v4; no 1v5. Separate five-size clutch coefficients would be poorly supported.

[Development residuals](development-residuals.md) use saved models only. Public objective-credit groups are validation diagnostics, never feature inputs or actor labels for replay extraction. August baseline objective-positive rows (11) have bias -0.0382 versus +0.0034 for 21 objective-negative rows. The separate-opening event folds show -0.0393 on 58 objective-positive rows versus +0.0113 on 241 others. This is consistent with missing objective information but is not a causal estimate. Do not impute credit or patch the rating from public logs. Short maps and clutch-positive rows also deserve attention; cells overlap and observations within maps are correlated.

NEXT ACTION: audit the current stored-data trade definition and preregister a controlled comparison of 5/6/7/8/10-second windows with identical actor/eligibility rules and fixed event splits. Recompute only research metrics from cached normalized rounds; no replay parsing, live database changes or final-target access. Preserve the current baseline until a robust development gain is demonstrated. Candidate freeze and final evaluation remain premature while trade semantics and residual limitations remain unresolved.
