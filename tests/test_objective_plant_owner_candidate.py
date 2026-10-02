"""Structural plant selector controls; no target-guided or score actor logic."""
import copy
from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research'))
from objective_plant_owner_candidate import candidate


def evidence():
    header=dict(codeVersion=9883691,gamemode=dict(name='Bomb'),
        teams=[dict(role='Attack'),dict(role='Defense')],
        players=[dict(username=f'p{i}',id=i+1,teamIndex=0 if i<5 else 1) for i in range(10)],
        objectiveOccurrences=[dict(kind='plant',source='defuser_state_v1',plantStateOffset=100)])
    binding=dict(owner=1000,player='p0',slot='27c08dca',class_hash='b2216bf3')
    run=dict(state=0,start_record=20,end_record=35,end_offset=35,end_reason='explicit_state_2',
        first_timer=7,last_timer=.01,monotonic_timer=True,samples=[dict(offset=23),dict(offset=36)],
        binding=binding,records=[dict(fields=[dict(offset=36,size=4)])])
    slots={(1000,'27c08dca'):[dict(offset=1,component=2000,class_hash='b2216bf3')],
           (1000,'4154dcc4'):[dict(offset=1,component=3000,class_hash='0c98c63f')]}
    return dict(header=header,observed=dict(episodes=[run],orphan_records=[]),owners={1000:'p0'},slots=slots,
        properties=[dict(entity=3000,hash='e788f6a5',size=4,offset=5,value=0)],deaths=[],full_feedback=[])


def test_unique_verified_plant_does_not_require_bonus_score_or_team_win():
    name,reason,context=candidate(**evidence())
    assert name=='p0' and reason=='direct_plant_completer_with_occurrence_and_body'
    assert context['numeric_uid']==1 and context['end']==45


def test_different_completer_after_two_canceled_starters():
    data=evidence()
    for start,last in ((1,2.881),(8,6.694)):
        previous=copy.deepcopy(data['observed']['episodes'][0])
        previous.update(start_record=start,last_timer=last,binding=previous['binding']|dict(player='starter',owner=1010),
                        records=[dict(fields=[dict(offset=start+2,size=1)])])
        data['observed']['episodes'].insert(0,previous)
    assert candidate(**data)[0]=='p0'


@pytest.mark.parametrize('change,reason',[
    ('occurrence','no_unique_verified_plant_occurrence'),
    ('duplicate_anchor','no_unique_verified_plant_occurrence'),
    ('partial','missing_or_competing_complete_plant_runs'),
    ('no_terminal','missing_or_competing_complete_plant_runs'),
    ('late_terminal','missing_or_competing_complete_plant_runs'),
    ('competing','missing_or_competing_complete_plant_runs'),
    ('restart','later_preplant_attempt'),('overlap','overlapping_plant_attempts'),
    ('orphan','unbound_preplant_timer_evidence'),('defender','timer_owner_identity_or_role_conflict'),
    ('dead','timer_owner_dead_by_terminal'),('zero_offset','unknown_death_offset'),
    ('all_opponents_dead','all_opponents_dead_by_terminal'),
    ('body_unknown','timer_owner_body_unresolved'),('body_dbno','timer_owner_body_unresolved'),
    ('shared_body','timer_owner_body_unresolved'),('leave','player_leave_timing_unknown'),
    ('unknown_class','unsupported_timer_component_route')])
def test_canceled_ambiguous_ineligible_plant_stays_unresolved(change,reason):
    data=evidence();run=data['observed']['episodes'][0]
    if change=='occurrence': data['header']['objectiveOccurrences']=[]
    if change=='duplicate_anchor': data['header']['objectiveOccurrences']*=2
    if change=='partial': run['last_timer']=3
    if change=='no_terminal': run['end_reason']='round_ended_without_explicit_terminal'
    if change=='late_terminal': run['records'][0]['fields'][0]['offset']=101
    if change=='competing': data['observed']['episodes'].append(copy.deepcopy(run))
    if change in ('restart','overlap'):
        other=copy.deepcopy(run)
        other.update(start_record=60 if change=='restart' else 15,last_timer=2,
                     records=[dict(fields=[dict(offset=65 if change=='restart' else 21,size=4)])])
        data['observed']['episodes'].append(other)
    if change=='orphan': data['observed']['orphan_records']=[dict(record_start=25)]
    if change=='defender':
        data['header']['teams'].reverse()
    if change in ('dead','zero_offset'):
        data['deaths']=[dict(offset=30 if change=='dead' else 0,feedback=dict(type=dict(name='Death'),username='p0'))]
    if change=='all_opponents_dead':
        data['deaths']=[dict(offset=10+i,feedback=dict(type=dict(name='Kill'),username='p0',target=f'p{i}')) for i in range(5,10)]
    if change in ('body_unknown','body_dbno'): data['properties'][0]['value']=99 if change=='body_unknown' else 3
    if change=='shared_body': data['slots'][9999,'other']=[dict(offset=30,component=3000,class_hash='anything')]
    if change=='leave': data['full_feedback']=[dict(type=dict(name='PlayerLeave'))]
    if change=='unknown_class': run['binding']['class_hash']='anything'
    assert candidate(**data)[:2]==(None,reason)


def test_exact_consumed_build_variant_and_no_unknown_class_fallback():
    data=evidence()
    data['header']['codeVersion']=9734089
    data['observed']['episodes'][0]['binding']['class_hash']='a859ffff'
    assert candidate(**data)[0]=='p0'
    data['header']['codeVersion']=9883691
    assert candidate(**data)[0] is None


def test_near_zero_state2_is_not_a_plant_without_global_completion():
    data=evidence()
    data['observed']['episodes'][0]['last_timer']=0
    data['header']['objectiveOccurrences']=[]
    assert candidate(**data)[0] is None
