"""Roster removal is historical; identity deletion is unused-only and atomic."""
from copy import deepcopy
import json
from pathlib import Path
import sqlite3

import pytest
from fastapi.testclient import TestClient

from r6stats.db import repository as repo, teams, appearances
from r6stats.export import export
from r6stats import roster_admin
from r6stats.admin.server import create_app
from r6stats.parser.models import Player
from test_teams import replay, settings


def dump(db):
    return {r[0]:[tuple(x) for x in db.execute(f'SELECT * FROM "{r[0]}" ORDER BY rowid')]
            for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}


def setup(tmp_path, *, history=False):
    db=repo.connect(tmp_path/'data/r6stats.sqlite');repo.season_create(db,'Fall 2026')
    repo.roster_add(db,'Our0',team_id=2,start_date='2026-09-01',substitute_eligible=True)
    repo.roster_add_alias(db,1,'OldAlias',make_current=False)
    mid=repo.insert_map(db,replay(),'map',0,'Opponent',organization_team_id=2) if history else None
    (tmp_path/'config').mkdir();(tmp_path/'config/settings.json').write_text(json.dumps(settings()),encoding='utf-8')
    export(db,settings(),tmp_path/'web/public/data')
    return db,mid


def files(root):
    return {str(p.relative_to(root)):p.read_bytes() for p in root.rglob('*.json')}


def test_remove_closes_membership_preserves_every_historical_count_identity_and_sub_setting(tmp_path):
    db,mid=setup(tmp_path,history=True);before=dump(db)
    root=tmp_path/'web/public/data';old_map=(root/f'matches/{mid}.json').read_bytes()
    old_stats=json.loads((root/'players/our0/fall-2026.json').read_text())
    teams.remove(db,1,2,'2026-10-07')
    assert db.execute('SELECT end_date FROM team_memberships').fetchone()[0]=='2026-10-07'
    for table,rows in before.items():
        if table!='team_memberships':assert dump(db)[table]==rows
    assert teams.member(db,1,2,'2026-10-06') and not teams.member(db,1,2,'2026-10-07')
    p=db.execute('SELECT * FROM players').fetchone()
    assert p['status']=='Active' and p['tracked']==1 and p['profile_id']=='our-0' and p['substitute_eligible']==1
    assert appearances.classify(db,p,2,'2026-10-07')['appearance_role']=='sub'
    export(db,settings(),root)
    assert (root/f'matches/{mid}.json').read_bytes()==old_map
    new_stats=json.loads((root/'players/our0/fall-2026.json').read_text())
    for k in old_stats:
        if k!='memberships':assert old_stats[k]==new_stats[k]
    assert json.loads((root/'teams/white/index.json').read_text())['roster']==[]
    assert not repo.roster_deletion_audit(db,1)['can_delete']


def test_same_day_unused_mistaken_membership_cancel_keeps_identity_and_aliases(tmp_path):
    db,_=setup(tmp_path)
    repo.roster_add(db,'Nanor555',team_id=2,start_date='2026-10-07')
    before=[tuple(r) for r in db.execute('SELECT * FROM players')]
    teams.remove(db,2,2,'2026-10-07')
    assert [tuple(r) for r in db.execute('SELECT * FROM players')]==before
    assert db.execute('SELECT username FROM aliases WHERE player_id=2').fetchone()[0]=='Nanor555'
    assert db.execute('SELECT count(*) FROM team_memberships WHERE player_id=2').fetchone()[0]==0
    assert db.execute('SELECT status,substitute_eligible FROM players WHERE id=2').fetchone()[:]==('Active',0)


def test_removal_refuses_wrong_team_before_start_and_same_day_historical_membership(tmp_path):
    db,mid=setup(tmp_path,history=True)
    before=dump(db)
    for team,on in [(1,'2026-10-07'),(2,'2026-08-31'),(2,'2026-09-01')]:
        with pytest.raises(ValueError):teams.remove(db,1,team,on)
        assert dump(db)==before


def test_unused_deletion_removes_aliases_memberships_identity_and_public_profile(tmp_path):
    db,_=setup(tmp_path)
    assert repo.roster_deletion_audit(db,1)['can_delete']
    result=roster_admin.delete_and_export(db,1,'Our0',settings(),tmp_path)
    assert result['ok']
    for table in ('players','aliases','team_memberships'):assert db.execute(f'SELECT count(*) FROM {table}').fetchone()[0]==0
    assert not list((tmp_path/'web/public/data/players').rglob('*.json'))
    assert json.loads((tmp_path/'web/public/data/index.json').read_text())['players']==[]
    assert not list((tmp_path/'data').glob('.roster-delete-*'))


