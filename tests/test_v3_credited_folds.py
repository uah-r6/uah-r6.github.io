from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research'))
from v3_credited_fit import folds, baseline_row, fit


def test_every_player_and_map_of_validation_event_is_excluded_from_training():
    rows=[dict(event=e,map=m,player=p) for e in ('A','B','C') for m in ('one','two') for p in ('p','q')]
    for event,train,validation in folds(rows):
        assert len(train)==8 and len(validation)==4
        assert all(r['event']!=event for r in train)
        assert all(r['event']==event for r in validation)


def test_exact_baseline_contract_keeps_original_features_without_mutating_corrected_rows():
    r=dict(event='A',rounds=[{'kills':2}],original_v2_rounds=[{'kills':1}])
    baseline=baseline_row(r)
    assert baseline['rounds']==[{'kills':1}] and r['rounds']==[{'kills':2}]
