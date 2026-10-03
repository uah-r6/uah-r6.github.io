from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research"))
from credited_uid_variable_frames import discover, frame_at


def packet():
    entries = []
    for i in range(1, 11):
        opaque = ((b"\xf9\x01\x00\x01\xff"+bytes(10)) if i % 3 == 0 else
                  (b"\x39\x14\x04\x00\xff"+bytes(16)) if i % 3 == 1 else b"\x21\x00\xff")
        entries.append(i.to_bytes(8, "little")+opaque)
    return b"\x0a"+b"".join(entries)


def test_mixed_width_counted_frame_preserves_only_opaque_bytes_and_ids():
    result = frame_at(packet(), 0, set(range(1, 11)))
    assert result["end"] == len(packet())
    assert [e["uid"] for e in result["entries"]] == list(range(1, 11))
    assert "health" not in result["entries"][0] and "attacker" not in result


def test_unknown_form_truncation_count_replacement_and_duplicate_refused():
    p = packet(); expected = set(range(1, 11))
    bad_form = p[:9]+b"\x40"+p[10:]
    duplicate = p[:1]+(2).to_bytes(8, "little")+p[9:]
    for data in (p[:-1], b"\x09"+p[1:], bad_form, duplicate):
        assert frame_at(data, 0, expected) is None
    assert frame_at(p, 0, set(range(2, 12))) is None


def test_literal_references_cannot_promote_an_unframed_cooccurrence():
    p = packet(); f = frame_at(p, 0, set(range(1, 11)))
    refs = [{"uid": e["uid"], "relative_offset": e["offset"]} for e in f["entries"]]
    assert len(discover(p, refs)) == 1
    assert discover(b"\x09"+p[1:], refs) == []
