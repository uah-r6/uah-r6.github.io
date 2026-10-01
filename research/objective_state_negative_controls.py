"""Scan cached development rounds without public objectives for state toggles.

This is a read-only specificity check for a possible defuser-state property.
Public logs define the negative-control set but never supply parser features.
The reserved final Rating event is not included.
"""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import subprocess
import tempfile

from objective_transition_probe import (DEVELOPMENT_MATCHES, PARSER, ROOT,
                                        replay_file, state_events)


def negative_rounds() -> list[tuple[int, int]]:
    result = []
    for match_id in DEVELOPMENT_MATCHES:
        path = ROOT / "data/research/diagnostics" / f"objective-timer-{match_id}.jsonl"
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            row = json.loads(line)
            if not row["public_objectives"]:
                result.append((match_id, row["round"]))
    return result


def audit(match_id: int, round_number: int) -> dict:
    cache = (ROOT / "data/research/diagnostics/objective-state-controls" /
             f"{match_id}-R{round_number:02d}.json")
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    rec, diagnostic = replay_file(match_id, round_number)
    with tempfile.TemporaryDirectory() as directory:
        dump = Path(directory) / "round.dump"
        subprocess.run([str(PARSER), "--dump", "-o", str(dump), str(rec)],
                       check=True, capture_output=True, text=True)
        events = state_events(dump.read_bytes())
    result = {"match_id": match_id, "round": round_number,
              "physical_file": rec.name, "public_objectives": diagnostic["public_objectives"],
              "state_events": events}
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(result), encoding="utf-8")
    return result


def main() -> None:
    controls = negative_rounds()
    counts = Counter()
    for match_id, number in controls:
        row = audit(match_id, number)
        values = tuple(event["value"] for event in row["state_events"])
        counts[values] += 1
        if values:
            print(match_id, f"R{number:02d}", "state_values", values, flush=True)
    print("NEGATIVE_CONTROL_ROUNDS", len(controls), "STATE_VALUE_PATTERNS",
          dict((str(key), count) for key, count in counts.items()))


if __name__ == "__main__":
    main()
