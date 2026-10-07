"""Browser admin API checks, including the manual NECC decision boundary."""
import json
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from r6stats.admin.server import create_app
from r6stats.db import repository as repo
from r6stats.parser.siege_dissect import normalize


def match_fixture(kind: str, replay_id: str) -> dict:
    return {"rounds": [{"matchID": replay_id, "timestamp": "2026-09-29T20:00:00Z",
                        "matchType": {"name": kind}, "map": {"name": "Bank"},
                        "gamemode": {"name": "Bomb"}, "roundNumber": 1, "site": "B Lockers",
                        "teams": [{"won": True, "role": "Attack", "winCondition": "KilledOpponents"},
                                  {"won": False, "role": "Defense"}],
                        "players": [{"profileID": f"ours-{i}", "username": f"Player{i}",
                                     "teamIndex": 0, "operator": {"name": "Buck"}} for i in range(5)] +
                                   [{"profileID": f"enemy-{i}", "username": f"Enemy{i}",
                                     "teamIndex": 1, "operator": {"name": "Wamai"}} for i in range(5)],
                        "matchFeedback": []}]}


def test_admin_manages_roster_and_only_imports_confirmed_custom_game():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        replays = root / "replays"
        replays.mkdir()
        for name in ("ranked", "custom"):
            folder = replays / name
            folder.mkdir()
            (folder / f"{name}-R01.rec").write_bytes((name + " one").encode())
            (folder / f"{name}-R02.rec").write_bytes((name + " two").encode())
        (root / "config").mkdir()
        (root / "config/settings.json").write_text(json.dumps({
            "team": {"name": "Test", "short_name": "T", "accent": "#82e3db"},
            "replays": {"path": str(replays)},
            "stats": {"trade_window_seconds": 8, "rating_version": "collegiate_v1"},
            "publishing": {"enabled": False, "branch": "main"},
        }), encoding="utf-8")
        app = create_app(root)
        with TestClient(app) as client:
            token = client.get("/api/admin/session").json()["token"]
            headers = {"X-R6-Admin-Token": token}
            assert client.post("/api/admin/seasons", json={"name": "Fall 2026"}).status_code == 403
            assert client.post("/api/admin/seasons", json={"name": "Fall 2026"},
                               headers={**headers, "Origin": "https://evil.example"}).status_code == 403
            assert client.post("/api/admin/seasons", json={"name": "Fall 2026"}, headers=headers).status_code == 200
            assert client.post("/api/admin/seasons", json={"name": "Spring 2027"}, headers=headers).status_code == 200
            for index in range(5):
                assert client.post("/api/admin/roster", json={**({"username": f"Player{index}"}), 'team_id': 1}, headers=headers).status_code == 200
            roster = client.get("/api/admin/roster").json()
            first_id = next(row["id"] for row in roster if row["username"] == "Player0")
            assert client.patch(f"/api/admin/roster/{first_id}", json={"display_name": "Captain"}, headers=headers).status_code == 200
            assert client.post(f"/api/admin/roster/{first_id}/aliases",
                               json={"username": "RenamedCaptain"}, headers=headers).status_code == 200
            roster = client.get("/api/admin/roster").json()
            captain = next(row for row in roster if row["id"] == first_id)
            assert captain["display_name"] == "Captain"
            assert set(captain["aliases"]) == {"Player0", "RenamedCaptain"}
            assert client.get("/api/admin/dashboard").json()["roster_count"] == 5

            def parse(path, *, allow_incomplete=False):
                kind = "Ranked" if Path(path).name == "ranked" else "CustomGameOnline"
                raw = match_fixture(kind, f"replay-{Path(path).name}")
                raw["rounds"].append({**raw["rounds"][0], "roundNumber": 2})
                return normalize(raw)

            with patch("r6stats.admin.server.parse_match", side_effect=parse):
                scan = client.get("/api/admin/replays", params={'team_id': 1})
                assert scan.status_code == 200
                results = {row["name"]: row for row in scan.json()}
                assert results["ranked"]["eligible"] is False
                assert results["custom"]["eligible"] is True
                with closing(repo.connect(root / "data/r6stats.sqlite")) as db:
                    assert db.execute("SELECT count(*) FROM maps").fetchone()[0] == 0
                assert not list((root / "data").rglob("manifest.json"))
                rejected = client.post("/api/admin/replays/preview", json={**({"replay_id": results["ranked"]["id"]}), 'team_id': 1}, headers=headers)
                assert rejected.status_code == 400
                assert "Ranked" in rejected.json()["detail"]
                preview = client.post("/api/admin/replays/preview", json={**({"replay_id": results["custom"]["id"], "season_slug": "spring-2027"}), 'team_id': 1}, headers=headers)
                assert preview.status_code == 200
                data = preview.json()
                assert data["match_type"] == "CustomGameOnline"
                assert data["competition_if_confirmed"] == "NECC"
                assert data["tracked_players"]
                request = {"preview_token": data["preview_token"], "season_slug": "spring-2027",
                           "opponent": "UAB", "week": "Week 1", "notes": "", "team": 0,
                           "confirm_necc": False}
                assert client.post("/api/admin/replays/import", json={**(request), 'team_id': 1}, headers=headers).status_code == 400
                with closing(repo.connect(root / "data/r6stats.sqlite")) as db:
                    assert db.execute("SELECT count(*) FROM maps").fetchone()[0] == 0
                assert not list((root / "data").rglob("manifest.json"))
                request["confirm_necc"] = True
                imported = client.post("/api/admin/replays/import", json={**(request), 'team_id': 1}, headers=headers)
                assert imported.status_code == 200, imported.text
                assert imported.json()["competition"] == "NECC"
                archive = client.get(f"/api/admin/matches/{imported.json()['map_id']}/archive").json()
                assert archive["status"] == "Healthy" and archive["rounds"] == 2
                assert client.post("/api/admin/replays/import", json={**(request), 'team_id': 1}, headers=headers).status_code == 400
                with closing(repo.connect(root / "data/r6stats.sqlite")) as db:
                    row = db.execute("SELECT se.slug, s.competition, m.match_type FROM maps m JOIN series s ON s.id=m.series_id JOIN seasons se ON se.id=s.season_id").fetchone()
                    assert tuple(row) == ("spring-2027", "NECC", "CustomGameOnline")
                    assert db.execute("SELECT count(*) FROM maps").fetchone()[0] == 1
                assert client.patch(f"/api/admin/roster/{first_id}", json={"tracked": False}, headers=headers).status_code == 200
                assert client.get("/api/admin/dashboard").json()["roster_count"] == 4
                with closing(repo.connect(root / "data/r6stats.sqlite")) as db:
                    assert db.execute("SELECT count(*) FROM round_players WHERE player_id=?", (first_id,)).fetchone()[0] == 2


