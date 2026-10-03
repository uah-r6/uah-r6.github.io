from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research"))
from credited_uid_roster_frames import frame_at, frames


def packet(ids=range(1, 11), suffix=b"\x21\x00\xff"):
    return b"\x0a" + b"".join(i.to_bytes(8, "little")+suffix for i in ids)


def test_explicit_count_width_complete_unique_identity_list():
    data = b"prefix" + packet() + b"after" + packet(reversed(range(1, 11)))
    found = frames(data, set(range(1, 11)))
    assert [f["start"] for f in found] == [6, 122]
    assert all(len(f["entries"]) == 10 for f in found)
    assert "attacker" not in found[0] and "victim" not in found[0]


def test_duplicate_replacement_truncation_count_and_unknown_suffix_refused():
    expected = set(range(1, 11))
    for bad in (packet([1]*10), packet(range(2, 12)), packet()[:-1],
                b"\x09"+packet()[1:], packet(suffix=b"\x22\x00\xff")):
        assert frame_at(bad, 0, expected) is None


def test_negative_offset_and_incomplete_expected_roster_refused():
    assert frame_at(packet(), -1, set(range(1, 11))) is None
    assert frames(packet(), set(range(1, 10))) == []
