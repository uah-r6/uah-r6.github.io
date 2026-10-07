"""Private replay retention, verification, backfill, reparse and delete."""

import json
import tempfile
from contextlib import closing
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from r6stats.admin.server import create_app
from r6stats.db import repository as repo
from r6stats.parser.siege_dissect import normalize
from r6stats.replay_archive import commit, prepare, replay_fingerprint, verify

from test_admin import match_fixture


def source_rounds(root: Path) -> Path:
    source = root / "Match-test"
    source.mkdir()
    (source / "Match-test-R01.rec").write_bytes(b"first physical round")
    (source / "Match-test-R02.rec").write_bytes(b"second physical round")
    return source


def two_round_match():
    raw = match_fixture("CustomGameOnline", "replay-archive-test")
    raw["rounds"].append({**raw["rounds"][0], "roundNumber": 2})
    return normalize(raw)


def test_archive_integrity_and_no_orphan_after_failed_prepare():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        source = source_rounds(root)
        fingerprint = replay_fingerprint(list(source.glob("*.rec")))
        archive_root = root / "data/replay-archive"
        with closing(repo.connect(root / "data/test.sqlite")) as db:
            repo.season_create(db, "Fall 2026")
            match = two_round_match()
            repo.roster_add(db, match.rounds[0].players[0].username, team_id=1)
            map_id = repo.insert_map(db, match, fingerprint, 0, "Opponent", organization_team_id=1)
            assert verify(db, archive_root, map_id)["status"] == "Missing"
            try:
                prepare(source, archive_root, "wrong-fingerprint", 2)
            except ValueError as error:
                assert "changed while copying" in str(error)
            else:
                raise AssertionError("Mismatched replay was accepted")
            assert not list(archive_root.glob(".pending-*"))
            prepared = prepare(source, archive_root, fingerprint, 2)
            try:
                target = commit(prepared, archive_root, db, map_id)
            finally:
                prepared.cleanup()
            assert verify(db, archive_root, map_id)["status"] == "Healthy"
            manifest = json.loads((target / "manifest.json").read_text(encoding="utf-8"))
            assert manifest["map_id"] == map_id
            assert [item["physical_round_number"] for item in manifest["files"]] == [1, 2]
            assert [item["filename"] for item in manifest["files"]] == ["Match-test-R01.rec", "Match-test-R02.rec"]
            second = target / "Match-test-R02.rec"
            second.write_bytes(b"changed replay bytes")
            assert verify(db, archive_root, map_id)["status"] == "Hash mismatch"
            second.unlink()
            assert verify(db, archive_root, map_id)["status"] == "Incomplete"
            (target / "manifest.json").write_text("{invalid", encoding="utf-8")
            assert verify(db, archive_root, map_id)["status"] == "Manifest invalid"


