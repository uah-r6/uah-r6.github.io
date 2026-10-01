"""Exercise the admin rehost preview with real folders and a temporary database.

The configured SQLite is opened read-only to copy active roster identities.
This script never calls an import endpoint or writes to the configured database.
"""
import argparse
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from r6stats.admin.server import create_app
from r6stats.db import repository as repo


def main(folder_names: list[str], exclusions: list[dict]):
    settings = json.loads((ROOT / "config/settings.json").read_text(encoding="utf-8"))
    replay_root = Path(settings["replays"]["path"])
    paths = [replay_root / name for name in folder_names]
    if any(not path.is_dir() for path in paths):
        raise ValueError("Every selected replay folder must exist.")
    live_path = ROOT / "data/r6stats.sqlite"
    with sqlite3.connect(live_path.resolve().as_uri() + "?mode=ro", uri=True) as live:
        live.row_factory = sqlite3.Row
        roster = list(live.execute("""SELECT username,display_name,profile_id FROM players
                                    WHERE tracked=1 ORDER BY id"""))
    with tempfile.TemporaryDirectory(prefix="r6-rehost-preview-") as directory:
        temporary_root = Path(directory)
        (temporary_root / "config").mkdir()
        (temporary_root / "config/settings.json").write_text(json.dumps(settings), encoding="utf-8")
        with closing(repo.connect(temporary_root / "data/r6stats.sqlite")) as db:
            repo.season_create(db, "Preview only")
            for player in roster:
                repo.roster_add(db, player["username"], player["display_name"])
                db.execute("UPDATE players SET profile_id=? WHERE username=?",
                           (player["profile_id"], player["username"]))
            db.commit()
        with TestClient(create_app(temporary_root)) as client:
            token = client.get("/api/admin/session").json()["token"]
            response = client.post("/api/admin/replays/rehost/preview",
                                   json={"segments": [{"path": str(path)} for path in paths],
                                         "exclusions": exclusions},
                                   headers={"X-R6-Admin-Token": token})
            if response.status_code != 200:
                raise ValueError(f"Admin preview failed: {response.status_code} {response.text}")
            result = response.json()
            print(json.dumps({"map": result["map"], "rounds": result["rounds"],
                              "score": result["score"], "our_team": result["our_team"],
                              "tracked_players": result["tracked_players"],
                              "roster_change_required": result["roster_change_required"],
                              "score_override_required": result["score_override_required"],
                              "segments": result["segments"],
                              "physical_rounds": [
                                  {"segment": row["segment"],
                                   "physical_number": row["physical_number"],
                                   "logical_number": row["logical_number"],
                                   "exclusion_reason": row["exclusion_reason"]}
                                  for row in result["physical_rounds"]]}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("folders", nargs="+", help="MatchReplay folder names in competitive order")
    parser.add_argument("--exclude", nargs=3, action="append", default=[],
                        metavar=("SEGMENT", "ROUND", "REASON"),
                        help="Exclude a physical round with a reason")
    args = parser.parse_args()
    main(args.folders, [{"segment": int(segment), "physical_number": int(round_number),
                        "reason": reason} for segment, round_number, reason in args.exclude])
