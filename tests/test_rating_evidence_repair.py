"""Archive evidence maintenance refuses conflicts and preserves historical data."""
from copy import deepcopy
import json
from pathlib import Path
import sqlite3

from fastapi.testclient import TestClient
import pytest

from r6stats.admin.server import create_app
from r6stats import credited_refresh as credit, rating_evidence as maintenance
from r6stats.rating_inputs_v3 import load_inputs, store_objective_evidence, digest
from r6stats.parser.models import Match
from r6stats.stats.calculate import calculate_match
from r6stats.series_export import player_total
from test_credited_production import make_db
from test_rating_v3 import evidence


def healthy(monkeypatch):
    monkeypatch.setattr(maintenance.replay_archive, 'verify', lambda *a: {'status':'Healthy','path':'private','rounds':2})
    monkeypatch.setattr(maintenance.replay_archive, 'sha256', lambda *a: 'fixture-sha256')


def setup(tmp_path, monkeypatch):
    db, mid, m, records = make_db(tmp_path)
    evidence(m, records)
    # Use unchanged normalized elimination counts for the evidence-only repair.
    for n, record in enumerate(records, 1):
        for i,p in enumerate(record['credit']['players']):
            k = 2 if i == 1 else 1 if i == 7 else 0
            p.update(initial=(n-1)*k, terminal=n*k, kills=k)
    healthy(monkeypatch)
    monkeypatch.setattr(credit, 'read_archive', lambda *a: (deepcopy(records), 'current-binary'))
    return db, mid, m, records


def incomplete(db, mid, records):
    old = deepcopy(records); old[1]['credit']['complete'] = False
    credit.store(db, mid, old, 'old-binary')
    return dict(db.execute('SELECT * FROM map_kill_credit WHERE map_id=?',(mid,)).fetchone())


def reconcile(db, mid, records, prior):
    return credit.reconcile_incomplete(db, mid, records, 'current-binary', archive_root=Path('archive'),
        fingerprint='fingerprint', prior_sha256=prior['evidence_sha256'])


def test_store_still_refuses_incomplete_overwrite_and_explicit_reconciliation_audits(tmp_path, monkeypatch):
    db, mid, m, records = setup(tmp_path, monkeypatch)
    prior = incomplete(db, mid, records)
    normalized = db.execute('SELECT normalized_json FROM maps').fetchone()[0]
    snapshots = [tuple(r) for r in db.execute('SELECT * FROM rating_input_snapshots')]
    with pytest.raises(ValueError,match='explicit reconciliation'): credit.store(db,mid,records,'current-binary')
    assert reconcile(db,mid,records,prior)['complete']
    assert credit.load(db,mid)['complete']
    assert db.execute('SELECT normalized_json FROM maps').fetchone()[0] == normalized
    assert snapshots == [tuple(r) for r in db.execute('SELECT * FROM rating_input_snapshots')]
    audit = db.execute('SELECT * FROM rating_evidence_audit').fetchone()
    assert json.loads(audit['before_json']) == prior
    assert json.loads(audit['after_json'])['parser_sha256'] == 'current-binary'
    with pytest.raises(ValueError,match='Complete credited'): reconcile(db,mid,records,dict(db.execute('SELECT * FROM map_kill_credit').fetchone()))


@pytest.mark.parametrize('mutation',['fingerprint','inventory','profile','team','partial','reader','old_digest','display'])
def test_reconciliation_rejects_identity_inventory_incomplete_and_reader_mismatches(tmp_path,monkeypatch,mutation):
    db,mid,m,records=setup(tmp_path,monkeypatch);prior=incomplete(db,mid,records)
    if mutation=='fingerprint': db.execute("UPDATE maps SET fingerprint='different'")
    elif mutation=='inventory': records[1]['physical_round']=3
    elif mutation=='profile': records[1]['credit']['players'][0]['profileID']=records[0]['credit']['players'][1]['profileID']
    elif mutation=='team': records[1]['credit']['players'][0]['team']=1
    elif mutation=='partial':records[1]['credit']['complete']=False
    elif mutation=='reader':monkeypatch.setattr(credit,'read_archive',lambda *a:([],'other-binary'))
    elif mutation=='old_digest': prior['evidence_sha256']='wrong'
    else:
        for r in records:
            for i,p in enumerate(r['credit']['players']):
                if i in (0,1):p.update(initial=(r['logical_round']-1)*(2 if i==0 else 0),terminal=r['logical_round']*(2 if i==0 else 0),kills=2 if i==0 else 0)
    with pytest.raises(ValueError): reconcile(db,mid,records,prior)
    assert dict(db.execute('SELECT * FROM map_kill_credit').fetchone())['evidence_sha256']==prior['evidence_sha256'] or mutation=='old_digest'


