"""Compare exact-player scoreboard counters with replay feed and public K/D.

This opt-in diagnostic runs a Go test against cached professional replays. It
does not modify the tracker database or public website data.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/research"
SOURCES = json.loads((ROOT / "research/sources.json").read_text(encoding="utf-8"))["matches"]
GO = ROOT / ".local-tools/go/bin/go.exe"
DISSECT = ROOT / "third_party/siege-dissect"


def main() -> None:
    report = []
    for source in SOURCES:
        target = json.loads((DATA / "targets" / f"siegegg-match-{source['siegegg_match_id']}-player-stats.json").read_text())
        for mapping in source["maps"]:
            extraction = DATA / "extracted" / source.get("extraction_label", source["label"])
            folders = list(extraction.rglob(mapping["folder"]))
            if len(folders) != 1:
                raise ValueError(f"Ambiguous replay folder: {mapping['folder']}")
            output = DATA / "diagnostics" / f"scoreboard-{mapping['folder']}.json"
            env = dict(os.environ, R6_PRO_REPLAY_FOLDER=str(folders[0]),
                       R6_PRO_SCOREBOARD_OUTPUT=str(output))
            completed = subprocess.run(
                [str(GO), "test", "./dissect", "-run", "TestProfessionalScoreboardDiagnostic", "-count=1"],
                cwd=DISSECT, env=env, capture_output=True, text=True,
            )
            if completed.returncode:
                raise RuntimeError(completed.stdout[-4000:] + completed.stderr[-4000:])
            observed = json.loads(output.read_text())
            public_rows = target[str(mapping["siegegg_game_id"])]
            for username, player_id in source["players"].items():
                public_k, public_d = map(int, re.match(r"(\d+)-(\d+)", public_rows[str(player_id)]["kd"]).groups())
                report.append({"event": source["event"], "map": mapping["folder"],
                               "player": username, "feed_k": observed["feed"].get(username, 0),
                               "scoreboard_k": observed["scoreboard"].get(username, 0),
                               "public_k": public_k, "public_d": public_d})
            matching = sum(row["scoreboard_k"] == row["public_k"] for row in report[-10:])
            print(f"{mapping['folder']}: scoreboard/public kills match {matching}/10", flush=True)
    destination = DATA / "diagnostics/scoreboard-report.json"
    destination.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"All rows: scoreboard/public {sum(x['scoreboard_k'] == x['public_k'] for x in report)}/{len(report)}; "
          f"feed/public {sum(x['feed_k'] == x['public_k'] for x in report)}/{len(report)}")


if __name__ == "__main__":
    main()
