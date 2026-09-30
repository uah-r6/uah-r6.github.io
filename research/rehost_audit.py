"""Read-only physical-round audit of cached professional rehost candidates.

Usage: python research/rehost_audit.py UBISOFT_MATCH_ID [...]
Raw parser JSON and compact evidence remain in ignored data/research/diagnostics/.
No logical rounds are inferred or admitted to the rating dataset here.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/research"
PARSER = ROOT / ".local-tools/bin/siege-dissect.exe"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def event_type(event: dict) -> str:
    value = event.get("type") or ""
    return str(value.get("name", "")) if isinstance(value, dict) else str(value)


def inspect_segment(folder: Path, number: int, destination: Path) -> dict:
    files = sorted(folder.glob("*.rec"))
    if not files:
        raise ValueError(f"No physical .rec rounds in {folder}")
    raw_path = destination / f"segment-{number:02d}-raw.json"
    process = subprocess.run([str(PARSER), str(folder), "-o", str(raw_path)],
                             capture_output=True, text=True)
    if process.returncode:
        return {"folder": folder.name, "source": str(folder), "parser_error":
                (process.stderr or process.stdout)[-2000:]}
    parsed = json.loads(raw_path.read_text(encoding="utf-8"))
    if len(parsed["rounds"]) != len(files):
        raise ValueError(f"Physical/raw round mismatch in {folder}")
    rounds = []
    for rec, row in zip(files, parsed["rounds"]):
        teams = row["teams"]
        winners = [team["name"] for team in teams if team.get("won")]
        feedback = row.get("matchFeedback") or []
        kills = [event for event in feedback if event_type(event) == "Kill"]
        objectives = [event for event in feedback if event_type(event).startswith("Defuser")]
        players = [{"username": p["username"], "profile_id": p.get("profileID"),
                    "team": teams[p["teamIndex"]]["name"],
                    "operator": (p.get("operator") or {}).get("name")
                                if isinstance(p.get("operator"), dict) else p.get("operator"),
                    "operator_source": p.get("operatorSource")}
                   for p in row["players"]]
        rounds.append({"physical_file": rec.name, "file_size": rec.stat().st_size,
                       "sha256": sha256(rec), "timestamp": row.get("timestamp"),
                       "replay_id": row.get("matchID"),
                       "parser_round_number": row.get("roundNumber"),
                       "site": row.get("site"), "winner": winners,
                       "teams": [{key: team.get(key) for key in
                                  ("name", "startingScore", "score", "won", "role", "winCondition")}
                                 for team in teams],
                       "players": players,
                       "kills": [{"killer": event.get("username"),
                                  "victim": event.get("target"),
                                  "time": event.get("timeInSeconds")}
                                 for event in kills],
                       "opening_event": {"killer": kills[0].get("username"),
                                         "victim": kills[0].get("target")}
                                        if kills else None,
                       "objectives": [{"type": event_type(event),
                                       "player": event.get("username"),
                                       "time": event.get("timeInSeconds")}
                                      for event in objectives]})
    return {"folder": folder.name, "source": str(folder), "rounds": rounds}


def audit(match_id: int) -> dict:
    report = json.loads((DATA / "diagnostics" / f"candidate-{match_id}.json").read_text())
    extraction = DATA / "extracted" / report["extraction_label"]
    target_id = report["siegegg_match_id"]
    meta = json.loads((DATA / "targets" / f"siegegg-match-{target_id}-api.json").read_text())
    stats = json.loads((DATA / "targets" / f"siegegg-match-{target_id}-player-stats.json").read_text())
    game = meta["games"][0]
    game_id = str(game["id"])
    destination = DATA / "diagnostics" / "rehost" / str(match_id)
    destination.mkdir(parents=True, exist_ok=True)
    folders = [next(extraction.rglob(name)) for name in report["replay_folders"]]
    segments = [inspect_segment(folder, index, destination)
                for index, folder in enumerate(folders, start=1)]
    result = {"official": report["official"], "siegegg_match_id": target_id,
              "public_game": {"id": game["id"], "map": game["map"]["name"],
                              "win_roster_id": game["win_roster_id"],
                              "loss_roster_id": game["loss_roster_id"],
                              "win_score": game["win_score"],
                              "loss_score": game["loss_score"]},
              "public_players": [{"player_id": p["id"], "ign": p["ign"],
                                  "roster_id": p["roster_id"],
                                  "kd": stats[game_id][str(p["id"])]["kd"]}
                                 for p in meta["players"] if str(p["id"]) in stats[game_id]],
              "segments": segments}
    path = destination / "audit.json"
    path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(match_id, report["official"]["teams"],
          game["map"]["name"], f"public {game['win_score']}-{game['loss_score']}")
    for segment in segments:
        if "parser_error" in segment:
            print(" ", segment["folder"], "PARSER ERROR", segment["parser_error"][-150:])
            continue
        print(" ", segment["folder"], "physical rounds", len(segment["rounds"]),
              "winners", dict(Counter(r["winner"][0] for r in segment["rounds"])),
              "score states", [(r["teams"][0]["startingScore"], r["teams"][0]["score"],
                                r["teams"][1]["startingScore"], r["teams"][1]["score"])
                               for r in segment["rounds"]])
    print("  evidence", path)
    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("Usage: rehost_audit.py UBISOFT_MATCH_ID [...]")
    for value in sys.argv[1:]:
        audit(int(value))
