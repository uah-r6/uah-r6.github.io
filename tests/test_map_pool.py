import json
import sqlite3
from contextlib import closing

import pytest
from fastapi.testclient import TestClient

from r6stats.admin.server import create_app
from r6stats.db import map_pool, repository as repo
from r6stats.export import export
from r6stats.map_analytics import build_analytics, project_pool
from r6stats.publishing import validate_public_data
from tests.test_map_analytics import match, find
from tests.test_teams import seed, replay, settings


def test_migration_preserves_existing_visible_catalog_and_is_idempotent(tmp_path):
    path=tmp_path/'legacy.sqlite'
    with sqlite3.connect(path) as db:
        db.executescript(repo.SCHEMA)
        db.execute("INSERT INTO seasons(slug,name,active) VALUES('fall','Fall',1)")
        db.commit(); db.row_factory=sqlite3.Row
        before=[dict(r) for r in db.execute('SELECT * FROM seasons')]
        map_pool.migrate(db)
        assert [dict(r) for r in db.execute('SELECT * FROM seasons')]==before
        assert len(map_pool.load(db,'fall')['maps'])==26
        assert map_pool.load(db,'fall')['origin']=='preserved_visible_catalog_v1'
        map_pool.save(db,'fall',['border'])
        snapshot=map_pool.load(db,'fall')
        map_pool.migrate(db)
        assert map_pool.load(db,'fall')==snapshot
        map_pool.save(db,'fall',[],True)
        map_pool.migrate(db)
        assert map_pool.load(db,'fall')['maps']==[]
        assert db.execute('PRAGMA foreign_key_check').fetchall()==[]


def test_migration_rolls_back_when_seasons_are_missing(tmp_path):
    with sqlite3.connect(tmp_path/'broken.sqlite') as db:
        db.row_factory=sqlite3.Row
        with pytest.raises(sqlite3.OperationalError):map_pool.migrate(db)
        assert not db.execute("SELECT 1 FROM sqlite_master WHERE name='map_pool_catalog'").fetchone()


def test_model_season_isolation_validation_empty_confirmation_and_integrity(tmp_path):
    with closing(repo.connect(tmp_path/'db.sqlite')) as db:
        seed(db); repo.season_create(db,'Spring 2027')
        assert not map_pool.load(db,'spring-2027')['configured']
        map_pool.save(db,'fall-2026',['nighthaven-labs','border','bank'])
        original=map_pool.load(db,'fall-2026')
        map_pool.save(db,'spring-2027',['chalet'])
        assert map_pool.load(db,'fall-2026')==original
        assert [m['slug'] for m in original['maps']]==['bank','border','nighthaven-labs']
        for invalid in (['border','border'],['ClubHouseY10'],['Clubhouse'],['arbitrary'],None,'border',[1]):
            with pytest.raises(ValueError):map_pool.save(db,'fall-2026',invalid)
            assert map_pool.load(db,'fall-2026')==original
        with pytest.raises(ValueError,match='Season not found'):map_pool.save(db,'missing',['bank'])
        with pytest.raises(ValueError,match='Confirm'):map_pool.save(db,'fall-2026',[])
        assert map_pool.load(db,'fall-2026')==original
        map_pool.save(db,'fall-2026',[],True)
        assert map_pool.load(db,'fall-2026')['configured'] and not map_pool.load(db,'fall-2026')['maps']
        with pytest.raises(sqlite3.IntegrityError):
            db.execute("INSERT INTO season_map_pool VALUES(1,'unrecognized')")
        db.rollback()
        with pytest.raises(sqlite3.IntegrityError):
            db.execute("INSERT INTO season_map_pool VALUES(999,'bank')")


def test_career_current_pool_no_active_fallback_and_no_configuration(tmp_path):
    with closing(repo.connect(tmp_path/'db.sqlite')) as db:
        seed(db);repo.season_create(db,'Spring 2027','2027-01-01')
        assert map_pool.public_pool(db,'career',None)['season'] is None
        map_pool.save(db,'fall-2026',['bank'])
        map_pool.save(db,'spring-2027',['border'])
        assert map_pool.public_pool(db,'career','fall-2026')['maps'][0]['slug']=='bank'
        assert map_pool.public_pool(db,'career',None)['maps'][0]['slug']=='border'
        assert map_pool.public_pool(db,'fall-2026',None)['maps'][0]['slug']=='bank'
        map_pool.save(db,'spring-2027',[],True)
        assert map_pool.public_pool(db,'career',None)['configured']
        assert map_pool.public_pool(db,'career',None)['maps']==[]


