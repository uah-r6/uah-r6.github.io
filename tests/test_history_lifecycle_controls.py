from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"research"))
from credited_history_lifecycle_controls import independent_bounds,lifecycle


def test_tied_scalar_bounds_use_explicit_list_ordinal_not_scalar_sort():
    items=[{"kind_byte":1,"opaque_scalar":10},{"kind_byte":5,"opaque_scalar":10},{"kind_byte":1,"opaque_scalar":10}]
    r=independent_bounds(items,[{"offset":100},{"offset":200}],1,50)
    assert r["resolved"] and (r["lower_feed_offset"],r["upper_feed_offset"]) == (100,200)
    assert r["elapsed_seconds"] is None


def test_zero_legacy_anchor_is_unresolved_not_elapsed_fallback():
    r=independent_bounds([{"kind_byte":1},{"kind_byte":5},{"kind_byte":3}],[{"offset":100},{"offset":0}],1,50)
    assert not r["resolved"] and r["elapsed_seconds"] is None


def test_incomplete_or_promoted_go_history_refuses_lifecycle_claim():
    for h in ({"complete":False,"production_authoritative":False},{"complete":True,"production_authoritative":True}):
        with pytest.raises(ValueError):lifecycle(h,{}, {})
