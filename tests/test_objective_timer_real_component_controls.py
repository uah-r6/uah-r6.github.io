"""Replay-derived research state controls, not accepted actor predictions."""
from collections import defaultdict
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research'))
from objective_timer_component_episodes import component_episodes
from objective_timer_negative_controls import completion_like


def test_consumed_structural_controls_keep_cancellations_separate_and_actors_null():
    fixture = json.loads((Path(__file__).parent/'fixtures/objective-timer-components.json').read_text(encoding='utf-8'))
    by_key = {}
    for case in fixture['cases']:
        slots = defaultdict(list)
        for d in case['declarations']:
            slots[d['owner'],d['slot_hash']].append(d)
        observed = component_episodes({int(k):v for k,v in case['owners'].items()},slots,case['fields'])
        expected = [dict(player=e['binding']['player'],state=e['state'],first_timer=e['first_timer'],
                         last_timer=e['last_timer'],end_reason=e['end_reason'],actor=e['actor']) for e in observed['episodes']]
        assert expected == case['expected']
        assert not observed['orphan_records']
        assert all(e['actor'] is None for e in observed['episodes'])
        by_key[case['match_id'],case['round']] = observed
    mixed = by_key[4150,11]['episodes']
    assert [e['binding']['player'] for e in mixed] == ['Kason.100T','Kason.100T','Hotancold.100T']
    assert [e['last_timer'] for e in mixed] == [2.881,6.694,.015]
    # Mandatory controls are observations only, never confident Aiden/njr.
    assert all(e['actor'] is None for e in by_key[4139,7]['episodes'])
    assert all(e['actor'] is None for e in by_key[3563,2]['episodes'])


def test_real_negative_controls_disprove_near_zero_plus_state_2_as_completion():
    fixture = json.loads((Path(__file__).parent/'fixtures/objective-timer-components.json').read_text(encoding='utf-8'))
    for key in ((4141,14),(4138,9)):
        case = next(c for c in fixture['cases'] if (c['match_id'],c['round']) == key)
        slots = defaultdict(list)
        for d in case['declarations']:
            slots[d['owner'],d['slot_hash']].append(d)
        observed = component_episodes({int(k):v for k,v in case['owners'].items()},slots,case['fields'])
        assert sum(completion_like(e) for e in observed['episodes']) == 1
        assert all(e['actor'] is None for e in observed['episodes'])
