from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"research"))
from credited_history_framing_v2 import framed_items, cumulative_consensus


def ref(uid):
    return uid.to_bytes(8,"little")+(30).to_bytes(8,"little")+(2).to_bytes(4,"little")


def test_kind10_exact_bound_and_header_reference_are_required():
    data = bytes(25)+bytes([10])+bytes([4,0,0,0])+ref(1)+bytes([1])
    box = {"start": 0, "end": len(data), "item_count": 2}
    players = [{"id":1,"roleImage":30,"alliance":2,"username":"A"}]
    assert framed_items(data,box,players,{})["complete"]
    for altered in (data[:-1],data[:-1]+b"\x02",data+b"\x00"):
        b = {**box,"end":len(altered)}
        assert not framed_items(altered,b,players,{})["complete"]


def test_unknown_middle_kind_is_never_skipped():
    data = bytes(25)+b"\x03"+bytes(40)
    r = framed_items(data,{"start":0,"end":len(data),"item_count":2},[],{})
    assert not r["complete"] and r["items"] == [] and r["remaining_hex"] == data[25:].hex()


def box(raw,scalar=10):
    return {"item_count":len(raw)+1,"framed":{"complete":True,"items":[{"raw_hex":r,"opaque_scalar":scalar} for r in raw]}}


def test_cumulative_order_is_byte_prefix_not_scalar_sort():
    r = cumulative_consensus([box([]),box(["aa"]),box(["aa","bb"])])
    assert r["complete"] and r["scalar_ties"] == {"10":2}
    assert [i["raw_hex"] for i in r["items"]] == ["aa","bb"]
    r = cumulative_consensus([box(["aa"]),box(["bb","aa"])])
    assert not r["complete"]


def test_any_partial_copy_prevents_complete_history_promotion():
    r = cumulative_consensus([box(["aa"]),{"item_count":3,"framed":{"complete":False,"items":[]}}])
    assert not r["complete"] and r["reason"] == "partial_container_retained"
