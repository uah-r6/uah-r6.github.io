import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'research'))
from objective_oce_body_clock_scope import first_epoch_window


def test_serialized_later_phase_does_not_invalidate_earlier_complete_second():
    ticks = [dict(offset=15, value=80), dict(offset=20, value=79),
             dict(offset=30, value=0), dict(offset=40, value=44), dict(offset=50, value=43)]
    window, scope = first_epoch_window(ticks, 10, 60, 80)
    assert window == (15, 19)
    assert scope['first_countdown_end'] == 40
    assert scope['action_marker_changed'] is False
    assert scope['round_omitted'] is False


def test_only_postplant_value_is_unavailable_in_first_epoch():
    ticks = [dict(offset=15, value=80), dict(offset=20, value=79),
             dict(offset=30, value=0), dict(offset=40, value=44), dict(offset=50, value=43)]
    window, scope = first_epoch_window(ticks, 10, 60, 44)
    assert window is None
    assert scope['reason'] == 'displayed_clock_tick_missing'


def test_repeated_displayed_value_selects_only_first_epoch():
    ticks = [dict(offset=15, value=44), dict(offset=20, value=43),
             dict(offset=30, value=0), dict(offset=40, value=44), dict(offset=50, value=43)]
    assert first_epoch_window(ticks, 10, 60, 44)[0] == (15, 19)


def test_marker_absence_and_missing_next_tick_still_abstain():
    ticks = [dict(offset=15, value=80), dict(offset=20, value=78)]
    assert first_epoch_window(ticks, 0, 30, 80)[0] is None
    assert first_epoch_window(ticks, 10, 30, 80)[0] is None


def test_no_reset_preserves_the_explicit_anchor_bound():
    ticks = [dict(offset=15, value=80), dict(offset=20, value=79)]
    window, scope = first_epoch_window(ticks, 10, 30, 80)
    assert window == (15, 19)
    assert scope['first_countdown_end'] == 30
    assert scope['observed_reset'] is None
