"""Observed counter/score pairings in consumed validation replay rounds.

The result describes packet adjacency, not causal score attribution. Excludes
the objective packet neighborhood and does not read public actor labels.
"""
from collections import Counter, defaultdict
import json

from objective_production_check import candidate_raw
from objective_transition_probe import ROOT


def main():
    base = ROOT / "data/research/diagnostics/objective-score-delta-validation"
    occurrence = json.loads((ROOT / "data/research/diagnostics/objective-occurrence-holdout/summary.json").read_text())
    rows = [row for row in occurrence["results"] if row["result"]["plant"]]
    folders = {}
    totals = defaultdict(Counter)
    examples = defaultdict(list)
    for row in rows:
        folder_name, number = row["folder"], row["round"]
        if folder_name not in folders:
            folder = next((ROOT / "data/research/extracted").rglob(folder_name))
            folders[folder_name] = candidate_raw(folder)
        build = folders[folder_name]["rounds"][number - 1]["codeVersion"]
        saved = json.loads((base / f"{folder_name}-R{number:02d}.json").read_text())
        events = saved["ledger"]["events"]
        centers = [event["offset"] for event in row["events"] if event["value"] in (0, 1)]
        entities = defaultdict(list)
        for event in events:
            entities[event["entity"]].append(event)
        for entity, changes in entities.items():
            for counter in changes:
                if counter["counter"] not in ("kills", "assists") or counter["delta"] != 1:
                    continue
                if min(abs(counter["offset"] - center) for center in centers) <= 20000:
                    continue
                nearby = [event for event in changes if event is not counter
                          and event["counter"] in ("kills", "assists")
                          and abs(event["offset"] - counter["offset"]) <= 5000]
                scores = [event for event in changes if event["counter"] == "score"
                          and event["delta"] > 0
                          and 0 <= event["offset"] - counter["offset"] <= 5000]
                if nearby or len(scores) != 1:
                    continue
                score = scores[0]
                key = build, counter["counter"]
                totals[key][score["delta"]] += 1
                if len(examples[(key, score["delta"])]) < 2:
                    examples[(key, score["delta"])].append(
                        f"{row['match_id']}/{row['game_id']} R{number:02d}")
    lines = ["# Observed score-counter grammar by replay build", "",
             "Consumed 12-map actor-validation rounds only. Each entry is a single positive score packet within 5,000 decompressed bytes **after** one isolated kill or assist counter increment on the same score component, at least 20,000 bytes from every objective state transition. This is packet adjacency, not proof that the counter caused the entire score delta. Delayed or combined updates are excluded rather than assigned a fixed value.", "",
             "| Code version | Counter | Score delta counts | Example round(s) |",
             "| ---: | --- | --- | --- |"]
    for key, counts in sorted(totals.items()):
        listing = ", ".join(f"+{delta}: {count}" for delta, count in counts.most_common())
        sample = ", ".join(examples[(key, counts.most_common(1)[0][0])])
        lines.append(f"| {key[0]} | {key[1]} | {listing} | {sample} |")
    lines += ["", "The same counter type can be followed by different score deltas within a build. A universal kill=100 or assist=75 subtraction is unsupported. Pairing must also account for score packets that precede or batch with later game-state packets.", ""]
    path = ROOT / "research/output/objective-score-grammar.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    print(path)


if __name__ == "__main__":
    main()
