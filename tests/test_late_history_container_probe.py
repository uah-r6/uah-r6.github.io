from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research"))
from credited_late_history_container_probe import container_at


def packet(count=2, size=66, item=bytes(53)):
    descriptor = b"\x09"+(100).to_bytes(4,"little")+(3).to_bytes(4,"little")
    data = (42).to_bytes(4,"little")+size.to_bytes(8,"little")+count.to_bytes(4,"little")+descriptor+item
    return data, descriptor


def test_exact_payload_length_count_and_entry_bounds():
    data, descriptor = packet()
    c = {"start": 25, "end": 78}
    result = container_at(data,16,descriptor,{25:c})
    assert result["complete"] and result["end"] == len(data) and result["item_count"] == 2
    assert result["known_items"] == [c]


def test_unknown_item_and_count_mismatch_remain_partial_not_repaired():
    data, descriptor = packet()
    assert not container_at(data,16,descriptor,{})["complete"]
    data, descriptor = packet(count=3)
    result = container_at(data,16,descriptor,{25:{"start":25,"end":78}})
    assert not result["complete"] and result["unknown_kind_byte"] is None


def test_out_of_buffer_and_entry_past_declared_size_refused():
    data, descriptor = packet(size=1000)
    assert container_at(data,16,descriptor,{}) is None
    data, descriptor = packet(size=13)
    assert container_at(data,16,descriptor,{25:{"start":25,"end":78}}) is None
