# UAH rating comparison — exploratory model

Model: `grouped-operator-20260930T103355Z`. Trained only on professional events; UAH data was not used to fit or choose coefficients. Ratings below are experimental and do not change `collegiate_v1` or the public website.

| Player | Scope | Rounds | collegiate_v1 | Raw candidate | Difference |
| --- | --- | ---: | ---: | ---: | ---: |
| Tallman3.14 | Kafe Dostoyevsky | 14 | 0.361 | 0.760 | +0.400 |
| OhWowJay | Kafe Dostoyevsky | 14 | 1.051 | 1.043 | -0.007 |
| DinoFireKing | Kafe Dostoyevsky | 14 | 0.818 | 0.922 | +0.105 |
| Lgon | Kafe Dostoyevsky | 14 | 2.021 | 1.507 | -0.514 |
| AzoozNewzz | Kafe Dostoyevsky | 14 | 0.868 | 1.029 | +0.161 |
| Tallman3.14 | Border | 14 | 0.044 | 0.468 | +0.424 |
| Lgon | Border | 14 | 1.434 | 1.178 | -0.256 |
| DinoFireKing | Border | 14 | 1.051 | 0.843 | -0.208 |
| OhWowJay | Border | 14 | 1.602 | 1.214 | -0.388 |
| AzoozNewzz | Border | 14 | 0.526 | 0.678 | +0.151 |
| Tallman3.14 | Fortress | 10 | 0.362 | 0.720 | +0.359 |
| AzoozNewzz | Fortress | 10 | 1.045 | 1.212 | +0.167 |
| DinoFireKing | Fortress | 10 | 0.940 | 0.811 | -0.129 |
| Lgon | Fortress | 10 | 1.692 | 1.487 | -0.205 |
| OhWowJay | Fortress | 10 | 1.930 | 1.499 | -0.431 |
| **Lgon** | **Season** | **38** | **1.719** | **1.380** | **-0.338** |
| **OhWowJay** | **Season** | **38** | **1.486** | **1.226** | **-0.260** |
| **AzoozNewzz** | **Season** | **38** | **0.779** | **0.948** | **+0.169** |
| **Tallman3.14** | **Season** | **38** | **0.218** | **0.642** | **+0.424** |
| **DinoFireKing** | **Season** | **38** | **0.938** | **0.864** | **-0.074** |

## Component contributions

Each contribution is measured relative to the professional training-set mean. The model intercept is added to the sum.

Intercept: **0.959**

| Player | Scope | kpr | teamkills | multikill | opening | clutch | kost | survival | trade | objectives |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Tallman3.14 | Kafe Dostoyevsky | -0.050 | -0.000 | -0.018 | +0.023 | -0.008 | -0.019 | -0.078 | -0.035 | -0.014 |
| OhWowJay | Kafe Dostoyevsky | +0.060 | -0.000 | +0.021 | -0.023 | -0.008 | +0.018 | +0.024 | -0.008 | +0.001 |
| DinoFireKing | Kafe Dostoyevsky | -0.123 | -0.000 | -0.018 | +0.023 | -0.008 | +0.055 | +0.024 | +0.010 | +0.001 |
| Lgon | Kafe Dostoyevsky | +0.243 | -0.000 | +0.099 | +0.011 | +0.049 | +0.018 | +0.126 | +0.001 | +0.001 |
| AzoozNewzz | Kafe Dostoyevsky | +0.097 | -0.000 | +0.041 | +0.011 | -0.008 | -0.019 | -0.044 | -0.008 | +0.001 |
| Tallman3.14 | Border | -0.269 | -0.000 | -0.056 | -0.023 | -0.008 | -0.019 | -0.112 | +0.019 | -0.022 |
| Lgon | Border | +0.207 | -0.000 | +0.060 | +0.011 | -0.008 | +0.018 | -0.044 | -0.026 | +0.001 |
| DinoFireKing | Border | -0.086 | -0.000 | -0.018 | -0.012 | -0.008 | -0.019 | -0.010 | +0.036 | +0.001 |
| OhWowJay | Border | +0.207 | -0.000 | +0.099 | -0.023 | -0.008 | -0.019 | -0.010 | +0.010 | +0.001 |
| AzoozNewzz | Border | -0.160 | -0.000 | -0.018 | -0.023 | +0.049 | -0.056 | -0.112 | +0.036 | +0.001 |
| Tallman3.14 | Fortress | -0.138 | -0.000 | -0.029 | -0.000 | +0.072 | -0.108 | -0.051 | +0.013 | +0.001 |
| AzoozNewzz | Fortress | +0.119 | -0.000 | +0.025 | +0.016 | +0.072 | +0.047 | -0.003 | -0.024 | +0.001 |
| DinoFireKing | Fortress | -0.138 | -0.000 | -0.056 | -0.000 | -0.008 | -0.005 | +0.044 | +0.013 | +0.001 |
| Lgon | Fortress | +0.272 | -0.000 | +0.106 | +0.064 | -0.008 | +0.047 | +0.044 | +0.001 | +0.001 |
| OhWowJay | Fortress | +0.170 | -0.000 | +0.079 | +0.048 | +0.072 | +0.099 | +0.044 | +0.026 | +0.001 |
| Lgon | Season | +0.237 | -0.000 | +0.086 | +0.025 | +0.013 | +0.025 | +0.042 | -0.009 | +0.001 |
| OhWowJay | Season | +0.143 | -0.000 | +0.065 | -0.005 | +0.013 | +0.025 | +0.017 | +0.007 | +0.001 |
| AzoozNewzz | Season | +0.008 | -0.000 | +0.015 | -0.000 | +0.034 | -0.015 | -0.058 | +0.004 | +0.001 |
| Tallman3.14 | Season | -0.154 | -0.000 | -0.035 | -0.000 | +0.013 | -0.043 | -0.083 | -0.003 | -0.013 |
| DinoFireKing | Season | -0.113 | -0.000 | -0.028 | +0.004 | -0.008 | +0.012 | +0.017 | +0.020 | +0.001 |

The candidate is a research comparison only. Operator-adjusted candidates performed worse on the August validation event. The frozen raw model was subsequently evaluated once on September Stage 2 (16 clean rows; MAE 0.0632); that event was not used to fit or select the model.
