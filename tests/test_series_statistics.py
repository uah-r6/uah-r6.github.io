"""No-count policy excludes aggregates, preserves history, and is reversible."""
from contextlib import closing
from copy import deepcopy
import json
import sqlite3
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from r6stats.admin.server import create_app
from r6stats.db import repository as repo, teams
from r6stats.export import export
from r6stats.publishing import validate_public_data
from r6stats.credited_refresh import store
from r6stats.rating_inputs_v3 import store_objective_evidence, load_inputs
from r6stats.stats.calculate import COUNTS
from test_credited_production import make_db
from test_rating_v3 import evidence

CONFIG = {'team': {}, 'stats': {'rating_version': 'siege_style_v3', 'trade_window_seconds': 8}}


def setup_maps(tmp_path, *, sub=False):
    db, first, match, records = make_db(tmp_path)
    if sub:
        # Historical roles are assigned at import. One Blue player substitutes
        # for White; other players establish White's normal side.
        repo.roster_update(db, 1, substitute_eligible=True)
        for pid in range(2, 6):
            teams.move(db, pid, 2, '2026-01-01')
        repo.match_delete(db, first)
        first = repo.insert_map(db, match, 'first-white', 0, 'Placements', organization_team_id=2)
    evidence(match, records)
    store(db, first, records, 'binary')
    store_objective_evidence(db, first, match)
    sid = db.execute('SELECT series_id FROM maps WHERE id=?', (first,)).fetchone()[0]
    with db:
        db.execute('UPDATE series SET opponent=? WHERE id=?', ('Placements', sid))
    team = 2 if sub else 1
    second_match = deepcopy(match)
    second_match.replay_id = 'placements-second'
    second = repo.insert_map(db, second_match, 'second', 0, 'Placements', series_id=sid, organization_team_id=team)
    store(db, second, deepcopy(records), 'binary')
    store_objective_evidence(db, second, second_match)
    regular_match = deepcopy(match)
    regular_match.replay_id = 'regular-series'
    regular = repo.insert_map(db, regular_match, 'regular', 0, 'League opponent', organization_team_id=team)
    store(db, regular, deepcopy(records), 'binary')
    store_objective_evidence(db, regular, regular_match)
    db.commit()
    return db, sid, [first, second], regular


def read(root, path):
    return json.loads((root/'web/public/data'/path).read_text(encoding='utf-8'))


def documents(root):
    return {str(p.relative_to(root/'web/public/data')): json.loads(p.read_text(encoding='utf-8'))
            for p in (root/'web/public/data').rglob('*.json') if p.name != 'index.json'}


