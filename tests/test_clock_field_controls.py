import sys
from pathlib import Path

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"research"))
from credited_clock_field_controls import bracket,analyze


def test_clock_brackets_preserve_raw_zero_and_no_time_interpolation():
    samples=[{"offset":10,"unsigned_bits":0},{"offset":20,"unsigned_bits":45000}]
    r=bracket(samples,15)
    assert r["before"]==samples[0] and r["at_or_after"]==samples[1]
    assert r["elapsed_seconds"] is None
    assert bracket(samples,25)["at_or_after"] is None


def test_clock_brackets_refuse_duplicate_or_unknown_event_sources():
    with pytest.raises(ValueError,match="Duplicate"):
        bracket([{"offset":10},{"offset":10}],11)
    assert not bracket([],0)["resolved_order"]


def test_clock_analysis_rejects_promoted_units_before_using_header():
    raw={"clock":{"production_authoritative":False,"elapsed_seconds":.033}}
    with pytest.raises(ValueError,match="unpromoted"):
        analyze(raw,{}, {})
