"""Public consumed controls and explicit uncertainty regressions; no live writes."""
from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research'))
from objective_combined_candidate import combine, declared_body_states

CASES = json.loads((Path(__file__).parent/'fixtures/objective-combined-cases.json').read_text())


def run(case):
    return combine(**{k:case[k] for k in ('row','deaths','timers','body','full_feedback','previous_state')})


def sole_case():
    return deepcopy(next(c for c in CASES if c['expected']=='Lollo.HERETICS'))


@pytest.mark.parametrize('case',CASES,ids=[c['case'] for c in CASES])
def test_actual_actor_controls_and_later_kill_boundaries(case):
    assert run(case)[:2]==(case['expected'],case['mode'])


def test_disconnect_without_timing_abstains_for_the_whole_round():
    case = sole_case()
    case['full_feedback'].append({'type':{'name':'PlayerLeave'},'username':'Lollo.HERETICS'})
    assert run(case)[:2]==(None,'player_leave_timing_unknown')


def test_unknown_death_never_becomes_a_dead_teammate():
    case = sole_case()
    case['deaths'][0]['offset']=0
    assert run(case)[:2]==(None,'unknown_death_offset')


def test_dead_body_without_feedback_cannot_exclude_a_teammate():
    case = sole_case()
    excluded = next(p for p in case['body'] if p.endswith('.HERETICS') and p!=case['expected'])
    case['deaths']=[d for d in case['deaths'] if d['feedback'].get('target')!=excluded]
    assert run(case)[0] is None


def test_unknown_or_missing_actor_body_abstains():
    case = sole_case()
    for field in case['body'][case['expected']]:
        if field['value']==0:
            field['value']=3
    assert run(case)[0] is None
    case['body'][case['expected']]=[]
    assert run(case)[:2]==(None,'incomplete_declared_body_identity')


def test_observed_low_health_state2_is_not_a_death_filter():
    case = sole_case()
    for field in case['body'][case['expected']]:
        if field['value']==0:
            field['value']=2
    assert run(case)[0]==case['expected']


def test_down_and_revive_during_interaction_stays_unresolved():
    case = sole_case()
    span = run(case)[2]['interaction_span']
    fields = case['body'][case['expected']]
    fields += [dict(offset=span['first_offset']+1,value=3),dict(offset=span['first_offset']+2,value=2)]
    fields.sort(key=lambda p:p['offset'])
    assert run(case)[0] is None


def test_excluded_teammate_revive_conflicts_with_sole_evidence():
    case = sole_case()
    span = run(case)[2]['interaction_span']
    excluded = next(p for p in case['body'] if p.endswith('.HERETICS') and p!=case['expected'])
    case['body'][excluded].append(dict(offset=span['first_offset']+1,value=0))
    case['body'][excluded].sort(key=lambda p:p['offset'])
    assert run(case)[0] is None


def test_missing_roster_identity_cannot_create_sole_survivor():
    case = sole_case()
    case['row']['header']['players'][0]['id']=None
    assert run(case)[:2]==(None,'incomplete_player_roster')


def test_incomplete_timer_run_does_not_prove_sole_throughout():
    case = sole_case()
    case['timers']=[]
    assert run(case)[:2]==(None,'incomplete_interaction_span')


def test_body_guard_cannot_credit_a_dead_score_source():
    case = deepcopy(next(c for c in CASES if c['expected']=='Hotancold.100T'))
    for field in case['body'][case['expected']]:
        field['value']=4
    assert run(case)[0] is None


def test_score_and_sole_disagreement_does_not_silently_fall_back():
    case = deepcopy(next(c for c in CASES if c['expected']=='Surf'))
    span = run(case)[2]['interaction_span']
    case['deaths']=[d for d in case['deaths'] if 0<d['offset']<span['first_offset']]
    other = next(p for p in case['body'] if p!=case['expected'] and p in {'Canadian','Spoit','Ambi','Rexen'})
    entity = next(int(k) for k,v in case['row']['identity']['entity_names'].items() if v==[other])
    case['row']['all_changes']=[dict(counter='score',delta=100,offset=case['row']['center']+1,entity=entity)]
    assert run(case)[:2]==(None,'evidence_conflict')


def test_unique_relative_wave_cannot_override_sole_actor():
    case = sole_case()
    wave = run(case)[2]['relative_wave']
    actor_events = [e for e in wave['changes'] if e['entity'] in
                    {int(k) for k,v in case['row']['identity']['entity_names'].items() if v==[case['expected']]}]
    last = max(actor_events,key=lambda e:e['offset'])
    other = next(int(k) for k,v in case['row']['identity']['entity_names'].items()
                 if len(v)==1 and v[0].endswith('.HERETICS') and v[0]!=case['expected'])
    next(e for e in case['row']['all_changes'] if e['offset']==last['offset'])['entity']=other
    assert run(case)[:2]==(None,'relative_wave_conflicts_with_sole')


def test_remote_kill_does_not_eliminate_an_independently_sole_planter():
    # Synthetic remote/gadget scoring collision. This is not a claim that one
    # of the inspected replay kills was actually a claymore kill.
    case = deepcopy(next(c for c in CASES if c['expected']=='Surf'))
    span = run(case)[2]['interaction_span']
    case['deaths'].append(dict(offset=span['first_offset']+1,
                              feedback=dict(type=dict(name='Kill'),username='Surf',target='J9O')))
    entity = next(int(k) for k,v in case['row']['identity']['entity_names'].items() if v==['Surf'])
    case['row']['all_changes'].append(dict(counter='kills',delta=1,offset=span['first_offset']+1,entity=entity))
    assert run(case)[:2]==('Surf','sole_proven_survivor_throughout_interaction')


def body_raw():
    return dict(header=dict(players=[dict(id=1,username='A')]),
                declarations=[dict(owner=10,component=20,slot_hash='4154dcc4',class_hash='0c98c63f')],
                properties=[dict(kind='numeric_uid',entity=10,value=1),
                            dict(kind='component_state',entity=20,hash='e788f6a5',size=4,value=0,offset=42)])


def test_component_join_requires_numeric_identity_and_exact_declared_class():
    raw = body_raw()
    assert declared_body_states(raw)['A'][0]['value']==0
    raw['declarations'][0]['class_hash']='unknown'
    assert declared_body_states(raw)=={}


def test_reused_uid_or_component_never_uses_nearest_player_identity():
    raw = body_raw()
    raw['properties'].append(dict(kind='numeric_uid',entity=10,value=999))
    assert declared_body_states(raw)=={}
    raw = body_raw()
    raw['declarations'].append(dict(owner=99,component=20,slot_hash='4154dcc4',class_hash='0c98c63f'))
    assert declared_body_states(raw)=={}
