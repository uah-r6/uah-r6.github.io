"""Read-only score-wave control in a round with no objective occurrence."""
import json
from pathlib import Path
import subprocess
import tempfile

from objective_production_check import candidate_raw
from objective_score_identity import score_identity_candidates
from objective_score_ledger import ledger
from objective_transition_probe import PARSER, ROOT


def main():
    validation = json.loads((ROOT / "data/research/diagnostics/objective-score-delta-validation/summary.json").read_text())
    event = next(e for e in validation["events"] if e["match_id"] == 3563
                 and e["game_id"] == 6675 and e["round"] == 2)
    folder = next((ROOT / "data/research/extracted").rglob(event["folder"]))
    raw = candidate_raw(folder)["rounds"][3]
    if raw.get("objectiveOccurrences"):
        raise ValueError("Negative-control round has an objective occurrence")
    rec = next(folder.glob("*-R04.rec"))
    with tempfile.TemporaryDirectory() as temporary:
        dump = Path(temporary) / "round.dump"
        subprocess.run([str(PARSER), "--dump", "-o", str(dump), str(rec)],
                       check=True, capture_output=True)
        data = dump.read_bytes()
    events = ledger(data)["events"]
    identities = score_identity_candidates(data, raw["players"])["entity_names"]
    names = {int(k): value[0] for k, value in identities.items() if len(value) == 1}
    last = max(e["offset"] for e in events if e["counter"] == "score")
    rows = [{"distance_from_final_score_packet": e["offset"] - last,
             "player": names.get(e["entity"]), "counter": e["counter"],
             "delta": e["delta"]} for e in events
            if last - 8000 <= e["offset"] <= last and names.get(e["entity"]) in
            {"J9O", "Fultz", "njr", "kyno", "Nuers"}]
    print(json.dumps({"match_id": 3563, "game_id": 6675, "round": 4,
                      "build": raw["codeVersion"], "objective_occurrences": 0,
                      "rows": rows}, indent=2))


if __name__ == "__main__":
    main()
