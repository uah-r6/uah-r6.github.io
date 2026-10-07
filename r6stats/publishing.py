"""Export and publish only generated public statistics."""
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from r6stats.export import export
from r6stats.series_export import player_series

DATA_PATHSPEC = ":(glob)web/public/data/**/*.json"


def validate_public_data(root: Path) -> int:
    """Validate generated references and reject private replay fields before publishing."""
    data_root = root / "web/public/data"
    paths = list(data_root.rglob("*.json"))
    if not paths:
        raise ValueError("Website export contains no JSON files.")
    documents = {}
    forbidden = {"profile_id", "profileid", "username", "normalized_json", "recordingprofileid",
                 "fingerprint", "archive_path", "source_path", "rehost_json", "database_path"}

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
    player_slugs = {p['slug'] for p in index.get('players', [])}
    for team in index.get('teams', []):
        slug = team['slug']
        for period in [s['slug'] for s in index.get('seasons', [])] + ['career']:
            name = f'teams/{slug}/{period}.json'
            scope = documents.get(name)
            if not isinstance(scope, dict) or scope.get('team', {}).get('slug') != slug:
                raise ValueError(f'Website team scope is missing or incorrect: {name}')
            matches = scope.get('matches', [])
            if scope.get('maps') != len(matches) or scope.get('rating_version') != index.get('rating_version'):
                raise ValueError(f'Website team scope counts/version differ: {name}')
            for match in matches:
                original = documents.get(f"matches/{match['id']}.json", {})
                if match.get('team_slug') != slug or original.get('team_slug') != slug or (
                        period != 'career' and match.get('season') != period):
                    raise ValueError(f'Website team match ownership differs: {name}')
            if any(p['slug'] not in player_slugs for p in scope.get('players', [])):
                raise ValueError(f'Website team player reference is unknown: {name}')
        for alias in team.get('aliases', []):
            for period in ['index', 'career'] + [s['slug'] for s in index.get('seasons', [])]:
                if documents.get(f'teams/{alias}/{period}.json') != documents.get(f'teams/{slug}/{period}.json'):
                    raise ValueError(f'Website team slug alias is missing or stale: {alias}')
    for name, series in documents.items():
        if not name.startswith('series/'):
            continue
        maps = series.get('maps', [])
        sid = series.get('id')
        if (name != f'series/{sid}.json' or sid != series.get('series_id') or
                not maps or len({m['id'] for m in maps}) != len(maps) or
                series.get('rating_version') != index.get('rating_version')):
            raise ValueError('Website series identity or logical map inventory differs.')
        record = series.get('recorded_maps', {})
        if record != {'count': len(maps), 'wins': sum(m['result'] == 'WIN' for m in maps),
                      'losses': sum(m['result'] == 'LOSS' for m in maps)}:
            raise ValueError('Website recorded series result differs.')
        for m in maps:
            original = documents.get(f"matches/{m['id']}.json", {})
            if any(original.get(k) != series.get(k) or m.get(k) != series.get(k)
                   for k in ('series_id', 'team_slug', 'team_name', 'season', 'opponent', 'week', 'notes')):
                raise ValueError('Website series map metadata differs.')
        for player in series.get('players', []):
            if (player['slug'] not in player_slugs or
                    not 0 <= player['rating_rounds'] <= player['rounds'] or
                    not 0 <= player['rating_maps'] <= player['maps'] or
                    ((player['rating'] is None) != (player['rating_rounds'] == 0))):
                raise ValueError('Website Series Rating player or coverage is invalid.')
    series_documents = {d['id']: d for name, d in documents.items() if name.startswith('series/')}
    if series_documents:
        for name, document in documents.items():
            if name.startswith('matches/') and document.get('series_id') not in series_documents:
                raise ValueError('Website map series reference is missing.')
            if not name.startswith('players/'):
                continue
            seen = set()
            for point in document.get('series_ratings', []):
                sid = point.get('id')
                series = series_documents.get(sid, {})
                player = next((p for p in series.get('players', []) if p['slug'] == document.get('slug')), None)
                if not player or sid in seen or point != player_series(series, player):
                    raise ValueError('Website player Series Rating reference differs.')
                if not name.endswith('/career.json') and point['season'] != name.split('/')[-1][:-5]:
                    raise ValueError('Website player Series Rating season differs.')
                seen.add(sid)
    for name, document in documents.items():
        if not name.startswith('matches/'):
            continue
        participants = {p['slug'] for p in document.get('players', [])}
        for round_ in document.get('rounds', []):
            groups = round_.get('highlights', [])
            if len(groups) > 2 or len({g['player_slug'] for g in groups}) != len(groups):
                raise ValueError('Website round highlights exceed compact group limits.')
            for group in groups:
                if (set(group) != {'player_slug', 'player_name', 'labels', 'emphasis'} or
                        group['player_slug'] not in participants or not 1 <= len(group['labels']) <= 2 or
                        group['emphasis'] not in ('strong', 'notable', 'objective') or
                        len(set(group['labels'])) != len(group['labels']) or
                        any(label not in ('3K', '4K', 'ACE', '1v1', '1v2', '1v3', '1v4', '1v5', 'Plant', 'Disable') for label in group['labels'])):
                    raise ValueError('Website round highlight is invalid or private.')
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
