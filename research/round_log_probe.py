"""Compare public round multikill notes with cached normalized replay rounds.

This is a diagnostic. SiegeGG's round notes are incomplete and are not used to
rewrite player kills or admit a row through the quality gate.
"""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from r6stats.parser.models import Match  # noqa: E402
from r6stats.stats.calculate import calculate_match  # noqa: E402

DATA = ROOT / "data/research"
SOURCES = json.loads((ROOT / "research/sources.json").read_text(encoding="utf-8"))["matches"]


def norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.casefold())


def analyze() -> dict:
    compared = 0
    disagreements = []
    aligned_rounds = 0
    unaligned_rounds = 0
    for source in SOURCES:
        meta = json.loads((DATA / "targets" /
                           f"siegegg-match-{source['siegegg_match_id']}-api.json").read_text())
        player_rosters = {player["id"]: player["roster_id"] for player in meta["players"]}
        for mapping in source["maps"]:
            game = next(g for g in meta["games"] if g["id"] == mapping["siegegg_game_id"])
            match = Match.from_dict(json.loads((DATA / "derived" /
                                               f"{mapping['folder']}.json").read_text()))
            if len(game["rounds"]) != len(match.rounds):
                continue
            for round_, public_round in zip(match.rounds, game["rounds"]):
                winner = next(p for p in round_.players if p.team == round_.winner)
                winner_roster = player_rosters[source["players"][winner.username]]
                public_winner = (public_round["def_roster_id"] if public_round["def_win"]
                                 else public_round["atk_roster_id"])
                if winner_roster != public_winner:
                    unaligned_rounds += 1
                    continue
                aligned_rounds += 1
                stats = calculate_match(Match(match.replay_id, match.timestamp,
                                              match.map_name, match.match_type,
                                              match.game_mode, [round_]))
                for event in public_round["events"]:
                    if event["type"] != "multikill":
                        continue
                    operator = re.search(r'alt="([^"]+)"', event["html"])
                    count = re.search(r"gets a (\d)k\b", event["html"])
                    if not operator or not count:
                        continue
                    players = [p for p in round_.players if norm(p.operator) == norm(operator[1])]
                    if len(players) != 1:
                        continue
                    player = players[0]
                    replay_kills = stats[player.key]["kills"]
                    public_kills = int(count[1])
                    compared += 1
                    if replay_kills != public_kills:
                        disagreements.append({"event": source["event"], "map": match.map_name,
                                              "folder": mapping["folder"],
                                              "round": round_.number, "player": player.username,
                                              "operator": player.operator,
                                              "replay_kills": replay_kills,
                                              "public_multikill_note": public_kills})
    return {"aligned_rounds": aligned_rounds, "unaligned_rounds": unaligned_rounds,
            "compared_notes": compared, "disagreements": disagreements}


def main() -> None:
    result = analyze()
    print(f"Round winner alignment: {result['aligned_rounds']} aligned, "
          f"{result['unaligned_rounds']} unaligned")
    print(f"Compared {result['compared_notes']} public multikill notes by unique round operator; "
          f"{len(result['disagreements'])} disagree with replay-derived round kills")
    for row in result["disagreements"]:
        print(json.dumps(row))


if __name__ == "__main__":
    main()
