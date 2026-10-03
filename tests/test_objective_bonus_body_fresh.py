"""Prospective actor-only reserve safeguards, without opening event outcomes."""
import copy
from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research'))
from objective_bonus_body_fresh_pipeline import chronology
from objective_bonus_body_fresh_review import evaluate_gates, primary_constraints


def item(n, start, end):
    players=[dict(profile_id=f'00000000-0000-0000-0000-{i+1:012d}',username=f'p{i}.TEAM',team=i//5) for i in range(10)]
    return dict(folder='Match-2026-09-04',filename=f'match-R{n:02d}.rec',physical_round=n,sha256=str(n),map='Villa',
        header=dict(players=[dict(id=i+1,username=p['username']) for i,p in enumerate(players)],
            teams=[dict(role='Attack' if i==0 else 'Defense',startingScore=start[i],score=end[i]) for i in (0,1)]),
        players=players)


def test_physical_order_survives_reversed_parser_input_and_zero_internal_rounds():
    rows=[item(2,[1,0],[1,1]),item(1,[0,0],[1,0])]
    for row in rows:row['header']['roundNumber']=0
    complete,excluded,_,score=chronology(rows,[[1,1]])
    assert [r['physical_round'] for r in complete]==[1,2]
    assert [r['logical_round'] for r in complete]==[1,2]
    assert score==[1,1] and not excluded


@pytest.mark.parametrize('failure',['duplicate_source','profile_change','duplicate_uid','partial_roster','discontinuous_score'])
def test_actor_validation_never_relaxes_identity_or_completed_chronology(failure):
    rows=[item(1,[0,0],[1,0]),item(2,[1,0],[1,1])]
    if failure=='duplicate_source':rows[1]['sha256']=rows[0]['sha256']
    if failure=='profile_change':rows[1]['players'][0]['profile_id']='different-account'
    if failure=='duplicate_uid':rows[1]['header']['players'][0]['id']=rows[1]['header']['players'][1]['id']
    if failure=='partial_roster':rows[1]['players'].pop()
    if failure=='discontinuous_score':rows[1]['header']['teams'][0]['startingScore']=0
    with pytest.raises(ValueError):chronology(rows,[[1,1]])


def test_explicit_zero_score_attempt_is_recorded_not_invented_as_completed():
    rows=[item(1,[0,0],[0,0]),item(2,[0,0],[1,0])]
    complete,excluded,_,score=chronology(rows,[[0,1]])
    assert len(complete)==len(excluded)==1 and complete[0]['logical_round']==1 and score==[1,0]


def acceptance():
    return dict(min_complete_rounds=80,min_complete_maps=8,min_verified_plants=20,min_no_plant_controls=50,
        min_bonus_recoveries=3,min_distinct_bonus_maps=2,min_independently_constrained_bonus_actors=2,
        max_known_independent_wrong_actors=0,max_no_plant_false_positives=0,max_original_actor_changes=0,
        max_independent_objective_occurrence_conflicts=0,max_independent_aggregate_conflicts=0)


def valid_counts():
    return dict(rounds=100,maps=10,plants=25,no_plant_controls=75,bonus_recoveries=3,bonus_maps=2,
        independent_bonus_agreements=2)


def test_unseen_actor_validation_requires_positive_bonus_cases_and_primary_constraints():
    counts=valid_counts();counts['bonus_recoveries']=0;counts['independent_bonus_agreements']=0
    gates=evaluate_gates(counts,acceptance())
    assert gates['status']=='INSUFFICIENT' and not gates['production_deployed']
    assert evaluate_gates(valid_counts(),acceptance())['status']=='PASSED'


@pytest.mark.parametrize('field',['independent_wrong_actors','no_plant_false_positives','original_actor_changes','occurrence_conflicts','aggregate_conflicts'])
def test_fresh_actor_rule_fails_on_any_known_error_or_control_regression(field):
    assert evaluate_gates(valid_counts()|{field:1},acceptance())['status']=='FAILED'


def primary_case():
    row=item(1,[0,0],[1,0]); row.update(round=1,teams=row['header']['teams'],winner=0,verified_plant=True,
        original=dict(actor=None),proposed=dict(actor='p0.TEAM',reason='research_bonus'))
    prediction=dict(map='Villa',score=[1,0],rounds=[row])
    teams=[dict(id=10+i,score=1 if i==0 else 0,players=[dict(id=j+1,name=f'p{j}',
        stats=dict(diffuserPlanted=dict(count=1 if j==0 else 0))) for j in range(i*5,(i+1)*5)]) for i in (0,1)]
    payload=dict(id=123,games=[dict(map=dict(name='Villa'),teams=teams,
        rounds=[dict(index=1,winnerId=10,attackerId=10,defenderId=11)])])
    return prediction,payload,dict(official_match_id=123,team_ids=[10,11])


def test_independent_single_planter_constraint_is_separate_from_aggregate_totals():
    review=primary_constraints(*primary_case())
    assert review['constraints'][0]['verdict']=='agreement' and review['constraints'][0]['bonus_recovery']
    assert not review['aggregate_conflicts'] and not review['occurrence_conflicts']


def test_unresolved_primary_name_never_uses_remaining_player_or_objective_total():
    prediction,payload,source=primary_case();payload['games'][0]['teams'][0]['players'][4]['name']='different'
    review=primary_constraints(prediction,payload,source)
    assert review['status']=='primary_identity_unresolved_whole_map' and not review['constraints']


def test_primary_actor_disagreement_is_not_overridden_to_match_proposal():
    prediction,payload,source=primary_case()
    payload['games'][0]['teams'][0]['players'][0]['stats']['diffuserPlanted']['count']=0
    payload['games'][0]['teams'][0]['players'][1]['stats']['diffuserPlanted']['count']=1
    review=primary_constraints(prediction,payload,source)
    assert review['constraints'][0]['verdict']=='disagreement' and review['aggregate_conflicts']
