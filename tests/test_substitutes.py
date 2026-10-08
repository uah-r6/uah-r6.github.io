"""Historical roles isolate appearances without changing any stat formula."""
from contextlib import closing
from copy import deepcopy
import json
import sqlite3
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from r6stats.db import repository as repo, appearances, teams
from r6stats.export import export
from r6stats.stats.calculate import calculate_match, aggregate
from r6stats.admin.server import create_app
from r6stats.publishing import validate_public_data
from test_teams import replay, settings, seed
from test_confirmed_rehost import segment


def role(db, mid, pid=1):
    return dict(db.execute('SELECT * FROM map_player_appearances WHERE map_id=? AND player_id=?', (mid, pid)).fetchone())


@pytest.mark.parametrize('regular,eligible,owner,expected', [
    (1, False, 1, 'roster'), (1, True, 1, 'roster'),
    (2, False, 2, 'roster'), (2, True, 2, 'roster'),
    (1, True, 2, 'sub'), (2, True, 1, 'sub'),
    (None, True, 1, 'sub'), (None, True, 2, 'sub'),
])
def test_global_eligibility_and_dated_regular_membership(tmp_path, regular, eligible, owner, expected):
    with closing(repo.connect(tmp_path/'db')) as db:
        repo.season_create(db, 'Fall 2026')
        repo.roster_add(db, 'Our0', team_id=regular, substitute_eligible=eligible)
        match = replay()
        assert repo.choose_team(db, match, 0, team_id=owner)[0] == 0
        mid = repo.insert_map(db, match, 'map', 0, 'Opponent', organization_team_id=owner)
        assert role(db, mid)['appearance_role'] == expected
        assert role(db, mid)['regular_team_id'] == regular
        assert db.execute('SELECT team_id FROM maps').fetchone()[0] == owner
        assert db.execute('SELECT count(*) FROM players').fetchone()[0] == 1
        with pytest.raises(ValueError, match='already'):
            repo.insert_map(db, match, 'map', 0, 'Opponent', organization_team_id=owner)


@pytest.mark.parametrize('regular,owner', [(1,2), (2,1), (None,1), (None,2)])
def test_noneligible_known_player_cannot_be_silently_ignored(tmp_path, regular, owner):
    with closing(repo.connect(tmp_path/'db')) as db:
        repo.season_create(db, 'Fall 2026')
        repo.roster_add(db, 'Our0', team_id=regular)
        with pytest.raises(ValueError, match='not substitute eligible'):
            repo.insert_map(db, replay(), 'bad', 0, 'Opponent', organization_team_id=owner)
        assert db.execute('SELECT count(*) FROM maps').fetchone()[0] == 0
        assert db.execute('SELECT profile_id FROM players').fetchone()[0] is None


def test_eligible_pool_does_not_vote_and_frozen_roles_survive_moves_reparse_and_alumni(tmp_path):
    with closing(repo.connect(tmp_path/'db')) as db:
        seed(db)
        for pid in range(1,6):
            repo.roster_update(db, pid, substitute_eligible=True)
        with pytest.raises(ValueError, match='ambiguous'):
            repo.choose_team(db, replay(), team_id=2)
        mid = repo.insert_map(db, replay(), 'sub', 0, 'Opponent', organization_team_id=2)
        original = [dict(r) for r in db.execute('SELECT * FROM map_player_appearances')]
        for pid in range(1,6):
            repo.roster_update(db, pid, substitute_eligible=False)
            teams.move(db, pid, 2, '2026-10-01')
        repo.roster_update(db, 1, status='Alumni')
        repo.reparse_map(db, mid, replay(), 'sub')
        repo.match_update(db, mid, played_on='2026-10-03')
        assert [dict(r) for r in db.execute('SELECT * FROM map_player_appearances')] == original
        with pytest.raises(sqlite3.IntegrityError, match='immutable'):
            db.execute("UPDATE map_player_appearances SET appearance_role='roster'")
        db.rollback()
        later = repo.insert_map(db, replay('later', '2026-10-03T00:00:00Z'), 'later', 0, 'Opponent', organization_team_id=2)
        assert role(db, later)['appearance_role'] == 'roster'