def test_admin_backfill_reparse_and_delete_archive_without_changing_metadata():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        source = source_rounds(root)
        fingerprint = replay_fingerprint(list(source.glob("*.rec")))
        (root / "config").mkdir()
        (root / "config/settings.json").write_text(json.dumps({
            "team": {"name": "Test", "short_name": "T", "accent": "#82e3db"},
            "replays": {"path": str(source.parent)},
            "stats": {"trade_window_seconds": 8, "rating_version": "collegiate_v1"},
            "publishing": {"enabled": False, "branch": "main"},
        }), encoding="utf-8")
        with closing(repo.connect(root / "data/r6stats.sqlite")) as db:
            repo.season_create(db, "Fall 2026")
            for index in range(5):
                repo.roster_add(db, f"Player{index}", team_id=1)
            original = two_round_match()
            map_id = repo.insert_map(db, original, fingerprint, 0, "Opponent", "Week 3", "Keep notes", organization_team_id=1)
            repo.match_update(db, map_id, played_on="2026-09-30")
            before = dict(db.execute("SELECT * FROM maps WHERE id=?", (map_id,)).fetchone())
            series = dict(db.execute("SELECT * FROM series WHERE id=?", (before["series_id"],)).fetchone())
            player_binding = db.execute("SELECT player_id FROM round_players WHERE player_key='ours-0'").fetchone()[0]
        app = create_app(root)
        with TestClient(app) as client:
            headers = {"X-R6-Admin-Token": client.get("/api/admin/session").json()["token"]}
            archive_url = f"/api/admin/matches/{map_id}/archive"
            assert client.get(archive_url).json()["status"] == "Missing"
            wrong = client.post(archive_url, json={"path": str(source), "confirm_map_id": "wrong"}, headers=headers)
            assert wrong.status_code == 400
            bad_source = root / "different"
            bad_source.mkdir()
            for file in source.glob("*.rec"):
                (bad_source / file.name).write_bytes(b"different")
            wrong_bytes = client.post(archive_url, json={"path": str(bad_source),
                                                          "confirm_map_id": map_id}, headers=headers)
            assert wrong_bytes.status_code == 400
            assert client.get(archive_url).json()["status"] == "Missing"
            archived = client.post(archive_url, json={"path": str(source),
                                                       "confirm_map_id": map_id}, headers=headers)
            assert archived.status_code == 200, archived.text
            assert archived.json()["status"] == "Healthy"
            archive_path = Path(archived.json()["path"])
            assert client.get(f"/api/admin/matches/{map_id}").json()["archive"]["rounds"] == 2
            with closing(repo.connect(root / "data/r6stats.sqlite")) as db:
                assert dict(db.execute("SELECT * FROM maps WHERE id=?", (map_id,)).fetchone()) == before
            replacement = deepcopy(original)
            replacement.rounds[0].players[0].operator = "Zofia"
            reparse_url = f"/api/admin/matches/{map_id}/reparse"
            with patch("r6stats.admin.server.parse_match", return_value=replacement):
                reparsed = client.post(reparse_url, json={"from_archive": True,
                                                          "confirm_map_id": map_id}, headers=headers)
            assert reparsed.status_code == 200, reparsed.text
            with closing(repo.connect(root / "data/r6stats.sqlite")) as db:
                after = dict(db.execute("SELECT * FROM maps WHERE id=?", (map_id,)).fetchone())
                assert {key: after[key] for key in before if key != "normalized_json"} == {
                    key: before[key] for key in before if key != "normalized_json"}
                assert dict(db.execute("SELECT * FROM series WHERE id=?", (before["series_id"],)).fetchone()) == series
                assert db.execute("SELECT player_id FROM round_players WHERE player_key='ours-0'").fetchone()[0] == player_binding
                assert db.execute("SELECT operator FROM round_players WHERE player_key='ours-0'").fetchone()[0] == "Zofia"
            broken = deepcopy(replacement)
            broken.replay_id = "wrong-replay"
            with patch("r6stats.admin.server.parse_match", return_value=broken):
                failed = client.post(reparse_url, json={"from_archive": True,
                                                        "confirm_map_id": map_id}, headers=headers)
            assert failed.status_code == 400
            with closing(repo.connect(root / "data/r6stats.sqlite")) as db:
                assert dict(db.execute("SELECT * FROM maps WHERE id=?", (map_id,)).fetchone()) == after
            (archive_path / "Match-test-R02.rec").write_bytes(b"corrupted")
            rejected = client.post(reparse_url, json={"from_archive": True,
                                                      "confirm_map_id": map_id}, headers=headers)
            assert rejected.status_code == 400 and "Hash mismatch" in rejected.text
            with closing(repo.connect(root / "data/r6stats.sqlite")) as db:
                assert dict(db.execute("SELECT * FROM maps WHERE id=?", (map_id,)).fetchone()) == after
            deleted = client.request("DELETE", f"/api/admin/matches/{map_id}",
                                     json={"confirm_map_id": map_id}, headers=headers)
            assert deleted.status_code == 200, deleted.text
            assert not archive_path.exists()
            with closing(repo.connect(root / "data/r6stats.sqlite")) as db:
                assert db.execute("SELECT count(*) FROM maps").fetchone()[0] == 0
                assert db.execute("SELECT count(*) FROM players WHERE profile_id='ours-0'").fetchone()[0] == 1
            assert not list((root / "data/replay-archive").glob(".pending-delete-*"))
