# Separate v3 development: verified objectives with definition-correct KOST

Experiment `v3-corrected-kost-20261002T221833Z`. Train284, EWC development22; fixed ridge alpha1, no search. A uses exact frozen v2 weights, B fits the same nine-family raw design. Both arms use fully objective-corrected KOST. No consumed final rows/errors used. The first v3 contract/result and failed APAC gate remain immutable.

| Split / model | N | MAE | RMSE | Median AE | Max AE | within .01 | .02 | .03 | .05 | .10 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| train/exact_v2_corrected_inputs | 284 | 0.03295 | 0.04400 | 0.02516 | 0.18155 | 22.9% | 39.8% | 58.1% | 78.2% | 96.8% |
| train/v3_corrected_inputs | 284 | 0.02943 | 0.03977 | 0.02158 | 0.15861 | 26.8% | 45.1% | 63.4% | 80.6% | 97.5% |
| development/exact_v2_corrected_inputs | 22 | 0.02606 | 0.03376 | 0.01993 | 0.07020 | 31.8% | 50.0% | 68.2% | 81.8% | 100.0% |
| development/v3_corrected_inputs | 22 | 0.02133 | 0.02510 | 0.01981 | 0.04868 | 22.7% | 50.0% | 77.3% | 100.0% | 100.0% |

## All coefficient drift

| Feature | v2 raw | v3 raw | Change |
| --- | ---: | ---: | ---: |
| kpr | 0.56174501 | 0.57822878 | +0.01648377 |
| teamkills | -0.20333046 | -0.22719032 | -0.02385986 |
| multikill | 0.22713744 | 0.21966899 | -0.00746844 |
| opening | 0.14629314 | 0.14741548 | +0.00112234 |
| clutch | 0.66888255 | 0.61971629 | -0.04916626 |
| kost | 0.50315735 | 0.48273167 | -0.02042568 |
| survival | 0.49004505 | 0.46594261 | -0.02410244 |
| trade | 0.14180459 | 0.13007287 | -0.01173171 |
| objectives | 0.00000000 | 0.40723158 | +0.40723158 |

## Every KOST input correction

| Split / player / match / game | Original | Corrected | Rounds |
| --- | ---: | ---: | ---: |
| train/Kyno.DZ/4149/7418 | 8 | 9 | 12 |
| train/live.LOUD/4112/8360 | 7 | 8 | 12 |
| train/Nayqo.VP/4283/8686 | 9 | 10 | 15 |
| train/kyno/3563/6675 | 6 | 7 | 11 |
| train/kyno/3554/6679 | 3 | 4 | 8 |
| train/Pikanzu.Daystar/3880/7625 | 4 | 5 | 10 |
| train/BGMan.ORC/3585/6722 | 7 | 8 | 12 |
| development/AsK/6156/10425 | 11 | 12 | 15 |
| development/VolpsZ/6157/10430 | 7 | 8 | 12 |

## Every objective-heavy residual change

| Split / player / match / game | Objectives | v2 | v3 | Target | AE change |
| --- | ---: | ---: | ---: | ---: | ---: |
| train/Hotancold.100T/4150/7419 | 2 | 1.14354 | 1.20350 | 1.19 | -0.03296 |
| train/Spiker.WC/4137/8073 | 2 | 1.29507 | 1.33848 | 1.33 | -0.02645 |
| train/live.LOUD/4112/8360 | 3 | 1.14549 | 1.24056 | 1.23 | -0.07395 |
| train/Canadian/3563/6673 | 2 | 0.78922 | 0.85730 | 0.94 | -0.06808 |
| train/kyno/3554/6679 | 2 | 0.75086 | 0.83483 | 0.84 | -0.08398 |
| train/Pikanzu.Daystar/3880/7625 | 2 | 0.57734 | 0.65221 | 0.59 | +0.04954 |
| train/SpeakEasy.WBG/3880/7625 | 2 | 1.13851 | 1.20273 | 1.19 | -0.03876 |
| development/kyno/6156/10425 | 3 | 0.73980 | 0.81063 | 0.81 | -0.06957 |
| development/vitaking/6157/10430 | 2 | 1.22255 | 1.27314 | 1.24 | +0.01569 |

Same small objective-complete subset as the first study; distinct input contract. Cannot compare different-input MAE changes as solely coefficient improvement. Consumed final errors never enter this fit or evaluation.

A genuinely new event and another prospective freeze are required before any future final. No automatic deployment; live v2/SQLite/archives/public JSON unchanged. Fit deduplicates the deliberate experiment; do not repeatedly refit.
