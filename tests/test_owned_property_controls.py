import importlib.util
from pathlib import Path
import sys

import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"research"))
from credited_owned_property_controls import summarize


def evidence():
    identity={"uid":100,"username":"target"}
    field={"offset":500,"tag_hex":"e788f6a5","width":4,"unsigned_bits":3,
           "route":{"identity":identity,"slot":0xc4dc5441,"class":0x3fc6980c},
           "candidate_numeric_references":[]}
    return {"production_authoritative":False,"elapsed_seconds":None,
            "reason":"bounded_scalar_text_prefixes_only_not_complete_component_or_causal_evidence",
            "query":{"target_uid":100,"target_start":400,"target_end":600},
            "prefixes":[{"stop_reason":"unsupported_field_width","fields":[field]}]}


def test_owned_reference_summary_preserves_unknowns_and_no_causal_actor():
    e=evidence()
    e["prefixes"][0]["fields"].append({"offset":499,"route":{"identity":{"uid":200}},
                                     "candidate_numeric_references":[{"identity":{"uid":100}}]})
    r=summarize(e,{"observation":{"offset":500}})
    assert r["target_raw3_exact_parity"] and r["incoming_reference_count"]==1
    assert r["causal_actor_uid"] is None and r["credited_victim_uid"] is None
    assert r["prefix_stop_counts"]=={"unsupported_field_width":1}


def test_owned_reference_summary_refuses_wrong_target_route():
    e=evidence();e["prefixes"][0]["fields"][0]["route"]["identity"]["uid"]=200
    with pytest.raises(ValueError,match="exact target"):
        summarize(e,{"observation":{"offset":500}})


def test_owned_reference_summary_retains_tool_refusals():
    e=evidence();e["reason"]="incomplete_or_ambiguous_uid_owners"
    r=summarize(e,{"observation":{"offset":500}})
    assert r["quality_refusal"]==e["reason"] and r["causal_actor_uid"] is None


def test_owned_reference_summary_rejects_clock_or_production_promotion():
    e=evidence();e["elapsed_seconds"]=1.2
    with pytest.raises(ValueError,match="Unpromoted"):
        summarize(e,{"observation":{"offset":500}})
