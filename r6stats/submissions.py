"""Private cloud intake and staging. The existing local importer owns all statistics."""
import hashlib
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
        if {p.name.casefold() for p in path.iterdir() if p.is_file() and p.suffix.lower() == '.rec'} != expected:
            raise ValueError('Staged replay inventory changed. Download and verify it again.')
        for f in files:
            p = (path / safe_name(f['name'], replay=True)).resolve()
            if not p.is_relative_to(base) or not p.is_file() or p.stat().st_size != f['actual_size'] or sha(p) != f['sha256']:
                raise ValueError('Staged replay size or checksum differs. Download and verify it again.')
        results.append({'id': folder['id'], 'name': folder['name'], 'path': str(path),
                        'files': len(files), 'bytes': sum(f['actual_size'] for f in files),
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


def source_context(root, paths, client=None):
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
    return {'submission_id': submission, 'folder_ids': ids}


def record_import(root, db, context, map_id, client=None):
    if context is None:
        return None
    try:
        with LOCK:
            archive = replay_archive.verify(db, Path(root) / 'data/replay-archive', map_id)
            if archive['status'] != 'Healthy':
                raise ValueError('Local archive must verify Healthy before cloud approval.')
            row = db.execute('SELECT t.slug team_slug,se.slug season_slug FROM maps m JOIN teams t ON t.id=m.team_id JOIN series s ON s.id=m.series_id JOIN seasons se ON se.id=s.season_id WHERE m.id=?', (map_id,)).fetchone()
            receipt = {**context, 'map_id': map_id, 'team_slug': row['team_slug'],
                       'season_slug': row['season_slug'], 'archive_verified': True, 'synced': False}
            path = directory(root, context['submission_id']) / 'receipts.json'
            receipts = json.loads(path.read_text(encoding='utf-8')) if path.exists() else []
            receipts.append(receipt)
            atomic_json(path, receipts)
            (client or Client(root)).call('/submissions/' + context['submission_id'] + '/consume', 'POST', receipt)
            receipt['synced'] = True
            atomic_json(path, receipts)
        return {'synced': True, 'message': 'Local import and archive verified; cloud review updated.'}
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
