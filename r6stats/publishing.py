"""Export and publish only generated public statistics."""
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from r6stats.export import export

DATA_PATHSPEC = ":(glob)web/public/data/**/*.json"


def validate_public_data(root: Path) -> int:
    """Validate generated references and reject private replay fields before publishing."""
    data_root = root / "web/public/data"
    paths = list(data_root.rglob("*.json"))
    if not paths:
        raise ValueError("Website export contains no JSON files.")
    documents = {}
    forbidden = {"profile_id", "profileid", "username", "normalized_json", "recordingprofileid"}

    def inspect(value):
        if isinstance(value, dict):
            if any(key.casefold() in forbidden for key in value):
                raise ValueError("Website export contains a private replay identity field.")
            for child in value.values():
                inspect(child)
        elif isinstance(value, list):
            for child in value:
                inspect(child)

    for path in paths:
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError(f"Generated website JSON is invalid: {path.name}") from error
        inspect(document)
        documents[path.relative_to(data_root).as_posix()] = document
    index = documents.get("index.json")
    method = documents.get("methodology.json")
    if not isinstance(index, dict) or not isinstance(method, dict):
        raise ValueError("Website index or methodology JSON is missing.")
    if index.get("rating_version") != method.get("rating_version"):
        raise ValueError("Website rating versions do not agree.")
    for season in index.get("seasons", []):
        name = f"seasons/{season['slug']}.json"
        document = documents.get(name)
        if not isinstance(document, dict):
            raise ValueError(f"Website season data is missing: {name}")
        if document.get("maps") != len(document.get("matches", [])):
            raise ValueError(f"Website season map count is inconsistent: {name}")
        for match in document["matches"]:
            if f"matches/{match['id']}.json" not in documents:
                raise ValueError(f"Website match data is missing: {match['id']}")
    for player in index.get("players", []):
        slug = player["slug"]
        if f"players/{slug}/career.json" not in documents:
            raise ValueError(f"Website career data is missing: {slug}")
        for season in index.get("seasons", []):
            if f"players/{slug}/{season['slug']}.json" not in documents:
                raise ValueError(f"Website player season data is missing: {slug} / {season['slug']}")
    return len(paths)


def _run(arguments: list[str], root: Path, *, check: bool = False) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(arguments, cwd=root, capture_output=True, text=True, check=check)
    except FileNotFoundError as error:
        raise ValueError(f"Required command was not found: {arguments[0]}") from error
    except subprocess.CalledProcessError as error:
        detail = (error.stderr or error.stdout or str(error)).strip()
        raise ValueError(f"{arguments[0]} failed: {detail}") from error


def publish_site(db, config: dict, root: Path) -> dict:
    root = root.resolve()
    export(db, config, root / "web/public/data")
    count = validate_public_data(root)
    if not config["publishing"].get("enabled", True):
        return {"status": "disabled", "message": f"Validated {count} website JSON files. Publishing is disabled in Settings."}
    if not (root / "web/node_modules").exists():
        raise ValueError("Website dependencies are missing. Run scripts/setup.ps1 before publishing.")
    _run(["npm.cmd" if shutil.which("npm.cmd") else "npm", "run", "build"], root / "web", check=True)
    if not (root / ".git").exists():
        return {"status": "needs_git", "message": "Website data validated and built. Initialize Git and add a GitHub remote before publishing."}
    branch = config["publishing"].get("branch", "main")
    valid_branch = _run(["git", "check-ref-format", "--branch", branch], root)
    if valid_branch.returncode:
        raise ValueError("Configured Git branch name is invalid.")
    remote_url = config["publishing"].get("remote_url", "").strip()
    if remote_url:
        current = _run(["git", "remote", "get-url", "origin"], root)
        if current.returncode:
            _run(["git", "remote", "add", "origin", remote_url], root, check=True)
        elif current.stdout.strip() != remote_url:
            _run(["git", "remote", "set-url", "origin", remote_url], root, check=True)
    _run(["git", "add", "-A", "--", DATA_PATHSPEC], root, check=True)
    diff = _run(["git", "diff", "--cached", "--quiet", "--", DATA_PATHSPEC], root)
    if diff.returncode not in (0, 1):
        raise ValueError((diff.stderr or diff.stdout or "Unable to check website changes.").strip())
    if diff.returncode == 1:
        active = db.execute("SELECT name FROM seasons WHERE active=1").fetchone()
        season = "All seasons" if not active else " ".join(active[0].split())
        maps = db.execute("SELECT count(*) FROM maps WHERE series_id IN (SELECT id FROM series WHERE demo=0)").fetchone()[0]
        description = f"Update NECC stats: {season} ({maps} maps)"
        _run(["git", "commit", "-m", description, "--", DATA_PATHSPEC], root, check=True)
    pushed = _run(["git", "push", "origin", f"HEAD:refs/heads/{branch}"], root)
    if pushed.returncode:
        return {"status": "push_failed", "message": "Local commit succeeded, but Git push failed. Your statistics are safe. Authenticate Git and push manually.",
                "detail": (pushed.stderr or pushed.stdout).strip()}
    commit = _run(["git", "rev-parse", "--short", "HEAD"], root, check=True).stdout.strip()
    result = {"status": "published", "message": "Website update submitted to GitHub Pages." if diff.returncode else "GitHub is up to date.",
              "at": datetime.now(timezone.utc).isoformat(), "commit": commit, "files_validated": count}
    status_file = root / "data/publish-status.json"
    status_file.parent.mkdir(parents=True, exist_ok=True)
    status_file.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result
