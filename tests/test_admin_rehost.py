"""The browser API imports explicit rehosts without changing normal imports."""
import json
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from r6stats.admin.server import create_app
from r6stats.db import repository as repo

from test_confirmed_rehost import segment


def test_scan_allows_one_round_custom_only_as_rehost_segment(tmp_path):
    replay_root = tmp_path / "replays"
    replay_root.mkdir()
    custom = segment(replay_root, "segment1", [0])
    ranked = segment(replay_root, "segment2", [0])
    ranked.match.match_type = "Ranked"
    (tmp_path / "config").mkdir()
    (tmp_path / "config/settings.json").write_text(json.dumps({
        "team": {"name": "Test", "short_name": "T", "accent": "#82e3db"},
        "replays": {"path": str(replay_root)},
        "stats": {"trade_window_seconds": 8, "rating_version": "collegiate_v1"},
        "publishing": {"enabled": False, "branch": "main"},
    }), encoding="utf-8")
    matches = {"segment1": custom.match, "segment2": ranked.match}
    with TestClient(create_app(tmp_path)) as client, patch(
            "r6stats.admin.server.parse_match",
            side_effect=lambda path, **kwargs: matches[Path(path).name]):
        response = client.get("/api/admin/replays", params={'team_id': 1})
    assert response.status_code == 200
    rows = {row["name"]: row for row in response.json()}
    assert rows["segment1"]["rounds"] == 1
    assert rows["segment1"]["eligible"] is False
    assert rows["segment1"]["rehost_eligible"] is True
    assert rows["segment2"]["rehost_eligible"] is False
    assert "Ranked" in rows["segment2"]["status"]


