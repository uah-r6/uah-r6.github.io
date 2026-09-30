from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import subprocess
import json

from r6stats.db import repository as repo
from r6stats.publishing import DATA_PATHSPEC, publish_site, validate_public_data


def test_publish_retries_push_when_generated_data_has_not_changed():
    with TemporaryDirectory() as directory:
        root = Path(directory)
        (root / ".git").mkdir()
        data = root / "web/public/data"
        data.mkdir(parents=True)
        (root / "web/node_modules").mkdir()
        (data / "index.json").write_text(json.dumps({"rating_version": "collegiate_v1", "seasons": [], "players": []}))
        (data / "methodology.json").write_text(json.dumps({"rating_version": "collegiate_v1"}))
        results = [
            subprocess.CompletedProcess([], 0, "", ""),  # public build
            subprocess.CompletedProcess([], 0, "", ""),  # valid branch
            subprocess.CompletedProcess([], 0, "", ""),  # git add
            subprocess.CompletedProcess([], 0, "", ""),  # no staged JSON difference
            subprocess.CompletedProcess([], 0, "", ""),  # retry push
            subprocess.CompletedProcess([], 0, "abc123\n", ""),  # commit ID
        ]
        with patch("r6stats.publishing.export"), patch("r6stats.publishing._run", side_effect=results) as run:
            result = publish_site(None, {"publishing": {"enabled": True, "branch": "main"}}, root)
        assert result["status"] == "published"
        assert run.call_args_list[4].args[0] == ["git", "push", "origin", "HEAD:refs/heads/main"]
        assert (root / "data/publish-status.json").exists()


def test_public_validation_rejects_private_replay_identity():
    with TemporaryDirectory() as directory:
        root = Path(directory)
        data = root / "web/public/data"
        data.mkdir(parents=True)
        (data / "index.json").write_text(json.dumps({"rating_version": "collegiate_v1", "seasons": [], "players": [], "profile_id": "private"}))
        (data / "methodology.json").write_text(json.dumps({"rating_version": "collegiate_v1"}))
        try:
            validate_public_data(root)
            assert False, "private profile ID was accepted"
        except ValueError as error:
            assert "private replay identity" in str(error)


def test_failed_push_keeps_local_match_data_and_uses_descriptive_commit():
    with TemporaryDirectory() as directory:
        root = Path(directory)
        (root / ".git").mkdir()
        (root / "web/node_modules").mkdir(parents=True)
        data = root / "web/public/data"
        data.mkdir(parents=True)
        (data / "index.json").write_text(json.dumps({"rating_version": "collegiate_v1", "seasons": [], "players": []}))
        (data / "methodology.json").write_text(json.dumps({"rating_version": "collegiate_v1"}))
        db = repo.connect(root / "data/r6stats.sqlite")
        try:
            repo.season_create(db, "Fall 2026")
            results = [subprocess.CompletedProcess([], 0, "", "") for _ in range(3)]
            results += [subprocess.CompletedProcess([], 1, "", ""),  # changed JSON
                        subprocess.CompletedProcess([], 0, "", ""),  # local commit
                        subprocess.CompletedProcess([], 1, "", "authentication failed")]
            with patch("r6stats.publishing.export"), patch("r6stats.publishing._run", side_effect=results) as run:
                result = publish_site(db, {"publishing": {"enabled": True, "branch": "main"}}, root)
            assert result["status"] == "push_failed"
            assert "Fall 2026 (0 maps)" in run.call_args_list[4].args[0][3]
            assert db.execute("SELECT count(*) FROM seasons").fetchone()[0] == 1
            assert not (root / "data/publish-status.json").exists()
        finally:
            db.close()


def test_git_pathspec_stages_only_generated_json():
    with TemporaryDirectory() as directory:
        root = Path(directory)
        data = root / "web/public/data"
        data.mkdir(parents=True)
        (data / "index.json").write_text("{}")
        (data / "unrelated.txt").write_text("do not stage")
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(["git", "add", "-A", "--", DATA_PATHSPEC], cwd=root, check=True)
        staged = subprocess.run(["git", "diff", "--cached", "--name-only"], cwd=root,
                                capture_output=True, text=True, check=True).stdout.splitlines()
        assert staged == ["web/public/data/index.json"]
        subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                        "commit", "-q", "-m", "Generated data", "--", DATA_PATHSPEC], cwd=root, check=True)
        tracked = subprocess.run(["git", "ls-files"], cwd=root,
                                 capture_output=True, text=True, check=True).stdout.splitlines()
        assert tracked == ["web/public/data/index.json"]
        (data / "matches").mkdir()
        stale = data / "matches/old.json"
        stale.write_text("{}")
        subprocess.run(["git", "add", "-A", "--", DATA_PATHSPEC], cwd=root, check=True)
        subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                        "commit", "-q", "-m", "Old map", "--", DATA_PATHSPEC], cwd=root, check=True)
        stale.unlink()
        subprocess.run(["git", "add", "-A", "--", DATA_PATHSPEC], cwd=root, check=True)
        deleted = subprocess.run(["git", "diff", "--cached", "--name-status"], cwd=root,
                                 capture_output=True, text=True, check=True).stdout.splitlines()
        assert deleted == ["D\tweb/public/data/matches/old.json"]
