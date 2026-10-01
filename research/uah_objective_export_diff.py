"""Compare current public JSON with a recalculation from a read-only DB backup.

Never opens the real SQLite for writing and never replaces public website data.
"""
import json
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path

from r6stats.admin.server import read_settings
from r6stats.db import repository as repo
from r6stats.export import export

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/r6stats.sqlite"
PUBLIC = ROOT / "web/public/data"
FIELDS = ("plants", "disables", "kost_rounds", "kost", "rating")


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    with tempfile.TemporaryDirectory() as temporary:
        directory = Path(temporary)
        copied = directory / "stats.sqlite"
        with closing(sqlite3.connect(SOURCE.resolve().as_uri() + "?mode=ro", uri=True)) as source:
            with closing(sqlite3.connect(copied)) as destination:
                source.backup(destination)
        with closing(repo.connect(copied)) as db:
            expected_maps = {row[0] for row in db.execute("SELECT id FROM maps")}
            current_maps = {p.stem for p in (PUBLIC / "matches").glob("*.json")}
            if expected_maps != current_maps:
                raise ValueError("Public JSON map IDs differ from the live database; baseline is stale.")
            generated = directory / "generated"
            export(db, read_settings(ROOT), generated)
            for map_id in sorted(expected_maps):
                before = {p["slug"]: p for p in read(PUBLIC / "matches" / f"{map_id}.json")["players"]}
                after = {p["slug"]: p for p in read(generated / "matches" / f"{map_id}.json")["players"]}
                for slug in sorted(before):
                    changes = {field: (before[slug][field], after[slug][field]) for field in FIELDS
                               if before[slug][field] != after[slug][field]}
                    if changes:
                        print("map", map_id, slug, changes)
            for current in sorted((PUBLIC / "seasons").glob("*.json")):
                before = {p["slug"]: p for p in read(current)["players"]}
                after = {p["slug"]: p for p in read(generated / "seasons" / current.name)["players"]}
                for slug in sorted(before):
                    changes = {field: (before[slug][field], after[slug][field]) for field in FIELDS
                               if before[slug][field] != after[slug][field]}
                    if changes:
                        print("season", current.stem, slug, changes)


if __name__ == "__main__":
    main()
