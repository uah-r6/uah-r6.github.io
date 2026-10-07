"""Private intake verification and existing local import transaction integration."""
import copy
import hashlib
import io
import json
from contextlib import closing
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from r6stats import submissions
from r6stats.admin.server import create_app
from r6stats.db import repository as repo
from r6stats.parser.siege_dissect import normalize
from tests.test_admin import match_fixture


class Inbox:
    def __init__(self):
        self.bytes = b'dissect\0 private replay fixture'
        self.calls = []
        self.fail_consume = False
        sid, fid = str(uuid4()), str(uuid4())
        self.remote = {'id': sid, 'status': 'pending', 'folders': [{'id': fid, 'name': 'Match-current', 'disposition': None}],
                       'files': [{'id': str(uuid4()), 'folder_id': fid, 'submission_id': sid,
                                  'name': f'Match-current-R{i:02}.rec', 'declared_size': len(self.bytes),
                                  'actual_size': len(self.bytes), 'sha256': hashlib.sha256(self.bytes if i == 1 else self.bytes[:-1] + b'2').hexdigest(),
                                  'status': 'uploaded'} for i in (1, 2)]}

    @property
    def configured(self):
        return True

    def call(self, path, method='GET', payload=None):
        self.calls.append((path, method, payload))
        if path.endswith('/consume'):
            if self.fail_consume:
                raise ValueError('Cloud unavailable')
            self.remote['status'] = 'imported'
            return self.remote
        if path.endswith('/review'):
            self.remote['status'] = 'reviewing'
        if path.startswith('/submissions?'):
            return [self.remote]
        return copy.deepcopy(self.remote)

    def request(self, path):
        f = next(f for f in self.remote['files'] if path.endswith(f['id']))
        response = io.BytesIO(self.bytes if f == self.remote['files'][0] else self.bytes[:-1] + b'2')
        response.headers = {'X-Replay-SHA256': f['sha256']}
        return response


def setup(root):
    (root / 'config').mkdir()
    (root / 'config/settings.json').write_text(json.dumps({
        'team': {'name': 'UAH Blue', 'short_name': 'UAH', 'accent': '#0058A4'},
        'stats': {'trade_window_seconds': 8, 'rating_version': 'collegiate_v1'},
        'publishing': {'enabled': False, 'branch': 'main'},
    }), encoding='utf-8')
    with closing(repo.connect(root / 'data/r6stats.sqlite')) as db:
        repo.season_create(db, 'Fall 2026')
        for i in range(5):
            repo.roster_add(db, f'Player{i}', team_id=1)


def parsed(*args, **kwargs):
    raw = match_fixture('CustomGameOnline', 'submission-fixture')
    raw['rounds'].append({**raw['rounds'][0], 'roundNumber': 2})
    return normalize(raw)


def test_staging_inventory_hash_resume_and_no_database(tmp_path):
    inbox = Inbox()
    sid = inbox.remote['id']
    folders = submissions.download(tmp_path, inbox, sid)
    assert folders[0]['files'] == 2
    assert not (tmp_path / 'data/r6stats.sqlite').exists()
    assert not (tmp_path / 'data/replay-archive').exists()
    assert submissions.source_context(tmp_path, [folders[0]['path']], inbox)['folder_ids'] == [folders[0]['id']]
    assert submissions.source_context(tmp_path, [tmp_path / 'ordinary']) is None
    with pytest.raises(ValueError, match='mix'):
        submissions.source_context(tmp_path, [folders[0]['path'], tmp_path / 'outside'], inbox)
    file = Path(folders[0]['path']) / inbox.remote['files'][0]['name']
    file.write_bytes(b'corrupt')
    with pytest.raises(ValueError, match='checksum'):
        submissions.verify_staging(tmp_path, sid)
    submissions.download(tmp_path, inbox, sid)
    assert file.read_bytes() == inbox.bytes
    file.unlink()
    with pytest.raises(ValueError, match='inventory'):
        submissions.verify_staging(tmp_path, sid)


