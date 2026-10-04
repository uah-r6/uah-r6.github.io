from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"research"))
from credited_history_framing_v3 import decode_at, decode_box, feed_parity

PLAYERS = [{"id":i,"roleImage":30,"alliance":2,"username":str(i)} for i in (1,2)]


def ref(i):
    return i.to_bytes(8,"little")+(30).to_bytes(8,"little")+(2).to_bytes(4,"little")


def item(kind):
    prefix = bytes([kind])+(99).to_bytes(4,"little")
    if kind == 10:
        return prefix+ref(1)+bytes([2])
    prefix += (3).to_bytes(8,"little")+(4).to_bytes(8,"little")
    return prefix+ref(1)+(ref(2)+bytes([0]) if kind in (1,2) else b"")


def test_exact_single_reference_death_has_no_named_actor_or_cause():
    data=item(3)
    r=decode_at(data,0,len(data),PLAYERS)
    assert r["end"] == 41 and r["reference"]["uid"] == 1
    assert "first" not in r and r["event_role"] is None and r["elapsed_seconds"] is None
    assert decode_at(data[:-1],0,len(data)-1,PLAYERS) is None


def test_friendly_layout_keeps_raw_type_without_opponent_credit():
    data=item(2)
    r=decode_at(data,0,len(data),PLAYERS)
    assert r["kind_byte"] == 2 and r["first"]["uid"] == 1 and r["second"]["uid"] == 2
    assert r["event_role"] is None and "credited_killer" not in r


def test_opaque_tail_two_and_declared_count_bounds():
    data=bytes(25)+item(10)+item(3)
    box={"start":0,"end":len(data),"item_count":3}
    assert decode_box(data,box,PLAYERS)["complete"]
    assert not decode_box(data,{**box,"item_count":2},PLAYERS)["complete"]
    altered=data[:50]+b"\x03"+data[51:]
    assert not decode_box(altered,box,PLAYERS)["complete"]


def test_wrong_identity_fields_and_unknown_type_are_refused():
    data=item(3)
    for altered in (bytes([4])+data[1:],data[:29]+bytes(8)+data[37:]):
        assert decode_at(altered,0,len(altered),PLAYERS) is None


def test_unknown_death_keeps_original_sequence_even_with_zero_offset():
    a=decode_at(item(1),0,62,PLAYERS)
    b=decode_at(item(3),0,41,PLAYERS)
    feed=[{"offset":10,"feedback":{"type":{"name":"Kill"},"username":"1","target":"2","weaponID":3}},
          {"offset":0,"feedback":{"type":{"name":"Death"},"username":"1"}}]
    r=feed_parity([a,b],feed)
    assert r["exact_original_filtered_feed_identity_weapon_headshot_order"] and r["legacy_zero_offset_count"] == 1
    assert r["cause_for_single_reference_deaths"] is None
