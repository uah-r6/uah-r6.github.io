"""Final-map K/D overrides affect display totals, never replay-derived features."""
import json
from contextlib import closing

from fastapi.testclient import TestClient

from r6stats.admin.server import create_app
from r6stats.db import repository as repo
from r6stats.parser.models import Kill, Match, Player, Round
from r6stats.stats.calculate import calculate_match


def fixture(replay_id):
    players = [Player(f"ours-{i}", f"Player{i}", 0, "Buck", "Attack") for i in range(5)]
    players += [Player(f"enemy-{i}", f"Enemy{i}", 1, "Wamai", "Defense") for i in range(5)]
    return Match(replay_id, "2026-09-29T20:00:00Z", "Bank", "Custom Game", "Bomb",
                 [Round(1, "Lockers", 0, "KilledOpponents", players,
                        [Kill(0, 25, "ours-0", "enemy-0", 0, 1, True)])])


def read(root, name):
    return json.loads((root / "web/public/data" / name).read_text(encoding="utf-8"))


def test_admin_manual_final_kd_is_auditable_and_rating_ineligible(tmp_path):
    (tmp_path / "config").mkdir()
    (tmp_path / "config/settings.json").write_text(json.dumps({
        "team": {"name": "Test", "short_name": "T", "accent": "#82e3db"},
        "replays": {"path": ""},
        "stats": {"trade_window_seconds": 8, "rating_version": "collegiate_v1"},
        "publishing": {"enabled": False, "branch": "main"},
    }), encoding="utf-8")
    with closing(repo.connect(tmp_path / "data/r6stats.sqlite")) as db:
        repo.season_create(db, "Fall 2026")
        for i in range(5):
            repo.roster_add(db, f"Player{i}", team_id=1)
        first = fixture("partial")
        second = fixture("complete")
        partial_id = repo.insert_map(db, first, "hash-partial", 0, "Opponent", organization_team_id=1)
        complete_id = repo.insert_map(db, second, "hash-complete", 0, "Opponent", organization_team_id=1)
        player_id = db.execute("SELECT id FROM players WHERE username='Player0'").fetchone()[0]
    app = create_app(tmp_path)
    with TestClient(app) as client:
        headers = {"X-R6-Admin-Token": client.get("/api/admin/session").json()["token"]}
        detail = client.get(f"/api/admin/matches/{partial_id}").json()
        player = next(p for p in detail["kd_players"] if p["player_id"] == player_id)
        assert player["replay_kills"] == 1 and player["replay_deaths"] == 0
        assert detail["rating_eligible"] is True
        baseline = read(tmp_path, "players/player0/fall-2026.json") if (tmp_path / "web/public/data/players/player0/fall-2026.json").exists() else None
        bad = client.put(f"/api/admin/matches/{partial_id}/kd-corrections/{player_id}",
                         json={"final_kills": 5, "final_deaths": 3, "reason": " "}, headers=headers)
        assert bad.status_code == 400
        saved = client.put(f"/api/admin/matches/{partial_id}/kd-corrections/{player_id}",
                           json={"final_kills": 5, "final_deaths": 3,
                                 "reason": "Missing final replay segment", "note": "Scoreboard confirmed"},
                           headers=headers)
        assert saved.status_code == 200, saved.text
        assert saved.json()["kill_adjustment"] == 4 and saved.json()["death_adjustment"] == 3
        detail = client.get(f"/api/admin/matches/{partial_id}").json()
        assert detail["replay_data_complete"] == 0 and detail["manual_kd_correction"]
        assert detail["rating_eligible"] is False
        map_player = next(p for p in read(tmp_path, f"matches/{partial_id}.json")["players"] if p["slug"] == "player0")
        assert (map_player["kills"], map_player["deaths"], map_player["kd"], map_player["rating"]) == (5, 3, 5/3, None)
        raw = calculate_match(first)["ours-0"]
        for key in ("kpr", "kost", "srv", "opening_kills", "refrag_kills", "deaths_traded",
                    "kills_traded", "clutches", "plants", "disables", "headshots", "hs", "operators", "sides"):
            assert map_player[key] == raw[key], key
        season = read(tmp_path, "players/player0/fall-2026.json")
        career = read(tmp_path, "players/player0/career.json")
        assert (season["kills"], season["deaths"], season["kd"]) == (6, 3, 2)
        assert (career["kills"], career["deaths"], career["kd"]) == (6, 3, 2)
        assert season["kpr"] == 1 and season["rating"] == calculate_match(
            second, rating_version="collegiate_v1")["ours-0"]["rating"]
        assert baseline is None or baseline["kpr"] == season["kpr"]
        public_text = (tmp_path / "web/public/data/matches" / f"{partial_id}.json").read_text()
        assert "Missing final replay segment" not in public_text and "Scoreboard confirmed" not in public_text
        with closing(repo.connect(tmp_path / "data/r6stats.sqlite")) as db:
            correction = db.execute("SELECT * FROM map_kd_corrections WHERE map_id=?", (partial_id,)).fetchone()
            assert tuple(correction[k] for k in ("replay_kills", "replay_deaths", "final_kills", "final_deaths")) == (1, 0, 5, 3)
            assert json.loads(db.execute("SELECT normalized_json FROM maps WHERE id=?", (partial_id,)).fetchone()[0]) == first.to_dict()
        edited = client.put(f"/api/admin/matches/{partial_id}/kd-corrections/{player_id}",
                            json={"final_kills": 4, "final_deaths": 2, "reason": "Corrected final board"},
                            headers=headers)
        assert edited.status_code == 200
        assert read(tmp_path, "players/player0/fall-2026.json")["kills"] == 5
        with closing(repo.connect(tmp_path / "data/r6stats.sqlite")) as db:
            repo.reparse_map(db, partial_id, first, "hash-partial")
            correction = db.execute("SELECT final_kills,replay_kills FROM map_kd_corrections WHERE map_id=?",
                                    (partial_id,)).fetchone()
            assert tuple(correction) == (4, 1)
        recalculated = client.post("/api/admin/recalculate", json={}, headers=headers)
        assert recalculated.status_code == 200, recalculated.text
        assert read(tmp_path, "players/player0/fall-2026.json")["kills"] == 5
        removed = client.request("DELETE", f"/api/admin/matches/{partial_id}/kd-corrections/{player_id}",
                                 json={}, headers=headers)
        assert removed.status_code == 200
        assert read(tmp_path, "players/player0/fall-2026.json")["kills"] == 2
        assert client.get(f"/api/admin/matches/{partial_id}").json()["rating_eligible"] is False
        client.put(f"/api/admin/matches/{partial_id}/kd-corrections/{player_id}",
                   json={"final_kills": 4, "final_deaths": 2, "reason": "Board"}, headers=headers)
        deleted = client.request("DELETE", f"/api/admin/matches/{partial_id}",
                                 json={"confirm_map_id": partial_id}, headers=headers)
        assert deleted.status_code == 200, deleted.text
        with closing(repo.connect(tmp_path / "data/r6stats.sqlite")) as db:
            assert db.execute("SELECT count(*) FROM map_kd_corrections").fetchone()[0] == 0
            assert db.execute("SELECT count(*) FROM players").fetchone()[0] == 5
        assert read(tmp_path, "players/player0/fall-2026.json")["kills"] == 1
        client.put(f"/api/admin/matches/{complete_id}/kd-corrections/{player_id}",
                   json={"final_kills": 2, "final_deaths": 1, "reason": "Incomplete map"},
                   headers=headers)
        only_partial = read(tmp_path, "players/player0/fall-2026.json")
        assert (only_partial["kills"], only_partial["deaths"], only_partial["rating"]) == (2, 1, None)
        assert read(tmp_path, "players/player0/career.json")["rating"] is None
