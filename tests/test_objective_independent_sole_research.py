"""Independent body evidence never guesses a missing score identity."""
from copy import deepcopy
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research'))
from objective_independent_sole_candidate import independent_sole

CASES = json.loads((Path(__file__).parent/'fixtures/objective-combined-cases.json').read_text())


def case():
    result = deepcopy(next(c for c in CASES if c['expected']=='Lollo.HERETICS'))
    result['row']['identity']['entity_names']={}
    return result


def run(c):
    return independent_sole(**{k:c[k] for k in ('row','deaths','timers','body','full_feedback','previous_state')})


def test_full_body_and_death_proof_does_not_need_a_guessed_score_identity():
    c = case()
    assert run(c)[:2]==('Lollo.HERETICS','sole_declared_body_without_score_binding')
    assert c['row']['identity']['entity_names']=={}


def test_body_only_dead_teammate_cannot_create_sole_actor():
    c = case()
    c['deaths']=[]
    assert run(c)[0] is None


def test_disconnect_and_unknown_death_still_block_independent_mode():
    c = case()
    c['deaths'][0]['offset']=0
    assert run(c)[:2]==(None,'unknown_death_offset')
    c = case()
    c['full_feedback'].append(dict(type=dict(name='PlayerLeave')))
    assert run(c)[:2]==(None,'player_leave_timing_unknown')


def test_unknown_or_down_state_never_excludes_a_living_teammate():
    c = case()
    victim = c['deaths'][0]['feedback'].get('target')
    c['deaths']=[d for d in c['deaths'] if d['feedback'].get('target')!=victim]
    if victim in c['body']:
        for field in c['body'][victim]:
            field['value']=3
    assert run(c)[0] is None


def test_frozen_disputed_and_later_kill_cases_remain_identical():
    for c in CASES:
        assert run(c)[:2]==(c['expected'],c['mode'])
