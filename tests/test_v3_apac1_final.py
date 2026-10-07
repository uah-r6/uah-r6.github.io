from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research'))
from r6stats.parser.models import Player
from v3_apac1_pipeline import bind_person
import v3_apac1_final as final


def test_numeric_name_never_binds_by_digit_stripping_or_remaining_person():
    p=Player('actual-profile','Nina666.SCARZ',0)
    meta={'players':[{'id':3072,'ign':'NINA','stylized_name':'Nina'}]}
    primary=[{'id':1453,'name':'Nina'}]
    assert bind_person(p,meta,primary,{})==(None,None,'Independent public identity unresolved')
    proven={'source':dict(independently_verified=True,replay_profile_id='actual-profile',siegegg_player_id=3072,name='Nina',observed_names=['Nina.SCARZ'])}
    public,official,reason=bind_person(p,meta,primary,proven)
    assert (public['id'],official['id'],reason)==(3072,1453,None)
    p.profile_id='different-profile'
    assert bind_person(p,meta,primary,proven)[2]=='Independent public identity unresolved'


def test_conflicting_exact_profile_identity_is_refused():
    p=Player('profile','Nina.SCARZ',0)
    meta={'players':[{'id':3072,'ign':'NINA','stylized_name':'Nina'}]}
    alias={'a':dict(independently_verified=True,replay_profile_id='profile',siegegg_player_id=999,name='Someone',observed_names=[])}
    with pytest.raises(ValueError,match='conflicts'):bind_person(p,meta,[],alias)


def test_final_consumption_marker_blocks_targets_and_second_evaluation(tmp_path,monkeypatch):
    monkeypatch.setattr(final,'DATA',tmp_path);monkeypatch.setattr(final,'RESULT',tmp_path/'result.json')
    (tmp_path/'rating-targets-opened.json').write_text('{}')
    with pytest.raises(ValueError,match='consumed'):final.evaluate()
    with pytest.raises(ValueError,match='consumed'):final.prepare_targets()


def test_no_coverage_means_no_target_download(tmp_path,monkeypatch):
    monkeypatch.setattr(final,'DATA',tmp_path);monkeypatch.setattr(final,'RESULT',tmp_path/'result.json')
    monkeypatch.setattr(final,'clean_tree',lambda:None)
    monkeypatch.setattr(final,'read_frozen',lambda:{'qualified':False})
    monkeypatch.setattr(final,'fetch',lambda *args:pytest.fail('Should not fetch insufficient-cohort targets'))
    with pytest.raises(ValueError,match='Insufficient prospective coverage'):final.prepare_targets()
