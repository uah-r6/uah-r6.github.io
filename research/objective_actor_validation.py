"""Evaluate the frozen packet actor rule on separate development maps.

Read research/objective_actor_validation_plan.md before modifying this script.
Public actors are used only to grade the frozen replay-derived candidates.
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIAGNOSTICS = ROOT / "data/research/diagnostics"
VALIDATION_MATCHES = (3637, 4140, 4118)


def actor(text):
    return text.split(" plants ")[0].split(" disables ")[0].strip().casefold()


def evaluate(match_ids=VALIDATION_MATCHES):
    summary = {"rounds": 0, "objective_rounds": 0, "public_events": 0,
               "detected_events": 0, "named": 0, "exact": 0, "different_name": 0,
               "unresolved": 0}
    for match_id in match_ids:
        path = DIAGNOSTICS / f"objective-timer-{match_id}.jsonl"
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            row = json.loads(line)
            summary["rounds"] += 1
            public = row["public_objectives"]
            completed = [run for run in row["timer_runs"] if run["min"] <= .10]
            summary["objective_rounds"] += bool(public)
            summary["public_events"] += len(public)
            summary["detected_events"] += len(completed)
            if len(public) != len(completed):
                print("COUNT_MISMATCH", match_id, row["round"], len(public), len(completed))
            for index, run in enumerate(completed, start=1):
                if index > len(public):
                    continue
                names = sorted({event["player"] for event in
                    run.get("near_completion_score_increases", [])
                    if event["delta"] == 100 and event["entity_delta"] == 4 and
                    0 <= event["offset"] - run["last_offset"] <= 2000})
                expected = actor(public[index - 1]["description"])
                if len(names) == 1:
                    summary["named"] += 1
                    actual = names[0].split(".")[0].casefold()
                    exact = actual == expected
                    summary["exact" if exact else "different_name"] += 1
                    result = "EXACT" if exact else "REVIEW_NAME"
                else:
                    summary["unresolved"] += 1
                    result = "UNRESOLVED"
                print(match_id, f"R{row['round']:02d}", index, public[index - 1]["type"],
                      result, "public=" + expected, "candidate=" + (",".join(names) or "none"))
    print("SUMMARY", summary)
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("match_ids", nargs="*", type=int, default=VALIDATION_MATCHES)
    args = parser.parse_args()
    evaluate(tuple(args.match_ids))
