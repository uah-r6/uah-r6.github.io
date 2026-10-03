from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research"))
from credited_late_history_body_controls import interval


def anchors():
    c = [{"opaque_scalar": s, "first": {"username": "a"}, "second": {"username": f"v{i}"},
          "weapon_id": 1, "headshot": False} for i,s in enumerate((100, 200))]
    f = [{"offset": o, "feedback": {"username": "a", "target": f"v{i}", "weaponID": 1}}
         for i,o in enumerate((1000, 3000))]
    return c,f


def test_independent_finisher_anchors_bound_scalar_without_interpolation():
    c,f = anchors()
    assert interval({"opaque_scalar": 150}, c,f, 100) == {"lower_feed_offset": 1000, "upper_feed_offset": 3000}
    assert interval({"opaque_scalar": 50}, c,f, 100)["lower_feed_offset"] == 100
    assert interval({"opaque_scalar": 200}, c,f, 100) is None


def test_unmatched_anchor_refused_instead_of_nearest_event_join():
    c,f = anchors(); f[0]["feedback"]["weaponID"] = 2
    with pytest.raises(ValueError, match="Anchor"): interval({"opaque_scalar": 150}, c,f, 100)