def test_season_match_maintenance_keeps_player_history():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        (root / "config").mkdir()
        (root / "config/settings.json").write_text(json.dumps({
            "team": {"name": "Test", "short_name": "T", "accent": "#82e3db"},
            "replays": {"path": ""},
            "stats": {"trade_window_seconds": 8, "rating_version": "collegiate_v1"},
            "publishing": {"enabled": False, "branch": "main"},
        }), encoding="utf-8")
        with closing(repo.connect(root / "data/r6stats.sqlite")) as db:
            repo.season_create(db, "Fall 2026")
            for index in range(5):
                repo.roster_add(db, f"Player{index}", team_id=1)
            maps = []
            for index in range(3):
                match = normalize(match_fixture("Custom Game", f"map-{index}"))
                series_id = maps[0][1] if index == 1 else None
                map_id = repo.insert_map(db, match, f"fingerprint-{index}", 0,
                                         "UAB" if index < 2 else "North", series_id=series_id, organization_team_id=1)
                group_id = db.execute("SELECT series_id FROM maps WHERE id=?", (map_id,)).fetchone()[0]
                maps.append((map_id, group_id))
            player_id = db.execute("SELECT id FROM players WHERE username='Player0'").fetchone()[0]

        app = create_app(root)
        with TestClient(app) as client:
            headers = {"X-R6-Admin-Token": client.get("/api/admin/session").json()["token"]}
            invalid_dates = client.patch("/api/admin/seasons/fall-2026", json={
                "name": "Autumn 2026", "start_date": "2026-12-01", "end_date": "2026-09-01"}, headers=headers)
            assert invalid_dates.status_code == 400
            edited = client.patch("/api/admin/seasons/fall-2026", json={
                "name": "Autumn 2026", "start_date": "2026-09-01", "end_date": "2026-12-15"}, headers=headers)
            assert edited.status_code == 200, edited.text
            season = client.get("/api/admin/seasons").json()[0]
            assert season["slug"] == "fall-2026" and season["name"] == "Autumn 2026"
            assert season["start_date"] == "2026-09-01"
            with closing(repo.connect(root / "data/r6stats.sqlite")) as db:
                repo.season_activate(db, "Autumn 2026")
                assert db.execute("SELECT slug FROM seasons WHERE active=1").fetchone()[0] == "fall-2026"
            detail = client.get(f"/api/admin/matches/{maps[1][0]}")
            assert detail.status_code == 200
            assert detail.json()["rounds"][0]["result"] == "Win"
            assert len(detail.json()["tracked_players"]) == 5
            moved = client.patch(f"/api/admin/matches/{maps[1][0]}", json={
                "played_on": "2026-10-03", "series_id": maps[2][1]}, headers=headers)
            assert moved.status_code == 200, moved.text
            assert moved.json()["series_id"] == maps[2][1]
            separate = client.patch(f"/api/admin/matches/{maps[1][0]}", json={
                "played_on": "2026-10-04", "make_new_series": True}, headers=headers)
            assert separate.status_code == 200, separate.text
            new_group = separate.json()["series_id"]
            assert new_group not in {maps[0][1], maps[2][1]}
            assert client.patch(f"/api/admin/series/{new_group}", json={
                "opponent": "West", "date": "2026-10-04", "week": "Week 3", "notes": "Playoffs"}, headers=headers).status_code == 200
            assert client.patch(f"/api/admin/roster/{player_id}", json={"tracked": False}, headers=headers).status_code == 200
            public = json.loads((root / "web/public/data/index.json").read_text(encoding="utf-8"))
            retired = next(p for p in public["players"] if p["slug"] == "player0")
            assert retired["active"] is False
            retired_stats = json.loads((root / "web/public/data/players/player0/fall-2026.json").read_text(encoding="utf-8"))
            assert retired_stats["maps"] == 3
            assert client.request("DELETE", f"/api/admin/matches/{maps[0][0]}", json={"confirm_map_id": "wrong"}, headers=headers).status_code == 400
            deleted = client.request("DELETE", f"/api/admin/matches/{maps[0][0]}", json={"confirm_map_id": maps[0][0]}, headers=headers)
            assert deleted.status_code == 200, deleted.text
            with closing(repo.connect(root / "data/r6stats.sqlite")) as db:
                assert db.execute("SELECT count(*) FROM maps").fetchone()[0] == 2
                assert db.execute("SELECT count(*) FROM rounds WHERE map_id=?", (maps[0][0],)).fetchone()[0] == 0
                player = db.execute("SELECT profile_id,tracked FROM players WHERE id=?", (player_id,)).fetchone()
                assert player["profile_id"] == "ours-0" and player["tracked"] == 0
            season_public = json.loads((root / "web/public/data/seasons/fall-2026.json").read_text(encoding="utf-8"))
            assert season_public["maps"] == 2
            retired_after = json.loads((root / "web/public/data/players/player0/fall-2026.json").read_text(encoding="utf-8"))
            assert retired_after["maps"] == 2
            assert not (root / f"web/public/data/matches/{maps[0][0]}.json").exists()
            assert client.post("/api/admin/recalculate", json={}, headers=headers).status_code == 200
            assert client.post("/api/admin/regenerate", json={}, headers=headers).status_code == 200
            settings = client.get("/api/admin/settings").json()
            settings.update({"remote_url": "https://github.com/example/stats.git",
                             "site_url": "https://example.github.io/stats/"})
            assert client.put("/api/admin/settings", json=settings, headers=headers).status_code == 200
            assert client.get("/api/admin/settings").json()["site_url"] == "https://example.github.io/stats/"
            settings["rating_version"] = "unsupported"
            assert client.put("/api/admin/settings", json=settings, headers=headers).status_code == 422


def test_existing_database_gets_optional_date_columns():
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "old.sqlite"
        db = sqlite3.connect(path)
        db.execute("CREATE TABLE seasons(id INTEGER PRIMARY KEY, slug TEXT, name TEXT, active INTEGER)")
        db.execute("""CREATE TABLE maps(id TEXT PRIMARY KEY, series_id TEXT, replay_id TEXT,
                    fingerprint TEXT, map_name TEXT, match_type TEXT, game_mode TEXT,
                    our_team INTEGER, our_score INTEGER, their_score INTEGER, normalized_json TEXT)""")
        db.commit()
        db.close()
        with closing(repo.connect(path)) as upgraded:
            assert {row["name"] for row in upgraded.execute("PRAGMA table_info(seasons)")} >= {"start_date", "end_date"}
            assert "played_on" in {row["name"] for row in upgraded.execute("PRAGMA table_info(maps)")}
