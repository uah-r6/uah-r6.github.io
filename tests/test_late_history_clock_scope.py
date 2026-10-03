from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research"))
from credited_late_history_clock_scope import clock_scope


def inputs(scalars=(100, 200), seconds=(6, 42)):
    c = [{"kind_byte": 1, "raw_hex": str(i), "opaque_scalar": v, "weapon_id": 1,
          "headshot": False, "first": {"username": "a"}, "second": {"username": f"v{i}"}} for i,v in enumerate(scalars)]
    f = [{"offset": i+1, "feedback": {"username": "a", "target": f"v{i}", "weaponID": 1,
           "type": {"name": "Kill"}, "timeInSeconds": v}} for i,v in enumerate(seconds)]
    return c, f


def test_plant_reset_keeps_scalar_order_and_never_converts_to_trade_seconds():
    result = clock_scope(*inputs())
    assert result["event_order_matches_known_feedback_offsets"]
    assert result["pairs"][0]["delta_remaining"] == -36
    assert result["pairs"][0]["elapsed_seconds"] is None
    assert result["pairs"][0]["scalar_units_per_displayed_clock_second"] is None


def test_numeric_ratio_is_not_a_calibrated_clock_and_duplicates_are_copies():
    c,f = inputs(seconds=(100, 90))
    result = clock_scope(c+[c[0]], f)
    assert result["pairs"][0]["scalar_units_per_displayed_clock_second"] == 10
    assert not result["elapsed_time_resolved"]
    f[0]["feedback"]["weaponID"] = 2
    with pytest.raises(ValueError, match="unmatched"): clock_scope(c, f)