def test_admin_rehost_preview_import_archive_reparse_delete(tmp_path):
    first = segment(tmp_path, "segment1", [0, 1, 0])
    second = segment(tmp_path, "segment2", [0, 1])
    (tmp_path / "config").mkdir()
    (tmp_path / "config/settings.json").write_text(json.dumps({
        "team": {"name": "Test", "short_name": "T", "accent": "#82e3db"},
        "replays": {"path": str(tmp_path)},
        "stats": {"trade_window_seconds": 8, "rating_version": "collegiate_v1"},
        "publishing": {"enabled": False, "branch": "main"},
    }), encoding="utf-8")
    with closing(repo.connect(tmp_path / "data/r6stats.sqlite")) as db:
        repo.season_create(db, "Fall 2026")
        for index in range(5):
            repo.roster_add(db, f"Our{index}", team_id=1)
    matches = {"segment1": first.match, "segment2": second.match,
               "segment-01": first.match, "segment-02": second.match}
    app = create_app(tmp_path)
    with TestClient(app) as client, patch(
            "r6stats.parser.confirmed_rehost.parse_match",
            side_effect=lambda path, **kwargs: matches[Path(path).name]):
        headers = {"X-R6-Admin-Token": client.get("/api/admin/session").json()["token"]}
        request = {"segments": [{"path": str(tmp_path / "segment1")},
                                {"path": str(tmp_path / "segment2")}],
                   "exclusions": [{"segment": 1, "physical_number": 3,
                                   "reason": "abandoned rehost round"}], "team": 0}
        preview = client.post("/api/admin/replays/rehost/preview", json={**(request), 'team_id': 1}, headers=headers)
        assert preview.status_code == 200, preview.text
        data = preview.json()
        assert data["score"] == [2, 2] and data["rounds"] == 4
        assert data["score_override_required"] is True
        assert data["roster_change_required"] is False
        assert [item["logical_number"] for item in data["physical_rounds"]] == [1, 2, None, 3, 4]
        with closing(repo.connect(tmp_path / "data/r6stats.sqlite")) as db:
            assert db.execute("SELECT count(*) FROM maps").fetchone()[0] == 0
        import_request = {"preview_token": data["preview_token"],
                          "season_slug": "fall-2026", "opponent": "Opponent",
                          "team": 0, "confirm_necc": True,
                          "confirm_folders_one_map": False,
                          "final_our_score": 2, "final_their_score": 2}
        assert client.post("/api/admin/replays/rehost/import", json={**(import_request), 'team_id': 1},
                           headers=headers).status_code == 400
        import_request["confirm_folders_one_map"] = True
        import_request["final_our_score"] = 3
        assert client.post("/api/admin/replays/rehost/import", json={**(import_request), 'team_id': 1},
                           headers=headers).status_code == 400
        import_request["final_our_score"] = 2
        import_request["confirm_score_override"] = True
        imported = client.post("/api/admin/replays/rehost/import", json={**(import_request), 'team_id': 1},
                               headers=headers)
        assert imported.status_code == 200, imported.text
        map_id = imported.json()["map_id"]
        archive_url = f"/api/admin/matches/{map_id}/archive"
        assert client.get(archive_url).json()["status"] == "Healthy"
        detail = client.get(f"/api/admin/matches/{map_id}").json()
        assert detail["source_kind"] == "rehost" and len(detail["rehost"]["segments"]) == 2
        with closing(repo.connect(tmp_path / "data/r6stats.sqlite")) as db:
            assert db.execute("SELECT count(*) FROM map_segments WHERE map_id=?", (map_id,)).fetchone()[0] == 2
            assert db.execute("SELECT count(*) FROM rounds WHERE map_id=?", (map_id,)).fetchone()[0] == 4
            assert db.execute("SELECT count(*) FROM kill_events").fetchone()[0] == 4
        public = (tmp_path / "web/public/data/matches" / f"{map_id}.json").read_text()
        assert "segment1" not in public and "source_path" not in public
        duplicate = client.post("/api/admin/replays/rehost/preview", json={**(request), 'team_id': 1}, headers=headers)
        assert duplicate.json()["duplicate"] is True
        with patch("r6stats.admin.server.parse_match", return_value=first.match):
            normal_preview = client.post("/api/admin/replays/preview",
                                         json={**({"path": str(tmp_path / "segment1")}), 'team_id': 1}, headers=headers)
        assert normal_preview.status_code == 200 and normal_preview.json()["duplicate"] is True
        archived_file = Path(client.get(archive_url).json()["path"]) / "segment-01/segment1-R03.rec"
        original = archived_file.read_bytes()
        archived_file.write_bytes(b"tampered excluded round")
        refused = client.post(f"/api/admin/matches/{map_id}/reparse",
                              json={"from_archive": True, "confirm_map_id": map_id}, headers=headers)
        assert refused.status_code == 400 and "Hash mismatch" in refused.text
        with closing(repo.connect(tmp_path / "data/r6stats.sqlite")) as db:
            assert db.execute("SELECT count(*) FROM rounds WHERE map_id=?", (map_id,)).fetchone()[0] == 4
        archived_file.write_bytes(original)
        reparsed = client.post(f"/api/admin/matches/{map_id}/reparse",
                               json={"from_archive": True, "confirm_map_id": map_id}, headers=headers)
        assert reparsed.status_code == 200, reparsed.text
        with closing(repo.connect(tmp_path / "data/r6stats.sqlite")) as db:
            assert db.execute("SELECT count(*) FROM rounds WHERE map_id=?", (map_id,)).fetchone()[0] == 4
        deleted = client.request("DELETE", f"/api/admin/matches/{map_id}",
                                 json={"confirm_map_id": map_id}, headers=headers)
        assert deleted.status_code == 200, deleted.text
        with closing(repo.connect(tmp_path / "data/r6stats.sqlite")) as db:
            assert db.execute("SELECT count(*) FROM maps").fetchone()[0] == 0
            assert db.execute("SELECT count(*) FROM players").fetchone()[0] == 5


