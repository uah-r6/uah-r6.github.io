"""Clock scope must abstain from elapsed trade timing across reset/overtime."""
import math
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'research'))
from credited_clock_epoch_audit import analyze


TEAMS = {'a': 0, 'aa': 0, 'b': 1, 'bb': 1}


def event(offset, remaining, killer, victim):
    return dict(offset=offset, feedback=dict(type=dict(name='Kill', id=0),
                username=killer, target=victim, timeInSeconds=remaining))


def test_postplant_countdown_is_not_earlier_elimination_or_elapsed_trade_time():
    # The independently filmed Bank case has action0:06 then postplant0:42.
    result = analyze([event(10, 6, 'a', 'b'), event(100, 42, 'bb', 'a')], TEAMS, [50])
    assert result['full_order_changed']
    assert result['reversals'][0]['cross_plant_state']
    trade = result['raw_finisher_refrag_candidates'][0]
    assert trade['elapsed_time_status'] == 'unresolved_phase_transition'
    assert trade['remaining_seconds_difference'] == -36
    assert trade['legacy_8s_numeric_predicate'] is False


def test_zero_clock_planting_overtime_never_claims_zero_elapsed_time():
    result = analyze([event(10, 0, 'a', 'b'), event(20, 0, 'bb', 'a')], TEAMS, [50])
    assert not result['full_order_changed']
    trade = result['raw_finisher_refrag_candidates'][0]
    assert trade['legacy_8s_numeric_predicate'] is True  # Numeric legacy rule, not trusted timing.
    assert trade['elapsed_time_status'] == 'unresolved_zero_remaining_or_overtime'


@pytest.mark.parametrize('anchors', [[], [15, 50]])
def test_missing_or_ambiguous_plant_epoch_cannot_claim_comparable_trade_clocks(anchors):
    result = analyze([event(10, 30, 'a', 'b'), event(20, 25, 'bb', 'a')], TEAMS, anchors)
    assert result['raw_finisher_refrag_candidates'][0]['elapsed_time_status'] == 'unresolved_missing_or_ambiguous_plant_epoch'


@pytest.mark.parametrize('anchors', [[0], [-1], [True], [50, 50]])
def test_invalid_physical_plant_sources_refuse(anchors):
    with pytest.raises(ValueError, match='Plant anchors'):
        analyze([], TEAMS, anchors)


@pytest.mark.parametrize('events', [
    [event(0, 30, 'a', 'b')],
    [event(10, 30, 'a', 'b'), event(10, 25, 'bb', 'a')],
    [event(10, math.nan, 'a', 'b')],
])
def test_unknown_duplicate_and_invalid_feedback_sources_refuse(events):
    with pytest.raises(ValueError):
        analyze(events, TEAMS, [50])
