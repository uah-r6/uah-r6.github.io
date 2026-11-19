"""A proven standalone-death boundary unlocks Rating, never rewrites history."""
from copy import deepcopy
import json
from pathlib import Path
import sqlite3

from fastapi.testclient import TestClient
import pytest

from r6stats import credited_refresh as credit, rating_credit_evidence as sealed, rating_evidence
from r6stats.admin.server import create_app
from r6stats.db import repository as repo
from r6stats.parser.models import Kill
from r6stats.rating_inputs_v3 import load_inputs
from test_credited_production import make_db
from test_rating_v3 import evidence


def recovery_fixture(tmp_path, monkeypatch):
    db, mid, match, records = make_db(tmp_path)
    round_ = match.rounds[0]
    for kill in round_.kills:
        kill.sequence += 1
    round_.kills.insert(0, Kill(0, 172, '', round_.players[4].key, -1, 0))
    evidence(match, records)
    repo.reparse_map(db, mid, match, 'fingerprint')
    for record in records:
        record['credit']['actionStartOffset'] = 500
        for i, player in enumerate(record['credit']['players']):
            player['samples'] = [dict(offset=100, value=player['initial'], component=i+201, owner=i+101),
                                 dict(offset=1600, value=player['terminal'], component=i+201, owner=i+101)]
    old = deepcopy(records)
    broken = old[0]['credit']
    broken['complete'] = False
    broken['reason'] = 'unresolved_player_counters'
    broken['finishes'][0]['offset'] = 0
    for p in broken['players']:
        p.update(initial=None, terminal=None, kills=None, reason='baseline_not_before_first_elimination')
    credit.store(db, mid, old, 'old-binary')
    finish = records[0]['credit']['finishes'][0]
    finish['offsetEvidence'] = dict(feedbackIndex=0, startOffset=finish['offset'],
        endOffset=finish['offset']+80, legacyOffset=0, markerValid=True, feedback=deepcopy(finish['feedback']))
    monkeypatch.setattr(credit, 'read_archive', lambda *a: (deepcopy(records), 'new-binary'))
    monkeypatch.setattr(rating_evidence.replay_archive, 'verify', lambda *a: dict(status='Healthy',path=str(tmp_path)))
    monkeypatch.setattr(rating_evidence.replay_archive, 'sha256', lambda *a: 'fixture-sha')
    monkeypatch.setattr(sealed, 'verify', lambda *a: dict(status='Healthy',path=str(tmp_path)))
    monkeypatch.setattr(sealed, 'sha256', lambda *a: 'fixture-manifest-sha')
    return db, mid, match, old, records


def test_death_recovery_preserves_display_sidecar_events_snapshots_and_uses_full_v3(tmp_path, monkeypatch):
    db, mid, match, old, records = recovery_fixture(tmp_path, monkeypatch)
    before = {name: [tuple(r) for r in db.execute(f'SELECT * FROM {name}')]
              for name in ('maps','rounds','round_players','kill_events','map_kill_credit','rating_input_snapshots')}
    # Counters differ from finishers: the existing display guard remains strict.
    with pytest.raises(ValueError, match='historical display'):
        credit.preserve_display(match, credit.validate_map_credit(records))
    assert sealed.death_offset_recovery(old, records)
    result = rating_evidence.repair(db, tmp_path, mid)
    assert result['after']['eligible'] and result['blockers'] == []
    assert result['changes'] == ['Rating-only credited evidence']
    assert result['after']['credited_status'] == 'complete (Rating only)'
    assert result['after']['credited_issues'] == []
    assert result['after']['display_credited_status'] == 'incomplete'
    for name, rows in before.items():
        assert [tuple(r) for r in db.execute(f'SELECT * FROM {name}')] == rows, name
    assert credit.load(db, mid) is None
    values, reason = load_inputs(db, mid)
    assert reason is None and values[match.rounds[0].players[0].key]['kills'] == 4
    saved = dict(db.execute('SELECT * FROM map_v3_kill_evidence').fetchone())
    audit_count = db.execute('SELECT count(*) FROM rating_evidence_audit').fetchone()[0]
    assert rating_evidence.repair(db, tmp_path, mid)['changes'] == []
    assert dict(db.execute('SELECT * FROM map_v3_kill_evidence').fetchone()) == saved
    assert db.execute('SELECT count(*) FROM rating_evidence_audit').fetchone()[0] == audit_count


