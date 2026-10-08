"""Structured intake uses the existing normal/rehost importer in isolated SQLite."""
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
from tests.test_submissions import Inbox, setup
from test_confirmed_rehost import segment


class StructuredInbox(Inbox):
    def __init__(self, root):
        super().__init__()
        self.remote.update(schema_version=2, display_id='R6-STRUCTURED', team_slug='blue', season_slug='fall-2026',
                           opponent='Submitted opponent', match_date='2026-10-07')
        self.remote['folders'], self.remote['files'], self.remote['maps'] = [], [], []
        self.payloads, self.matches = {}, {}
        for index, name in enumerate(['segment1', 'segment2', 'segment3']):
            match = segment(root, name, [0, 1]).match
            fid = str(uuid4())
            self.matches[fid] = match
            self.remote['folders'].append(dict(id=fid, name=name, disposition=None,
                first_file_modified_at='2026-10-07T19:00:00.000Z', last_file_modified_at='2026-10-07T19:20:00.000Z'))
            for replay in (root / name).glob('*.rec'):
                rid = str(uuid4())
                contents = b'dissect\0 synthetic ' + replay.read_bytes()
                self.payloads[rid] = contents
                self.remote['files'].append(dict(id=rid, folder_id=fid, submission_id=self.remote['id'],
                    name=replay.name, declared_size=len(contents), actual_size=len(contents),
                    status='uploaded', sha256=hashlib.sha256(contents).hexdigest()))
        for i, indices in enumerate([[0], [1, 2]], 1):
            mid = str(uuid4())
            parts = []
            for j, index in enumerate(indices, 1):
                f = self.remote['folders'][index]
                f.update(logical_map_id=mid, segment_index=j)
                parts.append(dict(index=j, folder_id=f['id']))
            self.remote['maps'].append(dict(id=mid, index=i, type='normal' if i == 1 else 'rehost', segments=parts))
        self.remote['reviewed_maps'] = copy.deepcopy(self.remote['maps'])

    def request(self, path):
        data = self.payloads[path.rsplit('/', 1)[-1]]
        response = io.BytesIO(data)
        response.headers = {'X-Replay-SHA256': hashlib.sha256(data).hexdigest()}
        return response

    def call(self, path, method='GET', payload=None):
        if path.endswith('/consume'):
            self.calls.append((path, method, payload))
            if self.fail_consume:
                raise ValueError('Cloud unavailable')
            for folder in self.remote['folders']:
                if folder['id'] in payload['folder_ids']:
                    folder.update(disposition='imported', map_id=payload['map_id'])
            self.remote['reviewed_maps'] = copy.deepcopy(payload['reviewed_maps'])
            self.remote['status'] = 'reviewing' if any(not f['disposition'] for f in self.remote['folders']) else 'imported'
            return copy.deepcopy(self.remote)
        return super().call(path, method, payload)


@pytest.mark.parametrize('change', ['maps', 'index', 'type', 'duplicate', 'unknown', 'order', 'binding', 'time'])
def test_structured_manifest_validation(tmp_path, change):
    remote = StructuredInbox(tmp_path).remote
    submissions.validate_manifest(remote)
    if change == 'maps': remote['maps'] = []
    if change == 'index': remote['maps'][1]['index'] = 1
    if change == 'type': remote['maps'][1]['type'] = 'normal'
    if change == 'duplicate': remote['maps'][1]['segments'][0]['folder_id'] = remote['folders'][0]['id']
    if change == 'unknown': remote['maps'][1]['segments'][0]['folder_id'] = str(uuid4())
    if change == 'order': remote['maps'][1]['segments'][1]['index'] = 1
    if change == 'binding': remote['folders'][0]['logical_map_id'] = str(uuid4())
    if change == 'time': remote['folders'][0]['last_file_modified_at'] = '2026-10-07T18:00:00.000Z'
    with pytest.raises(ValueError): submissions.validate_manifest(remote)


def test_staging_map_selection_order_corrections_and_legacy(tmp_path):
    inbox = StructuredInbox(tmp_path)
    sid = inbox.remote['id']
    folders = submissions.download(tmp_path, inbox, sid)
    assert folders[0]['files'] == 2 and folders[0]['first_file_modified_at']
    paths = [f['path'] for f in folders]
    assert submissions.source_context(tmp_path, paths[:1], inbox, mode='normal')['logical_map_id'] == inbox.remote['maps'][0]['id']
    assert submissions.source_context(tmp_path, paths[1:], inbox, mode='rehost')['folder_ids'] == [f['id'] for f in folders[1:]]
    for selected in [paths[:2], paths[1:2], paths[1:][::-1]]:
        with pytest.raises(ValueError, match='exactly one'): submissions.source_context(tmp_path, selected, inbox, mode='rehost')
    review = copy.deepcopy(inbox.remote['maps'])
    review[1]['segments'].reverse()
    for i, p in enumerate(review[1]['segments'], 1): p['index'] = i
    saved = submissions.save_review(tmp_path, sid, review)
    assert saved['submitted_maps'] == inbox.remote['maps'] and len(saved['history']) == 1
    assert submissions.source_context(tmp_path, paths[1:][::-1], inbox, mode='rehost')['reviewed_maps'] == review
    review[1]['type'] = 'unsure'
    submissions.save_review(tmp_path, sid, review)
    with pytest.raises(ValueError, match='Classify'): submissions.source_context(tmp_path, paths[1:][::-1], inbox)
    # A legacy manifest remains flat and needs an explicit local classification.
    legacy = tmp_path / 'legacy'; legacy.mkdir()
    old = Inbox(); staged = submissions.download(legacy, old, old.remote['id'])
    maps = submissions.reviewed_maps(legacy, old.remote['id'])
    assert maps[0]['type'] == 'unsure'
    assert submissions.source_context(legacy, [staged[0]['path']], old)
    maps[0]['type'] = 'normal'; submissions.save_review(legacy, old.remote['id'], maps)
    assert submissions.source_context(legacy, [staged[0]['path']], old, mode='normal')['logical_map_id'] == maps[0]['id']


