from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research"))
from credited_late_event_layout_probe import candidate_at, compare_finishes


def pair():
    return {"start": 21, "end": 61, "first": {"username": "finisher"}, "second": {"username": "victim"}}


def packet(kind=1):
    return bytes([kind])+(123).to_bytes(4,"little")+(99).to_bytes(8,"little")+(77).to_bytes(8,"little")+bytes(40)+b"\x01"


def test_explicit_boundaries_and_raw_scalar_not_elapsed_time():
    c = candidate_at(packet(), pair())
    assert c["weapon_id"] == 99 and c["opaque_scalar"] == 123 and c["headshot"]
    assert c["event_time"] is None and c["downer"] is None and c["credited_killer"] is None
    assert candidate_at(packet()[:-1], pair()) is None
    assert candidate_at(packet(2), pair()) is None


def test_repeated_late_payloads_not_double_counted_and_weapon_mismatch_refused():
    c = candidate_at(packet(), pair())
    f = [{"offset": 50, "feedback": {"type": {"name": "Kill"}, "username": "finisher", "target": "victim", "weaponID": 99, "headshot": True}}]
    result = compare_finishes([c,c], f)
    assert result["exact_identity_weapon_headshot_order_match"]
    assert result["duplicate_type1_physical_copies"] == 1
    f[0]["feedback"]["weaponID"] = 1
    assert not compare_finishes([c], f)["exact_identity_weapon_headshot_order_match"]
