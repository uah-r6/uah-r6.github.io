"""Exact independently passing native_triangular_size model, without fitting.

Source: research/v3-native-order-candidate.json, frozen before APAC North
Stage1 targets at e05dfc4. Raw replay statistics alone are NOT eligible inputs.
"""


class SiegeStyleV3Rating:
    version = 'siege_style_v3'
    intercept = 0.9873886639676113
    terms = (
        ('kpr', 0.18682577130471265, 0.6981624369782264, 0.3170056471951219),
        ('teamkills', -0.0025808916598358198, 0.0021325166062008166, 0.014970420657287641),
        ('multikill', 0.04154007508710459, 0.2260358062989642, 0.18860594663007044),
        ('opening', 0.02237169359759703, 4.2139031805104626e-20, 0.146080067002339),
        ('clutch', 0.026320552236229054, 0.02887273545168282, 0.10731630241942614),
        ('kost', 0.08027335174606536, 0.6259729670913882, 0.17481868393607577),
        ('survival', 0.08815984639807335, 0.29975444876760665, 0.18059046208567328),
        ('trade', 0.013342516159598559, 0.0001445922498554076, 0.1388022244044543),
        ('objectives', 0.023869776691413717, 0.02646333929228666, 0.05302031211621311),
    )

    @classmethod
    def calculate(cls, s):
        rounds = s['rounds']
        if not rounds:
            return 0.0
        if s['clutches'] != sum(s[f'clutch_1v{x}'] for x in range(1, 6)):
            raise ValueError('Clutch total/breakdown mismatch.')
        values = (s['kills'], s['teamkills'], s['multikill_extra'],
                  s['opening_kills'] - s['opening_deaths'],
                  sum(x * (x + 1) / 2 * s[f'clutch_1v{x}'] for x in range(1, 6)),
                  s['kost_rounds'], s['survived'], s['deaths_traded'] - s['kills_traded'],
                  s['plants'] + s['disables'])
        return cls.intercept + sum(weight * (value / rounds - mean) / scale
            for value, (_, weight, mean, scale) in zip(values, cls.terms))
