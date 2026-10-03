from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"research"))
from credited_late_history_development import analyze, interleave, immutable_write


def test_fixed_interleaving_preserves_pool_and_each_cohort_order():
    rows = [{"event": e, "replay_sha256": str(i)} for i, e in enumerate(["SAL", "SAL", "APAC", "APAC", "APAC"])]
    assert [r["replay_sha256"] for r in interleave(rows)] == ["0", "2", "1", "3", "4"]
    with pytest.raises(ValueError):
        interleave(rows+[rows[0]])


def test_missing_event_history_never_passes_from_zero_counts():
    finish = {"offset": 9, "feedback": {"type": {"name": "Kill"}, "username": "A", "target": "B", "weaponID": 3}}
    observation = {"credit": {"complete": True, "players": [{"uid": 1, "team": 0, "username": "A", "kills": 0}], "finishes": [finish]}}
    result = analyze([], observation)
    assert result["status"] == "quality_refused" and result["comparisons"] == []


def test_unknown_death_or_incomplete_counter_is_preserved_as_refusal():
    observation = {"credit": {"complete": False, "reason": "legacy zero offset", "players": [],
                               "finishes": [{"offset": 0, "feedback": {"type": {"name": "Death"}}}]}}
    result = analyze([], observation)
    assert len(result["quality_refusals"]) == 2 and result["comparisons"] == []
    assert "named Kill" in result["comparison"]["unresolved"]


def test_cached_failure_cannot_be_replaced_with_success(tmp_path):
    path = tmp_path/"result.json"
    immutable_write(path, {"status": "quality_refused"})
    immutable_write(path, {"status": "quality_refused"})
    with pytest.raises(ValueError):
        immutable_write(path, {"status": "counter_agreement"})
