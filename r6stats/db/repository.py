import json
import sqlite3
from pathlib import Path
from uuid import uuid4

from r6stats.parser.models import Match
from r6stats.eligibility import is_custom_game
from r6stats.db import teams, appearances

SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS seasons (
 id INTEGER PRIMARY KEY, slug TEXT UNIQUE NOT NULL, name TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 0,
 start_date TEXT, end_date TEXT);
CREATE TABLE IF NOT EXISTS players (
 id INTEGER PRIMARY KEY, slug TEXT UNIQUE NOT NULL, profile_id TEXT UNIQUE,
 display_name TEXT NOT NULL, username TEXT NOT NULL, tracked INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS aliases (
 player_id INTEGER NOT NULL REFERENCES players(id), username TEXT COLLATE NOCASE UNIQUE NOT NULL);
CREATE TABLE IF NOT EXISTS series (
 id TEXT PRIMARY KEY, season_id INTEGER NOT NULL REFERENCES seasons(id),
 opponent TEXT NOT NULL, date TEXT NOT NULL, week TEXT, notes TEXT,
 competition TEXT NOT NULL CHECK(competition='NECC'), demo INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS maps (
 id TEXT PRIMARY KEY, series_id TEXT NOT NULL REFERENCES series(id),
 replay_id TEXT UNIQUE, fingerprint TEXT UNIQUE NOT NULL, map_name TEXT NOT NULL,
 match_type TEXT NOT NULL, game_mode TEXT NOT NULL, our_team INTEGER NOT NULL,
 our_score INTEGER NOT NULL, their_score INTEGER NOT NULL, normalized_json TEXT NOT NULL,
 played_on TEXT, rehost_json TEXT, replay_data_complete INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS map_segments (
 map_id TEXT NOT NULL REFERENCES maps(id) ON DELETE CASCADE,
 segment_order INTEGER NOT NULL, replay_id TEXT UNIQUE, fingerprint TEXT UNIQUE NOT NULL,
 source_name TEXT NOT NULL, PRIMARY KEY(map_id,segment_order));
CREATE TABLE IF NOT EXISTS map_kd_corrections (
 map_id TEXT NOT NULL REFERENCES maps(id) ON DELETE CASCADE,
 player_id INTEGER NOT NULL REFERENCES players(id),
 replay_kills INTEGER NOT NULL, replay_deaths INTEGER NOT NULL,
 final_kills INTEGER NOT NULL, final_deaths INTEGER NOT NULL,
 reason TEXT NOT NULL, note TEXT NOT NULL DEFAULT '', updated_at TEXT NOT NULL,
 PRIMARY KEY(map_id,player_id));
CREATE TABLE IF NOT EXISTS rounds (
 id INTEGER PRIMARY KEY, map_id TEXT NOT NULL REFERENCES maps(id) ON DELETE CASCADE,
 number INTEGER NOT NULL, site TEXT NOT NULL, winning_team INTEGER NOT NULL,
 win_condition TEXT NOT NULL, UNIQUE(map_id,number));
CREATE TABLE IF NOT EXISTS round_players (
 round_id INTEGER NOT NULL REFERENCES rounds(id) ON DELETE CASCADE,
 player_key TEXT NOT NULL, player_id INTEGER REFERENCES players(id),
 username TEXT NOT NULL, profile_id TEXT, team INTEGER NOT NULL,
 operator TEXT NOT NULL, side TEXT NOT NULL, PRIMARY KEY(round_id,player_key));
CREATE TABLE IF NOT EXISTS kill_events (
 round_id INTEGER NOT NULL REFERENCES rounds(id) ON DELETE CASCADE,
 sequence INTEGER NOT NULL, remaining REAL NOT NULL,
 killer_key TEXT, victim_key TEXT NOT NULL,
 killer_team INTEGER NOT NULL, victim_team INTEGER NOT NULL,
 headshot INTEGER NOT NULL, teamkill INTEGER NOT NULL, PRIMARY KEY(round_id,sequence));
CREATE TABLE IF NOT EXISTS objective_events (
 round_id INTEGER NOT NULL REFERENCES rounds(id) ON DELETE CASCADE,
 sequence INTEGER NOT NULL, kind TEXT NOT NULL, player_key TEXT NOT NULL,
 team INTEGER NOT NULL, remaining REAL NOT NULL, PRIMARY KEY(round_id,sequence));
CREATE TABLE IF NOT EXISTS rating_input_snapshots (
 map_id TEXT NOT NULL REFERENCES maps(id) ON DELETE CASCADE,
 version TEXT NOT NULL, normalized_json TEXT NOT NULL, source_sha256 TEXT NOT NULL,
 PRIMARY KEY(map_id,version));
"""


def connect(path: str | Path = "data/r6stats.sqlite") -> sqlite3.Connection:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # FastAPI can execute a yield dependency and its route on different workers.
    # Each request owns its connection, but SQLite must allow that thread handoff.
    db = sqlite3.connect(path, check_same_thread=False)
    db.row_factory = sqlite3.Row
    db.executescript(SCHEMA)
    # Existing local databases predate the optional season and map dates.
    for table, column in (("seasons", "start_date"), ("seasons", "end_date"),
                          ("maps", "played_on"), ("maps", "rehost_json"),
                          ("maps", "replay_data_complete")):
        existing = {row["name"] for row in db.execute(f"PRAGMA table_info({table})")}
        if column not in existing:
            definition = "INTEGER NOT NULL DEFAULT 1" if column == "replay_data_complete" else "TEXT"
            db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
    # Existing one-folder imports become explicit single-segment sources.
    db.execute("""INSERT INTO map_segments(map_id,segment_order,replay_id,fingerprint,source_name)
                  SELECT m.id,1,m.replay_id,m.fingerprint,'' FROM maps m
                  WHERE NOT EXISTS (SELECT 1 FROM map_segments ms WHERE ms.map_id=m.id)""")
    db.commit()
    teams.migrate(db)
    appearances.migrate(db)
    return db


def slugify(name: str) -> str:
    import re
    slug = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    return slug or "item"


def season_create(db, name: str, start_date: str | None = None,
                  end_date: str | None = None) -> None:
    name = name.strip()
    if not name:
        raise ValueError("Season name cannot be blank.")
    if db.execute("SELECT 1 FROM seasons WHERE name=? COLLATE NOCASE", (name,)).fetchone():
        raise ValueError("A season with that name already exists.")
    slug = slugify(name)
    db.execute("INSERT INTO seasons(slug,name,active,start_date,end_date) VALUES(?,?,?,?,?)",
               (slug, name, 0, start_date, end_date))
    if not db.execute("SELECT 1 FROM seasons WHERE active=1").fetchone():
        db.execute("UPDATE seasons SET active=1 WHERE slug=?", (slug,))
    db.commit()


def season_activate(db, name: str) -> None:
    row = db.execute("SELECT slug FROM seasons WHERE slug=? OR name=? COLLATE NOCASE",
                     (slugify(name), name.strip())).fetchone()
    if not row:
        raise ValueError(f"Season not found: {name}")
    with db:
        db.execute("UPDATE seasons SET active=0")
        db.execute("UPDATE seasons SET active=1 WHERE slug=?", (row["slug"],))


def season_update(db, slug: str, name: str, start_date: str | None, end_date: str | None) -> None:
    name = name.strip()
    if not name:
        raise ValueError("Season name cannot be blank.")
    if not db.execute("SELECT 1 FROM seasons WHERE slug=?", (slug,)).fetchone():
        raise ValueError("Season not found.")
    if db.execute("SELECT 1 FROM seasons WHERE name=? COLLATE NOCASE AND slug!=?", (name, slug)).fetchone():
        raise ValueError("A season with that name already exists.")
    with db:
        # Keep the slug stable so historical match and player URLs never change.
        db.execute("UPDATE seasons SET name=?,start_date=?,end_date=? WHERE slug=?",
                   (name, start_date, end_date, slug))


def roster_add(db, username: str, display_name: str | None = None, *, team_id: int | None = None,
               start_date: str = "0001-01-01", substitute_eligible: bool = False) -> None:
    username = username.strip()
    if not username:
        raise ValueError("Username cannot be empty.")
    slug = slugify(display_name or username)
    if db.execute("SELECT 1 FROM players WHERE slug=?", (slug,)).fetchone():
        slug += "-" + uuid4().hex[:6]
    with db:
        cur = db.execute("INSERT INTO players(slug,display_name,username,substitute_eligible) VALUES(?,?,?,?)",
                         (slug, display_name or username, username, int(substitute_eligible)))
        db.execute("INSERT INTO aliases(player_id,username) VALUES(?,?)", (cur.lastrowid, username))
        if team_id is not None:
            teams.require(db, team_id, active=True)
            from datetime import date
            date.fromisoformat(start_date)
            db.execute("INSERT INTO team_memberships(player_id,team_id,start_date) VALUES(?,?,?)",
                       (cur.lastrowid, team_id, start_date))


def roster_alias(db, old: str, new: str) -> None:
    row = db.execute("SELECT p.* FROM players p JOIN aliases a ON a.player_id=p.id WHERE a.username=?", (old.strip(),)).fetchone()
    if not row:
        raise ValueError(f"Unknown roster username: {old}")
    with db:
        db.execute("INSERT INTO aliases(player_id,username) VALUES(?,?)", (row["id"], new.strip()))
        db.execute("UPDATE players SET username=? WHERE id=?", (new.strip(), row["id"]))


def roster_remove(db, username: str) -> None:
    row = db.execute("SELECT player_id FROM aliases WHERE username=?", (username.strip(),)).fetchone()
    if not row:
        raise ValueError(f"Unknown roster username: {username}")
    with db:
        db.execute("UPDATE players SET tracked=0,status='Alumni' WHERE id=?", (row[0],))


def roster_update(db, player_id: int, *, display_name: str | None = None,
                  tracked: bool | None = None, status: str | None = None, substitute_eligible: bool | None = None) -> None:
    row = db.execute("SELECT id FROM players WHERE id=?", (player_id,)).fetchone()
    if not row:
        raise ValueError("Player not found.")
    if display_name is not None:
        display_name = display_name.strip()
        if not display_name:
            raise ValueError("Display name cannot be empty.")
    if status is not None:
        if status not in ("Active", "Alumni"):
            raise ValueError("Player status must be Active or Alumni.")
        tracked = status == "Active"
    with db:
        if substitute_eligible is not None:
            db.execute("UPDATE players SET substitute_eligible=? WHERE id=?", (int(substitute_eligible), player_id))
        if display_name is not None:
            db.execute("UPDATE players SET display_name=? WHERE id=?", (display_name, player_id))
        if tracked is not None:
            db.execute("UPDATE players SET tracked=?,status=? WHERE id=?",
                       (int(tracked), "Active" if tracked else "Alumni", player_id))


def roster_add_alias(db, player_id: int, username: str, *, make_current: bool = True) -> None:
    username = username.strip()
    if not username:
        raise ValueError("Username cannot be empty.")
    row = db.execute("SELECT id FROM players WHERE id=?", (player_id,)).fetchone()
    if not row:
        raise ValueError("Player not found.")
    owner = db.execute("SELECT player_id FROM aliases WHERE username=?", (username,)).fetchone()
    if owner and owner["player_id"] != player_id:
        raise ValueError("That Ubisoft username belongs to another roster player.")
    with db:
        if not owner:
            db.execute("INSERT INTO aliases(player_id,username) VALUES(?,?)", (player_id, username))
        if make_current:
            db.execute("UPDATE players SET username=? WHERE id=?", (username, player_id))


def identity_match(db, player):
    """Historical global identity lookup; a profile binding outranks an alias."""
    if player.profile_id:
        row = db.execute('SELECT * FROM players WHERE profile_id=?', (player.profile_id,)).fetchone()
        if row:
            return row
    row = db.execute('SELECT p.* FROM players p JOIN aliases a ON a.player_id=p.id WHERE a.username=?', (player.username.strip(),)).fetchone()
    if row and row['profile_id'] and player.profile_id and row['profile_id'] != player.profile_id:
        raise ValueError(f'Profile ID conflict for {player.username}; review roster aliases before import.')
    return row


def roster_match(db, player, team_id: int | None = None, on: str | None = None) -> sqlite3.Row | None:
    if player.profile_id:
        row = db.execute("SELECT * FROM players WHERE profile_id=? AND (? IS NOT NULL OR tracked=1)", (player.profile_id, team_id)).fetchone()
        if row:
            return row if team_id is None or teams.member(db, row["id"], team_id, on) else None
    row = db.execute("SELECT p.* FROM players p JOIN aliases a ON p.id=a.player_id WHERE a.username=? AND (? IS NOT NULL OR p.tracked=1)",
                     (player.username.strip(), team_id)).fetchone()
    if row and row["profile_id"] and player.profile_id and row["profile_id"] != player.profile_id:
        raise ValueError(f"Profile ID conflict for {player.username}; review roster aliases before import.")
    return row if row is None or team_id is None or teams.member(db, row["id"], team_id, on) else None


def bind_profiles(db, match: Match, team_id=None, side=None) -> None:
    for p in (player for round_ in match.rounds for player in round_.players):
        if side is not None and p.team != side:
            continue
        row = identity_match(db, p) if side is not None else roster_match(db, p, team_id, match.timestamp[:10])
        if row and p.profile_id and not row["profile_id"]:
            db.execute("UPDATE players SET profile_id=? WHERE id=?", (p.profile_id, row["id"]))
        if row and p.username.strip() and p.username.strip().casefold() != row["username"].strip().casefold():
            db.execute("INSERT OR IGNORE INTO aliases(player_id,username) VALUES(?,?)",
                       (row["id"], p.username.strip()))
            db.execute("UPDATE players SET username=? WHERE id=?", (p.username.strip(), row["id"]))


def choose_team(db, match: Match, explicit: int | None = None, *, team_id: int | None = None) -> tuple[int, list]:
    members = [set(), set()]
    names = {}
    for round_ in match.rounds:
        for p in round_.players:
            row = roster_match(db, p, team_id, match.timestamp[:10])
            if row:
                members[p.team].add(row["id"])
                names[row["id"]] = row["display_name"]
    counts = [len(members[0]), len(members[1])]
    tracked = sorted(names.values())
    team = explicit if explicit in (0, 1) else (counts.index(max(counts)) if max(counts) >= 3 and counts[0] != counts[1] else None)
    if team is None:
        raise ValueError(f"{'No configured roster member was found for side detection. ' if not tracked else ''}Team is ambiguous ({counts[0]} vs {counts[1]} tracked). Choose team 0 or team 1 after reviewing participants.")
    if team_id is not None:
        # Global substitutes never vote in side detection. Classify only after a
        # regular-roster majority or explicit reviewed side establishes ownership.
        selected = appearances.participants(db, match, team_id, team)
        if members[1-team]:
            raise ValueError('A regular roster member appears on the opposing team; review participants.')
        return team, sorted(db.execute('SELECT display_name FROM players WHERE id=?', (pid,)).fetchone()[0] for pid in selected)
    if not tracked or counts[team] == 0:
        raise ValueError("Selected team has no tracked roster members.")
    if members[0] & members[1]:
        raise ValueError("A tracked player changed teams across replay rounds.")
    for round_ in match.rounds:
        for p in round_.players:
            row = roster_match(db, p)
            if row and p.team != team:
                raise ValueError(f"Tracked player {p.username} changed team in round {round_.number}.")
    return team, tracked


def insert_map(db, match: Match, fingerprint: str, team: int, opponent: str,
               week: str = "", notes: str = "", series_id: str | None = None,
               demo: bool = False, season_slug: str | None = None,
               rehost_manifest: dict | None = None,
               source_segments: list[dict] | None = None, organization_team_id: int | None = None) -> str:
    teams.require(db, organization_team_id, active=True)
    if not is_custom_game(match.match_type):
        raise ValueError("Only Custom Game replay types can be stored as NECC maps.")
    if db.execute("SELECT 1 FROM series WHERE demo!=? LIMIT 1", (int(demo),)).fetchone():
        raise ValueError("Demo and real matches cannot coexist in this database.")
    season = (db.execute("SELECT * FROM seasons WHERE slug=?", (season_slug,)).fetchone()
              if season_slug else db.execute("SELECT * FROM seasons WHERE active=1").fetchone())
    if not season:
        raise ValueError("Select an existing season before import.")
    if db.execute("SELECT 1 FROM maps WHERE fingerprint=? OR (replay_id IS NOT NULL AND replay_id=?)",
                  (fingerprint, match.replay_id or None)).fetchone():
        raise ValueError("This replay has already been imported. No changes were made.")
    sources = source_segments or [{"replay_id": match.replay_id, "fingerprint": fingerprint,
                                   "source_name": ""}]
    if len({source["fingerprint"] for source in sources}) != len(sources) or any(
            db.execute("""SELECT 1 FROM map_segments WHERE fingerprint=? OR
                          (replay_id IS NOT NULL AND replay_id=?)""",
                       (source["fingerprint"], source.get("replay_id") or None)).fetchone()
            for source in sources):
        raise ValueError("One of these replay folders has already been imported.")
    if any(source.get("team_id", organization_team_id) != organization_team_id or
           source.get("season_slug", season["slug"]) != season["slug"] for source in sources):
        raise ValueError("Rehost sources must share the selected team and season.")
    score = [sum(r.winner == i for r in match.rounds) for i in (0, 1)]
    map_id = uuid4().hex[:12]
    with db:
        if not db.in_transaction:
            db.execute("BEGIN IMMEDIATE")
        choose_team(db, match, team, team_id=organization_team_id)
        roles = appearances.participants(db, match, organization_team_id, team)
        bind_profiles(db, match, organization_team_id, team)
        db.execute("INSERT OR IGNORE INTO team_seasons VALUES(?,?)", (organization_team_id, season["id"]))
        if series_id:
            row = db.execute("SELECT * FROM series WHERE id=?", (series_id,)).fetchone()
            if not row or row["season_id"] != season["id"] or row["demo"] != int(demo) or row["team_id"] != organization_team_id:
                raise ValueError("Series not found in the selected team, season and data mode.")
            if row["opponent"].casefold() != opponent.casefold():
                raise ValueError("Opponent differs from the selected series.")
        else:
            series_id = uuid4().hex[:12]
            db.execute("INSERT INTO series(id,season_id,opponent,date,week,notes,competition,demo,team_id) VALUES(?,?,?,?,?,?,?,?,?)",
                       (series_id, season["id"], opponent, match.timestamp[:10], week, notes, "NECC", int(demo), organization_team_id))
        db.execute("""INSERT INTO maps(id,series_id,replay_id,fingerprint,map_name,match_type,
                   game_mode,our_team,our_score,their_score,normalized_json,played_on,rehost_json,team_id)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                   (map_id, series_id, match.replay_id or None, fingerprint, match.map_name,
                    match.match_type, match.game_mode, team, score[team], score[1-team],
                    json.dumps(match.to_dict(), separators=(",", ":")), match.timestamp[:10],
                    json.dumps(rehost_manifest, separators=(",", ":")) if rehost_manifest else None, organization_team_id))
        for role in roles.values():
            db.execute("INSERT INTO map_player_appearances VALUES(?,?,?,?,?)",
                       (map_id, role["player_id"], role["appearance_role"], role["classified_on"], role["regular_team_id"]))
        for order, source in enumerate(sources, start=1):
            db.execute("""INSERT INTO map_segments(map_id,segment_order,replay_id,fingerprint,source_name)
                          VALUES(?,?,?,?,?)""", (map_id, order, source.get("replay_id") or None,
                                                 source["fingerprint"], source.get("source_name", "")))
        for round_ in match.rounds:
            cursor = db.execute("INSERT INTO rounds(map_id,number,site,winning_team,win_condition) VALUES(?,?,?,?,?)",
                                (map_id, round_.number, round_.site, round_.winner, round_.win_condition))
            round_id = cursor.lastrowid
            for participant in round_.players:
                roster = identity_match(db, participant) if participant.team == team else None
                db.execute("""INSERT INTO round_players
                           (round_id,player_key,player_id,username,profile_id,team,operator,side)
                           VALUES(?,?,?,?,?,?,?,?)""",
                           (round_id, participant.key, roster["id"] if roster else None,
                            participant.username, participant.profile_id or None,
                            participant.team, participant.operator, participant.side))
            for kill in round_.kills:
                db.execute("""INSERT INTO kill_events
                           (round_id,sequence,remaining,killer_key,victim_key,killer_team,victim_team,headshot,teamkill)
                           VALUES(?,?,?,?,?,?,?,?,?)""",
                           (round_id, kill.sequence, kill.remaining, kill.killer or None, kill.victim,
                            kill.killer_team, kill.victim_team, int(kill.headshot), int(kill.teamkill)))
            for sequence, objective in enumerate(round_.objectives):
                db.execute("""INSERT INTO objective_events
                           (round_id,sequence,kind,player_key,team,remaining) VALUES(?,?,?,?,?,?)""",
                           (round_id, sequence, objective.kind, objective.player, objective.team, objective.remaining))
    return map_id


def match_update(db, map_id: str, *, played_on: str, series_id: str | None = None,
                 make_new_series: bool = False) -> str:
    current = db.execute("""SELECT m.series_id,m.team_id,s.season_id,s.opponent,s.week,s.notes,s.demo
                            FROM maps m JOIN series s ON s.id=m.series_id WHERE m.id=?""", (map_id,)).fetchone()
    if not current or current["demo"]:
        raise ValueError("NECC map not found.")
    if make_new_series and series_id:
        raise ValueError("Choose an existing series or make a new one, not both.")
    target = current["series_id"]
    if series_id:
        destination = db.execute("SELECT season_id,demo,team_id FROM series WHERE id=?", (series_id,)).fetchone()
        if not destination or destination["demo"] or destination["season_id"] != current["season_id"] or destination["team_id"] != current["team_id"]:
            raise ValueError("Choose an existing NECC series from the same team and season.")
        target = series_id
    with db:
        if make_new_series:
            target = uuid4().hex[:12]
            db.execute("""INSERT INTO series(id,season_id,opponent,date,week,notes,competition,demo,team_id)
                          VALUES(?,?,?,?,?,?,'NECC',0,?)""",
                       (target, current["season_id"], current["opponent"], played_on,
                        current["week"], current["notes"], current["team_id"]))
        db.execute("UPDATE maps SET series_id=?,played_on=? WHERE id=?", (target, played_on, map_id))
        if target != current["series_id"]:
            db.execute("DELETE FROM series WHERE id=? AND NOT EXISTS (SELECT 1 FROM maps WHERE series_id=?)",
                       (current["series_id"], current["series_id"]))
    return target


def match_delete(db, map_id: str) -> None:
    row = db.execute("""SELECT m.series_id,s.demo FROM maps m JOIN series s ON s.id=m.series_id
                        WHERE m.id=?""", (map_id,)).fetchone()
    if not row or row["demo"]:
        raise ValueError("NECC map not found.")
    with db:
        # Round/event tables cascade. Roster players, aliases and profile bindings remain.
        db.execute("DELETE FROM maps WHERE id=?", (map_id,))
        db.execute("DELETE FROM series WHERE id=? AND NOT EXISTS (SELECT 1 FROM maps WHERE series_id=?)",
                   (row["series_id"], row["series_id"]))


def reparse_map(db, map_id: str, match: Match, fingerprint: str) -> None:
    """Replace replay-derived rows for one existing map in a single transaction."""
    row = db.execute("""SELECT m.*,s.demo FROM maps m JOIN series s ON s.id=m.series_id
                        WHERE m.id=?""", (map_id,)).fetchone()
    if not row or row["demo"]:
        raise ValueError("Existing NECC map not found.")
    if fingerprint != row["fingerprint"] or match.replay_id != row["replay_id"]:
        raise ValueError("Replay identity or file contents differ from this imported map; no changes were made.")
    if not is_custom_game(match.match_type):
        raise ValueError("Only the original Custom Game replay can replace this NECC map.")
    if not match.rounds:
        raise ValueError("The reparsed replay has no rounds.")
    score = [sum(r.winner == team for r in match.rounds) for team in (0, 1)]
    old_bindings = {r["player_key"]: r["player_id"] for r in db.execute("""SELECT rp.player_key,rp.player_id
        FROM round_players rp JOIN rounds rd ON rd.id=rp.round_id WHERE rd.map_id=?""", (map_id,))}
    corrections = list(db.execute("SELECT player_id FROM map_kd_corrections WHERE map_id=?", (map_id,)))
    if corrections:
        from r6stats.stats.calculate import calculate_match
        reparsed_stats = calculate_match(match)
        corrected_ids = {item["player_id"] for item in corrections}
        new_keys = {key for key, player_id in old_bindings.items()
                    if player_id in corrected_ids and key in reparsed_stats}
        if {old_bindings[key] for key in new_keys} != corrected_ids:
            raise ValueError("Reparse lost a manually corrected player; no changes were made.")
    with db:
        db.execute("DELETE FROM rounds WHERE map_id=?", (map_id,))
        db.execute("""UPDATE maps SET map_name=?,match_type=?,game_mode=?,our_score=?,their_score=?,
                    normalized_json=? WHERE id=?""",
                   (match.map_name, match.match_type, match.game_mode,
                    score[row["our_team"]], score[1-row["our_team"]],
                    json.dumps(match.to_dict(), separators=(",", ":")), map_id))
        for round_ in match.rounds:
            cursor = db.execute("INSERT INTO rounds(map_id,number,site,winning_team,win_condition) VALUES(?,?,?,?,?)",
                                (map_id, round_.number, round_.site, round_.winner, round_.win_condition))
            round_id = cursor.lastrowid
            for participant in round_.players:
                player_id = old_bindings.get(participant.key)
                db.execute("""INSERT INTO round_players
                           (round_id,player_key,player_id,username,profile_id,team,operator,side)
                           VALUES(?,?,?,?,?,?,?,?)""",
                           (round_id, participant.key, player_id, participant.username,
                            participant.profile_id or None, participant.team,
                            participant.operator, participant.side))
            for kill in round_.kills:
                db.execute("""INSERT INTO kill_events
                           (round_id,sequence,remaining,killer_key,victim_key,killer_team,victim_team,headshot,teamkill)
                           VALUES(?,?,?,?,?,?,?,?,?)""",
                           (round_id, kill.sequence, kill.remaining, kill.killer or None, kill.victim,
                            kill.killer_team, kill.victim_team, int(kill.headshot), int(kill.teamkill)))
            for sequence, objective in enumerate(round_.objectives):
                db.execute("""INSERT INTO objective_events
                           (round_id,sequence,kind,player_key,team,remaining) VALUES(?,?,?,?,?,?)""",
                           (round_id, sequence, objective.kind, objective.player,
                            objective.team, objective.remaining))
        if corrections:
            for key in new_keys:
                raw = reparsed_stats[key]
                db.execute("""UPDATE map_kd_corrections SET replay_kills=?,replay_deaths=?
                              WHERE map_id=? AND player_id=?""",
                           (raw["kills"], raw["deaths"], map_id, old_bindings[key]))