def test_unhealthy_archive_cannot_collect_or_repair(tmp_path,monkeypatch):
    db,mid,m,records=make_db(tmp_path)
    monkeypatch.setattr(maintenance.replay_archive,'verify',lambda *a:{'status':'Hash mismatch'})
    with pytest.raises(ValueError,match='Healthy'): maintenance.repair(db,tmp_path,mid)
    monkeypatch.setattr(credit,'verify',lambda *a:{'status':'Hash mismatch'})
    exe=tmp_path/'reader.exe';exe.write_bytes(b'not executed')
    with pytest.raises(ValueError,match='healthy'): credit.read_archive(db,tmp_path,mid,exe)


def test_matching_objective_sidecar_gains_full_inputs_and_preserves_normalized(tmp_path,monkeypatch):
    db,mid,m,records=setup(tmp_path,monkeypatch)
    credit.store(db,mid,records,'current-binary')
    old=db.execute('SELECT normalized_json FROM maps').fetchone()[0]
    monkeypatch.setattr(maintenance.objective_refresh,'parse_archive',lambda *a:deepcopy(m))
    assert load_inputs(db,mid)[0] is None
    result=maintenance.repair(db,tmp_path,mid)
    assert result['after']['eligible'] and result['changes']==['objective evidence']
    assert db.execute('SELECT normalized_json FROM maps').fetchone()[0]==old
    assert maintenance.repair(db,tmp_path,mid)['changes']==[]
    a=maintenance.objective_candidate(Match.from_dict(json.loads(old)),m)
    assert calculate_match(a)==calculate_match(Match.from_dict(json.loads(old)))


@pytest.mark.parametrize('mutation',['actor','missing','roster','team','winner','round','replay'])
def test_objective_candidate_never_changes_actors_identities_or_rounds(tmp_path,monkeypatch,mutation):
    db,mid,m,records=setup(tmp_path,monkeypatch)
    original=Match.from_dict(json.loads(db.execute('SELECT normalized_json FROM maps').fetchone()[0]))
    if mutation=='actor':m.rounds[0].objective_occurrences[0].actor=m.rounds[0].players[0].key
    elif mutation=='missing':m.rounds[0].objective_occurrences=[]
    elif mutation=='roster':m.rounds[0].players[0].profile_id='other'
    elif mutation=='team':m.rounds[0].players[0].team=1
    elif mutation=='winner':m.rounds[0].winner=1
    elif mutation=='round':m.rounds[0].number=3
    else:m.replay_id='different'
    with pytest.raises(ValueError):maintenance.objective_candidate(original,m)


@pytest.mark.parametrize('mutation',['fingerprint','normalized','corruption','conflict'])
def test_objective_seals_and_conflict_fail_closed(tmp_path,monkeypatch,mutation):
    db,mid,m,records=setup(tmp_path,monkeypatch);credit.store(db,mid,records,'sha');store_objective_evidence(db,mid,m)
    if mutation=='fingerprint':db.execute("UPDATE map_v3_objective_evidence SET fingerprint='wrong'")
    elif mutation=='normalized':db.execute("UPDATE map_v3_objective_evidence SET normalized_sha256='wrong'")
    elif mutation=='corruption':db.execute("UPDATE map_v3_objective_evidence SET evidence_json='{}'")
    else:
        m.rounds[0].objective_occurrences[0].plant_state_offset+=1
        with pytest.raises(ValueError,match='Existing objective evidence'):store_objective_evidence(db,mid,m)
        return
    if mutation=='corruption':
        with pytest.raises(ValueError,match='integrity'):load_inputs(db,mid)
    else:assert load_inputs(db,mid)[0] is None
    with pytest.raises(ValueError):store_objective_evidence(db,mid,m)


@pytest.mark.parametrize('mutation',['offset','parity','identity'])
def test_objective_backfill_cannot_bypass_remaining_native_gates(tmp_path,monkeypatch,mutation):
    db,mid,m,records=setup(tmp_path,monkeypatch)
    if mutation=='offset':records[0]['credit']['finishes'][0]['offset']=0
    elif mutation=='parity':records[0]['credit']['finishes'][0]['feedback']['timeInSeconds']=999
    else:records[0]['credit']['players'][0]['username']='different'
    credit.store(db,mid,records,'sha')
    monkeypatch.setattr(maintenance.objective_refresh,'parse_archive',lambda *a:deepcopy(m))
    result=maintenance.repair(db,tmp_path,mid)
    assert 'objective evidence' in result['changes'] and not result['after']['eligible']
    assert result['after']['exclusion']