@pytest.mark.parametrize('mutation', ['size', 'hash', 'path', 'owner', 'duplicate', 'missing'])
def test_untrusted_manifest_is_rejected(tmp_path, mutation):
    inbox = Inbox()
    f = inbox.remote['files'][0]
    if mutation == 'size': f['actual_size'] -= 1
    if mutation == 'hash': f['sha256'] = 'not-a-hash'
    if mutation == 'path': f['name'] = '../bad.rec'
    if mutation == 'owner': f['submission_id'] = str(uuid4())
    if mutation == 'duplicate': inbox.remote['files'][1]['name'] = f['name'].upper()
    if mutation == 'missing': inbox.remote['files'] = []
    with pytest.raises(ValueError):
        submissions.download(tmp_path, inbox, inbox.remote['id'])
    assert not list(tmp_path.rglob('manifest.json'))


@pytest.mark.parametrize('bad_bytes', [b'dissect\0 short', b'not-rec\0 private replay fixture'])
def test_download_rejects_actual_bytes_and_removes_partial(tmp_path, bad_bytes):
    inbox = Inbox()
    inbox.bytes = bad_bytes
    with pytest.raises(ValueError):
        submissions.download(tmp_path, inbox, inbox.remote['id'])
    assert not list(tmp_path.rglob('*.part'))
    assert not list(tmp_path.rglob('*.rec'))


def test_admin_normal_import_keeps_local_data_on_cloud_failure(tmp_path):
    setup(tmp_path)
    inbox = Inbox()
    sid = inbox.remote['id']
    with patch('r6stats.submissions.Client', return_value=inbox), patch('r6stats.admin.server.parse_match', side_effect=parsed):
        with TestClient(create_app(tmp_path)) as client:
            headers = {'X-R6-Admin-Token': client.get('/api/admin/session').json()['token']}
            url = '/api/admin/submissions/' + sid
            assert client.post(url + '/stage', json={}).status_code == 403
            folders = client.post(url + '/stage', json={}, headers=headers).json()['folders']
            inspected = client.post(url + '/inspect', json={'team_id': 1, 'season_slug': 'fall-2026'}, headers=headers)
            assert inspected.status_code == 200, inspected.text
            assert inspected.json()['folders'][0]['tracked_count'] == 5
            assert inspected.json()['folders'][0]['our_score'] == 2
            with closing(repo.connect(tmp_path / 'data/r6stats.sqlite')) as db:
                assert db.execute('SELECT COUNT(*) FROM maps').fetchone()[0] == 0
            preview = client.post('/api/admin/replays/preview', json={'path': folders[0]['path'], 'team_id': 1, 'season_slug': 'fall-2026'}, headers=headers).json()
            payload = {'preview_token': preview['preview_token'], 'team_id': 1, 'season_slug': 'fall-2026', 'opponent': 'Fixture', 'team': 0, 'confirm_necc': False}
            assert client.post('/api/admin/replays/import', json=payload, headers=headers).status_code == 400
            payload['confirm_necc'] = True
            inbox.fail_consume = True
            imported = client.post('/api/admin/replays/import', json=payload, headers=headers)
            assert imported.status_code == 200, imported.text
            assert imported.json()['submission']['synced'] is False
            map_id = imported.json()['map_id']
            with closing(repo.connect(tmp_path / 'data/r6stats.sqlite')) as db:
                assert db.execute('SELECT COUNT(*) FROM maps').fetchone()[0] == 1
                assert submissions.replay_archive.verify(db, tmp_path / 'data/replay-archive', map_id)['status'] == 'Healthy'
            with pytest.raises(ValueError, match='already imported locally'):
                submissions.source_context(tmp_path, [folders[0]['path']], inbox)
            inbox.fail_consume = False
            synced = client.post(url + '/sync', json={}, headers=headers)
            assert synced.status_code == 200, synced.text
            assert synced.json()['receipts'] == 1
            assert inbox.remote['status'] == 'imported'
            exported = '\n'.join(p.read_text(encoding='utf-8') for p in (tmp_path / 'web/public/data').rglob('*.json'))
            assert sid not in exported


def test_private_configuration_and_paths(tmp_path):
    assert not submissions.Client(tmp_path).configured
    with pytest.raises(ValueError, match='not configured'):
        submissions.Client(tmp_path).call('/storage')
    for name in ('../file.rec', 'CON.rec', 'C:\\file.rec', 'file.exe', 'file.rec.'):
        with pytest.raises(ValueError): submissions.safe_name(name, replay=True)
    with pytest.raises(ValueError): submissions.directory(tmp_path, '../outside')