@pytest.mark.parametrize('sub', [False, True])
def test_exclusion_all_aggregate_scopes_history_and_exact_restore(tmp_path, sub):
    with closing(setup_maps(tmp_path, sub=sub)[0]) as db:
        rows = db.execute('SELECT id,series_id FROM maps ORDER BY rowid').fetchall()
        sid, mids, regular = rows[0]['series_id'], [r['id'] for r in rows[:2]], rows[2]['id']
        out = tmp_path/'web/public/data'
        export(db, CONFIG, out)
        assert validate_public_data(tmp_path)
        baseline = documents(tmp_path)
        tables = {r[0]: [tuple(x) for x in db.execute('SELECT * FROM '+r[0])]
                  for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name!='series'").fetchall()}
        sealed = {mid: load_inputs(db, mid) for mid in mids+[regular]}
        repo.series_statistics_set(db, sid, True)
        export(db, CONFIG, out)
        assert validate_public_data(tmp_path)
        slug = 'white' if sub else 'blue'
        for period in ('fall-2026', 'career'):
            for path in (f'seasons/{period}.json', f'teams/{slug}/{period}.json'):
                doc = read(tmp_path, path)
                assert (doc['maps'], doc['excluded_maps'], len(doc['matches'])) == (1, 2, 3)
                assert doc['rounds'] == 2
                assert sum(m['exclude_from_stats'] for m in doc['matches']) == 2
            team = read(tmp_path, f'teams/{slug}/{period}.json')
            assert all(p['maps'] == 1 and p['rounds'] == 2 for p in team['players']+team['sub_players'])
            assert team['opening_engagements'] == read(tmp_path, f'matches/{regular}.json')['opening_engagements']
            analytics = read(tmp_path, f'teams/{slug}/maps/{period}.json')
            assert sum(m['maps_played'] for m in analytics['maps']+analytics['historical_maps']) == 1
            for player in read(tmp_path, f'matches/{regular}.json')['players']:
                suffix = f"subs/{slug}/{period}.json" if player['appearance_role'] == 'sub' else f'{period}.json'
                profile = read(tmp_path, f"players/{player['slug']}/{suffix}")
                assert profile['maps'] == 1 and len(profile['matches']) == 3
                assert profile['rating_maps'] == 1 and profile['rating_rounds'] == 2
                for field in (*COUNTS, 'operators', 'sides', 'rating'):
                    assert profile[field] == player[field], field
        for mid in mids:
            name = str(Path(f'matches/{mid}.json'))
            original = baseline[name]
            current = read(tmp_path, f'matches/{mid}.json')
            assert current == {**original, 'exclude_from_stats': True}
        series = read(tmp_path, f'series/{sid}.json')
        assert series['exclude_from_stats'] and len(series['maps']) == 2
        assert all(p['maps'] == 2 and p['rating_maps'] == 2 for p in series['players'])
        for table, before in tables.items():
            assert [tuple(r) for r in db.execute('SELECT * FROM '+table)] == before, table
        assert {mid: load_inputs(db, mid) for mid in mids+[regular]} == sealed
        repo.series_statistics_set(db, sid, False)
        export(db, CONFIG, out)
        assert documents(tmp_path) == baseline
        assert validate_public_data(tmp_path)


def test_all_excluded_has_zero_statistics_without_losing_participants(tmp_path):
    with closing(setup_maps(tmp_path)[0]) as db:
        for row in db.execute('SELECT id FROM series').fetchall():
            repo.series_statistics_set(db, row['id'], True)
        export(db, CONFIG, tmp_path/'web/public/data')
        assert validate_public_data(tmp_path)
        team = read(tmp_path, 'teams/blue/career.json')
        assert team['maps'] == team['rounds'] == team['wins'] == 0
        assert team['players'] == [] and len(team['matches']) == 3
        for p in read(tmp_path, 'index.json')['players']:
            profile = read(tmp_path, f"players/{p['slug']}/career.json")
            assert profile['maps'] == profile['rounds'] == 0 and profile['rating'] is None
            assert len(profile['matches']) == 3 and len(profile['series_ratings']) == 2
            assert all(s['exclude_from_stats'] for s in profile['series_ratings'])


def test_migration_defaults_include_existing_series_and_preserves_explicit_setting(tmp_path):
    path = tmp_path/'legacy.sqlite'
    with sqlite3.connect(path) as db:
        db.executescript(repo.SCHEMA)
        db.execute("INSERT INTO seasons(slug,name,active) VALUES('fall-2026','Fall 2026',1)")
        db.execute("INSERT INTO series VALUES('old',1,'Placements','2026-09-23','','','NECC',0)")
    with closing(repo.connect(path)) as db:
        assert db.execute('SELECT exclude_from_stats FROM series').fetchone()[0] == 0
        repo.series_statistics_set(db, 'old', True)
    with closing(repo.connect(path)) as db:
        assert db.execute('SELECT exclude_from_stats FROM series').fetchone()[0] == 1
        assert db.execute('PRAGMA foreign_key_check').fetchall() == []


def test_simultaneous_first_admin_connections_migrate_counting_policy_once(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    path = tmp_path/'concurrent.sqlite'
    with sqlite3.connect(path) as db:
        db.executescript(repo.SCHEMA)
    def open_database(_):
        with closing(repo.connect(path)) as db:
            return [r['name'] for r in db.execute('PRAGMA table_info(series)')].count('exclude_from_stats')
    with ThreadPoolExecutor(max_workers=4) as pool:
        assert list(pool.map(open_database, range(4))) == [1, 1, 1, 1]


def test_later_maps_inherit_series_policy_and_moving_to_new_series_restores_counting(tmp_path):
    db, sid, mids, regular = setup_maps(tmp_path)
    with closing(db):
        from r6stats.parser.models import Match
        match = Match.from_dict(json.loads(db.execute('SELECT normalized_json FROM maps WHERE id=?', (regular,)).fetchone()[0]))
        records = json.loads(db.execute('SELECT evidence_json FROM map_kill_credit WHERE map_id=?', (regular,)).fetchone()[0])
        repo.series_statistics_set(db, sid, True)
        match.replay_id = 'late-map'
        late = repo.insert_map(db, match, 'late-fingerprint', 0, 'Placements', series_id=sid, organization_team_id=1)
        store(db, late, records, 'binary')
        store_objective_evidence(db, late, match)
        export(db, CONFIG, tmp_path/'web/public/data')
        assert read(tmp_path, f'matches/{late}.json')['exclude_from_stats'] is True
        assert read(tmp_path, 'teams/blue/career.json')['maps'] == 1
        repo.match_update(db, late, played_on='2026-10-06', make_new_series=True)
        export(db, CONFIG, tmp_path/'web/public/data')
        assert read(tmp_path, f'matches/{late}.json')['exclude_from_stats'] is False
        assert read(tmp_path, 'teams/blue/career.json')['maps'] == 2
        assert validate_public_data(tmp_path)


def test_admin_checkbox_saves_only_policy_regenerates_and_metadata_edits_preserve_it(tmp_path):
    db, sid, mids, regular = setup_maps(tmp_path)
    (tmp_path/'data').mkdir()
    with sqlite3.connect(tmp_path/'data/r6stats.sqlite') as target:
        db.backup(target)
    db.close()
    (tmp_path/'config').mkdir()
    (tmp_path/'config/settings.json').write_text(json.dumps(CONFIG), encoding='utf-8')
    with TestClient(create_app(tmp_path)) as client:
        headers = {'X-R6-Admin-Token': client.get('/api/admin/session').json()['token']}
        url = f'/api/admin/series/{sid}/statistics'
        assert client.patch(url, json={'exclude_from_stats': True}).status_code == 403
        for invalid in ('true', 1, None):
            assert client.patch(url, json={'exclude_from_stats': invalid}, headers=headers).status_code == 422
        assert client.patch('/api/admin/series/missing/statistics', json={'exclude_from_stats': True}, headers=headers).status_code == 400
        result = client.patch(url, json={'exclude_from_stats': True}, headers=headers)
        assert result.status_code == 200, result.text
        assert result.json()['exclude_from_stats'] is True
        assert next(s for s in client.get('/api/admin/series').json() if s['id'] == sid)['exclude_from_stats'] is True
        assert client.patch(f'/api/admin/series/{sid}',json={'opponent':'Renamed'},headers=headers).status_code == 200
        assert read(tmp_path, f'series/{sid}.json')['exclude_from_stats'] is True
        assert read(tmp_path, 'teams/blue/career.json')['maps'] == 1
        assert client.post('/api/admin/recalculate', json={}, headers=headers).status_code == 200
        assert read(tmp_path, 'teams/blue/career.json')['maps'] == 1
        assert client.patch(url, json={'exclude_from_stats': False}, headers=headers).status_code == 200
        assert read(tmp_path, 'teams/blue/career.json')['maps'] == 3
        assert validate_public_data(tmp_path)


@pytest.mark.parametrize('mutation', ['label', 'count', 'history_label', 'profile_total'])
def test_publishing_rejects_stale_exclusion_projections(tmp_path, mutation):
    db, sid, mids, regular = setup_maps(tmp_path)
    with closing(db):
        repo.series_statistics_set(db, sid, True)
        export(db, CONFIG, tmp_path/'web/public/data')
    path = tmp_path/'web/public/data/teams/blue/career.json'
    doc = json.loads(path.read_text(encoding='utf-8'))
    if mutation == 'label':
        path = tmp_path/f'web/public/data/matches/{mids[0]}.json'
        doc = json.loads(path.read_text(encoding='utf-8')); doc['exclude_from_stats'] = 'true'
    elif mutation == 'count': doc['maps'] += 2
    elif mutation == 'history_label': doc['matches'][0]['exclude_from_stats'] = not doc['matches'][0]['exclude_from_stats']
    else: doc['players'][0]['kills'] += 1
    path.write_text(json.dumps(doc), encoding='utf-8')
    with pytest.raises(ValueError):
        validate_public_data(tmp_path)
