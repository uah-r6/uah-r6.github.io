from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"research"))
from credited_history_missing_actor_audit import audit


def test_incomplete_or_mismatched_history_cannot_prove_absent_actor():
    h={"cumulative":{"complete":False},"feed_parity":{"exact_original_filtered_feed_identity_weapon_headshot_order":True}}
    with pytest.raises(ValueError,match="incomplete"):
        audit(h,{}, {})
    h["cumulative"]["complete"]=True
    h["feed_parity"]["exact_original_filtered_feed_identity_weapon_headshot_order"]=False
    with pytest.raises(ValueError,match="unmatched"):
        audit(h,{}, {})


def test_raw_state_audit_refuses_changed_numeric_identity():
    h={"cumulative":{"complete":True},"feed_parity":{"exact_original_filtered_feed_identity_weapon_headshot_order":True}}
    obs={"header":{"players":[{"id":1,"username":"A","profileID":"p","teamIndex":0}]}}
    state={"header":{"players":[{"id":2,"username":"A","profileID":"p","teamIndex":0}]}}
    with pytest.raises(ValueError,match="identity differs"):
        audit(h,obs,state)
