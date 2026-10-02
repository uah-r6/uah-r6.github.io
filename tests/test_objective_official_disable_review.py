"""Map-level source evidence must not guess ambiguous round actor labels."""
import copy
from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research'))
from objective_official_disable_review import constrained_disable_labels


def game():
    return dict(teams=[dict(id=10,score=2,players=[dict(id=i,name=f'p{i}',disables=2 if i==1 else 0)
                                               for i in range(1,6)]),
                       dict(id=20,score=1,players=[dict(id=i,name=f'p{i}',disables=0)
                                               for i in range(6,11)])],
                rounds=[dict(id=100+i,index=i,winMethod=3 if i<3 else 1,
                             winnerId=10 if i<3 else 20,attackerId=20,defenderId=10)
                        for i in range(1,4)])


def test_single_player_covers_two_disable_wins():
    rows=constrained_disable_labels(game())
    assert rows[0]['constrained_round_labels']==[dict(round=1,player='p1',id=1),dict(round=2,player='p1',id=1)]
    assert rows[1]['constrained_round_labels']==[]


def test_multiple_players_does_not_assign_rounds_from_map_totals():
    data=game()
    data['teams'][0]['players'][0]['disables']=1
    data['teams'][0]['players'][1]['disables']=1
    row=constrained_disable_labels(data)[0]
    assert row['disable_rounds']==[1,2]
    assert row['constrained_round_labels']==[]
    assert row['inference']=='multiple_players_round_assignment_unresolved'


@pytest.mark.parametrize('change,message',[
    ('counts','totals'),('winner','Defense'),('index','indexes'),('identity','players'),('score','score')])
def test_inconsistent_official_data_cannot_supply_reviewed_labels(change,message):
    data=copy.deepcopy(game())
    if change=='counts': data['teams'][0]['players'][0]['disables']=1
    if change=='winner': data['rounds'][0]['winnerId']=20
    if change=='index': data['rounds'][0]['index']=0
    if change=='identity': data['teams'][1]['players'][0]['id']=1
    if change=='score': data['teams'][0]['score']=3
    with pytest.raises(ValueError,match=message):
        constrained_disable_labels(data)