def test_alias_profile_identity_conflicts_and_changed_side_remain_protected(tmp_path):
    with closing(repo.connect(tmp_path/'db')) as db:
        repo.season_create(db,'Fall 2026')
        repo.roster_add(db,'Old',substitute_eligible=True)
        repo.roster_add_alias(db,1,'Our0')
        match = replay()
        mid = repo.insert_map(db,match,'first',0,'Opponent',organization_team_id=2)
        assert role(db,mid)['appearance_role']=='sub'
        changed = replay('changed')
        for r in changed.rounds:
            r.players[0].username='NewAlias'
        assert repo.choose_team(db,changed,0,team_id=1)[1]==['Old']
        assert db.execute('SELECT count(*) FROM players').fetchone()[0]==1
        conflict=replay('conflict');conflict.rounds[0].players[0].profile_id='wrong-profile'
        with pytest.raises(ValueError,match='Profile ID conflict'):
            repo.choose_team(db,conflict,0,team_id=1)
        changed.rounds[-1].players[0].team=1
        with pytest.raises(ValueError,match='changed teams'):
            repo.choose_team(db,changed,0,team_id=1)


@pytest.mark.parametrize("regular,owner", [(1,2),(2,1)])
def test_cross_team_sub_stats_and_rating_are_strictly_isolated(tmp_path, regular, owner):
    with closing(repo.connect(tmp_path/'db')) as db:
        seed(db)
        if regular == 2:
            for pid in range(1,6):teams.move(db,pid,2,'2026-01-01')
        for i in range(1,5):repo.roster_add(db,f'Partner{i}',team_id=owner)
        first=replay('roster'); mid=repo.insert_map(db,first,'first',0,'Opponent',organization_team_id=regular)
        config=settings();config['stats']['rating_version']='siege_style_v3'
        inputs={mid:calculate_match(first)}
        def generate():
            with patch('r6stats.export.load_v3',side_effect=lambda db,mid,window:(inputs[mid],None)):
                export(db,config,tmp_path/'web/public/data')
        def load(path):return json.loads((tmp_path/'web/public/data'/path).read_text(encoding='utf8'))
        generate()
        regular_slug='blue' if regular==1 else 'white'
        owner_slug='blue' if owner==1 else 'white'
        names=['players/our0/'+p+'.json' for p in ('fall-2026','career')]+['teams/'+regular_slug+'/'+p+'.json' for p in ('fall-2026','career')]
        before={n:load(n) for n in names}
        repo.roster_update(db,1,substitute_eligible=True)
        # Four regular teammates establish side zero; the other team's player subs.
        repo.roster_add(db,'Unused',substitute_eligible=True)
        second=replay('sub','2026-10-02T00:00:00Z')
        for r in second.rounds:
            for i in range(1,5):r.players[i].username=f'Partner{i}';r.players[i].profile_id=f'partner-{i}'
        assert repo.choose_team(db,second,team_id=owner)[0]==0
        sub=repo.insert_map(db,second,'second',0,'Opponent',organization_team_id=owner)
        inputs[sub]=calculate_match(second)
        generate()
        for n in names:
            after=load(n)
            if n.startswith('players/'):
                after.pop('sub_teams');expected=deepcopy(before[n]);expected.pop('sub_teams')
                assert after==expected  # Normal trend, maps, every count and exact Rating.
            else:assert after==before[n]
        scope=load('teams/'+owner_slug+'/career.json')
        assert {p['slug'] for p in scope['players']}=={'partner1','partner2','partner3','partner4'}
        assert {p['slug'] for p in scope['sub_players']}=={'our0'}
        profile=load('players/our0/subs/'+owner_slug+'/career.json')
        assert profile['rounds']==2 and profile['maps']==1
        key=second.rounds[0].players[0].key
        expected=aggregate([inputs[sub][key]],'siege_style_v3')['rating']
        assert profile['rating']==expected
        series=load('series/'+load('matches/'+sub+'.json')['series_id']+'.json')
        participant=next(p for p in series['players'] if p['slug']=='our0')
        assert participant['appearance_role']=='sub' and participant['rating']==expected
        assert validate_public_data(tmp_path)>0
        # Manual display correction excludes only that map's Rating and never normal stats.
        from r6stats.manual_kd import save
        save(db,sub,1,3,0,'verified test score','',8)
        generate()
        assert load('players/our0/subs/'+owner_slug+'/career.json')['kills']==3
        assert load('players/our0/subs/'+owner_slug+'/career.json')['rating'] is None
        assert load('players/our0/career.json')['rating']==before['players/our0/career.json']['rating']


