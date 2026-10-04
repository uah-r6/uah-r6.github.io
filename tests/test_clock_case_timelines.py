import sys
from pathlib import Path

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"research"))
from credited_clock_case_timelines import raw_span,case
from credited_clock_prefix_controls import clock_regions,event_bracket


def event(samples,offset):
    return {"offset":offset,"clock_bracket":event_bracket(samples,offset)}


def test_raw_span_keeps_interval_uncertainty_and_no_elapsed_seconds():
    samples=clock_regions([{"entity":123,"offset":i*10+1,"unsigned_bits":v} for i,v in enumerate((20000,19966,19000,18966))])
    r=raw_span(event(samples,6),event(samples,26))
    assert (r["lower_raw_units"],r["upper_raw_units"])==(966,1034)
    assert r["elapsed_seconds"] is None
    same=raw_span(event(samples,6),event(samples,7))
    assert (same["lower_raw_units"],same["upper_raw_units"])==(0,34)


def test_raw_span_refuses_reset_zero_missing_and_reverse_order():
    samples=clock_regions([{"entity":123,"offset":i*10+1,"unsigned_bits":v} for i,v in enumerate((20000,19966,44966,44932,0))])
    assert raw_span(event(samples,6),event(samples,26))["status"]=="different_serialized_clock_provider_or_region"
    assert raw_span(event(samples,26),event(samples,36))["status"]=="unsupported_event_bracket"
    assert raw_span(event(samples,6),event(samples,56))["status"]=="unsupported_event_bracket"
    assert raw_span(event(samples,26),event(samples,6))["status"]=="unknown_or_reversed_physical_order"


def test_case_rejects_counter_header_identity_mismatch_before_timing():
    target={"id":100,"profileID":"a","username":"target","teamIndex":0}
    selection={"target_identity":target}
    lifecycle={"finding":{"post_action_body":[]}}
    observation={"header":{"players":[target]},"credit":{"players":[{"uid":101,"profileID":"a","username":"target","team":0,"samples":[]}]}}
    with pytest.raises(ValueError,match="UID-profile-name-team"):
        case(selection,lifecycle,observation,{}, {"groups":[]})