def test_two_map_admin_pipeline_shared_series_archive_receipts_and_partial_sync(tmp_path):
    setup(tmp_path)
    with closing(repo.connect(tmp_path / 'data/r6stats.sqlite')) as db:
        for i in range(5): repo.roster_add(db, f'Our{i}', team_id=1)
    inbox = StructuredInbox(tmp_path)
    sid = inbox.remote['id']
    parser = lambda path, **kw: inbox.matches[Path(path).name]
    with patch('r6stats.submissions.Client', return_value=inbox), patch('r6stats.admin.server.parse_match', side_effect=parser), patch('r6stats.parser.confirmed_rehost.parse_match', side_effect=parser):
        with TestClient(create_app(tmp_path)) as client:
            headers = {'X-R6-Admin-Token': client.get('/api/admin/session').json()['token']}
            def post(path, body):
                result = client.post('/api/admin' + path, json=body, headers=headers)
                assert result.status_code == 200, result.text
                return result.json()
            url = '/submissions/' + sid
            folders = post(url + '/stage', {})['folders']
            inspected = post(url + '/inspect', {'team_id': 1, 'season_slug': 'fall-2026'})
            assert len(inspected['reviewed_maps']) == 2 and all(f['tracked_count'] == 5 for f in inspected['folders'])
            with closing(repo.connect(tmp_path / 'data/r6stats.sqlite')) as db:
                assert db.execute('SELECT count(*) FROM maps').fetchone()[0] == 0
            preview = post('/replays/preview', {'path': folders[0]['path'], 'team_id': 1, 'season_slug': 'fall-2026'})
            first = post('/replays/import', {'preview_token': preview['preview_token'], 'team_id': 1, 'season_slug': 'fall-2026', 'opponent': 'Corrected opponent', 'team': 0, 'confirm_necc': True})
            assert first['submission']['synced'] and inbox.remote['status'] == 'reviewing'
            assert [f['disposition'] for f in inbox.remote['folders']] == ['imported', None, None]
            context = client.get('/api/admin' + url).json()['series_context']
            assert context['opponent'] == 'Corrected opponent' and context['team_slug'] == 'blue'
            changed = copy.deepcopy(inbox.remote['maps']); changed[0]['type'] = 'unsure'
            assert client.post('/api/admin' + url + '/structure', json={'maps': changed}, headers=headers).status_code == 400
            preview = post('/replays/rehost/preview', {'segments': [{'path': f['path']} for f in folders[1:]], 'team_id': 1, 'season_slug': 'fall-2026', 'team': 0})
            payload = {'preview_token': preview['preview_token'], 'team_id': 1, 'season_slug': 'fall-2026', 'opponent': context['opponent'], 'series_id': context['series_id'], 'team': 0, 'confirm_necc': True, 'confirm_folders_one_map': True, 'confirm_score_override': True, 'final_our_score': 2, 'final_their_score': 2}
            inbox.fail_consume = True
            second = post('/replays/rehost/import', payload)
            assert not second['submission']['synced'] and inbox.remote['status'] == 'reviewing'
            for body in [{'reason': 'Do not reject local imports'}, {'reason': 'Do not reject local imports', 'folder_ids': [folders[1]['id']]}]:
                assert client.post('/api/admin' + url + '/reject', json=body, headers=headers).status_code == 400
            with closing(repo.connect(tmp_path / 'data/r6stats.sqlite')) as db:
                maps = db.execute('SELECT id,series_id FROM maps').fetchall()
                assert len(maps) == 2 and {m['series_id'] for m in maps} == {context['series_id']}
                for m in maps: assert submissions.replay_archive.verify(db, tmp_path / 'data/replay-archive', m['id'])['status'] == 'Healthy'
            with pytest.raises(ValueError, match='already imported locally'): submissions.source_context(tmp_path, [f['path'] for f in folders[1:]], inbox)
            inbox.fail_consume = False
            assert post(url + '/sync', {})['receipts'] == 2
            assert inbox.remote['status'] == 'imported'
            receipts = [call[2] for call in inbox.calls if call[0].endswith('/consume')]
            assert receipts[0]['folder_ids'] == [folders[0]['id']]
            assert receipts[-1]['folder_ids'] == [f['id'] for f in folders[1:]]
            assert all(r['archive_verified'] and r['logical_map_id'] for r in receipts)
            assert json.loads((submissions.directory(tmp_path, sid) / 'manifest.json').read_text())['maps'] == inbox.remote['maps']
            public = '\n'.join(p.read_text() for p in (tmp_path / 'web/public/data').rglob('*.json'))
            assert sid not in public and 'first_file_modified_at' not in public
