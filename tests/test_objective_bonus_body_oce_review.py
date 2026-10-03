"""Identity snapshot rejects ambiguous, colliding and partial official binding."""
from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research'))
from objective_bonus_body_oce_review import bindings


def roster():
    return ([dict(username=f'p{i}.TEAM',profile_id=f'uid-{i}',team=i//5) for i in range(10)],
            [dict(id=i,name=f'p{i}',team_id=i//5+100) for i in range(10)])


def test_full_exact_basename_roster_binds_without_stats():
    players,people=roster()
    assert bindings(players,people,{})['status']=='full_unique_primary_identity'


def test_one_unknown_blocks_entire_map_and_not_filled_by_remaining_person():
    players,people=roster();players[-1]['username']='decorated999'
    result=bindings(players,people,{})
    assert result['status']=='identity_unresolved_whole_map'
    assert result['players'][-1]['status']=='unresolved'


def test_collision_is_rejected_instead_of_inferred_from_team():
    players,people=roster();players[0]['username']='p1.TEAM'
    with pytest.raises(ValueError,match='collide'):bindings(players,people,{})


def test_cross_team_conflict_is_rejected():
    players,people=roster();people[0]['team_id']=101
    with pytest.raises(ValueError,match='team'):bindings(players,people,{})
