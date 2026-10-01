"""The browser API imports explicit rehosts without changing normal imports."""
import json
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from r6stats.admin.server import create_app
from r6stats.db import repository as repo

from test_confirmed_rehost import segment


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
            repo.roster_add(db, f"Our{index}")
    matches = {"segment1": first.match, "segment2": second.match,
               "segment-01": first.match, "segment-02": second.match}
    app = create_app(tmp_path)
    with TestClient(app) as client, patch(
            "r6stats.parser.confirmed_rehost.parse_match",
            side_effect=lambda path: matches[Path(path).name]):
        headers = {"X-R6-Admin-Token": client.get("/api/admin/session").json()["token"]}
        request = {"segments": [{"path": str(tmp_path / "segment1")},
                                {"path": str(tmp_path / "segment2")}],
                   "exclusions": [{"segment": 1, "physical_number": 3,
                                   "reason": "abandoned rehost round"}], "team": 0}
        preview = client.post("/api/admin/replays/rehost/preview", json=request, headers=headers)
        assert preview.status_code == 200, preview.text
        data = preview.json()
        assert data["score"] == [2, 2] and data["rounds"] == 4
        assert [item["logical_number"] for item in data["physical_rounds"]] == [1, 2, None, 3, 4]
        with closing(repo.connect(tmp_path / "data/r6stats.sqlite")) as db:
            assert db.execute("SELECT count(*) FROM maps").fetchone()[0] == 0
        import_request = {"preview_token": data["preview_token"],
                          "season_slug": "fall-2026", "opponent": "Opponent",
                          "team": 0, "confirm_necc": True,
                          "confirm_folders_one_map": False,
                          "final_our_score": 2, "final_their_score": 2}
        assert client.post("/api/admin/replays/rehost/import", json=import_request,
                           headers=headers).status_code == 400
        import_request["confirm_folders_one_map"] = True
        import_request["final_our_score"] = 3
        assert client.post("/api/admin/replays/rehost/import", json=import_request,
                           headers=headers).status_code == 400
        import_request["final_our_score"] = 2
        imported = client.post("/api/admin/replays/rehost/import", json=import_request,
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
        duplicate = client.post("/api/admin/replays/rehost/preview", json=request, headers=headers)
        assert duplicate.json()["duplicate"] is True
        with patch("r6stats.admin.server.parse_match", return_value=first.match):
            normal_preview = client.post("/api/admin/replays/preview",
                                         json={"path": str(tmp_path / "segment1")}, headers=headers)
        assert normal_preview.status_code == 200 and normal_preview.json()["duplicate"] is True
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
