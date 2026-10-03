from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research"))
from credited_history_opaque_items import expand_container


def test_single_unknown_terminal_preserved_exactly_without_role_or_time():
    data = bytes(25)+b"\xffopaque"
    box = {"start":0,"end":len(data),"item_count":2}
    r = expand_container(data,box,[],{})
    assert r["complete"] and bytes.fromhex(r["items"][0]["raw_hex"]) == b"\xffopaque"
    assert r["items"][0]["event_role"] is None


def test_unknown_middle_or_later_known_candidate_never_skipped():
    data = bytes(25)+b"\xffopaque"
    box = {"start":0,"end":len(data),"item_count":3}
    assert not expand_container(data,box,[],{})["complete"]
    box["item_count"] = 2
    assert not expand_container(data,box,[],{28:{"start":28,"end":30}})["complete"]


def test_kind10_requires_exact_metadata_and_never_becomes_objective():
    player = {"id":1,"username":"p","roleImage":2,"alliance":3}
    ref = (1).to_bytes(8,"little")+(2).to_bytes(8,"little")+(3).to_bytes(4,"little")
    data = bytes(25)+b"\x0a"+bytes(4)+ref
    box = {"start":0,"end":len(data),"item_count":2}
    r = expand_container(data,box,[player],{})
    assert r["complete"] and r["items"][0]["kind"] == "opaque_single_reference"
    assert "objective" not in r["items"][0]
    box["item_count"] = 3
    assert not expand_container(data,box,[{**player,"roleImage":9}],{})["complete"]
