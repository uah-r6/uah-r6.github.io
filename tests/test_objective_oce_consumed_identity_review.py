"""Additional consumed aliases preserve exact spelling and account identity."""
from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research'))
from objective_oce_consumed_identity_review import exact_history_identity


def test_literal_account_history_team_suffix_is_accepted():
    p=dict(username='PODCAST.CHIEFS',profile_id='uuid')
    h=dict(profile_id='uuid',source_url='https://stats.cc/siege/Lunchbox.CHF/uuid',status='retrieved',history_names=['Lunchbox.CHF'])
    assert exact_history_identity(p,[dict(id=1,name='Lunchbox',team_id=10)],h)['status']=='verified'


@pytest.mark.parametrize('source,target',[('Elementz77','Elementz'),('wizard','Wiízard'),('pIayxr','Playxr'),('Swordera','Sword')])
def test_no_digit_prefix_confusable_or_accent_repair(source,target):
    p=dict(username=source,profile_id='uuid')
    assert exact_history_identity(p,[dict(id=1,name=target,team_id=10)],None)['status']=='unresolved'


def test_wrong_uuid_source_is_rejected():
    p=dict(username='name',profile_id='uuid');h=dict(profile_id='other',source_url='https://stats.cc/siege/name/other',status='retrieved',history_names=['name'])
    with pytest.raises(ValueError,match='exact account'):exact_history_identity(p,[],h)
