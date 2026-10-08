"""Private cloud intake and staging. The existing local importer owns all statistics."""
import hashlib
from copy import deepcopy
from datetime import datetime, timezone
import json
import re
import threading
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from uuid import UUID

from r6stats import replay_archive

LOCK = threading.RLock()


def safe_name(value, *, replay=False):
    if (not isinstance(value, str) or not 0 < len(value) <= 160 or
            re.search(r'[<>:"/\\|?*\x00-\x1f\x7f]', value) or value.endswith(('.', ' ')) or
            value in ('.', '..') or re.match(r'^(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\.|$)', value, re.I) or
            (replay and not value.lower().endswith('.rec'))):
        raise ValueError('Submission contains an unsafe replay filename.')
    return value


def identity(value):
    try:
        if str(UUID(value)) != value:
            raise ValueError()
    except (ValueError, TypeError, AttributeError):
        raise ValueError('Invalid submission identity.') from None
    return value


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    temporary.replace(path)


class Client:
    def __init__(self, root):
        self.root = Path(root).resolve()
        path = self.root / 'data/private/submissions.json'
        self.config = json.loads(path.read_text(encoding='utf-8')) if path.is_file() else {}
        self.url = self.config.get('worker_url', '').rstrip('/')
        self.token = self.config.get('admin_token', '')
        if self.url and (urlparse(self.url).scheme != 'https' or
                         not (urlparse(self.url).hostname or '').endswith('.workers.dev') or urlparse(self.url).username or urlparse(self.url).query or urlparse(self.url).fragment or urlparse(self.url).path not in ('', '/')):
            raise ValueError('The private submission configuration must use an HTTPS workers.dev URL.')

    @property
    def configured(self):
        return bool(self.url and len(self.token) >= 32)

    def request(self, path, method='GET', payload=None):
        if not self.configured:
            raise ValueError('Replay inbox is not configured on this PC. See docs/SUBMISSIONS.md.')
        request = Request(self.url + '/v1/admin' + path, method=method,
                          headers={'Authorization': 'Bearer ' + self.token,
                                   'Content-Type': 'application/json', 'User-Agent': 'UAH-R6-local-admin'},
                          data=None if payload is None else json.dumps(payload).encode())
        try:
            return urlopen(request, timeout=120)
        except HTTPError as error:
            try:
                message = json.loads(error.read(8192)).get('error', 'Request failed.')
            except (ValueError, UnicodeError):
                message = 'Request failed.'
            raise ValueError(f'Replay inbox ({error.code}): {message}') from None
        except (URLError, TimeoutError):
            raise ValueError('Cannot reach the replay inbox. Local statistics remain safe; retry later.') from None

    def call(self, path, method='GET', payload=None):
        with self.request(path, method, payload) as response:
            return json.load(response)


def staging_root(root):
    return (Path(root).resolve() / 'data/submission-staging').resolve()


def directory(root, submission):
    base = staging_root(root)
    result = (base / identity(submission)).resolve()
    if not result.is_relative_to(base):
        raise ValueError('Submission staging path is outside the private inbox.')
    return result


