"""Snapshot or compare current UAH operator usage without changing SQLite."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from r6stats.parser.siege_dissect import parse_match  # noqa: E402
BASELINE = ROOT / "data/research/diagnostics/uah-operator-baseline.json"


def usage():
    db = sqlite3.connect(ROOT / "data/r6stats.sqlite")
    db.row_factory = sqlite3.Row
    try:
        return [dict(row) for row in db.execute("""SELECT p.display_name,rp.side,rp.operator,
                    count(*) AS n FROM round_players rp JOIN players p ON p.id=rp.player_id
                    JOIN rounds r ON r.id=rp.round_id JOIN maps m ON m.id=r.map_id
                    JOIN series s ON s.id=m.series_id WHERE s.demo=0
                    GROUP BY p.display_name,rp.side,rp.operator
                    ORDER BY p.display_name,rp.side,rp.operator""")]
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("snapshot", "compare", "reparse-check"))
    args = parser.parse_args()
    rows = usage()
    if args.mode == "snapshot":
        BASELINE.parent.mkdir(parents=True, exist_ok=True)
        BASELINE.write_text(json.dumps(rows, indent=2), encoding="utf-8")
        print(f"Saved {len(rows)} operator rows to {BASELINE}")
    elif args.mode == "compare":
        expected = json.loads(BASELINE.read_text(encoding="utf-8"))
        if rows != expected:
            raise SystemExit("Stored UAH operator usage changed")
        print(f"Stored UAH operator usage unchanged: {len(rows)} rows")
    else:
        db = sqlite3.connect(ROOT / "data/r6stats.sqlite")
        db.row_factory = sqlite3.Row
        counts = Counter()
        try:
            for record in db.execute("""SELECT m.id,se.slug FROM maps m
                    JOIN series s ON s.id=m.series_id JOIN seasons se ON se.id=s.season_id
                    WHERE s.demo=0"""):
                identities = {row["player_key"]: row["display_name"] for row in db.execute("""SELECT DISTINCT
                    rp.player_key,p.display_name FROM round_players rp JOIN rounds r ON r.id=rp.round_id
                    JOIN players p ON p.id=rp.player_id WHERE r.map_id=?""", (record["id"],))}
                source = ROOT / "data/replay-archive" / record["slug"] / record["id"]
                match = parse_match(source)
                for round_ in match.rounds:
                    for player in round_.players:
                        if player.key in identities:
                            counts[identities[player.key], player.side, player.operator] += 1
        finally:
            db.close()
        reparsed = [{"display_name": name, "side": side, "operator": operator, "n": n}
                    for (name, side, operator), n in sorted(counts.items())]
        expected = json.loads(BASELINE.read_text(encoding="utf-8"))
        if reparsed != expected:
            missing = [x for x in expected if x not in reparsed]
            extra = [x for x in reparsed if x not in expected]
            raise SystemExit(f"Reparse changed UAH operator usage; old={missing}, new={extra}")
        print(f"Reparsed UAH operator usage unchanged: {len(reparsed)} rows")
