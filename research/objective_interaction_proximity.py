"""Read-only probe for player references near defuser timer-run boundaries.

This does not infer an actor. Exact DissectID and entity-minus-four hits can
occur in unrelated nearby packets; compare their distributions across players.
"""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile

from objective_timer_audit import PARSER, ROOT


def audit(match_id: int, round_number: int, radius: int = 4096):
    sources = json.loads((ROOT / "research/sources.json").read_text(encoding="utf-8"))["matches"]
    source = next(row for row in sources if row.get("siegegg_match_id") == match_id)
    if len(source["maps"]) != 1:
        raise ValueError("Expected one physical map")
    folders = [p for p in (ROOT / "data/research/extracted").rglob(source["maps"][0]["folder"])
               if p.is_dir()]
    if len(folders) != 1:
        raise ValueError(f"Expected one cached replay folder: {len(folders)}")
    diagnostic = ROOT / "data/research/diagnostics" / f"objective-timer-{match_id}.jsonl"
    row = next(json.loads(line) for line in diagnostic.read_text(encoding="utf-8-sig").splitlines()
               if json.loads(line)["round"] == round_number)
    identities = json.loads((ROOT / "data/research/diagnostics" /
                             f"defuser-ids-{match_id}.json").read_text(encoding="utf-8-sig"))
    rec = folders[0] / row["physical_file"]
    with tempfile.TemporaryDirectory() as directory:
        dump = Path(directory) / "round.dump"
        subprocess.run([str(PARSER), "--dump", "-o", str(dump), str(rec)],
                       check=True, capture_output=True, text=True)
        data = dump.read_bytes()
    for run in row["timer_runs"]:
        if run["min"] > .10:
            continue
        print(match_id, f"R{round_number:02d}", row["public_objectives"],
              "timer", run["first"], "to", run["last"])
        for boundary in ("first_offset", "last_offset"):
            center = run[boundary]
            window = data[max(0, center - radius):center + radius]
            hits = []
            for name, encoded in identities[row["physical_file"]].items():
                value = int.from_bytes(bytes.fromhex(encoded), "little")
                for kind, number in (("id", value), ("entity", value - 4)):
                    pattern = number.to_bytes(4, "little")
                    offsets = []
                    start = 0
                    while (at := window.find(pattern, start)) >= 0:
                        offsets.append(at + max(0, center - radius) - center)
                        start = at + 1
                    if offsets:
                        hits.append((name, kind, len(offsets),
                                     min(offsets, key=abs)))
            print(" ", boundary, sorted(hits, key=lambda item: abs(item[3])))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("match_id", type=int)
    parser.add_argument("round_number", type=int)
    parser.add_argument("--radius", type=int, default=4096)
    args = parser.parse_args()
    audit(args.match_id, args.round_number, args.radius)
