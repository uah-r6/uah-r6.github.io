"""Research-only liveness safeguards; no replay or public target dependency."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'research'))
from objective_actor_liveness import interaction_span, player_ledger, sole_interval_candidate


def players(a, b):
    return [{'player': 'A', 'alive_at_completion': a},
            {'player': 'B', 'alive_at_completion': b}]


@pytest.mark.parametrize('start,end,expected', [
    (players(True, False), players(True, False), 'A'),
    (players(True, True), players(True, False), None),
    (players(True, False), players(False, False), None),
    (players(True, None), players(True, False), None),
    (players(True, False), players(True, None), None),
    (players(True, False), [], None),
])
def test_sole_candidate_requires_complete_stable_liveness(start, end, expected):
    assert sole_interval_candidate(start, end) == expected


def test_timer_fragment_or_previous_objective_cannot_establish_interaction_start():
    timers = [{'offset': 100, 'value': '7'}, {'offset': 200, 'value': '0.025'}]
    assert interaction_span(timers, 300, 0)['first_offset'] == 100
    assert interaction_span(timers, 300, 201) is None
    assert interaction_span(timers[1:], 300, 0) is None
    assert interaction_span(timers, 150, 0) is None


def test_death_offsets_and_score_order_are_preserved_without_guessing_credit():
    header = {'teams': [{'role': 'Attack'}],
              'players': [{'username': n, 'id': i, 'teamIndex': 0} for i, n in enumerate(('A', 'B', 'C'), 1)]}
    events = [
        {'offset': 100, 'feedback': {'type': {'name': 'Kill'}, 'username': 'Enemy', 'target': 'A'}},
        {'offset': 0, 'feedback': {'type': {'name': 'Death'}, 'username': 'B'}},
        {'offset': 300, 'feedback': {'type': {'name': 'Kill'}, 'username': 'Enemy', 'target': 'C'}},
    ]
    scores = [dict(entity=5, counter='score', offset=150, previous=20, value=120, delta=100),
              dict(entity=5, counter='score', offset=250, previous=120, value=320, delta=200)]
    ledger = player_ledger(header, events, scores, {'entity_names': {'5': ['A']}}, 200, 'Attack')
    assert [p['alive_at_completion'] for p in ledger] == [False, None, True]
    assert ledger[0]['score_before_completion'] == 120
    assert ledger[0]['score_final'] == 320
    assert [e['distance_from_completion'] for e in ledger[0]['score_updates']] == [-50, 50]
    assert ledger[1]['score_before_completion'] is None
    assert all(p['actor'] is None for p in ledger)
