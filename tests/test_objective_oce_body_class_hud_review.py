import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'research'))
from objective_oce_body_class_hud_review import action_clock_window, classify_observation


def test_clock_bracket_ends_before_the_next_second():
    ticks = [dict(offset=5, value=44), dict(offset=15, value=79),
             dict(offset=17, value=79), dict(offset=30, value=78)]
    assert action_clock_window(ticks, 10, 40, 79)[0] == (15, 29)


def test_reset_cannot_select_a_postplant_second_as_action():
    ticks = [dict(offset=15, value=44), dict(offset=20, value=43),
             dict(offset=30, value=0), dict(offset=40, value=44), dict(offset=50, value=43)]
    assert action_clock_window(ticks, 10, 60, 44)[1] == 'clock_reset_inside_action_bounds'


def test_skipped_next_clock_tick_abstains():
    ticks = [dict(offset=15, value=79), dict(offset=30, value=77)]
    assert action_clock_window(ticks, 10, 40, 79)[1] == 'adjacent_next_clock_tick_missing'


def test_no_marker_or_missing_displayed_tick_abstains():
    ticks = [dict(offset=15, value=79), dict(offset=30, value=78)]
    assert action_clock_window(ticks, 0, 40, 79)[0] is None
    assert action_clock_window(ticks, 10, 40, 80)[0] is None


def test_transition_inside_a_displayed_second_remains_unresolved():
    interval = dict(route_status='unique_unchanged_typed_route', class_hash='b529300b',
                    prior_state_present=True, states=[dict(value=3), dict(value=2)])
    assert classify_observation(interval)[1] == 'raw_transition_within_displayed_second'


def test_raw_stability_does_not_bypass_temporal_route_or_class_uncertainty():
    interval = dict(route_status='unique_unchanged_typed_route', class_hash='b529300b',
                    prior_state_present=True, states=[dict(value=3)])
    assert classify_observation(interval) == (3, 'stable_raw_value_over_displayed_second')
    assert classify_observation(interval | dict(route_status='missing_shared_or_replaced_route'))[0] is None
    assert classify_observation(interval | dict(class_hash='unknown'))[0] is None
    assert classify_observation(interval | dict(prior_state_present=False))[0] is None
