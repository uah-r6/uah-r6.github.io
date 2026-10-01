"""Validate defuser progress hypotheses against cached development round logs.

This is a read-only diagnostic. It never credits a plant or disable to a player,
and thresholds here do not become parser rules.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIAGNOSTICS = ROOT / "data/research/diagnostics"
MATCHES = (4150, 4132, 3585, 6156)
THRESHOLDS = (0.01, 0.05, 0.1, 0.2)


def main(match_ids: tuple[int, ...] = MATCHES) -> None:
    rows = []
    for match_id in match_ids:
        path = DIAGNOSTICS / f"objective-timer-{match_id}.jsonl"
        content = path.read_bytes()
        encoding = "utf-16" if content.startswith((b"\xff\xfe", b"\xfe\xff")) else "utf-8-sig"
        for line in content.decode(encoding).splitlines():
            row = json.loads(line)
            minimum = min((run["min"] for run in row["timer_runs"]), default=None)
            rows.append({"match": match_id, "round": row["round"],
                         "public": [item["type"] for item in row["public_objectives"]],
                         "min_timer": minimum,
                         "near_zero_runs": sum(run["min"] <= 0.1 for run in row["timer_runs"])})
    print(f"Audited {len(rows)} development rounds; "
          f"{sum(bool(row['public']) for row in rows)} with public objectives; "
          f"{sum(len(row['public']) for row in rows)} public completion events")
    count_mismatches = [f"{row['match']}:R{row['round']:02d}" for row in rows
                        if row["near_zero_runs"] != len(row["public"])]
    print(f"0.10-second run count mismatches: {count_mismatches}")
    for threshold in THRESHOLDS:
        false_positive = [f"{row['match']}:R{row['round']:02d}" for row in rows
                          if row["min_timer"] is not None and
                          row["min_timer"] <= threshold and not row["public"]]
        false_negative = [f"{row['match']}:R{row['round']:02d}" for row in rows
                          if row["public"] and (row["min_timer"] is None or
                                                row["min_timer"] > threshold)]
        print(f"threshold <= {threshold:.2f}: false positive {len(false_positive)} "
              f"{false_positive}; false negative {len(false_negative)} {false_negative}")
    print("Objective rounds:")
    for row in rows:
        if row["public"]:
            print(row)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("match_ids", nargs="*", type=int, default=MATCHES)
    arguments = parser.parse_args()
    main(tuple(arguments.match_ids))
