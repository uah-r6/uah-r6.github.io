import json
import sqlite3
from pathlib import Path
from uuid import uuid4

from r6stats.parser.models import Match
from r6stats.eligibility import is_custom_game

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
 played_on TEXT);
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
    for table, column in (("seasons", "start_date"), ("seasons", "end_date"), ("maps", "played_on")):
        existing = {row["name"] for row in db.execute(f"PRAGMA table_info({table})")}
        if column not in existing:
            db.execute(f"ALTER TABLE {table} ADD COLUMN {column} TEXT")
    db.commit()
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


def roster_add(db, username: str, display_name: str | None = None) -> None:
    username = username.strip()
    if not username:
        raise ValueError("Username cannot be empty.")
    slug = slugify(display_name or username)
    if db.execute("SELECT 1 FROM players WHERE slug=?", (slug,)).fetchone():
        slug += "-" + uuid4().hex[:6]
    with db:
        cur = db.execute("INSERT INTO players(slug,display_name,username) VALUES(?,?,?)",
                         (slug, display_name or username, username))
        db.execute("INSERT INTO aliases(player_id,username) VALUES(?,?)", (cur.lastrowid, username))


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
        db.execute("UPDATE players SET tracked=0 WHERE id=?", (row[0],))


def roster_update(db, player_id: int, *, display_name: str | None = None,
                  tracked: bool | None = None) -> None:
    row = db.execute("SELECT id FROM players WHERE id=?", (player_id,)).fetchone()
    if not row:
        raise ValueError("Player not found.")
    if display_name is not None:
        display_name = display_name.strip()
        if not display_name:
            raise ValueError("Display name cannot be empty.")
    with db:
        if display_name is not None:
            db.execute("UPDATE players SET display_name=? WHERE id=?", (display_name, player_id))
        if tracked is not None:
            db.execute("UPDATE players SET tracked=? WHERE id=?", (int(tracked), player_id))


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


def roster_match(db, player) -> sqlite3.Row | None:
    if player.profile_id:
        row = db.execute("SELECT * FROM players WHERE profile_id=? AND tracked=1", (player.profile_id,)).fetchone()
        if row:
            return row
    row = db.execute("SELECT p.* FROM players p JOIN aliases a ON p.id=a.player_id WHERE a.username=? AND p.tracked=1",
                     (player.username.strip(),)).fetchone()
    if row and row["profile_id"] and player.profile_id and row["profile_id"] != player.profile_id:
        raise ValueError(f"Profile ID conflict for {player.username}; review roster aliases before import.")
    return row


def bind_profiles(db, match: Match) -> None:
    for p in match.rounds[0].players:
        row = roster_match(db, p)
        if row and p.profile_id and not row["profile_id"]:
            db.execute("UPDATE players SET profile_id=? WHERE id=?", (p.profile_id, row["id"]))
        if row and p.username.strip() and p.username.strip().casefold() != row["username"].strip().casefold():
            db.execute("INSERT OR IGNORE INTO aliases(player_id,username) VALUES(?,?)",
                       (row["id"], p.username.strip()))
            db.execute("UPDATE players SET username=? WHERE id=?", (p.username.strip(), row["id"]))


def choose_team(db, match: Match, explicit: int | None = None) -> tuple[int, list]:
    counts = [0, 0]
    tracked = []
    for p in match.rounds[0].players:
        row = roster_match(db, p)
        if row:
            counts[p.team] += 1
            tracked.append(row["display_name"])
    if not tracked:
        raise ValueError("No configured roster member was found in this replay.")
    team = explicit if explicit in (0, 1) else (counts.index(max(counts)) if max(counts) >= 3 and counts[0] != counts[1] else None)
    if team is None:
        raise ValueError(f"Team is ambiguous ({counts[0]} vs {counts[1]} tracked). Choose team 0 or team 1 after reviewing participants.")
    if counts[team] == 0:
        raise ValueError("Selected team has no tracked roster members.")
    for round_ in match.rounds:
        for p in round_.players:
            row = roster_match(db, p)
            if row and p.team != team:
                raise ValueError(f"Tracked player {p.username} changed team in round {round_.number}.")
    return team, tracked


def insert_map(db, match: Match, fingerprint: str, team: int, opponent: str,
               week: str = "", notes: str = "", series_id: str | None = None,
               demo: bool = False, season_slug: str | None = None) -> str:
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
    score = [sum(r.winner == i for r in match.rounds) for i in (0, 1)]
    map_id = uuid4().hex[:12]
    with db:
        bind_profiles(db, match)
        if series_id:
            row = db.execute("SELECT * FROM series WHERE id=?", (series_id,)).fetchone()
            if not row or row["season_id"] != season["id"] or row["demo"] != int(demo):
                raise ValueError("Series not found in the selected season and data mode.")
            if row["opponent"].casefold() != opponent.casefold():
                raise ValueError("Opponent differs from the selected series.")
        else:
            series_id = uuid4().hex[:12]
            db.execute("INSERT INTO series VALUES(?,?,?,?,?,?,?,?)",
                       (series_id, season["id"], opponent, match.timestamp[:10], week, notes, "NECC", int(demo)))
        db.execute("""INSERT INTO maps(id,series_id,replay_id,fingerprint,map_name,match_type,
                   game_mode,our_team,our_score,their_score,normalized_json,played_on)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                   (map_id, series_id, match.replay_id or None, fingerprint, match.map_name,
                    match.match_type, match.game_mode, team, score[team], score[1-team],
                    json.dumps(match.to_dict(), separators=(",", ":")), match.timestamp[:10]))
        for round_ in match.rounds:
            cursor = db.execute("INSERT INTO rounds(map_id,number,site,winning_team,win_condition) VALUES(?,?,?,?,?)",
                                (map_id, round_.number, round_.site, round_.winner, round_.win_condition))
            round_id = cursor.lastrowid
            for participant in round_.players:
                roster = roster_match(db, participant)
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
    current = db.execute("""SELECT m.series_id,s.season_id,s.opponent,s.week,s.notes,s.demo
                            FROM maps m JOIN series s ON s.id=m.series_id WHERE m.id=?""", (map_id,)).fetchone()
    if not current or current["demo"]:
        raise ValueError("NECC map not found.")
    if make_new_series and series_id:
        raise ValueError("Choose an existing series or make a new one, not both.")
    target = current["series_id"]
    if series_id:
        destination = db.execute("SELECT season_id,demo FROM series WHERE id=?", (series_id,)).fetchone()
        if not destination or destination["demo"] or destination["season_id"] != current["season_id"]:
            raise ValueError("Choose an existing NECC series from the same season.")
        target = series_id
    with db:
        if make_new_series:
            target = uuid4().hex[:12]
            db.execute("""INSERT INTO series(id,season_id,opponent,date,week,notes,competition,demo)
                          VALUES(?,?,?,?,?,?,'NECC',0)""",
                       (target, current["season_id"], current["opponent"], played_on,
                        current["week"], current["notes"]))
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
