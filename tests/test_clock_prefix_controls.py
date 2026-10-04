import sys
from pathlib import Path

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"research"))
from credited_clock_prefix_controls import clock_regions,event_bracket,analyze


def test_clock_regions_retains_resets_terminal_zero_and_no_elapsed_seconds():
    values=[45000,44000,0,179000,1000,0,45000]
    samples=clock_regions([{"offset":i*10+1,"unsigned_bits":v} for i,v in enumerate(values)])
    assert [s["serialized_region"] for s in samples]==[0,0,1,2,2,3,4]
    assert event_bracket(samples,6)["status"]=="same_serialized_positive_countdown_region_raw_units_only"
    assert event_bracket(samples,26)["status"]=="zero_or_terminal_clock"
    assert event_bracket(samples,76)["status"]=="missing_one_side"
    assert event_bracket(samples,26)["elapsed_seconds"] is None


def test_clock_brackets_refuse_positive_reset_and_zero_offset():
    samples=clock_regions([{"offset":1,"unsigned_bits":29000},{"offset":11,"unsigned_bits":44950}])
    assert event_bracket(samples,6)["status"]=="serialized_region_change"
    assert event_bracket(samples,0)["status"]=="nonpositive_original_feed_offset"
    with pytest.raises(ValueError,match="Distinct"):
        clock_regions([{"offset":1,"unsigned_bits":2},{"offset":1,"unsigned_bits":1}])


def test_clock_prefix_analysis_keeps_scale_failure_and_partial_groups():
    def p(offset,bits):return {"offset":offset,"unsigned_bits":bits,"entity":123,"width":4}
    groups=[{"record":90,"entity":123,"coarse":[p(100,179)],"fine":[p(110,170000)],"stop_reason":"unsupported_field_width"},
            {"record":120,"entity":123,"coarse":[],"fine":[p(130,169999)],"stop_reason":"no_inherited_continuation"}]
    raw={"production_authoritative":False,"elapsed_seconds":None,"groups":groups}
    r=analyze(raw,{"header":{"actionPhaseStartOffset":109},"credit":{"finishes":[]}}, {"complete":True,"items":[]})
    assert len(r["paired_scale_failures"])==1 and len(r["single_field_prefixes"])==1
    assert r["elapsed_seconds"] is None
    assert r["prefix_stop_counts"]["unsupported_field_width"]==1
