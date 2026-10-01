"""Read-only search for player IDs near completed defuser timer packets."""
from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from collections import Counter
from pathlib import Path

from objective_timer_audit import packets, ROOT

DIAGNOSTICS = ROOT / "data/research/diagnostics"
PARSER = ROOT / ".local-tools/bin/siege-dissect.exe"


def packet_runs(entries):
    groups = []
    current = []
    for entry in entries:
        if current and (entry["timer"] > current[-1]["timer"] + .5 or
                        entry["offset"] - current[-1]["offset"] > 100000):
            groups.append(current)
            current = []
        current.append(entry)
    if current:
        groups.append(current)
    return groups


def main(match_ids):
    distributions = Counter()
    nearby_entity = Counter()
    nearby_correct = Counter()
    nearby_wrong = Counter()
    for match_id in match_ids:
        rows = [json.loads(line) for line in
                (DIAGNOSTICS / f"objective-timer-{match_id}.jsonl").read_text(encoding="utf-8-sig").splitlines()]
        identities = json.loads((DIAGNOSTICS / f"defuser-ids-{match_id}.json").read_text(encoding="utf-8-sig"))
        for row in rows:
            if not row["public_objectives"]:
                continue
            name = row["physical_file"]
            candidates = list((ROOT / "data/research/extracted").rglob(name))
            if len(candidates) != 1:
                raise ValueError(f"Expected one cached replay for {name}: {len(candidates)}")
            with tempfile.TemporaryDirectory() as temporary:
                dump = Path(temporary) / "round.dump"
                subprocess.run([str(PARSER), "--dump", "-o", str(dump), str(candidates[0])],
                               check=True, capture_output=True, text=True)
                data = dump.read_bytes()
            completed = [run for run in packet_runs(packets(data)) if min(p["timer"] for p in run) <= .1]
            for number, run in enumerate(completed, start=1):
                terminal = run[-1]["offset"]
                expected = row["public_objectives"][number - 1]["description"].split(" ")[0].casefold()
                hits = []
                player_numbers = {player: int.from_bytes(bytes.fromhex(hex_id), "little")
                                  for player, hex_id in identities[name].items() if hex_id}
                for player, hex_id in identities[name].items():
                    player_id = bytes.fromhex(hex_id)
                    if player_id == bytes(4):
                        continue
                    for offset in range(-32, 160):
                        if data[terminal + offset:terminal + offset + 4] == player_id:
                            hits.append((offset, player))
                            distributions[offset] += 1
                for offset in range(-32, 160):
                    value = int.from_bytes(data[terminal + offset:terminal + offset + 4], "little")
                    matches = sorted((pid - value, player) for player, pid in player_numbers.items()
                                     if 0 <= pid - value <= 64)
                    if not matches:
                        continue
                    delta, player = matches[0]
                    nearby_entity[offset] += 1
                    base = player.casefold().split(".")[0]
                    if base == expected or base.startswith(expected):
                        nearby_correct[offset] += 1
                    else:
                        nearby_wrong[offset] += 1
                print(json.dumps({"match": match_id, "round": row["round"], "event": number,
                                  "public": row["public_objectives"][number - 1]["description"],
                                  "hits": hits}, ensure_ascii=False))
    print("repeated_offsets", distributions.most_common(25))
    print("entity_offset_candidates", sorted(
        ((offset, count, nearby_correct[offset], nearby_wrong[offset])
         for offset, count in nearby_entity.items() if count >= 3),
        key=lambda item: (-item[2], item[3], -item[1]))[:30])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("match_ids", nargs="+", type=int)
    args = parser.parse_args()
    main(args.match_ids)
