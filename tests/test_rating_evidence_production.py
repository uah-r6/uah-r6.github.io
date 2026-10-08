"""Production failure shapes and secondary post-import maintenance safeguards."""
from copy import deepcopy
import json
import sqlite3

import pytest
from fastapi.testclient import TestClient
from r6stats import rating_evidence as maintenance, credited_refresh as credit
from r6stats.admin.server import create_app
from r6stats.parser.models import Match, ObjectiveOccurrence
from r6stats.rating_inputs_v3 import load_inputs, validate_objectives
from test_rating_evidence_repair import setup


def tables(db):
    return {r[0]:[tuple(x) for x in db.execute(f'SELECT * FROM "{r[0]}" ORDER BY rowid')]
        for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}


def correction_fixture(tmp_path,monkeypatch):
    db,mid,fresh,records=setup(tmp_path,monkeypatch)
    original=deepcopy(fresh)
    original.rounds[0].objectives=[]
    original.rounds[0].objective_occurrences=[ObjectiveOccurrence('plant','defuser_state_v1',2000,
        actor_reason='unbound_timer_evidence')]
    db.execute('UPDATE maps SET normalized_json=? WHERE id=?',(json.dumps(original.to_dict()),mid))
    rid=db.execute('SELECT id FROM rounds WHERE map_id=? AND number=1',(mid,)).fetchone()[0]
    db.execute('DELETE FROM objective_events WHERE round_id=?',(rid,));db.commit()
    credit.store(db,mid,records,'sha')
    monkeypatch.setattr(maintenance.objective_refresh,'parse_archive',lambda *a:deepcopy(fresh))
    return db,mid,original,fresh,records


def test_supported_missing_actor_correction_passes_full_inputs_without_replacing_rounds(tmp_path,monkeypatch):
    db,mid,original,fresh,records=correction_fixture(tmp_path,monkeypatch);before=tables(db)
    assert load_inputs(db,mid)[1]=='Whole map has unsupported core objective evidence.'
    result=maintenance.repair(db,tmp_path,mid)
    assert result['after']['eligible'] and result['changes']==['supported objective actor correction']
    assert load_inputs(db,mid)[0] is not None
    after=tables(db)
    for name in before:
        if name not in ('maps','objective_events','rating_evidence_audit'):assert before[name]==after[name],name
    assert db.execute('SELECT normalized_json FROM rating_input_snapshots').fetchone()[0]==json.dumps(original.to_dict())
    row=db.execute("SELECT after_json FROM rating_evidence_audit WHERE operation='objective_actor_correction'").fetchone()
    assert json.loads(row[0])['changes'][0]['before']==[]
    state=tables(db)
    assert maintenance.repair(db,tmp_path,mid)['changes']==[]
    assert tables(db)==state


@pytest.mark.parametrize('mutation',['actor_source','actor_reason','uid_zero','uid_missing','uid_bool','side','offset_zero','offset_negative','duplicate','actor_mismatch'])
def test_trusted_objective_rules_still_reject_every_unsupported_shape(tmp_path,monkeypatch,mutation):
    db,mid,m,records=setup(tmp_path,monkeypatch)
    o=m.rounds[0].objective_occurrences[0]
    if mutation=='actor_source':o.actor_source=None
    elif mutation=='actor_reason':o.actor_reason=None
    elif mutation=='uid_zero':o.actor_uid=0
    elif mutation=='uid_missing':o.actor_uid=None
    elif mutation=='uid_bool':o.actor_uid=True
    elif mutation=='side':next(p for p in m.rounds[0].players if p.key==o.actor).side='Defense'
    elif mutation=='offset_zero':o.plant_state_offset=0
    elif mutation=='offset_negative':o.plant_state_offset=-1
    elif mutation=='duplicate':m.rounds[0].objective_occurrences.append(deepcopy(o))
    else:o.actor=m.rounds[0].players[0].key
    with pytest.raises(ValueError):validate_objectives(m)


