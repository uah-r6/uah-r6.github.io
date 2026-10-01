"""Read-only baseline of stored local objective credits before parser repair."""
import sqlite3
import argparse
from collections import Counter
from pathlib import Path

DATABASE = Path(__file__).resolve().parents[1] / "data/r6stats.sqlite"


def main(reparse: bool = False):
    db = sqlite3.connect(DATABASE.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        rows = db.execute("""SELECT m.id,m.map_name,rd.number,o.kind,o.player_key,
                   rp.username,rp.side,rp.team,o.team
                   FROM objective_events o JOIN rounds rd ON rd.id=o.round_id
                   JOIN maps m ON m.id=rd.map_id
                   LEFT JOIN round_players rp ON rp.round_id=rd.id AND rp.player_key=o.player_key
                   ORDER BY m.map_name,rd.number,o.sequence""").fetchall()
        print("maps", db.execute("SELECT count(*) FROM maps").fetchone()[0])
        print("stored_objectives", len(rows))
        print("role_impossible", sum((kind == "plant" and side != "Attack") or
                                     (kind == "disable" and side != "Defense")
                                     for _, _, _, kind, _, _, side, _, _ in rows))
        for map_id, map_name, round_number, kind, key, username, side, player_team, event_team in rows:
            print(map_id, map_name, f"R{round_number:02d}", kind, username or key,
                  side, "team_match" if player_team == event_team else "team_mismatch")
        if reparse:
            from r6stats.parser.siege_dissect import parse_match
            counts = Counter()
            for map_id, season_slug in db.execute("""SELECT m.id,se.slug FROM maps m
                JOIN series s ON s.id=m.series_id JOIN seasons se ON se.id=s.season_id
                WHERE s.demo=0"""):
                archive = DATABASE.parent / "replay-archive" / season_slug / map_id
                match = parse_match(archive)
                for round_ in match.rounds:
                    counts[map_id] += len(round_.objectives)
            print("verified_objectives_after_readonly_reparse", sum(counts.values()))
            print("by_map", dict(counts))
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--reparse", action="store_true")
    args = parser.parse_args()
    main(args.reparse)