def test_sub_only_profiles_and_team_specific_career_and_mixed_series_trend(tmp_path):
    with closing(repo.connect(tmp_path/'db')) as db:
        repo.season_create(db,'Fall 2026')
        repo.roster_add(db,'Our0',substitute_eligible=True)
        inputs={};config=settings();config['stats']['rating_version']='siege_style_v3'
        for owner in (1,2):
            match=replay(str(owner));mid=repo.insert_map(db,match,str(owner),0,'Opponent',organization_team_id=owner)
            inputs[mid]=calculate_match(match)
        def generate():
            with patch('r6stats.export.load_v3',side_effect=lambda db,mid,window:(inputs[mid],None)):
                export(db,config,tmp_path/'web/public/data')
        def load(path):return json.loads((tmp_path/'web/public/data'/path).read_text(encoding='utf8'))
        generate()
        normal=load('players/our0/career.json')
        assert normal['rounds']==0 and normal['rating'] is None and normal['series_ratings']==[]
        assert {t['team_slug'] for t in normal['sub_teams']}=={'blue','white'}
        assert len(load('index.json')['players'])==1
        for team in ('blue','white'):
            assert load('teams/'+team+'/career.json')['players']==[]
            assert load('teams/'+team+'/career.json')['sub_players'][0]['rounds']==2
            assert load('players/our0/subs/'+team+'/career.json')['rounds']==2
        teams.move(db,1,1,'2026-10-01')
        old_series=load('matches/'+list(inputs)[0]+'.json')['series_id']
        match=replay('later','2026-10-02T00:00:00Z')
        mid=repo.insert_map(db,match,'later',0,'Opponent',series_id=old_series,organization_team_id=1)
        inputs[mid]=calculate_match(match);generate()
        normal=load('players/our0/career.json')
        point=normal['series_ratings'][0]
        assert point['rounds']==point['rating_rounds']==2 and point['maps']==1
        series=load('series/'+old_series+'.json')
        assert series['players'][0]['appearance_role']=='mixed'
        assert series['players'][0]['rounds']==4
        assert validate_public_data(tmp_path)>0
        roles = [dict(r) for r in db.execute('SELECT * FROM map_player_appearances')]
        # Incomplete SUB map makes the combined participant Rating unavailable;
        # its complete regular-roster map still supplies the normal trend.
        inputs[list(inputs)[0]] = None
        generate()
        normal_after = load('players/our0/career.json')
        assert {k:v for k,v in normal_after.items() if k!='sub_teams'} == {k:v for k,v in normal.items() if k!='sub_teams'}
        participant = load('series/'+old_series+'.json')['players'][0]
        assert participant['rating'] is None
        assert (participant['rating_maps'], participant['maps'], participant['rating_rounds'], participant['rounds']) == (1, 2, 2, 4)
        assert participant['roster_stats']['rating'] == point['rating']
        assert roles == [dict(r) for r in db.execute('SELECT * FROM map_player_appearances')]
        assert validate_public_data(tmp_path)>0


