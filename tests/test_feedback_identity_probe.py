from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research"))
from credited_feedback_identity_probe import direct_references


def test_exact_full_uid_and_username_matches_are_only_literal_evidence():
    uid = 0x123456789ABCDEF0
    packet = b"prefix" + uid.to_bytes(8, "little") + b"Killer" + uid.to_bytes(8, "little")
    result = direct_references(packet, [{"id": uid, "username": "Killer"},
                                        {"id": uid + 1, "username": "Other"}])
    assert [r["relative_offset"] for r in result["literal_numeric_uid_references"]] == [6, 20]
    assert result["literal_username_references"] == [{"player": "Killer", "relative_offset": 14}]
    assert "credited_player" not in result


def test_zero_invalid_uid_empty_name_and_partial_uid_never_match():
    result = direct_references(bytes(20) + b"\x01\x02\x03\x04", [
        {"id": 0, "username": ""}, {"id": -1, "username": "absent"},
        {"id": 2 ** 64, "username": "absent"},
        {"id": 0xFFFFFFFF04030201, "username": "absent"}])
    assert result == {"literal_numeric_uid_references": [], "literal_username_references": []}
