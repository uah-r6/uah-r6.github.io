"""Consumed identity evidence must stay independent of actor correctness."""
from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research'))
from objective_bonus_body_asia_identity_review import identity, spellings, bind

UID='62e12cb2-8e51-4cb6-80d6-fe66b566ad26'


def history(names, status='retrieved'):
    return dict(profile_id=UID,source_url=f'https://stats.cc/siege/handle/{UID}',
                status=status,history_names=names)


def test_exact_uuid_history_maps_independently_of_current_decorated_name():
    result=identity(dict(username='KlzzSS..',profile_id=UID),
                    [dict(id=1,name='Klz',team_id=10)],history(['Klz.F5']))
    assert result['status']=='verified' and result['evidence_name']=='Klz.F5'


@pytest.mark.parametrize('name,official',[('AZuKi86.Daystar','AZuKi'),('JustOnlyi9.SH','i9'),
                                        ('KI11ERz','Kl11ERz'),('SUNSTRIKE.-','STRIKE')])
def test_no_digit_stripping_suffix_identity_or_confusable_guess(name,official):
    assert identity(dict(username=name,profile_id=UID),[dict(id=1,name=official,team_id=10)])['status']=='unresolved'


def test_hidden_history_does_not_supply_fabricated_alias():
    assert identity(dict(username='decorated',profile_id=UID),[dict(id=1,name='Klz',team_id=10)],
                    history(['Klz.F5'],'history_hidden'))['status']=='unresolved'


def test_wrong_profile_evidence_rejected():
    with pytest.raises(ValueError,match='exact replay UUID'):
        identity(dict(username='decorated',profile_id='different'),[],history(['Klz.F5']))


def test_recorded_name_with_dots_only_removes_documented_final_team_suffix():
    assert 'nay.pew' in spellings('Nay.Pew.Elevate')
    assert 'nay' not in spellings('Nay.Pew.Elevate')


def test_partial_identity_does_not_fill_remaining_official_player():
    players=[dict(username=f'p{i}.WBG',profile_id=f'uid-{i}',team=i//5) for i in range(10)]
    players[-1]['username']='unknown'
    people=[dict(id=i,name=f'p{i}',team_id=i//5+10) for i in range(10)]
    review=bind(players,people,{})
    assert review['status']=='identity_blocked_whole_map'
    assert review['players'][-1]['status']=='unresolved'


def test_duplicate_profile_roster_rejected():
    players=[dict(username=f'p{i}.WBG',profile_id='same',team=i//5) for i in range(10)]
    with pytest.raises(ValueError,match='ten-player'): bind(players,[],{})