def test_migration_is_idempotent_atomic_and_preserves_old_bindings(tmp_path):
    path=tmp_path/'legacy'
    with closing(repo.connect(path)) as db:
        seed(db);repo.insert_map(db,replay(),'original',0,'Opponent',organization_team_id=1)
        # Simulate the pre-role schema with existing trusted participant bindings.
        db.execute('DROP TABLE map_player_appearances');db.execute('DROP TABLE appearance_schema_version')
        db.execute('ALTER TABLE players DROP COLUMN substitute_eligible');db.commit()
        before=[dict(r) for r in db.execute('SELECT * FROM round_players')]
        appearances.migrate(db)
        roles=[dict(r) for r in db.execute('SELECT * FROM map_player_appearances')]
        assert len(roles)==5 and all(r['appearance_role']=='roster' for r in roles)
        appearances.migrate(db)
        assert roles==[dict(r) for r in db.execute('SELECT * FROM map_player_appearances')]
        assert before==[dict(r) for r in db.execute('SELECT * FROM round_players')]
        assert db.execute('PRAGMA foreign_key_check').fetchall()==[]
    with closing(sqlite3.connect(tmp_path/'broken')) as db:
        db.row_factory=sqlite3.Row;db.executescript(repo.SCHEMA);teams.migrate(db)
        db.execute('DROP TABLE round_players');db.commit()
        with pytest.raises(sqlite3.OperationalError):appearances.migrate(db)
        assert 'substitute_eligible' not in {r['name'] for r in db.execute('PRAGMA table_info(players)')}
        assert db.execute("SELECT 1 FROM sqlite_master WHERE name='map_player_appearances'").fetchone() is None


def test_admin_preview_import_role_history_and_global_roster_controls(tmp_path):
    (tmp_path/'config').mkdir();(tmp_path/'config/settings.json').write_text(json.dumps(settings()))
    source=tmp_path/'source';source.mkdir();(source/'Match-R01.rec').write_bytes(b'one');(source/'Match-R02.rec').write_bytes(b'two')
    with TestClient(create_app(tmp_path)) as client, patch('r6stats.admin.server.parse_match',return_value=replay()):
        headers={'X-R6-Admin-Token':client.get('/api/admin/session').json()['token']}
        def post(path,payload):return client.post('/api/admin'+path,json=payload,headers=headers)
        assert post('/seasons',{'name':'Fall 2026'}).status_code==200
        assert post('/roster',{'username':'Our0','team_id':None,'substitute_eligible':True}).status_code==200
        assert post('/roster',{'username':'Our1','team_id':2}).status_code==200
        payload={'path':str(source),'team_id':2,'team':0,'season_slug':'fall-2026'}
        preview=post('/replays/preview',payload)
        assert preview.status_code==200,preview.text
        assert {p['name']:p['appearance_role'] for p in preview.json()['appearances']}=={'Our0':'sub','Our1':'roster'}
        imported=post('/replays/import',{'preview_token':preview.json()['preview_token'],'team_id':2,'team':0,'season_slug':'fall-2026','opponent':'Opponent','confirm_necc':True})
        assert imported.status_code==200,imported.text
        mid=imported.json()['map_id']
        assert client.patch('/api/admin/roster/1',headers=headers,json={'substitute_eligible':False,'status':'Alumni'}).status_code==200
        detail=client.get('/api/admin/matches/'+mid).json()
        assert detail['appearances'][0]['appearance_role']=='sub'
        assert detail['appearances'][0]['regular_team_name'] is None
        # Turning off capability blocks a later preview, with an actionable error.
        refused=post('/replays/preview',payload)
        assert refused.status_code==400 and 'not substitute eligible' in refused.text
        assert client.get('/api/admin/roster').json()[0]['status'] in ('Active','Alumni')