@pytest.mark.parametrize('mutation', [
    'missing_proof','marker','boundary','end','clock','identity','legacy_offset','kill',
    'feedback_index','samples','missing_samples','sources','other_refusal','other_offset',
    'action_start','partial','missing_finish','counter_owner',
])
def test_rating_only_death_recovery_rejects_changed_or_unproven_observations(tmp_path, monkeypatch, mutation):
    db, mid, match, old, records = recovery_fixture(tmp_path, monkeypatch)
    f = records[0]['credit']['finishes'][0]
    if mutation == 'missing_proof': f.pop('offsetEvidence')
    elif mutation == 'marker': f['offsetEvidence']['markerValid'] = False
    elif mutation == 'boundary': f['offsetEvidence']['startOffset'] += 1
    elif mutation == 'end': f['offsetEvidence']['endOffset'] = f['offset']
    elif mutation == 'clock': f['offsetEvidence']['feedback']['timeInSeconds'] -= 1
    elif mutation == 'identity': f['feedback']['username'] = 'Other'
    elif mutation == 'legacy_offset': f['offsetEvidence']['legacyOffset'] = 10
    elif mutation == 'kill': f['feedback']['type']['name'] = 'Kill'
    elif mutation == 'feedback_index': f['offsetEvidence']['feedbackIndex'] = True
    elif mutation == 'samples': records[0]['credit']['players'][0]['samples'][0]['value'] += 1
    elif mutation == 'missing_samples':
        for target in (old, records): target[0]['credit']['players'][0].pop('samples')
    elif mutation == 'sources': records[0]['physical_round'] = 8
    elif mutation == 'other_refusal': old[0]['credit']['players'][0]['reason'] = 'missing_direct_uid_counter'
    elif mutation == 'other_offset': records[1]['credit']['finishes'][0]['offset'] += 1
    elif mutation == 'action_start': records[0]['credit']['actionStartOffset'] = 0
    elif mutation == 'partial': records[0]['credit']['complete'] = False
    elif mutation == 'missing_finish': records[0]['credit']['finishes'].pop()
    else: records[0]['credit']['players'][0]['samples'][0]['owner'] += 1
    assert not sealed.death_offset_recovery(old, records)


def test_admin_rating_repair_handles_zero_offset_death_without_reimport(tmp_path, monkeypatch):
    db, mid, match, old, records = recovery_fixture(tmp_path, monkeypatch)
    (tmp_path/'data').mkdir()
    db.commit()
    with sqlite3.connect(tmp_path/'data/r6stats.sqlite') as target:
        db.backup(target)
    (tmp_path/'config').mkdir()
    (tmp_path/'config/settings.json').write_text(json.dumps(dict(team={},stats={
        'trade_window_seconds':8,'rating_version':'siege_style_v3'})),encoding='utf-8')
    with TestClient(create_app(tmp_path)) as client:
        headers={'X-R6-Admin-Token':client.get('/api/admin/session').json()['token']}
        result=client.post(f'/api/admin/matches/{mid}/rating-evidence',
            json={'confirm_map_id':mid},headers=headers)
        assert result.status_code == 200, result.text
        assert result.json()['after']['eligible']
        assert result.json()['blockers'] == []
        audit=client.get('/api/admin/rating-evidence').json()
        assert audit[0]['credited_status'] == 'complete (Rating only)'
        document=json.loads((tmp_path/'web/public/data/matches'/f'{mid}.json').read_text(encoding='utf-8'))
        assert document['rating_eligible'] and all(p['rating'] is not None for p in document['players'])
