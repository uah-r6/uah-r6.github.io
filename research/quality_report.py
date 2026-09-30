"""Build a reproducible per-row audit of professional target mismatches."""
from __future__ import annotations

from collections import Counter, defaultdict
import json
from pathlib import Path
import re

from round_log_probe import analyze as analyze_round_logs

ROOT = Path(__file__).resolve().parents[1]
OBSERVATIONS = ROOT / "data/research/experiments/player_maps.jsonl"
OUTPUT = ROOT / "research/quality-report.md"


def main() -> None:
    rows = [json.loads(line) for line in OBSERVATIONS.read_text(encoding="utf-8").splitlines()]
    issues = Counter(issue for row in rows for issue in row["quality_issues"])
    kill_errors = death_errors = 0
    maps = defaultdict(list)
    for row in rows:
        target_k, target_d = map(int, re.match(r"(\d+)-(\d+)", row["public"]["kd"]).groups())
        kill_errors += row["derived"]["kills"] != target_k
        death_errors += row["derived"]["deaths"] != target_d
        maps[row["replay_folder"]].append((row, target_k, target_d))
    map_totals = [
        (group[0][0]["event"], group[0][0]["map"],
         sum(row["derived"]["kills"] for row, _, _ in group),
         sum(row["derived"]["deaths"] for row, _, _ in group),
         sum(k for _, k, _ in group), sum(d for _, _, d in group))
        for group in maps.values()]
    mismatched_maps = [item for item in map_totals if item[2:4] != item[4:6]]
    agreeing_maps = len(map_totals) - len(mismatched_maps)
    round_log = analyze_round_logs()
    reserved = Counter(row["event"] for row in rows
                       if row["reserved_for_final_test"] and row["fit_eligible"])
    reserved_summary = "; ".join(f"{event}: {count} clean rows" for event, count in reserved.items())
    lines = ["# Professional replay quality audit", "",
             f"{len(rows)} player-map rows from {len(maps)} maps; "
             f"{sum(row['fit_eligible'] for row in rows)} pass all gates. "
             f"Reserved rows by event: {reserved_summary}. "
             "Europe MENA Stage 2 was evaluated once and is historical; "
             "North America Stage 2 remains untouched for a new final test.", "",
             "| Cause | Rows | Treatment |", "| --- | ---: | --- |",
             f"| Replay/public per-player K/D mismatch | {issues['kills/deaths mismatch']} | Exclude |",
             f"| Unverified replay ↔ SiegeGG alias | {issues['player alias lacks independent identity confirmation']} | Exclude |",
             "| Map/team/score/round mismatch | 0 | Would reject entire map |", "",
             f"{kill_errors} rows have a kill discrepancy; {death_errors} have a death discrepancy. "
             f"{agreeing_maps} of {len(maps)} map-wide kill and death totals agree with public targets. "
             "The map-wide exceptions are listed below. The Europe MENA Chalet replay has one "
             "teamkill, but the evidence does not establish whether SiegeGG counted it as a kill. "
             "Most discrepancies are per-player attribution; map-wide differences remain excluded. "
             "A pilot probe found cumulative "
             "scoreboard kill packets, but the entity-to-player offset changes across builds and even maps; "
             "it is not yet safe to use those counters to rewrite replay kill events. "
             f"A separate read-only public round-log probe aligned "
             f"{round_log['aligned_rounds']} round winners "
             f"({round_log['unaligned_rounds']} unaligned) and compared "
             f"{round_log['compared_notes']} multikill notes by unique operator; "
             f"{len(round_log['disagreements'])} disagree with replay-derived round kills. "
             "The notes provide independent evidence of attribution differences, but are incomplete "
             "and cannot by themselves safely correct every kill. "
             "The two remaining aliases are `MARKELELE.SH` and `fenglixiaqiu`; their target identities "
             "lack independent profile confirmation. Other investigated aliases are backed by replay "
             "profile UUIDs and public username histories in `sources.json`.", "",
             "## Map-wide total differences", "",
             "| Event | Map | Replay K-D | Public K-D |", "| --- | --- | ---: | ---: |"]
    for event, map_name, replay_k, replay_d, public_k, public_d in mismatched_maps:
        lines.append(f"| {event} | {map_name} | {replay_k}-{replay_d} | {public_k}-{public_d} |")
    lines.extend(["",
             "## Excluded rows", "",
             "| Event | Map | Replay player | Replay K-D | Public K-D | Cause |",
             "| --- | --- | --- | ---: | ---: | --- |"])
    for row in rows:
        if row["fit_eligible"]:
            continue
        lines.append(f"| {row['event']} | {row['map']} | {row['player']} | "
                     f"{row['derived']['kills']}-{row['derived']['deaths']} | "
                     f"{row['public']['kd'].split(' ')[0]} | "
                     f"{'; '.join(row['quality_issues'])} |")
    lines.extend(["", "Quality gates were not relaxed to increase the fitting sample. "
                  "Public K/D may itself contain an attribution error in a given case; "
                  "the current evidence does not identify which side is correct for every row.", ""])
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUTPUT}; excluded {sum(not row['fit_eligible'] for row in rows)} rows")


if __name__ == "__main__":
    main()