@pytest.mark.parametrize('confirmation',['','our0','OldAlias','Other'])
def test_exact_current_username_is_required(tmp_path,confirmation):
    db,_=setup(tmp_path);before=dump(db);public=files(tmp_path/'web/public/data')
    with pytest.raises(ValueError,match='exact current'):roster_admin.delete_and_export(db,1,confirmation,settings(),tmp_path)
    assert dump(db)==before and files(tmp_path/'web/public/data')==public


@pytest.mark.parametrize('reference',['round_players','map_player_appearances','map_kd_corrections','new_fk','new_column','snapshot','normalized','credit','unbound_alias','unbound_profile'])
def test_every_discovered_historical_reference_blocks_deletion_without_mutating_any_data(tmp_path,reference):
    db,mid=setup(tmp_path,history=True)
    # Isolate each guard in a synthetic database. Never alter production data.
    db.execute('DELETE FROM map_player_appearances');db.execute('UPDATE round_players SET player_id=NULL')
    original=db.execute('SELECT normalized_json FROM maps').fetchone()[0]
    db.execute("UPDATE maps SET normalized_json='{}'")
    if reference=='round_players':db.execute('UPDATE round_players SET player_id=1 WHERE player_key=?',('our-0',))
    elif reference=='map_player_appearances':db.execute('INSERT INTO map_player_appearances VALUES(?,?,?,?,?)',(mid,1,'roster','2026-09-29',2))
    elif reference=='map_kd_corrections':db.execute('INSERT INTO map_kd_corrections VALUES(?,?,?,?,?,?,?,?,?)',(mid,1,0,0,0,0,'test','','now'))
    elif reference=='new_fk':db.execute('CREATE TABLE future_stats(player INTEGER REFERENCES players(id) ON DELETE CASCADE)');db.execute('INSERT INTO future_stats VALUES(1)')
    elif reference=='new_column':db.execute('CREATE TABLE legacy_stats(player_id INTEGER)');db.execute('INSERT INTO legacy_stats VALUES(1)')
    elif reference=='snapshot':db.execute('INSERT INTO rating_input_snapshots VALUES(?,?,?,?)',(mid,'siege_style_v2',original,'sha'))
    elif reference=='normalized':db.execute('UPDATE maps SET normalized_json=?',(original,))
    elif reference=='credit':
        db.execute('CREATE TABLE map_kill_credit(map_id TEXT,evidence_json TEXT)');db.execute('INSERT INTO map_kill_credit VALUES(?,?)',(mid,json.dumps([{'credit':{'players':[{'username':'OldAlias','profileID':'our-0'}]}}])))
    elif reference=='unbound_profile':db.execute('UPDATE round_players SET username=? WHERE profile_id=?',('Renamed','our-0'))
    # The other guards still conservatively see unbound aliases/profile IDs.
    # Confirm the specifically named guard is reported, then verify all data.
    db.commit();before=dump(db)
    status=repo.roster_deletion_audit(db,1);assert not status['can_delete']
    expected={'new_fk':'future_stats','new_column':'legacy_stats','snapshot':'rating_input_snapshots','normalized':'maps','credit':'map_kill_credit','unbound_alias':'round_players','unbound_profile':'round_players'}.get(reference,reference)
    assert any(r['table']==expected for r in status['references'])
    with pytest.raises(ValueError,match='Remove from roster'):repo.roster_delete(db,1,'Our0')
    assert dump(db)==before


@pytest.mark.parametrize('failure',['export','validation','install','commit','delete'])
def test_delete_and_export_roll_back_identity_configuration_and_public_files(tmp_path,monkeypatch,failure):
    db,_=setup(tmp_path)
    if failure=='commit':db.execute('CREATE TABLE deferred_test(team_id INTEGER REFERENCES teams(id) DEFERRABLE INITIALLY DEFERRED)');db.commit()
    if failure=='delete':db.execute("CREATE TRIGGER refuse_delete BEFORE DELETE ON players BEGIN SELECT RAISE(ABORT,'delete failed'); END");db.commit()
    before=dump(db);public=files(tmp_path/'web/public/data')
    def fail(*a,**k):raise ValueError('export failed')
    if failure=='export':monkeypatch.setattr(roster_admin,'export',fail)
    elif failure=='validation':monkeypatch.setattr(roster_admin,'validate_public_data',fail)
    elif failure=='install':
        original=Path.rename
        def rename(self,target):
            if self.as_posix().endswith('/generated/web/public/data'):raise OSError('install failed')
            return original(self,target)
        monkeypatch.setattr(Path,'rename',rename)
    elif failure=='commit':
        original=roster_admin.export
        def prepare(db,config,root):original(db,config,root);db.execute('INSERT INTO deferred_test VALUES(999)')
        monkeypatch.setattr(roster_admin,'export',prepare)
    with pytest.raises((ValueError,OSError,sqlite3.Error)):roster_admin.delete_and_export(db,1,'Our0',settings(),tmp_path)
    assert dump(db)==before and files(tmp_path/'web/public/data')==public
    assert not list((tmp_path/'data').glob('.roster-delete-*'))


