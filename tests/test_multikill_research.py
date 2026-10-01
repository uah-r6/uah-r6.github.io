"""Research feature semantics and final-event isolation."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'research'))
from multikill_experiment import features, fit, predict


def sample():
    base = dict(teamkills=0, opening_kills=0, opening_deaths=0, clutches=0,
                kost_rounds=0, survived=0, deaths_traded=0, kills_traded=0,
                plants=99, disables=99)
    return {'rounds': [dict(base, kills=k) for k in range(6)]}


def test_multikill_definitions_exclude_objectives():
    row = sample()
    rate = features(row, 'multi_round_rate')
    buckets = features(row, 'size_buckets')
    assert rate['multi_round_rate'] == 4 / 6
    assert [buckets[f'kills_{k}'] for k in (2, 3, 4, 5)] == [1/6]*4
    assert 'objectives' not in rate and 'objectives' not in buckets
    assert rate['kpr'] == 2.5


def test_final_targets_cannot_enter_fit_or_prediction():
    # No rating or round fields: guard must reject before reading either.
    reserved = {'event': 'North America League Stage 2 2026', 'reserved_for_final_test': True}
    with pytest.raises(ValueError):
        fit([reserved], 'size_buckets')
    with pytest.raises(ValueError):
        predict({}, reserved)
    historical = {'event': 'Europe MENA League Stage 2 2026', 'reserved_for_final_test': False}
    with pytest.raises(ValueError):
        predict({}, historical)


def test_opening_terms_keep_kills_and_deaths_separate():
    from opening_experiment import features as opening_features
    row = sample()
    row['rounds'][0]['opening_kills'] = 1
    row['rounds'][1]['opening_deaths'] = 1
    values = opening_features(row, 'separate_openings')
    assert values['opening_kills'] == values['opening_deaths'] == 1/6
    assert 'opening' not in values and 'objectives' not in values
    assert values['multikill'] == 10/6
