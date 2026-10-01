"""Inspect possible defuser-state packets in private UAH archives read-only.

Stored objective rows are shown as historical context only. This does not
credit any actor, reparse into SQLite, or regenerate public website data.
"""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import sqlite3
import subprocess
import tempfile

from objective_transition_probe import PARSER, ROOT, state_events


def main() -> None:
    database = ROOT / "data/r6stats.sqlite"
    with sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True) as db:
        maps = db.execute("""SELECT m.id,se.slug,m.map_name FROM maps m
            JOIN series s ON s.id=m.series_id JOIN seasons se ON se.id=s.season_id
            WHERE s.demo=0 ORDER BY m.map_name""").fetchall()
        old = {(map_id, number): [] for map_id, _, _ in maps for number in range(1, 31)}
        for map_id, number, kind in db.execute("""SELECT rd.map_id,rd.number,o.kind
            FROM objective_events o JOIN rounds rd ON rd.id=o.round_id"""):
            old[(map_id, number)].append(kind)
    counts = Counter()
    for map_id, season, name in maps:
        archive = ROOT / "data/replay-archive" / season / map_id
        manifest = json.loads((archive / "manifest.json").read_text(encoding="utf-8"))
        files = [archive / item["filename"] for item in manifest["files"]]
        with tempfile.TemporaryDirectory() as directory:
            dumped = Path(directory) / "round.dump"
            for number, rec in enumerate(files, start=1):
                subprocess.run([str(PARSER), "--dump", "-o", str(dumped), str(rec)],
                               check=True, capture_output=True, text=True)
                events = state_events(dumped.read_bytes())
                values = tuple(event["value"] for event in events)
                counts[values] += 1
                historical = old[(map_id, number)]
                if values or historical:
                    print(map_id, name, f"R{number:02d}", "state_values", values,
                          "stored_objective_rows", historical, flush=True)
    print("MAPS", len(maps), "STATE_VALUE_PATTERNS",
          dict((str(key), count) for key, count in counts.items()))


if __name__ == "__main__":
    main()
