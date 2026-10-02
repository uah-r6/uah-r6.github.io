from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research'))
from v3_corrected_kost_development import groups


def samples():
    old=dict(kills=1,teamkills=0,opening_kills=0,opening_deaths=0,clutches=0,
        kost_rounds=0,survived=0,deaths_traded=0,kills_traded=0,plants=1,disables=0)
    return [dict(event=event,reserved_for_final_test=False,fit_eligible=True,objective_map_complete=True,
        paired_v2_rounds=[old.copy()],rounds=[old|dict(kost_rounds=1)]) for event in ('train','dev')]


def test_related_kost_correction_allowed_without_changing_other_inputs():
    train,dev=groups(samples(),dict(train_events=['train'],development_event='dev'))
    assert train[0]['rounds'][0]['kost_rounds']==1
    assert dev[0]['paired_v2_rounds'][0]['kost_rounds']==0


def test_corrected_kost_study_rejects_unrelated_kill_feature_change():
    rows=samples();rows[0]['rounds'][0]['kills']=2
    with pytest.raises(ValueError,match='Unrelated feature'):
        groups(rows,dict(train_events=['train'],development_event='dev'))
