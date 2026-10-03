from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research"))
from credited_uid_flag_layouts import WIDTHS, entry_at, frame_at


@pytest.mark.parametrize("prefix,width", WIDTHS.items())
def test_each_observed_form_has_explicit_bounds_without_damage_semantics(prefix, width):
    data = (1).to_bytes(8, "little")+bytes.fromhex(prefix)+bytes(width-3)
    e = entry_at(data, 0, {1})
    assert e["end"] == len(data) and e["uid"] == 1
    assert "victim" not in e and "health" not in e
    assert entry_at(data[:-1], 0, {1}) is None


def test_full_list_count_identity_replacement_unknown_and_duplicate_rejected():
    entries = [(i.to_bytes(8, "little")+bytes.fromhex("e101ff")+bytes(10)) for i in range(1, 11)]
    data = b"\x0a"+b"".join(entries)
    expected = set(range(1, 11))
    assert frame_at(data, 0, expected)["end"] == len(data)
    assert frame_at(data, 0, set(range(2, 12))) is None
    assert frame_at(b"\x0a"+entries[0]+b"".join(entries[:-1]), 0, expected) is None
    assert entry_at((1).to_bytes(8, "little")+bytes.fromhex("6201ff")+bytes(20), 0, expected) is None
