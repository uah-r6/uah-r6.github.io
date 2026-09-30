"""Reproducible, cached public replay and SiegeGG target collection.

Run from the repository root with `.venv/Scripts/python.exe research/pipeline.py all`.
Only source metadata and code belong in Git. Downloads, normalized rounds, and
player-map observations live in ignored data/research/.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote, urlparse
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from r6stats.parser.models import Match  # noqa: E402
from r6stats.parser.siege_dissect import parse_match, parser_executable  # noqa: E402
from r6stats.stats.calculate import calculate_match  # noqa: E402

DATA = ROOT / "data/research"
SOURCES = json.loads((ROOT / "research/sources.json").read_text(encoding="utf-8"))["matches"]
FINAL_TEST_RESERVATION = json.loads(
    (ROOT / "research/final-test-reservation.json").read_text(encoding="utf-8"))


def validate_source_reservation(sources: list[dict], reservation: dict) -> None:
    event = reservation["event"]
    missing = [source["label"] for source in sources if source["event"] == event
               and source.get("reserved_for_final_test") is not True]
    if missing:
        raise ValueError(f"Final-test event sources must be reserved: {', '.join(missing)}")


validate_source_reservation(SOURCES, FINAL_TEST_RESERVATION)


def cache_url(url: str, destination: Path) -> None:
    if destination.exists() and destination.stat().st_size:
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + ".partial")
    command = ["curl.exe", "--fail", "--location", "--retry", "3", "--continue-at", "-",
               "--output", str(temporary), url]
    subprocess.run(command, check=True)
    temporary.replace(destination)


def replay_zip(source: dict) -> Path:
    return DATA / "pro-replays" / unquote(Path(urlparse(source["archive_url"]).path).name)


def parser_hash() -> str:
    parser = parser_executable()
    if not parser:
        raise ValueError("Local siege-dissect binary is missing")
    digest = hashlib.sha256()
    with Path(parser).open("rb") as binary:
        for chunk in iter(lambda: binary.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect(source: dict, *, force: bool = False) -> None:
    archive = replay_zip(source)
    cache_url(source["archive_url"], archive)
    with zipfile.ZipFile(archive) as bundle:
        bad = bundle.testzip()
        if bad:
            raise ValueError(f"Corrupt ZIP member: {bad}")
        extraction = DATA / "extracted" / source.get("extraction_label", source["label"])
        extraction.mkdir(parents=True, exist_ok=True)
        for member in bundle.infolist():
            if member.is_dir():
                continue
            target = (extraction / member.filename).resolve()
            if not target.is_relative_to(extraction.resolve()):
                raise ValueError(f"Unsafe ZIP member: {member.filename}")
            if not target.exists() or target.stat().st_size != member.file_size:
                target.parent.mkdir(parents=True, exist_ok=True)
                with bundle.open(member) as input_file, target.open("wb") as output_file:
                    import shutil
                    shutil.copyfileobj(input_file, output_file)
    match_id = source["siegegg_match_id"]
    for suffix, endpoint in (("api", ""), ("player-stats", "/player-stats")):
        cache_url(f"https://siege.gg/api/stats/matches/{match_id}{endpoint}",
                  DATA / "targets" / f"siegegg-match-{match_id}-{suffix}.json")
    for mapping in source["maps"]:
        derived = DATA / "derived" / (mapping["folder"] + ".json")
        cache_record = DATA / "derived" / (mapping["folder"] + ".meta.json")
        folders = [path for path in extraction.rglob(mapping["folder"]) if path.is_dir()]
        if len(folders) != 1:
            raise ValueError(f"Expected one replay folder {mapping['folder']}, found {len(folders)}")
        source_files = sorted(folders[0].glob("*.rec"))
        signature = {"schema": 1, "parser_sha256": parser_hash(),
                     "replay_files": [{"name": path.name, "size": path.stat().st_size,
                                       "mtime_ns": path.stat().st_mtime_ns}
                                      for path in source_files]}
        if derived.exists() and cache_record.exists() and not force:
            try:
                if json.loads(cache_record.read_text(encoding="utf-8")) == signature:
                    continue
            except (OSError, json.JSONDecodeError):
                pass
        match = parse_match(folders[0])
        derived.parent.mkdir(parents=True, exist_ok=True)
        temporary = derived.with_name(derived.name + ".partial")
        temporary.write_text(json.dumps(match.to_dict(), indent=2), encoding="utf-8")
        temporary.replace(derived)
        cache_record.write_text(json.dumps(signature, indent=2), encoding="utf-8")


def score_by_roster(match: Match, first_round_player_ids: dict[str, int], player_to_roster: dict[int, int]):
    team_to_roster = {}
    for player in match.rounds[0].players:
        roster = player_to_roster[first_round_player_ids[player.username]]
        if player.team in team_to_roster and team_to_roster[player.team] != roster:
            raise ValueError("Mixed professional rosters on replay team")
        team_to_roster[player.team] = roster
    if len(team_to_roster) != 2:
        raise ValueError("Replay did not contain two complete teams")
    return Counter(team_to_roster[round_.winner] for round_ in match.rounds)


def canonical_map(name: str) -> str:
    result = re.sub(r"[^a-z0-9]", "", name.casefold())
    return "kafe" if result == "kafedostoyevsky" else result


def map_rows(source: dict, mapping: dict) -> list[dict]:
    match_id, game_id = source["siegegg_match_id"], mapping["siegegg_game_id"]
    match = Match.from_dict(json.loads((DATA / "derived" / (mapping["folder"] + ".json")).read_text()))
    meta = json.loads((DATA / "targets" / f"siegegg-match-{match_id}-api.json").read_text())
    targets = json.loads((DATA / "targets" / f"siegegg-match-{match_id}-player-stats.json").read_text())
    game = next(game for game in meta["games"] if game["id"] == game_id)
    if canonical_map(match.map_name) != canonical_map(game["map"]["name"]):
        raise ValueError(f"Map mismatch for {mapping['folder']}")
    player_ids = source["players"]
    usernames = {p.username for p in match.rounds[0].players}
    if usernames != set(player_ids):
        raise ValueError(f"Roster mismatch: missing {usernames - set(player_ids)}, extra {set(player_ids) - usernames}")
    player_to_roster = {p["id"]: p["roster_id"] for p in meta["players"]}
    scores = score_by_roster(match, player_ids, player_to_roster)
    official_scores = {game["win_roster_id"]: game["win_score"],
                       game["loss_roster_id"]: game["loss_score"]}
    if (any(scores[roster] != score for roster, score in official_scores.items()) or
            len(match.rounds) != sum(official_scores.values())):
        raise ValueError(f"Score/round mismatch: replay {scores}; SiegeGG {official_scores}")
    aggregate = calculate_match(match)
    # Keep round-level rows to permit alternate definitions without rerunning siege-dissect.
    per_round = [calculate_match(Match(match.replay_id, match.timestamp, match.map_name,
                                       match.match_type, match.game_mode, [round_]))
                 for round_ in match.rounds]
    rows = []
    for player in match.rounds[0].players:
        key, public = player.key, targets[str(game_id)][str(player_ids[player.username])]
        stats = aggregate[key]
        public_k, public_d = map(int, re.match(r"(\d+)-(\d+)", public["kd"]).groups())
        rounds = []
        for round_, round_stats in zip(match.rounds, per_round):
            participant = next(p for p in round_.players if p.key == key)
            row = round_stats[key]
            rounds.append({"number": round_.number, "operator": participant.operator,
                           "side": participant.side, "winner": participant.team == round_.winner,
                           **{name: row[name] for name in ("kills", "deaths", "teamkills", "opening_kills",
                               "opening_deaths", "clutches", "clutch_1v1", "clutch_1v2", "clutch_1v3",
                               "clutch_1v4", "clutch_1v5", "kost_rounds", "survived", "kills_traded",
                               "deaths_traded", "plants", "disables")}})
        issues = []
        if (stats["kills"], stats["deaths"]) != (public_k, public_d):
            issues.append("kills/deaths mismatch")
        if stats["rounds"] != public["rounds"]:
            issues.append("round count mismatch")
        if player.username in source.get("unverified_player_aliases", []):
            issues.append("player alias lacks independent identity confirmation")
        verified_alias = source.get("verified_player_aliases", {}).get(player.username)
        if verified_alias and (player.profile_id != verified_alias["replay_profile_id"] or
                               player_ids[player.username] != verified_alias["siegegg_player_id"]):
            issues.append("verified player alias identity does not match replay")
        # A missing operator weakens any operator-normalized model, but raw metrics remain usable.
        unresolved_ops = sum(round_["operator"] == "Unknown" for round_ in rounds)
        rows.append({"event": source["event"], "match_id": match_id, "game_id": game_id,
                     "reserved_for_final_test": source.get("reserved_for_final_test", False),
                     "replay_folder": mapping["folder"], "map": match.map_name,
                     "player": player.username, "player_id": player_ids[player.username],
                     "roster_id": player_to_roster[player_ids[player.username]],
                     "rating": float(public["rating"]), "public": public,
                     "derived": stats, "rounds": rounds, "unresolved_operator_rounds": unresolved_ops,
                     "quality_issues": issues, "fit_eligible": not issues})
    return rows


def derive() -> list[dict]:
    rows = [row for source in SOURCES for mapping in source["maps"]
            for row in map_rows(source, mapping)]
    destination = DATA / "experiments/player_maps.jsonl"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    print(f"{len(rows)} player-map rows, {sum(r['fit_eligible'] for r in rows)} exact K/D and rounds; "
          f"{sum(r['unresolved_operator_rounds'] for r in rows)} unresolved operator rounds")
    for source in SOURCES:
        subset = [r for r in rows if r["match_id"] == source["siegegg_match_id"]]
        print(f"  {source['label']}: {len(subset)} rows, "
              f"{sum(r['fit_eligible'] for r in subset)} eligible")
        for r in subset:
            if r["quality_issues"]:
                print(f"    {r['map']} {r['player']}: {', '.join(r['quality_issues'])}; "
                      f"derived {r['derived']['kills']}-{r['derived']['deaths']} "
                      f"public {r['public']['kd']}")
    return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("collect", "derive", "all"))
    parser.add_argument("--force", action="store_true", help="Reparse cached rounds")
    args = parser.parse_args()
    if args.command in ("collect", "all"):
        for source in SOURCES:
            collect(source, force=args.force)
    if args.command in ("derive", "all"):
        derive()
