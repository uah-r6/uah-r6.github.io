"""Read-only actor-candidate audit for cached development timer diagnostics.

The public objective actor is used solely to evaluate candidates. No candidate
is written to the parser, normalized replay, SQLite, or Rating dataset.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIAGNOSTICS = ROOT / "data/research/diagnostics"
DEVELOPMENT = (4150, 4132, 3585, 6156)


def actor(description: str) -> str:
    return description.split(" plants ")[0].split(" disables ")[0].strip().casefold()


def audit(match_ids: tuple[int, ...] = DEVELOPMENT) -> list[dict]:
    output = []
    for match_id in match_ids:
        path = DIAGNOSTICS / f"objective-timer-{match_id}.jsonl"
        content = path.read_bytes()
        encoding = "utf-16" if content.startswith((b"\xff\xfe", b"\xfe\xff")) else "utf-8-sig"
        for line in content.decode(encoding).splitlines():
            row = json.loads(line)
            completions = [run for run in row["timer_runs"] if run["min"] <= .10]
            public = row["public_objectives"]
            if len(completions) != len(public):
                raise ValueError(f"Completion count disagreement: {match_id} R{row['round']}")
            for index, (run, objective) in enumerate(zip(completions, public), start=1):
                expected = actor(objective["description"])
                candidates = [{"name": event["player"], "delta": event["delta"],
                               "distance": event["offset"] - run["last_offset"],
                               "entity_delta": event["entity_delta"],
                               "near_kill_count_offsets": [kill["offset"] - event["offset"]
                                   for kill in run.get("near_completion_killcount_increases", [])
                                   if kill["player"] == event["player"] and
                                   abs(kill["offset"] - event["offset"]) <= 3000],
                               "match": event["player"].casefold().split(".")[0] == expected.split(".")[0]}
                              for event in run.get("near_completion_score_increases", [])
                              if event["delta"] == 100]
                output.append({"match": match_id, "round": row["round"], "event": index,
                               "type": objective["type"], "public_actor": expected,
                               "candidates": candidates})
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("match_ids", nargs="*", type=int, default=DEVELOPMENT)
    args = parser.parse_args()
    rows = audit(tuple(args.match_ids))
    unique = [r for r in rows if len(r["candidates"]) == 1]
    correct = [r for r in unique if r["candidates"][0]["match"]]
    absent = [r for r in rows if not r["candidates"]]
    print(f"objective_events={len(rows)} unique_plus100={len(unique)} "
          f"unique_matches_public={len(correct)} no_plus100={len(absent)}")
    print("unique_with_near_kill_counter", sum(bool(r["candidates"][0]["near_kill_count_offsets"])
                                               for r in unique))
    delta4 = [r for r in rows if len([c for c in r["candidates"] if c["entity_delta"] == 4]) == 1]
    print("unique_delta4", len(delta4), "exact_public_matches",
          sum(next(c for c in r["candidates"] if c["entity_delta"] == 4)["match"] for r in delta4))
    for row in rows:
        print(json.dumps(row, ensure_ascii=False))


if __name__ == "__main__":
    main()