@pytest.mark.parametrize('alias',['OldAlias','oldalias','OUR0'])
def test_case_insensitive_existing_alias_is_reused_by_membership_not_duplicated(tmp_path,alias):
    db,_=setup(tmp_path)
    row=repo.roster_identity(db,alias);assert row['id']==1
    before=dump(db)
    with pytest.raises(ValueError,match='existing player'):repo.roster_add(db,alias,team_id=1,start_date='2026-10-07')
    assert dump(db)==before
    teams.move(db,row['id'],1,'2026-10-07')
    assert db.execute('SELECT count(*) FROM players').fetchone()[0]==1
    assert teams.member(db,1,2,'2026-10-06') and teams.member(db,1,1,'2026-10-07')


def test_sub_only_identity_can_be_regular_roster_without_changing_global_eligibility(tmp_path):
    db,_=setup(tmp_path)
    repo.roster_add(db,'Nachofries_08',substitute_eligible=True)
    row=repo.roster_identity(db,'nachofries_08');assert row['id']==2
    teams.move(db,2,2,'2026-10-07')
    assert db.execute('SELECT count(*) FROM players').fetchone()[0]==2
    assert teams.member(db,2,2,'2026-10-07')
    assert db.execute('SELECT substitute_eligible FROM players WHERE id=2').fetchone()[0]==1
    db.execute("UPDATE players SET profile_id='proven-profile' WHERE id=2");db.commit()
    with pytest.raises(ValueError,match='Profile ID conflict'):repo.identity_match(db,Player('different-profile','nachofries_08',0))


def test_api_remove_and_delete_keep_confirmation_csrf_and_history_guards(tmp_path):
    db,mid=setup(tmp_path,history=True)
    repo.roster_add(db,'Mistake',team_id=2,start_date='2026-10-07');db.close()
    with TestClient(create_app(tmp_path)) as client:
        headers={'X-R6-Admin-Token':client.get('/api/admin/session').json()['token']}
        assert client.delete('/api/admin/roster/2').status_code==403
        assert client.request('DELETE','/api/admin/roster/2',json={'confirm_username':'wrong'},headers=headers).status_code==400
        assert client.get('/api/admin/roster/1/deletion').json()['can_delete'] is False
        response=client.request('DELETE','/api/admin/roster/1',json={'confirm_username':'Our0'},headers=headers)
        assert response.status_code==400 and 'Mark Alumni' in response.json()['detail']
        response=client.post('/api/admin/roster/1/remove-from-roster',json={'team_id':2,'effective_date':'2026-10-07'},headers=headers)
        assert response.status_code==200,response.text
        assert client.get('/api/admin/roster',params={'team_id':2}).json()[0]['status']=='Active'
        response=client.request('DELETE','/api/admin/roster/2',json={'confirm_username':'Mistake'},headers=headers)
        assert response.status_code==200,response.text
        assert len(client.get('/api/admin/roster').json())==1


def test_new_history_after_eligibility_preview_is_rechecked_at_delete(tmp_path):
    db,_=setup(tmp_path)
    assert repo.roster_deletion_audit(db,1)['can_delete']
    repo.insert_map(db,replay(),'new',0,'Opponent',organization_team_id=2)
    before=dump(db)
    with pytest.raises(ValueError,match='imported match history'):repo.roster_delete(db,1,'Our0')
    assert dump(db)==before


def test_conflicting_current_username_and_alias_are_not_merged(tmp_path):
    db,_=setup(tmp_path)
    repo.roster_add(db,'Different',substitute_eligible=True)
    db.execute("UPDATE players SET username='OldAlias' WHERE id=2");db.commit()
    before=dump(db)
    with pytest.raises(ValueError,match='conflicting player identities'):repo.roster_identity(db,'oldalias')
    with pytest.raises(ValueError,match='conflicting player identities'):repo.roster_add(db,'oldalias',team_id=2)
    assert dump(db)==before