def validate_manifest(remote):
    identity(remote['id'])
    folders = remote['folders']
    if not 0 < len(folders) <= 12 or not 0 < len(remote['files']) <= 240:
        raise ValueError('Submission has an invalid replay inventory.')
    ids = {identity(f['id']) for f in folders}
    if len(ids) != len(folders):
        raise ValueError('Submission has duplicate folder identities.')
    names = set()
    file_ids = set()
    for f in folders:
        safe_name(f['name'])
        first, last = f.get('first_file_modified_at'), f.get('last_file_modified_at')
        if first is not None or last is not None:
            try:
                if not all(isinstance(t, str) and re.fullmatch(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z', t) for t in (first, last)):
                    raise ValueError()
                if datetime.fromisoformat(first) > datetime.fromisoformat(last):
                    raise ValueError()
            except (ValueError, TypeError):
                raise ValueError('Invalid private replay file timestamp range.') from None
    for f in remote['files']:
        identity(f['id'])
        if f['id'] in file_ids:
            raise ValueError('Submission has duplicate replay identities.')
        file_ids.add(f['id'])
        if f['folder_id'] not in ids or f['submission_id'] != remote['id']:
            raise ValueError('Submission replay ownership differs.')
        safe_name(f['name'], replay=True)
        key = (f['folder_id'], f['name'].casefold())
        if key in names:
            raise ValueError('Submission contains duplicate ambiguous filenames.')
        names.add(key)
        if (not isinstance(f['declared_size'], int) or not 16 <= f['declared_size'] <= 64 * 1024**2 or
                f['actual_size'] != f['declared_size'] or f['status'] != 'uploaded' or
                not re.fullmatch(r'[a-f0-9]{64}', f['sha256'])):
            raise ValueError('Submission replay sizes or checksums are incomplete.')
    if any(not any(f['folder_id'] == folder for f in remote['files']) for folder in ids):
        raise ValueError('A submission folder contains no replay files.')
    if sum(f['declared_size'] for f in remote['files']) > 2 * 1024**3:
        raise ValueError('Submission exceeds the local staging limit.')
    version = remote.get('schema_version', 1)
    if type(version) is not int or version not in (1, 2):
        raise ValueError('Unsupported submission schema.')
    if version == 2:
        maps = validate_structure(remote.get('maps'), folders, max_maps=5)
        for m in maps:
            for part in m['segments']:
                folder = next(f for f in folders if f['id'] == part['folder_id'])
                if folder.get('logical_map_id') != m['id'] or folder.get('segment_index') != part['index']:
                    raise ValueError('Submission logical map/folder ownership differs.')


def validate_structure(maps, folders, *, max_maps=12):
    if not isinstance(maps, list) or not 1 <= len(maps) <= max_maps:
        raise ValueError('Choose a valid logical map count.')
    expected = {f['id'] for f in folders}
    used, map_ids, result = set(), set(), []
    for i, m in enumerate(maps, 1):
        if not isinstance(m, dict) or type(m.get('index')) is not int or m['index'] != i or m.get('type') not in ('normal', 'rehost', 'unsure'):
            raise ValueError(f'Map {i} has an invalid type/index.')
        mid = identity(m.get('id'))
        if mid in map_ids:
            raise ValueError('Duplicate logical map identity.')
        map_ids.add(mid)
        segments = m.get('segments')
        if (not isinstance(segments, list) or not 1 <= len(segments) <= 12 or
                (m['type'] == 'normal' and len(segments) != 1) or
                (m['type'] == 'rehost' and len(segments) < 2)):
            raise ValueError(f'Map {i} needs exactly one Normal folder or at least two Rehost parts.')
        parts = []
        for j, part in enumerate(segments, 1):
            if (not isinstance(part, dict) or type(part.get('index')) is not int or part['index'] != j or
                    part.get('folder_id') not in expected or part['folder_id'] in used):
                raise ValueError(f'Map {i} Part {j} has an invalid, unknown or duplicate folder assignment.')
            used.add(part['folder_id']); parts.append(dict(index=j, folder_id=part['folder_id']))
        result.append(dict(id=mid, index=i, type=m['type'], segments=parts))
    if used != expected:
        raise ValueError('Every submission folder must belong to exactly one reviewed map.')
    return result


def reviewed_maps(root, submission, manifest=None):
    manifest = manifest or local_manifest(root, submission)
    path = directory(root, submission) / 'review.json'
    if path.is_file():
        review = json.loads(path.read_text(encoding='utf-8'))
        if review['submitted_maps'] != manifest.get('maps', []):
            raise ValueError('Submitted structure changed; review it again.')
        return validate_structure(review['reviewed_maps'], manifest['folders'])
    initial = manifest.get('reviewed_maps') or manifest.get('maps')
    if initial:
        return validate_structure(initial, manifest['folders'])
    # Legacy folders remain separate and unclassified until a human groups them.
    return [dict(id=f['id'], index=i, type='unsure', segments=[dict(index=1, folder_id=f['id'])])
            for i, f in enumerate(manifest['folders'], 1)]


def save_review(root, submission, maps):
    with LOCK:
        manifest = local_manifest(root, submission)
        updated = validate_structure(maps, manifest['folders'])
        previous = reviewed_maps(root, submission, manifest)
        receipts_path = directory(root, submission) / 'receipts.json'
        receipts = json.loads(receipts_path.read_text(encoding='utf-8')) if receipts_path.exists() else []
        frozen = {f['id'] for f in manifest['folders'] if f.get('disposition')}
        frozen.update(fid for receipt in receipts for fid in receipt['folder_ids'])
        for fid in frozen:
            old = next(m for m in previous if any(p['folder_id'] == fid for p in m['segments']))
            new = next(m for m in updated if any(p['folder_id'] == fid for p in m['segments']))
            if old != new:
                raise ValueError('Resolved logical map assignments cannot change.')
        path = directory(root, submission) / 'review.json'
        prior = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
        history = prior.get('history', [])
        if previous != updated:
            history.append(dict(at=datetime.now(timezone.utc).isoformat(), before=previous, after=updated))
        review = dict(submitted_maps=manifest.get('maps', []), reviewed_maps=updated, history=history)
        atomic_json(path, review)
        return review


def enrich_detail(root, remote, db=None):
    result = deepcopy(remote)
    path = directory(root, remote['id'])
    if (path / 'manifest.json').is_file():
        result['reviewed_maps'] = reviewed_maps(root, remote['id'])
    elif not result.get('maps'):
        result['reviewed_maps'] = [dict(id=f['id'], index=i, type='unsure', segments=[dict(index=1, folder_id=f['id'])])
                                 for i, f in enumerate(remote['folders'], 1)]
    receipt_path = path / 'receipts.json'
    receipts = json.loads(receipt_path.read_text(encoding='utf-8')) if receipt_path.exists() else []
    result['local_receipts'] = receipts
    # Series context is a confirmed local import, never inferred from file times.
    result['series_context'] = next((dict(r) for receipt in reversed(receipts) if db is not None
        and (r := db.execute('SELECT s.id AS series_id,s.opponent,s.date AS match_date,t.slug AS team_slug,se.slug AS season_slug FROM maps m JOIN series s ON s.id=m.series_id JOIN teams t ON t.id=m.team_id JOIN seasons se ON se.id=s.season_id WHERE m.id=?', (receipt['map_id'],)).fetchone())), None)
    return result


def local_manifest(root, submission):
    path = directory(root, submission) / 'manifest.json'
    if not path.is_file():
        raise ValueError('Download the submission before opening an import preview.')
    manifest = json.loads(path.read_text(encoding='utf-8'))
    validate_manifest(manifest)
    return manifest


def verify_staging(root, submission):
    manifest = local_manifest(root, submission)
    base = directory(root, submission)
    results = []
    for folder in manifest['folders']:
        path = (base / identity(folder['id'])).resolve()
        if not path.is_relative_to(base):
            raise ValueError('Submission folder escaped staging.')
        files = [f for f in manifest['files'] if f['folder_id'] == folder['id']]
        expected = {f['name'].casefold() for f in files}
        entries = list(path.iterdir())
        if (any(not p.is_file() or p.is_symlink() for p in entries) or
                {p.name.casefold() for p in entries} != expected):
            raise ValueError('Staged replay inventory changed. Download and verify it again.')
        for f in files:
            p = (path / safe_name(f['name'], replay=True)).resolve()
            if not p.is_relative_to(base) or not p.is_file() or p.stat().st_size != f['actual_size'] or sha(p) != f['sha256']:
                raise ValueError('Staged replay size or checksum differs. Download and verify it again.')
        results.append({'id': folder['id'], 'name': folder['name'], 'path': str(path),
                        'files': len(files), 'bytes': sum(f['actual_size'] for f in files),
                        'first_file_modified_at': folder.get('first_file_modified_at'),
                        'last_file_modified_at': folder.get('last_file_modified_at'),
                        'disposition': folder.get('disposition')})
    return results


def download(root, client, submission):
    with LOCK:
        remote = client.call('/submissions/' + identity(submission))
        if remote['status'] not in ('pending', 'reviewing'):
            raise ValueError('Only pending or reviewing submissions can be staged.')
        validate_manifest(remote)
        client.call(f'/submissions/{submission}/review', 'POST', {})
        base = directory(root, submission)
        for f in remote['files']:
            folder = (base / identity(f['folder_id'])).resolve()
            if not folder.is_relative_to(base):
                raise ValueError('Submission folder escaped staging.')
            folder.mkdir(parents=True, exist_ok=True)
            destination = (folder / safe_name(f['name'], replay=True)).resolve()
            if not destination.is_relative_to(base):
                raise ValueError('Submission replay escaped staging.')
            if destination.is_file() and destination.stat().st_size == f['actual_size'] and sha(destination) == f['sha256']:
                continue
            temporary = destination.with_suffix('.part')
            digest, size = hashlib.sha256(), 0
            try:
                with client.request(f'/submissions/{submission}/files/{identity(f["id"])}') as response, temporary.open('wb') as output:
                    if response.headers.get('X-Replay-SHA256') != f['sha256']:
                        raise ValueError('Cloud replay checksum metadata differs.')
                    for chunk in iter(lambda: response.read(1024 * 1024), b''):
                        size += len(chunk)
                        if size > f['actual_size']:
                            raise ValueError('Cloud replay exceeds the expected size.')
                        digest.update(chunk)
                        output.write(chunk)
                if size != f['actual_size'] or digest.hexdigest() != f['sha256']:
                    raise ValueError('Downloaded replay size or checksum differs.')
                with temporary.open('rb') as replay:
                    if replay.read(7) != b'dissect':
                        raise ValueError('Downloaded file is not a Siege replay.')
                temporary.replace(destination)
            finally:
                temporary.unlink(missing_ok=True)
        atomic_json(base / 'manifest.json', remote)
        return verify_staging(root, submission)


def source_context(root, paths, client=None, *, mode=None):
    base = staging_root(root)
    selected = [Path(p).resolve() for p in paths]
    staged = [p for p in selected if p.is_relative_to(base)]
    if not staged:
        return None
    if len(staged) != len(selected):
        raise ValueError('Do not mix inbox folders and other replay folders in one rehost.')
    submissions = {p.relative_to(base).parts[0] for p in staged}
    if len(submissions) != 1:
        raise ValueError('A rehost must use folders from one submission.')
    submission = identity(submissions.pop())
    verified = verify_staging(root, submission)
    lookup = {Path(f['path']): f['id'] for f in verified}
    if any(p not in lookup for p in selected):
        raise ValueError('Select complete verified submission folders.')
    ids = [lookup[p] for p in selected]
    receipt_path = directory(root, submission) / 'receipts.json'
    receipts = json.loads(receipt_path.read_text(encoding='utf-8')) if receipt_path.exists() else []
    if any(set(r['folder_ids']) & set(ids) for r in receipts):
        raise ValueError('These folders were already imported locally. Retry cloud status sync instead of importing again.')
    remote = (client or Client(root)).call('/submissions/' + submission)
    if remote['status'] not in ('pending', 'reviewing') or any(f['disposition'] for f in remote['folders'] if f['id'] in ids):
        raise ValueError('These submission folders were already consumed or rejected.')
    context = {'submission_id': submission, 'folder_ids': ids}
    manifest = local_manifest(root, submission)
    if manifest.get('schema_version') == 2 or (directory(root, submission) / 'review.json').is_file():
        structure = reviewed_maps(root, submission, manifest)
        selected_map = next((m for m in structure if [p['folder_id'] for p in m['segments']] == ids), None)
        if not selected_map:
            raise ValueError('Select exactly one reviewed logical map in its saved part order. Do not mix maps; save structure corrections before previewing again.')
        if selected_map['type'] == 'unsure' or selected_map['type'] != (mode or ('normal' if len(ids) == 1 else 'rehost')):
            raise ValueError('Classify the reviewed logical map as Normal or Rehosted before import.')
        context.update(logical_map_id=selected_map['id'], submitted_maps=manifest.get('maps', []), reviewed_maps=structure)
    return context


def record_import(root, db, context, map_id, client=None):
    if context is None:
        return None
    try:
        with LOCK:
            archive = replay_archive.verify(db, Path(root) / 'data/replay-archive', map_id)
            if archive['status'] != 'Healthy':
                raise ValueError('Local archive must verify Healthy before cloud approval.')
            row = db.execute('SELECT t.slug team_slug,se.slug season_slug,s.id series_id,s.opponent,s.date match_date FROM maps m JOIN teams t ON t.id=m.team_id JOIN series s ON s.id=m.series_id JOIN seasons se ON se.id=s.season_id WHERE m.id=?', (map_id,)).fetchone()
            receipt = {**context, 'map_id': map_id, 'team_slug': row['team_slug'],
                       'season_slug': row['season_slug'], 'archive_verified': True, 'synced': False}
            path = directory(root, context['submission_id']) / 'receipts.json'
            receipts = json.loads(path.read_text(encoding='utf-8')) if path.exists() else []
            receipts.append(receipt)
            atomic_json(path, receipts)
            (client or Client(root)).call('/submissions/' + context['submission_id'] + '/consume', 'POST', receipt)
            receipt['synced'] = True
            atomic_json(path, receipts)
        return {'synced': True, 'message': 'Local import and archive verified; cloud review updated.', 'series_context': dict(row)}
    except (ValueError, OSError):
        return {'synced': False, 'message': 'Local import succeeded. Cloud approval is pending; retry status sync in Submissions.'}


def sync_receipts(root, db, submission, client=None):
    with LOCK:
        path = directory(root, submission) / 'receipts.json'
        receipts = json.loads(path.read_text(encoding='utf-8')) if path.exists() else []
        for receipt in receipts:
            if not receipt['synced']:
                if replay_archive.verify(db, Path(root) / 'data/replay-archive', receipt['map_id'])['status'] != 'Healthy':
                    raise ValueError('Repair the local archive before updating cloud approval.')
                (client or Client(root)).call('/submissions/' + identity(submission) + '/consume', 'POST', receipt)
                receipt['synced'] = True
                atomic_json(path, receipts)
        return {'synced': True, 'receipts': len(receipts)}
