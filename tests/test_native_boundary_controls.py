from copy import deepcopy
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research"))
from credited_native_boundary_controls import compare, SOURCE
from r6stats.kill_credit import validate_map_credit


def observations():
    feedback = {"type": {"name": "Death"}, "username": "Victim", "target": "", "time": "1:11", "timeInSeconds": 71}
    old = {"header": {"players": [{"operator": "Twitch"}], "actionPhaseDetected": True},
           "credit": {"complete": False, "reason": "unknown_finish_offset", "players": [],
                      "finishes": [{"offset": 0, "feedback": feedback}]}}
    new = {"header": deepcopy(old["header"]), "originalFinishes": deepcopy(old["credit"]["finishes"]),
           "credit": {"source": SOURCE, "complete": True, "reason": SOURCE, "players": [],
                      "finishes": [{"offset": 100, "feedback": deepcopy(feedback)}]},
           "nativeEnvelopes": [{"feedbackIndex": 0, "startOffset": 100, "endOffset": 173,
                                "legacyOffset": 0, "markerValid": True, "feedback": deepcopy(feedback)}]}
    return new, old


def test_exact_envelope_recovery_preserves_original():
    new, old = observations()
    before = deepcopy(old)
    result = compare(new, old)
    assert result["recovered"] == [{"victim": "Victim", "offset": 100, "end": 173}]
    assert old == before


@pytest.mark.parametrize("problem", ["header", "victim", "duplicate", "marker", "known_offset", "counter"])
def test_boundary_controls_refuse_unrelated_changes(problem):
    new, old = observations()
    if problem == "header": new["header"]["players"][0]["operator"] = "Deimos"
    if problem == "victim": new["credit"]["finishes"][0]["feedback"]["username"] = "Other"
    if problem == "duplicate": new["nativeEnvelopes"].append(deepcopy(new["nativeEnvelopes"][0]))
    if problem == "marker": new["nativeEnvelopes"][0]["markerValid"] = False
    if problem == "known_offset":
        old["credit"]["finishes"][0]["offset"] = 80
        new["originalFinishes"][0]["offset"] = 80
    if problem == "counter":
        old["credit"].update(complete=True, players=[{"kills": 2}])
        new["credit"]["players"] = [{"kills": 3}]
    with pytest.raises(ValueError): compare(new, old)


def test_native_source_still_excluded_from_production_credit_projection():
    new, _ = observations()
    with pytest.raises(ValueError, match="Unsupported credited-kill evidence source"):
        validate_map_credit([{"credit": new["credit"], "logical_round": 1, "physical_round": 1, "segment": "test"}])