def test_projection_has_only_pool_cards_unplayed_entries_and_historical_details():
    raw=build_analytics('blue','fall-2026','Fall',[match()])
    pool={'season':'fall-2026','season_name':'Fall','configured':True,'maps':[{'slug':'bank','name':'Bank'}]}
    projected=project_pool(raw,pool)
    assert [m['slug'] for m in projected['maps']]==['bank']
    assert projected['maps'][0]['maps_played']==0
    assert projected['historical_maps']==[find(raw)]
    assert find(projected)==find(raw)  # Counts/sites/recent references unchanged.


def test_export_season_pools_career_history_team_isolation_and_validation(tmp_path):
    root=tmp_path/'web/public/data'
    with closing(repo.connect(tmp_path/'db.sqlite')) as db:
        seed(db);map_pool.save(db,'fall-2026',['bank','border'])
        repo.insert_map(db,replay(),'fall',0,'UCF',organization_team_id=1)
        repo.season_create(db,'Spring 2027','2027-01-01');repo.season_activate(db,'spring-2027')
        spring=replay('spring','2027-02-01T20:00:00Z');spring.map_name='Border'
        # Verify an independent second season's map.
        repo.insert_map(db,spring,'spring',0,'UCF',organization_team_id=1)
        map_pool.save(db,'spring-2027',['border','chalet'])
        export(db,settings(),root)
    read=lambda p:json.loads((root/p).read_text(encoding='utf-8'))
    fall=read('teams/blue/maps/fall-2026.json'); career=read('teams/blue/maps/career.json')
    assert [m['slug'] for m in fall['maps']]==['bank','border']
    assert [m['slug'] for m in career['maps']]==['border','chalet']
    assert find(career,'Bank')['attack']=={'rounds':2,'wins':2,'losses':0}
    assert read('teams/white/maps/career.json')['pool']==career['pool']
    assert all(m['rounds']==0 for m in read('teams/white/maps/career.json')['maps'])
    assert validate_public_data(tmp_path)>0
    corrupted=read('teams/white/maps/career.json');corrupted['pool']['maps'].pop()
    (root/'teams/white/maps/career.json').write_text(json.dumps(corrupted),encoding='utf-8')
    with pytest.raises(ValueError,match='pool differs'):validate_public_data(tmp_path)


def test_admin_api_persistence_reload_validation_and_regenerated_pool(tmp_path):
    (tmp_path/'config').mkdir();(tmp_path/'config/settings.json').write_text(json.dumps(settings()),encoding='utf-8')
    with closing(repo.connect(tmp_path/'data/r6stats.sqlite')) as db:seed(db);repo.season_create(db,'Spring 2027')
    with TestClient(create_app(tmp_path)) as client:
        headers={'X-R6-Admin-Token':client.get('/api/admin/session').json()['token']}
        path='/api/admin/seasons/fall-2026/map-pool'
        data=client.get(path).json();assert len(data['catalog'])==26 and not data['configured']
        payload={'map_slugs':['border','bank']}
        assert client.put(path,json=payload).status_code==403
        assert client.put(path,headers=headers,json=payload).status_code==200
        assert [m['slug'] for m in client.get(path).json()['maps']]==['bank','border']
        for invalid in ({'map_slugs':['nope']},{'map_slugs':['bank','bank']},{'map_slugs':[]},{'map_slugs':['bank'],'display_order':[0,0]},{'map_slugs':[1]},{'map_slugs':'bank'},{'map_slugs':None},{}):
            assert client.put(path,headers=headers,json=invalid).status_code in (400,422)
            assert [m['slug'] for m in client.get(path).json()['maps']]==['bank','border']
        assert not client.get('/api/admin/seasons/spring-2027/map-pool').json()['configured']
        assert client.put('/api/admin/seasons/nope/map-pool',headers=headers,json=payload).status_code==400
        exported=json.loads((tmp_path/'web/public/data/teams/blue/maps/fall-2026.json').read_text(encoding='utf-8'))
        assert [m['slug'] for m in exported['maps']]==['bank','border']
        assert client.put(path,headers=headers,json={'map_slugs':[],'confirm_empty':True}).status_code==200
    with TestClient(create_app(tmp_path)) as fresh:
        assert fresh.get(path).json()['configured'] and fresh.get(path).json()['maps']==[]
