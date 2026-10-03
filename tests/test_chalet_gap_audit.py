from copy import deepcopy
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research"))
from credited_chalet_gap_audit import observed_routes


def evidence():
    return {"header": {"players": [{"id": 1, "username": "observed", "profileID": "profile"}]},
            "properties": [{"tag": 0xc845d4ee, "size": 8, "bits": 1, "entity": 10, "offset": 1},
                           {"tag": 0x9db1d21c, "size": 4, "bits": 0, "entity": 20, "offset": 3},
                           {"tag": 0x9db1d21c, "size": 4, "bits": 2, "entity": 20, "offset": 5}],
            "declarations": [{"owner": 10, "slot": 0x389b21eb, "component": 20, "class": 0xa191a518, "offset": 2}]}


def test_missing_roster_never_admitted_even_with_observed_counter_route():
    e = evidence(); before = deepcopy(e)
    result = observed_routes(e)
    assert len(result) == 1 and result[0]["observed_delta"] == 2
    assert result[0]["production_admission"] is False and e == before


def test_shared_unknown_class_wrong_width_and_uid_ambiguity_refuse_route():
    for mutation in ("shared", "class", "width", "uid"):
        e = evidence()
        if mutation == "shared": e["declarations"].append({**e["declarations"][0], "owner": 11})
        if mutation == "class": e["declarations"][0]["class"] = 1
        if mutation == "width":
            for p in e["properties"][1:]: p["size"] = 8
        if mutation == "uid": e["properties"].append({**e["properties"][0], "entity": 11})
        result = observed_routes(e)[0]
        assert result["observed_delta"] is None and result["production_admission"] is False