def test_rehost_submission_uses_existing_confirmations_and_archives(tmp_path):
    from test_confirmed_rehost import segment
    setup(tmp_path)
    with closing(repo.connect(tmp_path / 'data/r6stats.sqlite')) as db:
        for i in range(5): repo.roster_add(db, f'Our{i}', team_id=1)
    first = segment(tmp_path, 'segment1', [0, 1])
    second = segment(tmp_path, 'segment2', [0, 1])
    inbox = Inbox()
    sid = inbox.remote['id']
    source = [tmp_path / 'segment1', tmp_path / 'segment2']
    payloads, matches = {}, {}
    inbox.remote['folders'], inbox.remote['files'] = [], []
    for folder, match in zip(source, [first.match, second.match]):
        fid = str(uuid4())
        inbox.remote['folders'].append({'id': fid, 'name': folder.name, 'disposition': None})
        matches[fid] = match
        for replay in folder.glob('*.rec'):
            contents = b'dissect\0 synthetic ' + replay.read_bytes()
            rid = str(uuid4())
            payloads[rid] = contents
            inbox.remote['files'].append({'id': rid, 'folder_id': fid, 'submission_id': sid, 'name': replay.name,
                                          'declared_size': len(contents), 'actual_size': len(contents),
                                          'status': 'uploaded', 'sha256': hashlib.sha256(contents).hexdigest()})

    def request(path):
        rid = path.rsplit('/', 1)[-1]
        response = io.BytesIO(payloads[rid])
        response.headers = {'X-Replay-SHA256': hashlib.sha256(payloads[rid]).hexdigest()}
        return response

    inbox.request = request
    with patch('r6stats.submissions.Client', return_value=inbox), patch('r6stats.parser.confirmed_rehost.parse_match', side_effect=lambda path, **kw: matches[Path(path).name]):
        with TestClient(create_app(tmp_path)) as client:
            headers = {'X-R6-Admin-Token': client.get('/api/admin/session').json()['token']}
            folders = client.post('/api/admin/submissions/' + sid + '/stage', json={}, headers=headers).json()['folders']
            preview = client.post('/api/admin/replays/rehost/preview', json={'segments': [{'path': f['path']} for f in folders], 'team_id': 1, 'season_slug': 'fall-2026', 'team': 0}, headers=headers)
            assert preview.status_code == 200, preview.text
            payload = {'preview_token': preview.json()['preview_token'], 'team_id': 1, 'season_slug': 'fall-2026',
                       'opponent': 'Fixture', 'team': 0, 'confirm_necc': True, 'confirm_folders_one_map': False,
                       'confirm_score_override': True, 'final_our_score': 2, 'final_their_score': 2}
            assert client.post('/api/admin/replays/rehost/import', json=payload, headers=headers).status_code == 400
            assert not any(call[0].endswith('/consume') for call in inbox.calls)
            payload['confirm_folders_one_map'] = True
            imported = client.post('/api/admin/replays/rehost/import', json=payload, headers=headers)
            assert imported.status_code == 200, imported.text
            assert imported.json()['submission']['synced'] is True
            receipt = next(call[2] for call in inbox.calls if call[0].endswith('/consume'))
            assert set(receipt['folder_ids']) == {f['id'] for f in folders}
            with closing(repo.connect(tmp_path / 'data/r6stats.sqlite')) as db:
                assert submissions.replay_archive.verify(db, tmp_path / 'data/replay-archive', imported.json()['map_id'])['status'] == 'Healthy'


def test_staging_rejects_undeclared_nested_replay_sources(tmp_path):
    inbox = Inbox()
    folders = submissions.download(tmp_path, inbox, inbox.remote['id'])
    nested = Path(folders[0]['path']) / 'unexpected'
    nested.mkdir()
    (nested / 'Extra-R03.rec').write_bytes(inbox.bytes)
    with pytest.raises(ValueError, match='inventory'):
        submissions.verify_staging(tmp_path, inbox.remote['id'])
