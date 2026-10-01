"""Loopback-only FastAPI admin; the public Pages build never serves these routes."""
import hashlib
import json
import os
import secrets
import sqlite3
import sys
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Annotated
from urllib.parse import urlparse

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
from starlette.middleware.trustedhost import TrustedHostMiddleware

from r6stats.cli import fingerprint
from r6stats.db import repository as repo
from r6stats.eligibility import is_custom_game, rejection_message, scan_label
from r6stats.export import export
from r6stats import manual_kd
from r6stats.parser.models import Match
from r6stats.parser.confirmed_rehost import assemble_rehost, source_fingerprint
from r6stats.parser.siege_dissect import parse_match
from r6stats.publishing import publish_site
from r6stats import replay_archive
from r6stats.stats.calculate import RATING_VERSION, RATING_VERSIONS, calculate_match

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass
class Preview:
    path: Path
    fingerprint: str
    match: Match
    created: float
    paths: list[Path] | None = None
    rehost_manifest: dict | None = None


class SeasonCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    start_date: str | None = None
    end_date: str | None = None

    @field_validator("name")
    @classmethod
    def valid_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Season name cannot be blank.")
        return value.strip()

    @field_validator("start_date", "end_date")
    @classmethod
    def valid_date(cls, value: str | None) -> str | None:
        return date_value(value)


class SeasonUpdate(SeasonCreate):
    pass