def test_admin_rehost_5v5_to_4v5_requires_roster_confirmation_and_keeps_rating(tmp_path):
    first = segment(tmp_path, "segment1", [0, 1], start_score=(0, 0))
    second = segment(tmp_path, "segment2", [0, 1], ours_count=4,
                     start_score=(1, 1), ours_side="Defense")
    (tmp_path / "config").mkdir()
    (tmp_path / "config/settings.json").write_text(json.dumps({
        "team": {"name": "Test", "short_name": "T", "accent": "#82e3db"},
        "replays": {"path": str(tmp_path)},
        "stats": {"trade_window_seconds": 8, "rating_version": "collegiate_v1"},
        "publishing": {"enabled": False, "branch": "main"},
    }), encoding="utf-8")
    with closing(repo.connect(tmp_path / "data/r6stats.sqlite")) as db:
        repo.season_create(db, "Fall 2026")
        for index in range(5):
            repo.roster_add(db, f"Our{index}", team_id=1)
    matches = {"segment1": first.match, "segment2": second.match,
               "segment-01": first.match, "segment-02": second.match}
    app = create_app(tmp_path)
    with TestClient(app) as client, patch(
            "r6stats.parser.confirmed_rehost.parse_match",
            side_effect=lambda path, **kwargs: matches[Path(path).name]):
        headers = {"X-R6-Admin-Token": client.get("/api/admin/session").json()["token"]}
        request = {"segments": [{"path": str(tmp_path / "segment1")},
                                {"path": str(tmp_path / "segment2")}], "team": 0}
        response = client.post("/api/admin/replays/rehost/preview", json={**(request), 'team_id': 1}, headers=headers)
        assert response.status_code == 200, response.text
        preview = response.json()
        assert preview["score"] == [2, 2] and preview["rounds"] == 4
        assert preview["roster_change_required"] is True
        assert preview["score_override_required"] is False
        assert preview["segments"][1]["absent"][0] == ["Our4"]
        assert preview["segments"][1]["players"][0] == ["Our0", "Our1", "Our2", "Our3"]
        assert preview["segments"][1]["physical_start"] == [1, 1]
        assert preview["segments"][1]["logical_start"] == [1, 1]
        payload = {"preview_token": preview["preview_token"], "season_slug": "fall-2026",
                   "opponent": "Opponent", "team": 0, "confirm_necc": True,
                   "confirm_folders_one_map": True,
                   "final_our_score": 2, "final_their_score": 2}
        refused = client.post("/api/admin/replays/rehost/import", json={**(payload), 'team_id': 1}, headers=headers)
        assert refused.status_code == 400 and "roster change" in refused.text
        with closing(repo.connect(tmp_path / "data/r6stats.sqlite")) as db:
            assert db.execute("SELECT count(*) FROM maps").fetchone()[0] == 0
        payload["confirm_roster_change"] = True
        imported = client.post("/api/admin/replays/rehost/import", json={**(payload), 'team_id': 1}, headers=headers)
        assert imported.status_code == 200, imported.text
        map_id = imported.json()["map_id"]
        detail = client.get(f"/api/admin/matches/{map_id}").json()
        assert detail["replay_data_complete"] == 1 and detail["rating_eligible"] is True
        assert detail["rehost"]["roster_change_confirmed"] is True
        assert detail["rehost"]["score_override_confirmed"] is False
        assert detail["archive"]["status"] == "Healthy"
        with closing(repo.connect(tmp_path / "data/r6stats.sqlite")) as db:
            absent = db.execute("""SELECT p.id FROM players p WHERE p.username='Our4'""").fetchone()[0]
            assert db.execute("""SELECT count(*) FROM round_players rp JOIN rounds rd
                ON rd.id=rp.round_id WHERE rd.map_id=? AND rp.player_id=?""",
                (map_id, absent)).fetchone()[0] == 2
            assert db.execute("SELECT count(*) FROM round_players rp JOIN rounds rd ON rd.id=rp.round_id WHERE rd.map_id=?", (map_id,)).fetchone()[0] == 38
        public = json.loads((tmp_path / "web/public/data/matches" / f"{map_id}.json").read_text())
        absent_stats = next(p for p in public["players"] if p["name"] == "Our4")
        assert absent_stats["rounds"] == 2 and absent_stats["rating"] is not None
        assert absent_stats["sides"]["Defense"]["rounds"] == 0
        assert absent_stats["operators"]["Defense"] == {}
        assert public["rating_eligible"] is True
        assert "segment1" not in json.dumps(public)
        reparse = client.post(f"/api/admin/matches/{map_id}/reparse",
                              json={"from_archive": True, "confirm_map_id": map_id}, headers=headers)
        assert reparse.status_code == 200, reparse.text
        with closing(repo.connect(tmp_path / "data/r6stats.sqlite")) as db:
            assert db.execute("SELECT count(*) FROM round_players rp JOIN rounds rd ON rd.id=rp.round_id WHERE rd.map_id=?", (map_id,)).fetchone()[0] == 38
