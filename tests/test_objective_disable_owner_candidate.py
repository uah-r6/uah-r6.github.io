"""Disable-only hypothesis: occurrence, ownership and eligibility all required."""
import copy
from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research'))
from objective_disable_owner_candidate import candidate, active_body


def evidence(clear=False):
    header=dict(gamemode=dict(name='Bomb'),teams=[dict(role='Defense',score=1,startingScore=0),
               dict(role='Attack',score=0,startingScore=0)],
               players=[dict(username=f'p{i}',id=100+i,teamIndex=0 if i<5 else 1) for i in range(10)],
               objectiveOccurrences=[dict(kind='plant',source='defuser_state_v1',plantStateOffset=10),
               dict(kind='disable',source='defuser_state_and_defense_win_v1',plantStateOffset=10)])
    binding=dict(owner=1000,player='p0',slot='27c08dca',class_hash='b2216bf3')
    run=dict(state=1,start_record=20,end_record=None if clear else 35,end_offset=45 if clear else 35,
             end_reason='ownership_declaration_boundary' if clear else 'explicit_state_2',
             first_timer=7,last_timer=.01,monotonic_timer=True,samples=[dict(offset=23),dict(offset=36)],
             binding=binding,records=[dict(fields=[dict(offset=36,size=4)])])
    slots={(1000,'27c08dca'):[dict(offset=1,component=2000,class_hash='b2216bf3')],
           (1000,'4154dcc4'):[dict(offset=1,component=3000,class_hash='0c98c63f')]}
    if clear: slots[1000,'27c08dca'].append(dict(offset=45,component=0,class_hash='00000000'))
    return dict(header=header,observed=dict(episodes=[run],orphan_records=[]),owners={1000:'p0'},slots=slots,
                properties=[dict(entity=3000,hash='e788f6a5',size=4,offset=5,value=0)],deaths=[],full_feedback=[])


@pytest.mark.parametrize('clear',[False,True])
def test_disable_with_global_occurrence_and_unique_active_owner(clear):
    name,reason,context=candidate(**evidence(clear))
    assert name=='p0' and reason=='direct_disable_owner_with_occurrence_and_body'
    assert context['numeric_uid']==100 and context['end']==45


def test_plant_hypothesis_unsupported_including_required_fortress_control():
    data=evidence()
    data['header']['players'][0]['username']='Aiden.SSG'
    assert candidate(**data,kind='plant')[:2]==(None,'plants_unsupported')


@pytest.mark.parametrize('change,reason',[
    ('plant','no_verified_plant_and_disable_occurrence'),
    ('winner','no_unambiguous_defense_score_increment'),
    ('leave','player_leave_timing_unknown'),('unknown_death','unknown_death_offset'),
    ('dead','timer_owner_dead_by_terminal'),('dbno','timer_owner_body_unresolved'),
    ('unknown_body','timer_owner_body_unresolved'),('body_clear','timer_owner_body_unresolved'),
    ('sharing','timer_owner_body_unresolved'),('partial','missing_or_competing_complete_disable_runs'),
    ('replacement','missing_or_competing_complete_disable_runs'),
    ('competing','missing_or_competing_complete_disable_runs'),('orphan','unbound_postplant_timer_evidence'),
    ('role','timer_owner_identity_or_role_conflict')])
def test_ambiguous_or_ineligible_evidence_abstains(change,reason):
    data=evidence(clear=change=='replacement')
    if change=='plant': data['header']['objectiveOccurrences']=[]
    if change=='winner':
        data['header']['teams'][0]['score']=0;data['header']['teams'][1]['score']=1
    if change=='leave': data['full_feedback']=[dict(type=dict(name='PlayerLeave'))]
    if change in ('unknown_death','dead'):
        data['deaths']=[dict(offset=0 if change=='unknown_death' else 39,
                             feedback=dict(type=dict(name='Death'),username='p0'))]
    if change in ('dbno','unknown_body'): data['properties'][0]['value']=3 if change=='dbno' else 99
    if change=='body_clear': data['slots'][1000,'4154dcc4'].append(dict(offset=30,component=0,class_hash='00000000'))
    if change=='sharing': data['slots'][9999,'other']=[dict(offset=30,component=3000,class_hash='anything')]
    if change=='partial': data['observed']['episodes'][0]['last_timer']=3
    if change=='replacement': data['slots'][1000,'27c08dca'][-1].update(component=2001,class_hash='b2216bf3')
    if change=='competing': data['observed']['episodes'].append(copy.deepcopy(data['observed']['episodes'][0]))
    if change=='orphan': data['observed']['orphan_records']=[dict(record_start=30)]
    if change=='role':
        data['observed']['episodes'][0]['binding'].update(player='p5',owner=1005)
        data['owners'][1005]='p5'
    name,actual,_=candidate(**data)
    assert name is None and actual==reason


def test_body_component_replacement_cannot_reuse_old_state():
    data=evidence()
    data['slots'][1000,'4154dcc4'].append(dict(offset=30,component=3001,class_hash='0c98c63f'))
    active,reason,_=active_body(1000,'p0',20,45,data['owners'],data['slots'],data['properties'])
    assert not active and reason=='body_route_missing_shared_or_changed'


def test_same_body_declaration_refresh_does_not_create_another_player():
    data=evidence()
    data['slots'][1000,'4154dcc4'].append(dict(offset=30,component=3000,class_hash='0c98c63f'))
    assert candidate(**data)[0]=='p0'
