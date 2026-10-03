"""Public event formats and packet order controls must refuse guessing."""
import importlib
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'research'))
features=importlib.import_module('credited_kill_feature_audit')
opening=importlib.import_module('credited_kill_opening_order')


def test_public_multikill_parsing_preserves_exact_name_and_logical_round():
    game=dict(rounds=[dict(events=[]),dict(events=[dict(type='multikill',html='<a>icon</a> Exact.Name gets a 3k')])])
    assert features.public_multikills(game)==[dict(round=2,name='Exact.Name',kills=3)]
    game['rounds'][1]['events'][0]['html']='Unknown field'
    with pytest.raises(ValueError):features.public_multikills(game)


def event(offset,killer,victim,time,kind='Kill'):
    return dict(offset=offset,feedback=dict(type=dict(name=kind),username=killer,target=victim,timeInSeconds=time))


def test_packet_order_does_not_reinterpret_coarse_timer_or_teamkill():
    rows=[event(10,'a','b',40),event(20,'a','c',30),event(30,'b','d',45)]
    teams={'a':0,'b':0,'c':1,'d':1}
    assert opening.first_opponent_finish(rows,teams,packet_order=True)==rows[1]
    assert opening.first_opponent_finish(rows,teams,packet_order=False)==rows[2]


def test_duplicate_victim_and_nonkill_death_do_not_create_opening():
    teams={'a':0,'b':0,'c':1,'d':1}
    rows=[event(1,'c',None,60,'Death'),event(2,'a','c',50),event(3,'a','d',40)]
    assert opening.first_opponent_finish(rows,teams,packet_order=True)==rows[2]