@pytest.mark.parametrize('mutation',['native_offset','native_parity','identity','audit_write'])
def test_actor_correction_cannot_bypass_native_gates_or_partial_commit(tmp_path,monkeypatch,mutation):
    db,mid,old,fresh,records=correction_fixture(tmp_path,monkeypatch)
    if mutation=='audit_write':
        def fail(*a,**k):raise ValueError('audit write failed')
        monkeypatch.setattr(maintenance,'record_audit',fail)
    elif mutation=='identity':fresh.rounds[0].players[3].username='Other identity'
    else:
        if mutation=='native_offset':records[0]['credit']['finishes'][0]['offset']=0
        else:records[0]['credit']['finishes'][0]['feedback']['timeInSeconds']=999
        payload=json.dumps(records,sort_keys=True,separators=(',',':'))
        from r6stats.rating_inputs_v3 import digest
        db.execute('UPDATE map_kill_credit SET evidence_json=?,evidence_sha256=?',(payload,digest(payload)));db.commit()
    before=tables(db)
    if mutation=='audit_write':
        with pytest.raises(ValueError,match='audit write'):maintenance.repair(db,tmp_path,mid)
    else:assert not maintenance.repair(db,tmp_path,mid)['after']['eligible']
    after=tables(db)
    for name in before:
        if name!='rating_evidence_audit':assert before[name]==after[name],name


def test_post_import_attempts_credit_objectives_full_inputs_and_is_idempotent(tmp_path,monkeypatch):
    db,mid,m,records=setup(tmp_path,monkeypatch)
    monkeypatch.setattr(maintenance.objective_refresh,'parse_archive',lambda *a:deepcopy(m))
    def collect(*a):credit.store(db,mid,records,'sha');return dict(source=credit.SOURCE,complete=True)
    monkeypatch.setattr(credit,'collect_after_import',collect)
    result=maintenance.after_import(db,tmp_path,mid)
    assert result['eligible'] and result['reason'] is None
    before=tables(db);assert maintenance.after_import(db,tmp_path,mid)['eligible']
    assert tables(db)==before


def test_post_import_keeps_map_and_exact_failure_details_on_reader_exception(tmp_path,monkeypatch):
    db,mid,m,records=setup(tmp_path,monkeypatch);before=tables(db)
    def fail(*a):raise RuntimeError('fixture scoreboard extraction failed')
    monkeypatch.setattr(credit,'collect_after_import',fail)
    monkeypatch.setattr(maintenance,'repair',fail)
    result=maintenance.after_import(db,tmp_path,mid)
    assert not result['eligible'] and result['status']=='UNAVAILABLE'
    assert result['reason']=='Incomplete credited-kill evidence'
    assert result['kill_credit']['reason']=='fixture scoreboard extraction failed'
    assert 'fixture scoreboard extraction failed' in result['blockers']
    for name, rows in before.items():
        if name!='rating_evidence_audit':assert tables(db)[name]==rows,name
    audit=db.execute("SELECT explanation FROM rating_evidence_audit WHERE operation='post_import_evidence_error'").fetchone()
    provenance=json.loads(audit[0])
    assert 'parser_sha256' in provenance and 'archive_manifest_sha256' in provenance
    assert provenance['changes']==[]


def test_bulk_does_not_stop_after_one_map_fails_and_eligible_maps_stay_unchanged(tmp_path,monkeypatch):
    db,mid,m,records=setup(tmp_path,monkeypatch)
    from r6stats.db import repository as repo
    other=deepcopy(m);other.replay_id='other-source'
    other_id=repo.insert_map(db,other,'other-fingerprint',0,'Other opponent',organization_team_id=1)
    calls=[]
    def fail(*a):
        calls.append(a[-1])
        if a[-1]==mid:raise ValueError('specific blocked reader')
        state=dict(map_id=other_id,eligible=True,exclusion=None)
        return dict(before=state,after=state,changes=[],blockers=[],message='Already eligible')
    monkeypatch.setattr(maintenance,'repair',fail)
    result=maintenance.repair_all(db,tmp_path)
    assert result['audited']==2 and result['blocked']==1 and result['already_eligible']==1
    assert set(calls)=={mid,other_id}
    assert next(r for r in result['results'] if r['after']['map_id']==mid)['blockers']==['specific blocked reader']


