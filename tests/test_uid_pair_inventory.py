from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research"))
from credited_uid_pair_inventory import paired_at, reference_at


def players():
    return [{"id": 1, "username": "a", "roleImage": 100, "alliance": 3},
            {"id": 2, "username": "b", "roleImage": 200, "alliance": 4}]


def encoded(p):
    return p["id"].to_bytes(8, "little")+p["roleImage"].to_bytes(8, "little")+p["alliance"].to_bytes(4, "little")


def test_explicit_header_fields_and_contiguous_bounds_not_actor_roles():
    ps = players(); data = b"x"+encoded(ps[0])+encoded(ps[1])+b"z"
    p = paired_at(data, 1, ps)
    assert p["end"] == 41 and p["first"]["uid"] == 1 and p["second"]["uid"] == 2
    assert p["credited_killer"] is None and p["downer"] is None and p["event_time"] is None


def test_truncation_metadata_mismatch_duplicate_header_and_proximity_refused():
    ps = players(); a, b = encoded(ps[0]), encoded(ps[1])
    assert paired_at(a+b[:-1], 0, ps) is None
    assert paired_at(a+b"noise"+b, 0, ps) is None
    assert reference_at(a, 0, ps+[ps[0]]) is None
    assert reference_at(a, 0, [{**ps[0], "roleImage": 101}]) is None
    assert reference_at(a, 0, [{**ps[0], "alliance": 4}]) is None
    assert reference_at(a, -1, ps) is None
