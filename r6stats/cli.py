import argparse
import hashlib
import json
import logging
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

from r6stats.db import repository as repo
from r6stats.db import teams
from r6stats.eligibility import is_custom_game, rejection_message, scan_label
from r6stats.export import export
from r6stats.parser.siege_dissect import parse_match
from r6stats.publishing import publish_site
from r6stats import replay_archive
from r6stats.credited_refresh import collect_after_import
from r6stats.stats.calculate import RATING_VERSIONS, calculate_match


def config_load() -> dict:
    path = Path("config/settings.json")
    if not path.exists():
        raise ValueError("Run `python -m r6stats init` first to create config/settings.json.")
    value = json.loads(path.read_text(encoding="utf-8"))
    if value["stats"]["rating_version"] not in RATING_VERSIONS:
        raise ValueError(f"Unsupported Rating version: {value['stats']['rating_version']}.")
    if value["stats"]["rating_version"] in ("siege_style_v2", "siege_style_v3") and value["stats"]["trade_window_seconds"] != 8:
        raise ValueError("Siege-style Ratings require their frozen 8-second trade window.")
    return value


def fingerprint(path: Path) -> str:
    if path.suffix.lower() == ".zip":
        import zipfile
        with zipfile.ZipFile(path) as z:
            chunks = [(n, z.read(n)) for n in z.namelist() if n.lower().endswith(".rec")]
    else:
        chunks = [(p.name, p.read_bytes()) for p in path.glob("*.rec")]
    digest = hashlib.sha256()
    for name, data in sorted(chunks):
        digest.update(Path(name).name.encode())
        digest.update(data)
    return digest.hexdigest()


def replay_root(config):
    configured = config["replays"].get("path", "")
    if configured:
        root = Path(configured).expanduser()
    else:
        root = Path.home() / "Documents" / "My Games" / "Rainbow Six - Siege" / "MatchReplay"
    if not root.is_dir():
        raise ValueError(f"Replay folder not found: {root}. Set replays.path in config/settings.json.")
    return root


def scan(db, config):
    paths = sorted([p for p in replay_root(config).iterdir() if p.is_dir() or p.suffix.lower() == ".zip"],
                   key=lambda p: p.stat().st_mtime, reverse=True)[:12]
    if not paths:
        print("No replay folders found.")
        return []
    for i, path in enumerate(paths, 1):
        try:
            m = parse_match(path, allow_incomplete=True)
            status = scan_label(m.match_type) if len(m.rounds) >= 2 else "INCOMPLETE - only 1 replay round"
            count = sum(repo.roster_match(db, p) is not None for p in m.rounds[0].players)
            print(f"[{i}] {m.timestamp[:16]} | {m.map_name} | {status} | {len(m.rounds)} rounds | {count} roster matches | {path.name}")
        except ValueError as exc:
            print(f"[{i}] {path.name} | Unable to inspect: {exc}")
    return paths


def import_path(db, config, path, series_id=None, team=None, *, archive_root=None, organization_team_id=None):
    if db.execute("SELECT 1 FROM series WHERE demo=1 LIMIT 1").fetchone():
        raise ValueError("Demo data exists. Run `python -m r6stats demo --clear` before importing real NECC maps.")
    match = parse_match(path)
    if not is_custom_game(match.match_type):
        raise ValueError(rejection_message(match.match_type))
    fp = fingerprint(Path(path))
    if db.execute("SELECT 1 FROM maps WHERE fingerprint=? OR (replay_id IS NOT NULL AND replay_id=?)",
                  (fp, match.replay_id or None)).fetchone():
        raise ValueError("This replay has already been imported. No changes were made.")
    if organization_team_id is None:
        choices = db.execute("SELECT id,name FROM teams WHERE active=1 ORDER BY display_order,id").fetchall()
        for choice in choices:
            print(f"[{choice['id']}] {choice['name']}")
        selected = input("Select the organization team ID for this NECC map: ").strip()
        if not selected.isdigit():
            raise ValueError("An explicit organization team is required.")
        organization_team_id = int(selected)
    organization = teams.require(db, organization_team_id, active=True)
    try:
        our_team, tracked = repo.choose_team(db, match, team, team_id=organization_team_id)
    except ValueError as exc:
        if "ambiguous" not in str(exc).lower():
            raise
        print(str(exc))
        for index in (0, 1):
            print(f"Team {index}: " + ", ".join(p.username for p in match.rounds[0].players if p.team == index))
        selected = input("Which team is yours? Enter 0 or 1: ").strip()
        if selected not in {"0", "1"}:
            raise ValueError("No team selected; no changes made.")
        our_team, tracked = repo.choose_team(db, match, int(selected), team_id=organization_team_id)
    calculate_match(match, config["stats"]["trade_window_seconds"])
    score = [sum(r.winner == i for r in match.rounds) for i in (0, 1)]
    season = db.execute("SELECT name FROM seasons WHERE active=1").fetchone()
    if not season:
        raise ValueError("Create an active season before import.")
    print(f"\nCUSTOM GAME IMPORT PREVIEW\nOrganization: {organization['name']}\nSeason: {season[0]}\nDate: {match.timestamp[:10]}\nMap: {match.map_name}\nMode: {match.game_mode}\nMatch type: {match.match_type}\nTracked team: {', '.join(tracked)}\nScore: {score[our_team]}-{score[1-our_team]}\nRounds: {len(match.rounds)}\nCompetition if confirmed: NECC")
    opponent = input("Opponent name: ").strip()
    if not opponent:
        raise ValueError("Opponent is required; no changes made.")
    week = input("NECC week (optional): ").strip()
    notes = input("Notes (optional): ").strip()
    if input("Was this Custom Game an NECC map? Type NECC to import: ").strip() != "NECC":
        print("Cancelled. No statistics were changed.")
        return None
    archive_root = Path(archive_root) if archive_root else Path("data/replay-archive")
    prepared = replay_archive.prepare(path, archive_root, fp, len(match.rounds))
    try:
        map_id = repo.insert_map(db, match, fp, our_team, opponent, week, notes, series_id, organization_team_id=organization_team_id)
        try:
            replay_archive.commit(prepared, archive_root, db, map_id)
        except Exception:
            repo.match_delete(db, map_id)
            raise
    finally:
        prepared.cleanup()
    credit = collect_after_import(db, archive_root, map_id)
    export(db, config)
    print(f"Imported {len(match.rounds)} rounds as map {map_id}. Website data generated.")
    print(f"Kill count source: {credit['source']}.")
    return map_id