def test_rehost_uses_logical_date_and_counts_substitute_once(tmp_path):
    first=segment(tmp_path,'segment1',[0,1]);second=segment(tmp_path,'segment2',[0,1])
    second.match.timestamp='2026-10-02T00:00:00Z'
    (tmp_path/'config').mkdir();(tmp_path/'config/settings.json').write_text(json.dumps(settings()))
    with closing(repo.connect(tmp_path/'data/r6stats.sqlite')) as db:
        seed(db);repo.roster_update(db,1,substitute_eligible=True)
        for pid in range(2,6):teams.move(db,pid,2,'2026-09-01')
        teams.move(db,1,2,'2026-10-01')
    with TestClient(create_app(tmp_path)) as client, patch('r6stats.parser.confirmed_rehost.parse_match',side_effect=lambda path,**kw:first.match if PathName(path)=='segment1' else second.match):
        headers={'X-R6-Admin-Token':client.get('/api/admin/session').json()['token']}
        response=client.post('/api/admin/replays/rehost/preview',headers=headers,json={'team_id':2,'season_slug':'fall-2026','team':0,'segments':[{'path':str(tmp_path/'segment1')},{'path':str(tmp_path/'segment2')}]})
        assert response.status_code==200,response.text
        preview=response.json()
        assert next(p for p in preview['appearances'] if p['name']=='Our0')['appearance_role']=='sub'
        response=client.post('/api/admin/replays/rehost/import',headers=headers,json={'team_id':2,'season_slug':'fall-2026','team':0,'preview_token':preview['preview_token'],'opponent':'Opponent','confirm_necc':True,'confirm_folders_one_map':True,'confirm_score_override':True,'final_our_score':2,'final_their_score':2})
        assert response.status_code==200,response.text
        with closing(repo.connect(tmp_path/'data/r6stats.sqlite')) as db:
            assert db.execute("SELECT count(*) FROM map_player_appearances WHERE appearance_role='sub'").fetchone()[0]==1
            assert db.execute('SELECT count(*) FROM rounds').fetchone()[0]==4


def PathName(path):
    from pathlib import Path
    return Path(path).name


def test_duplicate_alias_identity_cannot_double_count_a_round(tmp_path):
    with closing(repo.connect(tmp_path/'db')) as db:
        repo.season_create(db,'Fall 2026')
        repo.roster_add(db,'Our0',substitute_eligible=True)
        repo.roster_add_alias(db,1,'Our1')
        match=replay()
        for r in match.rounds:
            r.players[0].profile_id='';r.players[1].profile_id=''
        with pytest.raises(ValueError,match='Duplicate configured player identity'):
            repo.insert_map(db,match,'bad',0,'Opponent',organization_team_id=1)
        assert db.execute('SELECT count(*) FROM maps').fetchone()[0]==0
        assert db.execute('SELECT count(*) FROM players').fetchone()[0]==1


def test_two_connections_migrate_roles_once(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    path=tmp_path/'db'
    with closing(repo.connect(path)) as db:
        seed(db);repo.insert_map(db,replay(),'map',0,'Opponent',organization_team_id=1)
        db.execute('DROP TABLE map_player_appearances');db.execute('DROP TABLE appearance_schema_version')
        db.execute('ALTER TABLE players DROP COLUMN substitute_eligible');db.commit()
    barrier=Barrier(2)
    def migrate():
        with closing(sqlite3.connect(path)) as db:
            db.row_factory=sqlite3.Row;barrier.wait(timeout=5);appearances.migrate(db)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(migrate) for _ in range(2)]
        for future in futures:future.result(timeout=10)
    with closing(repo.connect(path)) as db:
        assert db.execute('SELECT count(*) FROM map_player_appearances').fetchone()[0]==5
        assert db.execute('SELECT count(*) FROM appearance_schema_version').fetchone()[0]==1
