from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"research"))
from credited_history_append_inventory import append_inventory


def test_declared_single_append_boundary_requires_unchanged_prefix():
    data = bytes(25)+b"abc"+bytes(25)+b"abc"+bytes([10])+bytes(25)
    a = {"start": 0, "end": 28, "item_count": 2}
    b = {"start": 28, "end": len(data), "item_count": 3}
    r = append_inventory(data, [a,b])[0]
    assert r["single_item_append"] and r["kind_byte"] == 10 and r["width"] == 26
    data = data[:53]+b"xbc"+data[56:]
    assert not append_inventory(data, [a,b])[0]["single_item_append"]


def test_count_jump_is_not_split_into_guessed_item_sizes():
    data = bytes(25)+b"abc"+bytes(25)+b"abc"+bytes(52)
    a = {"start": 0, "end": 28, "item_count": 2}
    b = {"start": 28, "end": len(data), "item_count": 4}
    r = append_inventory(data, [a,b])[0]
    assert r["unchanged_item_prefix"] and not r["single_item_append"] and r["raw_hex"] is None