def test_bulk_endpoint_requires_csrf_and_confirmation(tmp_path,monkeypatch):
    db,mid,m,records=setup(tmp_path,monkeypatch)
    credit.store(db,mid,records,'sha')
    (tmp_path/'data').mkdir();target=sqlite3.connect(tmp_path/'data/r6stats.sqlite');db.backup(target);target.close()
    (tmp_path/'config').mkdir();(tmp_path/'config/settings.json').write_text(json.dumps({'team':{},'stats':{'trade_window_seconds':8,'rating_version':'siege_style_v3'}}))
    with TestClient(create_app(tmp_path)) as client:
        assert client.post('/api/admin/rating-evidence/repair-all',json={'confirm_all':True}).status_code==403
        headers={'X-R6-Admin-Token':client.get('/api/admin/session').json()['token']}
        assert client.post('/api/admin/rating-evidence/repair-all',json={},headers=headers).status_code==400
        monkeypatch.setattr(maintenance.objective_refresh,'parse_archive',lambda *a:deepcopy(m))
        response=client.post('/api/admin/rating-evidence/repair-all',json={'confirm_all':True},headers=headers)
        assert response.status_code==200,response.text
        assert response.json()['audited']==1 and response.json()['repaired']==1


@pytest.mark.parametrize('mode',['normal','rehost'])
def test_actual_import_api_keeps_success_and_archive_when_secondary_rating_reader_fails(tmp_path,monkeypatch,mode):
    from test_confirmed_rehost import segment
    from r6stats.db import repository as repo
    first=segment(tmp_path,'segment1',[0,1]);second=segment(tmp_path,'segment2',[1,0])
    (tmp_path/'config').mkdir();(tmp_path/'config/settings.json').write_text(json.dumps({
        'team':{},'replays':{'path':str(tmp_path)},'stats':{'trade_window_seconds':8,'rating_version':'siege_style_v3'}}))
    db=repo.connect(tmp_path/'data/r6stats.sqlite');repo.season_create(db,'Fall 2026')
    for i in range(5):repo.roster_add(db,f'Our{i}',team_id=1)
    db.close()
    matches={'segment1':first.match,'segment2':second.match}
    monkeypatch.setattr('r6stats.admin.server.parse_match',lambda path,**k:matches[path.name])
    monkeypatch.setattr('r6stats.parser.confirmed_rehost.parse_match',lambda path,**k:matches[path.name])
    def fail(*a):raise RuntimeError('precise fixture Rating reader failure')
    monkeypatch.setattr(credit,'collect_after_import',fail);monkeypatch.setattr(maintenance,'repair',fail)
    with TestClient(create_app(tmp_path)) as client:
        headers={'X-R6-Admin-Token':client.get('/api/admin/session').json()['token']}
        context={'team_id':1,'season_slug':'fall-2026'}
        if mode=='normal':
            preview=client.post('/api/admin/replays/preview',json={**context,'path':str(tmp_path/'segment1')},headers=headers)
            endpoint='/api/admin/replays/import';confirmation={}
        else:
            preview=client.post('/api/admin/replays/rehost/preview',json={**context,'segments':[{'path':str(tmp_path/'segment1')},{'path':str(tmp_path/'segment2')}],'exclusions':[],'team':0},headers=headers)
            endpoint='/api/admin/replays/rehost/import';confirmation={'confirm_folders_one_map':True,'confirm_roster_change':True,'confirm_score_override':True,'final_our_score':2,'final_their_score':2}
        assert preview.status_code==200,preview.text
        response=client.post(endpoint,json={**context,**confirmation,'preview_token':preview.json()['preview_token'],'opponent':'Fixture','team':0,'confirm_necc':True},headers=headers)
        assert response.status_code==200,response.text
        rating=response.json()['rating']
        assert rating['status']=='UNAVAILABLE' and 'precise fixture Rating reader failure' in rating['blockers']
        mid=response.json()['map_id']
        assert client.get('/api/admin/matches/'+mid).status_code==200
        assert (tmp_path/'data/replay-archive/fall-2026'/mid/'manifest.json').is_file()