def publish(db, config):
    result = publish_site(db, config, Path.cwd())
    print(result["message"])


def main():
    parser = argparse.ArgumentParser(prog="python -m r6stats")
    parser.add_argument("--verbose", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init")
    season = sub.add_parser("season")
    season.add_argument("action", choices=["create", "activate", "list"])
    season.add_argument("name", nargs="?")
    roster = sub.add_parser("roster")
    roster.add_argument("action", choices=["add", "list", "remove", "alias"])
    roster.add_argument("username", nargs="?")
    roster.add_argument("new_username", nargs="?")
    roster.add_argument("--display-name")
    roster.add_argument("--organization-team", type=int)
    sub.add_parser("scan")
    imp = sub.add_parser("import")
    imp.add_argument("path")
    imp.add_argument("--series")
    imp.add_argument("--team", type=int, choices=[0, 1], help="Replay side 0 or 1")
    imp.add_argument("--organization-team", type=int, help="Stable organization team ID")
    sub.add_parser("export")
    sub.add_parser("recalculate")
    sub.add_parser("publish")
    sub.add_parser("admin")
    sub.add_parser("update")
    demo = sub.add_parser("demo")
    demo.add_argument("--clear", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.WARNING)
    try:
        if args.command == "init":
            config_path = Path("config/settings.json")
            config_path.parent.mkdir(parents=True, exist_ok=True)
            if not config_path.exists():
                shutil.copyfile("config/settings.example.json", config_path)
            with repo.connect() as db:
                pass
            print("Created settings and local database.")
            return
        if args.command == "admin":
            import uvicorn
            print("Local admin: http://127.0.0.1:8000/admin")
            uvicorn.run("r6stats.admin.server:app", host="127.0.0.1", port=8000)
            return
        config = config_load()
        db = repo.connect()
        if args.command == "season":
            if args.action == "list":
                for row in db.execute("SELECT name,active FROM seasons ORDER BY id"):
                    print(("* " if row["active"] else "  ") + row["name"])
            elif not args.name:
                raise ValueError("Season name is required.")
            elif args.action == "create":
                repo.season_create(db, args.name)
            else:
                repo.season_activate(db, args.name)
        elif args.command == "roster":
            if args.action == "list":
                for row in db.execute("SELECT username,display_name,profile_id,tracked FROM players ORDER BY id"):
                    print(f"{row['username']} ({row['display_name']}) {'active' if row['tracked'] else 'inactive'}")
            elif not args.username:
                raise ValueError("Username is required.")
            elif args.action == "add":
                teams.require(db, args.organization_team, active=True)
                repo.roster_add(db, args.username, args.display_name, team_id=args.organization_team)
            elif args.action == "remove":
                repo.roster_remove(db, args.username)
            elif args.action == "alias":
                if not args.new_username:
                    raise ValueError("New username is required.")
                repo.roster_alias(db, args.username, args.new_username)
        elif args.command == "scan":
            scan(db, config)
        elif args.command == "import":
            import_path(db, config, args.path, args.series, args.team, organization_team_id=args.organization_team)
        elif args.command in {"export", "recalculate"}:
            export(db, config)
            print("Website statistics recalculated and exported from stored rounds.")
        elif args.command == "publish":
            publish(db, config)
        elif args.command == "update":
            paths = scan(db, config)
            if paths:
                selected = input("Select your NECC Custom Game replay number (blank to cancel): ").strip()
                if selected:
                    index = int(selected)
                    if index < 1 or index > len(paths):
                        raise ValueError("Replay number is out of range.")
                    if import_path(db, config, paths[index - 1]):
                        publish(db, config)
        elif args.command == "demo":
            from r6stats.demo import run
            run(db, config, args.clear)
    except (ValueError, OSError, sqlite3.Error, subprocess.CalledProcessError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
    finally:
        if "db" in locals():
            db.close()