class PlayerCreate(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    display_name: str | None = Field(default=None, max_length=80)


class PlayerUpdate(BaseModel):
    display_name: str | None = Field(default=None, max_length=80)
    tracked: bool | None = None


class AliasCreate(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    make_current: bool = True


class PreviewRequest(BaseModel):
    replay_id: str | None = None
    path: str | None = None
    team: int | None = Field(default=None, ge=0, le=1)


class ImportRequest(BaseModel):
    preview_token: str
    season_slug: str
    opponent: str = Field(min_length=1, max_length=120)
    week: str = Field(default="", max_length=80)
    notes: str = Field(default="", max_length=2000)
    series_id: str | None = None
    team: int | None = Field(default=None, ge=0, le=1)
    confirm_necc: bool

    @field_validator("opponent")
    @classmethod
    def valid_opponent(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Opponent name cannot be blank.")
        return value.strip()


class RehostSource(BaseModel):
    replay_id: str | None = None
    path: str | None = None


class RehostExclusion(BaseModel):
    segment: int = Field(ge=1)
    physical_number: int = Field(ge=1)
    reason: str = Field(min_length=1, max_length=240)


class RehostPreviewRequest(BaseModel):
    segments: list[RehostSource] = Field(min_length=2)
    exclusions: list[RehostExclusion] = Field(default_factory=list)
    team: int | None = Field(default=None, ge=0, le=1)


class RehostImportRequest(ImportRequest):
    confirm_folders_one_map: bool
    confirm_roster_change: bool = False
    confirm_score_override: bool = False
    final_our_score: int = Field(ge=0, le=30)
    final_their_score: int = Field(ge=0, le=30)


class SeriesUpdate(BaseModel):
    opponent: str = Field(min_length=1, max_length=120)
    week: str = Field(default="", max_length=80)
    notes: str = Field(default="", max_length=2000)
    date: str | None = None

    @field_validator("opponent")
    @classmethod
    def valid_opponent(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Opponent name cannot be blank.")
        return value.strip()

    @field_validator("date")
    @classmethod
    def valid_date(cls, value: str | None) -> str | None:
        return date_value(value)


class MatchUpdate(BaseModel):
    played_on: str
    series_id: str | None = None
    make_new_series: bool = False

    @field_validator("played_on")
    @classmethod
    def valid_played_on(cls, value: str) -> str:
        return date_value(value, required=True)


class MatchDelete(BaseModel):
    confirm_map_id: str


class KDCorrection(BaseModel):
    final_kills: int = Field(ge=0, le=100)
    final_deaths: int = Field(ge=0, le=100)
    reason: str = Field(min_length=1, max_length=240)
    note: str = Field(default="", max_length=2000)


class MatchReparse(BaseModel):
    path: str = ""
    segment_paths: list[str] = Field(default_factory=list)
    from_archive: bool = False
    confirm_map_id: str


class ArchiveBackfill(BaseModel):
    path: str = ""
    segment_paths: list[str] = Field(default_factory=list)
    confirm_map_id: str


class SettingsUpdate(BaseModel):
    team_name: str = Field(min_length=1, max_length=120)
    short_name: str = Field(min_length=1, max_length=24)
    accent: str
    replay_path: str = ""
    trade_window_seconds: int = Field(ge=1, le=60)
    publishing_enabled: bool = True
    branch: str = Field(min_length=1, max_length=120)
    remote_url: str = ""
    site_url: str = ""
    rating_version: str = RATING_VERSION

    @field_validator("team_name", "short_name", "branch")
    @classmethod
    def valid_required_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("This field cannot be blank.")
        return value.strip()

    @field_validator("accent")
    @classmethod
    def valid_color(cls, value: str) -> str:
        import re
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
            raise ValueError("Accent must be a six-digit hex color, such as #82e3db.")
        return value

    @field_validator("rating_version")
    @classmethod
    def valid_rating_version(cls, value: str) -> str:
        if value not in RATING_VERSIONS:
            raise ValueError(f"Rating version must be one of: {', '.join(RATING_VERSIONS)}.")
        return value

    @field_validator("remote_url")
    @classmethod
    def valid_remote_url(cls, value: str) -> str:
        value = value.strip()
        import re
        pattern = r"(?:https://github\.com/|git@github\.com:)[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/?"
        if value and not re.fullmatch(pattern, value):
            raise ValueError("Git remote must be a GitHub HTTPS or SSH repository URL.")
        return value

    @field_validator("site_url")
    @classmethod
    def valid_site_url(cls, value: str) -> str:
        value = value.strip()
        if value:
            parsed = urlparse(value)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                raise ValueError("Public website URL must begin with http:// or https://.")
        return value


def date_value(value: str | None, *, required: bool = False) -> str | None:
    if value is None or not value.strip():
        if required:
            raise ValueError("A date is required.")
        return None
    value = value.strip()
    import re
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError("Date must be YYYY-MM-DD.")
    try:
        date.fromisoformat(value)
    except ValueError as error:
        raise ValueError("Date is not valid.") from error
    return value


def validate_season_dates(start: str | None, end: str | None) -> None:
    if start and end and end < start:
        raise ValueError("Season end date must be on or after its start date.")


def read_settings(root: Path) -> dict:
    path = root / "config/settings.json"
    if not path.exists():
        raise ValueError("Settings are missing. Run the setup script once.")
    return json.loads(path.read_text(encoding="utf-8"))


def replay_directory(config: dict) -> Path:
    configured = config["replays"].get("path", "")
    root = (Path(configured).expanduser() if configured else
            Path.home() / "Documents" / "My Games" / "Rainbow Six - Siege" / "MatchReplay")
    if not root.is_dir():
        raise ValueError(f"Replay folder not found: {root}. Set it on the Settings page.")
    return root


def replay_key(path: Path) -> str:
    return hashlib.sha256(str(path.resolve()).encode("utf-8")).hexdigest()[:20]


def source_hashes(root: Path) -> dict[str, str]:
    """Snapshot source at startup so a launcher can spot an old live process."""
    return {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted((root / "r6stats").rglob("*.py"))}


def create_app(root: Path = PROJECT_ROOT) -> FastAPI:
    root = root.resolve()
    app = FastAPI(title="NECC Tracker Local Admin", docs_url=None, redoc_url=None, openapi_url=None)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "testserver"], www_redirect=False)
    app.state.root = root
    app.state.scanned = {}
    app.state.previews = {}
    app.state.token = secrets.token_urlsafe(32)
    app.state.source_hashes = source_hashes(root)

    @app.middleware("http")
    async def same_origin_only(request: Request, call_next):
        if request.url.path.startswith("/api/admin"):
            origin = request.headers.get("origin")
            if origin and origin != f"{request.url.scheme}://{request.headers.get('host')}":
                return JSONResponse({"detail": "Admin requests must come from this local site."}, status_code=403)
            if request.method not in {"GET", "HEAD", "OPTIONS"}:
                if request.headers.get("x-r6-admin-token") != app.state.token:
                    return JSONResponse({"detail": "Admin session token is missing or invalid."}, status_code=403)
                if request.headers.get("content-type", "").split(";")[0].strip() != "application/json":
                    return JSONResponse({"detail": "Send JSON to the admin API."}, status_code=415)
        return await call_next(request)

    @app.exception_handler(ValueError)
    async def value_error_handler(_request: Request, error: ValueError):
        return JSONResponse({"detail": str(error)}, status_code=400)

    @app.exception_handler(sqlite3.IntegrityError)
    async def database_error_handler(_request: Request, error: sqlite3.IntegrityError):
        return JSONResponse({"detail": f"Database rejected this change: {error}"}, status_code=409)

    def db_connection():
        db = repo.connect(root / "data/r6stats.sqlite")
        try:
            yield db
        finally:
            db.close()

    DB = Annotated[sqlite3.Connection, Depends(db_connection)]

    @app.get("/")
    def home():
        return RedirectResponse("/admin")

    build = root / "web/admin-dist"
    app.mount("/admin/assets", StaticFiles(directory=build / "assets", check_dir=False), name="admin-assets")

    @app.get("/admin", response_class=HTMLResponse)
    @app.get("/admin/", response_class=HTMLResponse)
    def admin_page():
        page = build / "admin.html"
        if not page.exists():
            return HTMLResponse("<h1>Admin UI has not been built</h1><p>Run <code>npm.cmd run build:admin</code> in the web folder.</p>", status_code=503)
        return FileResponse(page)

    @app.get("/api/admin/session")
    def session():
        return {"token": app.state.token}

    @app.get("/api/admin/runtime")
    def runtime():
        import r6stats
        import r6stats.parser.siege_dissect as adapter
        executable = adapter.parser_executable()
        return {"pid": os.getpid(), "sys_executable": sys.executable,
                "cwd": os.getcwd(), "project_root": str(root),
                "r6stats_file": str(Path(r6stats.__file__).resolve()),
                "siege_dissect_file": str(Path(adapter.__file__).resolve()),
                "parser_executable": executable,
                "parser_sha256": hashlib.sha256(Path(executable).read_bytes()).hexdigest() if executable else None,
                "server_file": str(Path(__file__).resolve()),
                "source_hashes": app.state.source_hashes}

    @app.get("/api/admin/dashboard")
    def dashboard(db: DB):
        active = db.execute("SELECT slug,name FROM seasons WHERE active=1").fetchone()
        last = db.execute("""SELECT m.id,m.map_name,s.opponent,
                                    COALESCE(m.played_on,s.date) AS date,se.name AS season
                             FROM maps m JOIN series s ON s.id=m.series_id
                             JOIN seasons se ON se.id=s.season_id ORDER BY m.rowid DESC LIMIT 1""").fetchone()
        database_path = root / "data/r6stats.sqlite"
        publish_path = root / "data/publish-status.json"
        last_publish = json.loads(publish_path.read_text(encoding="utf-8")) if publish_path.exists() else None
        return {"active_season": dict(active) if active else None,
                "roster_count": db.execute("SELECT count(*) FROM players WHERE tracked=1").fetchone()[0],
                "maps_imported": db.execute("SELECT count(*) FROM maps WHERE series_id IN (SELECT id FROM series WHERE demo=0)").fetchone()[0],
                "demo_maps": db.execute("SELECT count(*) FROM maps WHERE series_id IN (SELECT id FROM series WHERE demo=1)").fetchone()[0],
                "last_imported": dict(last) if last else None,
                "last_publish": last_publish,
                "database": {"status": db.execute("PRAGMA integrity_check").fetchone()[0],
                             "path": str(database_path), "size_bytes": database_path.stat().st_size}}

    @app.get("/api/admin/seasons")
    def seasons(db: DB):
        return [dict(row) for row in db.execute("SELECT slug,name,active,start_date,end_date FROM seasons ORDER BY id DESC")]

    @app.post("/api/admin/seasons")
    def add_season(payload: SeasonCreate, db: DB):
        validate_season_dates(payload.start_date, payload.end_date)
        repo.season_create(db, payload.name, payload.start_date, payload.end_date)
        export(db, read_settings(root), root / "web/public/data")
        return {"ok": True}

    @app.patch("/api/admin/seasons/{slug}")
    def edit_season(slug: str, payload: SeasonUpdate, db: DB):
        validate_season_dates(payload.start_date, payload.end_date)
        repo.season_update(db, slug, payload.name, payload.start_date, payload.end_date)
        export(db, read_settings(root), root / "web/public/data")
        return {"ok": True, "slug": slug}

    @app.post("/api/admin/seasons/{slug}/activate")
    def activate_season(slug: str, db: DB):
        repo.season_activate(db, slug)
        export(db, read_settings(root), root / "web/public/data")
        return {"ok": True}

    @app.get("/api/admin/roster")
    def roster(db: DB):
        result = []
        for row in db.execute("SELECT id,slug,display_name,username,profile_id,tracked FROM players ORDER BY tracked DESC,display_name"):
            item = dict(row)
            item["profile_bound"] = bool(item.pop("profile_id"))
            item["aliases"] = [alias[0] for alias in db.execute("SELECT username FROM aliases WHERE player_id=? ORDER BY username", (row["id"],))]
            result.append(item)
        return result

    @app.post("/api/admin/roster")
    def add_player(payload: PlayerCreate, db: DB):
        repo.roster_add(db, payload.username, payload.display_name)
        export(db, read_settings(root), root / "web/public/data")
        return {"ok": True}

    @app.patch("/api/admin/roster/{player_id}")
    def edit_player(player_id: int, payload: PlayerUpdate, db: DB):
        repo.roster_update(db, player_id, display_name=payload.display_name, tracked=payload.tracked)
        export(db, read_settings(root), root / "web/public/data")
        return {"ok": True}

    @app.post("/api/admin/roster/{player_id}/aliases")
    def add_alias(player_id: int, payload: AliasCreate, db: DB):
        repo.roster_add_alias(db, player_id, payload.username, make_current=payload.make_current)
        export(db, read_settings(root), root / "web/public/data")
        return {"ok": True}

    @app.get("/api/admin/replays")
    def scan_replays(response: Response, db: DB):
        response.headers["Cache-Control"] = "no-store"
        config = read_settings(root)
        paths = sorted((p for p in replay_directory(config).iterdir() if p.is_dir() or p.suffix.lower() == ".zip"),
                       key=lambda p: p.stat().st_mtime, reverse=True)[:12]
        scanned = {}
        items = []
        for path in paths:
            key = replay_key(path)
            scanned[key] = path
            try:
                match = parse_match(path, allow_incomplete=True)
                complete = len(match.rounds) >= 2
                eligible = complete and is_custom_game(match.match_type)
                rehost_eligible = is_custom_game(match.match_type)
                tracked = len({roster["id"] for round_ in match.rounds for player in round_.players
                               if (roster := repo.roster_match(db, player)) is not None})
                try:
                    our_team, _ = repo.choose_team(db, match)
                except ValueError:
                    our_team = None
                score = [sum(round_.winner == team for round_ in match.rounds) for team in (0, 1)]
                duplicate = bool(db.execute("SELECT 1 FROM map_segments WHERE replay_id=?",
                                            (match.replay_id,)).fetchone()) if match.replay_id else False
                items.append({"id": key, "name": path.name, "map": match.map_name,
                              "timestamp": match.timestamp, "match_type": match.match_type,
                              "status": (scan_label(match.match_type) if complete or not rehost_eligible
                                         else "REHOST SEGMENT - only 1 replay round"),
                              "eligible": eligible, "rehost_eligible": rehost_eligible,
                              "tracked_count": tracked, "rounds": len(match.rounds), "score": score,
                              "our_team": our_team, "duplicate": duplicate})
            except (ValueError, OSError) as error:
                items.append({"id": key, "name": path.name, "eligible": False,
                              "status": f"Unable to inspect: {error}"})
        app.state.scanned = scanned
        return items

    @app.post("/api/admin/replays/preview")
    def preview_replay(payload: PreviewRequest, db: DB):
        if payload.replay_id:
            path = app.state.scanned.get(payload.replay_id)
            if path is None:
                raise ValueError("Replay selection expired. Scan the folder again.")
        elif payload.path:
            path = Path(payload.path).expanduser()
        else:
            raise ValueError("Select a scanned replay or enter a match folder/ZIP path.")
        match = parse_match(path)
        if not is_custom_game(match.match_type):
            raise ValueError(rejection_message(match.match_type))
        digest = fingerprint(path)
        duplicate = bool(db.execute("SELECT 1 FROM map_segments WHERE fingerprint=? OR (replay_id IS NOT NULL AND replay_id=?)",
                                    (digest, match.replay_id or None)).fetchone())
        team = None
        tracked = []
        ambiguity = None
        try:
            team, tracked = repo.choose_team(db, match, payload.team)
        except ValueError as error:
            if "ambiguous" not in str(error).lower():
                raise
            ambiguity = str(error)
        teams = [{"index": index, "players": [p.username for p in match.rounds[0].players if p.team == index]}
                 for index in (0, 1)]
        score = [sum(round_.winner == index for round_ in match.rounds) for index in (0, 1)]
        token = secrets.token_urlsafe(24)
        app.state.previews = {key: value for key, value in app.state.previews.items()
                              if time.time() - value.created < 1800}
        app.state.previews[token] = Preview(path, digest, match, time.time())
        active = db.execute("SELECT slug FROM seasons WHERE active=1").fetchone()
        return {"preview_token": token, "map": match.map_name, "timestamp": match.timestamp,
                "match_type": match.match_type, "game_mode": match.game_mode,
                "rounds": len(match.rounds), "score": score, "our_team": team,
                "tracked_players": tracked, "teams": teams, "ambiguous": ambiguity,
                "duplicate": duplicate, "active_season": active["slug"] if active else None,
                "competition_if_confirmed": "NECC"}

    @app.post("/api/admin/replays/import")
    def import_replay(payload: ImportRequest, db: DB):
        if not payload.confirm_necc:
            raise ValueError("Confirm that this selected Custom Game was an NECC map.")
        preview = app.state.previews.get(payload.preview_token)
        if not preview or time.time() - preview.created >= 1800:
            raise ValueError("Import preview expired. Preview the replay again.")
        if fingerprint(preview.path) != preview.fingerprint:
            raise ValueError("Replay files changed since preview. Preview the replay again.")
        match = preview.match
        if not is_custom_game(match.match_type):
            raise ValueError(rejection_message(match.match_type))
        team, _ = repo.choose_team(db, match, payload.team)
        config = read_settings(root)
        calculate_match(match, config["stats"]["trade_window_seconds"])
        archive_root = root / "data/replay-archive"
        prepared = replay_archive.prepare(preview.path, archive_root, preview.fingerprint, len(match.rounds))
        try:
            map_id = repo.insert_map(db, match, preview.fingerprint, team, payload.opponent.strip(),
                                     payload.week.strip(), payload.notes.strip(), payload.series_id or None,
                                     season_slug=payload.season_slug)
            try:
                replay_archive.commit(prepared, archive_root, db, map_id)
            except Exception:
                repo.match_delete(db, map_id)
                raise
        finally:
            prepared.cleanup()
        app.state.previews.pop(payload.preview_token, None)
        export(db, config, root / "web/public/data")
        return {"ok": True, "map_id": map_id, "rounds": len(match.rounds), "competition": "NECC"}

    @app.post("/api/admin/replays/rehost/preview")
    def preview_rehost(payload: RehostPreviewRequest, db: DB):
        paths = []
        for source in payload.segments:
            if bool(source.replay_id) == bool(source.path):
                raise ValueError("Select a scanned replay or enter one folder path per segment.")
            path = (app.state.scanned.get(source.replay_id) if source.replay_id else
                    Path(source.path).expanduser())
            if path is None:
                raise ValueError("Replay selection expired. Scan the folder again.")
            paths.append(path)
        exclusions = [item.model_dump() for item in payload.exclusions]
        logical, manifest, digest = assemble_rehost(paths, exclusions)
        match = logical.match
        team = None
        tracked = []
        ambiguity = None
        try:
            team, tracked = repo.choose_team(db, match, payload.team)
        except ValueError as error:
            if "ambiguous" not in str(error).lower():
                raise
            ambiguity = str(error)
        duplicate = any(db.execute("""SELECT 1 FROM map_segments WHERE fingerprint=? OR
                                (replay_id IS NOT NULL AND replay_id=?)""",
                                   (source["fingerprint"], source["replay_id"])).fetchone()
                        for source in manifest["segments"])
        token = secrets.token_urlsafe(24)
        app.state.previews = {key: value for key, value in app.state.previews.items()
                              if time.time() - value.created < 1800}
        app.state.previews[token] = Preview(paths[0], digest, match, time.time(), paths,
                                            manifest)
        active = db.execute("SELECT slug FROM seasons WHERE active=1").fetchone()
        rounds = []
        logical_score = [0, 0]
        for item in logical.mapping:
            segment_index = int(item.folder.split("-")[1]) - 1
            segment = logical.segments[segment_index]
            team_mapping = logical.segment_details[segment_index]["team_mapping"]
            source_round = next(round_ for round_ in segment.rounds
                                if round_.physical_number == item.physical_number)
            winner = team_mapping[source_round.round.winner]
            if item.logical_number is not None:
                logical_score[winner] += 1
            rounds.append({"segment": int(item.folder.split("-")[1]),
                           "physical_number": item.physical_number,
                           "filename": item.filename, "site": source_round.round.site,
                           "winner": winner, "physical_score": list(source_round.ending_scores),
                           "logical_score": list(logical_score),
                           "players": [[p.username for p in source_round.round.players
                                        if team_mapping[p.team] == team] for team in (0, 1)],
                           "logical_number": item.logical_number,
                           "exclusion_reason": item.exclusion_reason})
        first_names = {p.key: p.username for round_ in logical.segments[0].match.rounds
                       for p in round_.players}
        segment_summaries = []
        for detail, segment in zip(logical.segment_details, logical.segments):
            names = {p.key: p.username for round_ in segment.match.rounds for p in round_.players}
            present = [sorted(names[key] for physical_team, keys in enumerate(detail["rosters"])
                              if detail["team_mapping"][physical_team] == team for key in keys)
                       for team in (0, 1)]
            canonical = [set(logical.segment_details[0]["rosters"][team]) for team in (0, 1)]
            current = [set(key for physical_team, keys in enumerate(detail["rosters"])
                           if detail["team_mapping"][physical_team] == team for key in keys)
                       for team in (0, 1)]
            segment_summaries.append({"segment": detail["segment"],
                                      "source_name": manifest["segments"][detail["segment"] - 1]["source_name"],
                                      "players": present,
                                      "absent": [sorted(first_names.get(key, key) for key in canonical[team] - current[team])
                                                 for team in (0, 1)],
                                      "added": [sorted(names.get(key, key) for key in current[team] - canonical[team])
                                                for team in (0, 1)],
                                      "physical_start": detail["physical_start"],
                                      "logical_start": detail["logical_start"],
                                      "score_mode": detail["score_mode"]})
        return {"preview_token": token, "map": match.map_name, "timestamp": match.timestamp,
                "match_type": match.match_type, "game_mode": match.game_mode,
                "rounds": len(match.rounds), "score": list(logical.final_scores),
                "our_team": team, "tracked_players": tracked, "ambiguous": ambiguity,
                "teams": [{"index": index, "players": [p.username for p in match.rounds[0].players
                                                   if p.team == index]} for index in (0, 1)],
                "duplicate": bool(duplicate), "active_season": active["slug"] if active else None,
                "competition_if_confirmed": "NECC", "segments": segment_summaries,
                "roster_change_required": manifest["roster_change_confirmed"],
                "score_override_required": manifest["score_override_confirmed"],
                "physical_rounds": rounds}

    @app.post("/api/admin/replays/rehost/import")
    def import_rehost(payload: RehostImportRequest, db: DB):
        if not payload.confirm_necc or not payload.confirm_folders_one_map:
            raise ValueError("Confirm these Custom Game folders are one NECC competitive map.")
        preview = app.state.previews.get(payload.preview_token)
        if not preview or not preview.paths or not preview.rehost_manifest or time.time() - preview.created >= 1800:
            raise ValueError("Rehost preview expired. Preview the segments again.")
        if (preview.rehost_manifest.get("roster_change_confirmed") and
                not payload.confirm_roster_change):
            raise ValueError("Confirm the expected roster change before importing this rehost.")
        if (preview.rehost_manifest.get("score_override_confirmed") and
                not payload.confirm_score_override):
            raise ValueError("Confirm the physical 0-0 score restart before importing this rehost.")
        for path, source in zip(preview.paths, preview.rehost_manifest["segments"]):
            if source_fingerprint(path) != source["fingerprint"]:
                raise ValueError("A replay segment changed since preview. Preview it again.")
        team, _ = repo.choose_team(db, preview.match, payload.team)
        expected = ((payload.final_our_score, payload.final_their_score) if team == 0 else
                    (payload.final_their_score, payload.final_our_score))
        actual = tuple(sum(round_.winner == index for round_ in preview.match.rounds)
                       for index in (0, 1))
        if actual != expected or len(preview.match.rounds) != sum(expected):
            raise ValueError(f"Counted rounds give score {actual}; confirm final competitive "
                             "score and physical round exclusions before import.")
        config = read_settings(root)
        calculate_match(preview.match, config["stats"]["trade_window_seconds"])
        archive_root = root / "data/replay-archive"
        prepared = replay_archive.prepare_rehost(preview.paths, archive_root,
                                                 preview.fingerprint, preview.rehost_manifest)
        try:
            map_id = repo.insert_map(db, preview.match, preview.fingerprint, team,
                                     payload.opponent.strip(), payload.week.strip(),
                                     payload.notes.strip(), payload.series_id or None,
                                     season_slug=payload.season_slug,
                                     rehost_manifest=preview.rehost_manifest,
                                     source_segments=preview.rehost_manifest["segments"])
            try:
                replay_archive.commit_rehost(prepared, archive_root, db, map_id)
            except Exception:
                repo.match_delete(db, map_id)
                raise
        finally:
            prepared.cleanup()
        app.state.previews.pop(payload.preview_token, None)
        export(db, config, root / "web/public/data")
        return {"ok": True, "map_id": map_id, "rounds": len(preview.match.rounds),
                "segments": len(preview.paths), "competition": "NECC"}

    @app.get("/api/admin/series")
    def series(db: DB, season: str | None = None):
        query = """SELECT s.id,s.opponent,s.date,s.week,s.notes,se.slug AS season_slug,
                   count(m.id) AS maps FROM series s JOIN seasons se ON se.id=s.season_id
                   LEFT JOIN maps m ON m.series_id=s.id WHERE s.demo=0"""
        params = []
        if season:
            query += " AND se.slug=?"
            params.append(season)
        query += " GROUP BY s.id ORDER BY s.date DESC,s.rowid DESC"
        return [dict(row) for row in db.execute(query, params)]

    @app.patch("/api/admin/series/{series_id}")
    def edit_series(series_id: str, payload: SeriesUpdate, db: DB):
        with db:
            result = db.execute("""UPDATE series SET opponent=?,week=?,notes=?,date=COALESCE(?,date)
                                   WHERE id=? AND demo=0""",
                                (payload.opponent, payload.week.strip(), payload.notes.strip(), payload.date, series_id))
            if result.rowcount != 1:
                raise ValueError("Series not found.")
        export(db, read_settings(root), root / "web/public/data")
        return {"ok": True}

    @app.get("/api/admin/matches")
    def matches(db: DB, season: str | None = None):
        query = """SELECT m.id,m.map_name,m.match_type,m.game_mode,m.our_score,m.their_score,
                   s.id AS series_id,s.opponent,s.date AS series_date,
                   COALESCE(m.played_on,s.date) AS date,s.week,s.notes,s.competition,s.demo,
                   se.slug AS season_slug,se.name AS season_name
                   FROM maps m JOIN series s ON s.id=m.series_id JOIN seasons se ON se.id=s.season_id WHERE 1=1"""
        params = []
        if season:
            query += " AND se.slug=?"
            params.append(season)
        query += " ORDER BY COALESCE(m.played_on,s.date) DESC,m.rowid DESC"
        return [dict(row) for row in db.execute(query, params)]

    @app.get("/api/admin/matches/{map_id}")
    def match_detail(map_id: str, db: DB):
        row = db.execute("""SELECT m.id,m.map_name,m.match_type,m.game_mode,m.our_team,
                          m.our_score,m.their_score,m.normalized_json,m.rehost_json,
                          m.replay_data_complete,m.series_id,
                          COALESCE(m.played_on,s.date) AS date,s.date AS series_date,
                          s.opponent,s.week,s.notes,s.competition,s.demo,
                          se.slug AS season_slug,se.name AS season_name
                          FROM maps m JOIN series s ON s.id=m.series_id
                          JOIN seasons se ON se.id=s.season_id WHERE m.id=? AND s.demo=0""",
                         (map_id,)).fetchone()
        if not row:
            raise ValueError("NECC map not found.")
        match = Match.from_dict(json.loads(row["normalized_json"]))
        details = dict(row)
        details.pop("normalized_json")
        source = json.loads(details.pop("rehost_json")) if row["rehost_json"] else None
        details["source_kind"] = "rehost" if source else "normal"
        details["rehost"] = ({"segments": [{"segment": item["segment"],
                                            "source_name": item["source_name"]}
                                           for item in source["segments"]],
                              "mapping": source["mapping"],
                              "final_scores": source["final_scores"],
                              "segment_details": source.get("segment_details", []),
                              "roster_change_confirmed": source.get("roster_change_confirmed", False),
                              "score_override_confirmed": source.get("score_override_confirmed", False)}
                             if source else None)
        details["rounds"] = [{"number": round_.number, "site": round_.site,
                               "result": "Win" if round_.winner == row["our_team"] else "Loss"}
                              for round_ in match.rounds]
        details["tracked_players"] = [r[0] for r in db.execute("""SELECT DISTINCT p.display_name
                    FROM round_players rp JOIN rounds rd ON rd.id=rp.round_id
                    JOIN players p ON p.id=rp.player_id WHERE rd.map_id=? ORDER BY p.display_name""", (map_id,))]
        details["kd_players"] = manual_kd.map_players(
            db, map_id, read_settings(root)["stats"]["trade_window_seconds"])
        details["manual_kd_correction"] = any(p["corrected"] for p in details["kd_players"])
        details["rating_eligible"] = bool(row["replay_data_complete"]) and not details["manual_kd_correction"]
        details["archive"] = replay_archive.verify(db, root / "data/replay-archive", map_id)
        return details

    @app.put("/api/admin/matches/{map_id}/kd-corrections/{player_id}")
    def save_kd_correction(map_id: str, player_id: int, payload: KDCorrection, db: DB):
        row = manual_kd.save(db, map_id, player_id, payload.final_kills, payload.final_deaths,
                             payload.reason, payload.note,
                             read_settings(root)["stats"]["trade_window_seconds"])
        export(db, read_settings(root), root / "web/public/data")
        return row

    @app.delete("/api/admin/matches/{map_id}/kd-corrections/{player_id}")
    def remove_kd_correction(map_id: str, player_id: int, db: DB):
        manual_kd.remove(db, map_id, player_id)
        export(db, read_settings(root), root / "web/public/data")
        return {"ok": True}

    @app.get("/api/admin/matches/{map_id}/archive")
    def verify_archive(map_id: str, db: DB):
        return replay_archive.verify(db, root / "data/replay-archive", map_id)

    @app.post("/api/admin/matches/{map_id}/archive")
    def backfill_archive(map_id: str, payload: ArchiveBackfill, db: DB):
        if payload.confirm_map_id != map_id:
            raise ValueError("Confirm this exact map ID before archiving its replay.")
        archive_root = root / "data/replay-archive"
        row = replay_archive.map_record(db, map_id)
        if not row:
            raise ValueError("NECC map not found.")
        if replay_archive.archive_path(archive_root, row).exists():
            raise ValueError("This map already has a replay archive.")
        if row["rehost_json"]:
            source = json.loads(row["rehost_json"])
            if len(payload.segment_paths) != len(source["segments"]):
                raise ValueError("Supply each original rehost segment in confirmed order.")
            prepared = replay_archive.prepare_rehost(
                [Path(path) for path in payload.segment_paths], archive_root,
                row["fingerprint"], source)
        else:
            if not payload.path.strip():
                raise ValueError("Enter the original replay folder path.")
            prepared = replay_archive.prepare(payload.path, archive_root, row["fingerprint"],
                                              len(json.loads(row["normalized_json"])["rounds"]))
        try:
            if row["rehost_json"]:
                replay_archive.commit_rehost(prepared, archive_root, db, map_id)
            else:
                replay_archive.commit(prepared, archive_root, db, map_id)
        finally:
            prepared.cleanup()
        return replay_archive.verify(db, archive_root, map_id)

    @app.post("/api/admin/matches/{map_id}/archive/open")
    def open_archive(map_id: str, db: DB):
        status = replay_archive.verify(db, root / "data/replay-archive", map_id)
        if status["status"] == "Missing":
            raise ValueError("This map has no replay archive to open.")
        if os.name != "nt":
            raise ValueError("Opening Explorer is available only on Windows.")
        os.startfile(status["path"])
        return {"ok": True}

    @app.patch("/api/admin/matches/{map_id}")
    def edit_match(map_id: str, payload: MatchUpdate, db: DB):
        group_id = repo.match_update(db, map_id, played_on=payload.played_on,
                                     series_id=payload.series_id, make_new_series=payload.make_new_series)
        export(db, read_settings(root), root / "web/public/data")
        return {"ok": True, "series_id": group_id}

    @app.delete("/api/admin/matches/{map_id}")
    def delete_match(map_id: str, payload: MatchDelete, db: DB):
        if payload.confirm_map_id != map_id:
            raise ValueError("Confirm this exact map ID before deleting it.")
        replay_archive.delete_map_and_archive(db, root / "data/replay-archive", map_id)
        export(db, read_settings(root), root / "web/public/data")
        return {"ok": True, "message": "Map and its private replay archive deleted. Statistics recalculated; historical player identities remain."}

    @app.post("/api/admin/matches/{map_id}/reparse")
    def reparse_match(map_id: str, payload: MatchReparse, db: DB):
        if payload.confirm_map_id != map_id:
            raise ValueError("Confirm this exact map ID before reparsing it.")
        row = replay_archive.map_record(db, map_id)
        if not row:
            raise ValueError("NECC map not found.")
        if payload.from_archive:
            status = replay_archive.verify(db, root / "data/replay-archive", map_id)
            if status["status"] != "Healthy":
                raise ValueError(f"Archive is {status['status']}: {status['message']}")
            path = Path(status["path"])
        elif row["rehost_json"] and payload.segment_paths:
            path = None
        elif payload.path.strip():
            path = Path(payload.path).expanduser()
        else:
            raise ValueError("Choose the archive or enter the original replay folder path.")
        if row["rehost_json"]:
            source = json.loads(row["rehost_json"])
            paths = ([path / f"segment-{index:02d}" for index in
                      range(1, len(source["segments"]) + 1)] if payload.from_archive else
                     [Path(item).expanduser() for item in payload.segment_paths])
            if len(paths) != len(source["segments"]):
                raise ValueError("Supply every rehost segment in the original order.")
            exclusions = [{"segment": item["segment"],
                           "physical_number": item["physical_number"],
                           "reason": item["exclusion_reason"]}
                          for item in source["mapping"] if item["logical_number"] is None]
            logical, _, digest = assemble_rehost(paths, exclusions,
                                                 tuple(source["final_scores"]),
                                                 manifest_version=source.get("version", 1))
            match = logical.match
            if digest != row["fingerprint"]:
                raise ValueError("Rehost source identity differs from this imported map.")
        else:
            match = parse_match(path)
            digest = fingerprint(path)
        config = read_settings(root)
        calculate_match(match, config["stats"]["trade_window_seconds"])
        repo.reparse_map(db, map_id, match, digest)
        export(db, config, root / "web/public/data")
        return {"ok": True, "map_id": map_id, "rounds": len(match.rounds),
                "message": "Map reparsed from its verified archive." if payload.from_archive else
                           "Map reparsed from its original replay. Statistics and local website data regenerated; nothing was published."}

    @app.get("/api/admin/settings")
    def settings():
        config = read_settings(root)
        return {"team_name": config["team"]["name"], "short_name": config["team"]["short_name"],
                "accent": config["team"]["accent"], "replay_path": config["replays"].get("path", ""),
                "trade_window_seconds": config["stats"]["trade_window_seconds"],
                "rating_version": config["stats"].get("rating_version", RATING_VERSION),
                "publishing_enabled": config["publishing"].get("enabled", True),
                "branch": config["publishing"].get("branch", "main"),
                "remote_url": config["publishing"].get("remote_url", ""),
                "site_url": config["publishing"].get("site_url", "")}

    @app.put("/api/admin/settings")
    def save_settings(payload: SettingsUpdate, db: DB):
        if payload.replay_path.strip() and not Path(payload.replay_path.strip()).expanduser().is_dir():
            raise ValueError("Replay folder does not exist. Select the folder containing match directories.")
        if payload.rating_version == "siege_style_v2" and payload.trade_window_seconds != 8:
            raise ValueError("siege_style_v2 requires its frozen 8-second trade window.")
        config = read_settings(root)
        config["team"] = {"name": payload.team_name.strip(), "short_name": payload.short_name.strip(),
                          "accent": payload.accent}
        config["replays"]["path"] = payload.replay_path.strip()
        config["stats"]["trade_window_seconds"] = payload.trade_window_seconds
        config["stats"]["rating_version"] = payload.rating_version
        config["publishing"] = {"enabled": payload.publishing_enabled, "branch": payload.branch,
                                "remote_url": payload.remote_url, "site_url": payload.site_url}
        target = root / "config/settings.json"
        temporary = target.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
        temporary.replace(target)
        export(db, config, root / "web/public/data")
        return {"ok": True}

    @app.post("/api/admin/publish")
    def publish_now(db: DB):
        return publish_site(db, read_settings(root), root)

    @app.post("/api/admin/recalculate")
    def recalculate(db: DB):
        count = db.execute("SELECT count(*) FROM maps").fetchone()[0]
        export(db, read_settings(root), root / "web/public/data")
        return {"ok": True, "maps": count,
                "message": f"Statistics recalculated from {count} stored normalized maps; website data regenerated."}

    @app.post("/api/admin/regenerate")
    def regenerate(db: DB):
        export(db, read_settings(root), root / "web/public/data")
        return {"ok": True, "message": "Public website JSON regenerated from the local database."}

    return app


app = create_app()