def test_admin_audit_and_repair_confirmation_csrf_and_whole_map_inputs(tmp_path,monkeypatch):
    db,mid,m,records=setup(tmp_path,monkeypatch);credit.store(db,mid,records,'sha')
    (tmp_path/'data').mkdir();target=sqlite3.connect(tmp_path/'data/r6stats.sqlite');db.backup(target);target.close()
    (tmp_path/'config').mkdir();(tmp_path/'config/settings.json').write_text(json.dumps({'team':{},'stats':{'trade_window_seconds':8,'rating_version':'siege_style_v3'}}))
    monkeypatch.setattr(maintenance.objective_refresh,'parse_archive',lambda *a:deepcopy(m))
    with TestClient(create_app(tmp_path)) as client:
        rows=client.get('/api/admin/rating-evidence').json();assert len(rows)==1 and not rows[0]['eligible']
        endpoint=f'/api/admin/matches/{mid}/rating-evidence'
        assert client.post(endpoint,json={'confirm_map_id':mid}).status_code==403
        headers={'X-R6-Admin-Token':client.get('/api/admin/session').json()['token']}
        assert client.post(endpoint,json={'confirm_map_id':'wrong'},headers=headers).status_code==400
        response=client.post(endpoint,json={'confirm_map_id':mid},headers=headers)
        assert response.status_code==200,response.text
        assert response.json()['after']['eligible']


def test_partial_to_full_uses_combined_raw_inputs_and_actual_participation():
    from test_series_export import record
    a,b=record('a',10,11),record('b',14,3,False)
    partial=player_total([a,b],'siege_style_v3')
    assert (partial['rating_maps'],partial['rating_rounds'])==(1,10)
    b['rating']=deepcopy(b['display'])
    exact=(a['rating']['rating']*10+b['rating']['rating']*14)/24
    for r in (a,b):r['rating']['rating']=round(r['rating']['rating'],2)
    full=player_total([a,b],'siege_style_v3')
    assert (full['rating_maps'],full['rating_rounds'])==(2,24)
    assert full['rating']==pytest.approx(exact,abs=1e-12)
    assert full['kills']==partial['kills'] and full['rounds']==partial['rounds']


def test_archive_reader_uses_confirmed_logical_mapping_and_excludes_abandoned_rounds(tmp_path,monkeypatch):
    from types import SimpleNamespace
    db,mid,m,records=setup(tmp_path,monkeypatch)
    # Exercise the real collector, not the injected synthetic reader.
    monkeypatch.undo()
    root=tmp_path/'replay-archive';root.mkdir();exe=tmp_path/'reader.exe';exe.write_bytes(b'fixture reader')
    mapping=[dict(logical_number=1,physical_number=4,segment=1,filename='A-R04.rec',sha256='a'),
             dict(logical_number=None,physical_number=5,segment=1,filename='A-R05.rec',sha256='discarded'),
             dict(logical_number=2,physical_number=1,segment=2,filename='B-R01.rec',sha256='b')]
    (root/'manifest.json').write_text(json.dumps({'archive_format_version':2,'source_manifest':{'mapping':mapping}}))
    monkeypatch.setattr(credit,'verify',lambda *a:{'status':'Healthy','path':str(root)})
    calls=[]
    def run(args,**kwargs):
        calls.append(args[1]);return SimpleNamespace(stdout=json.dumps({'credit':records[len(calls)-1]['credit']}))
    monkeypatch.setattr(credit.subprocess,'run',run)
    result,binary=credit.read_archive(db,root,mid,exe)
    assert [(r['logical_round'],r['physical_round'],r['segment']) for r in result]==[(1,4,'segment-01'),(2,1,'segment-02')]
    assert len(calls)==2 and all('R05' not in p for p in calls)


def test_recovered_credit_still_requires_full_native_gates(tmp_path,monkeypatch):
    db,mid,m,records=setup(tmp_path,monkeypatch)
    records[0]['credit']['finishes'][0]['offset']=0
    incomplete(db,mid,records)
    monkeypatch.setattr(maintenance.objective_refresh,'parse_archive',lambda *a:deepcopy(m))
    result=maintenance.repair(db,tmp_path,mid)
    assert credit.load(db,mid)['complete']
    assert result['changes']==['credited evidence','objective evidence']
    assert not result['after']['eligible'] and 'offset' in result['after']['exclusion']


def test_objective_sidecar_and_audit_are_one_transaction(tmp_path,monkeypatch):
    db,mid,m,records=setup(tmp_path,monkeypatch)
    def fail(*args,**kwargs):raise ValueError('audit failed')
    monkeypatch.setattr(maintenance,'record_audit',fail)
    with pytest.raises(ValueError,match='audit failed'):store_objective_evidence(db,mid,m,audit={'parser_sha256':'sha'})
    assert db.execute('SELECT count(*) FROM map_v3_objective_evidence').fetchone()[0]==0
