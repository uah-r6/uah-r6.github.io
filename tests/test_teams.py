import json
import sqlite3
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from r6stats.admin.server import create_app
from r6stats.db import repository as repo, teams
from r6stats.export import export
from r6stats.parser.siege_dissect import normalize
from r6stats.parser.models import Kill
from r6stats.stats.calculate import aggregate, calculate_match


def replay(identity='blue', timestamp='2026-09-29T20:00:00Z'):
    rows = []
    for number in (1, 2):
        rows.append({'matchID': identity, 'timestamp': timestamp, 'roundNumber': number,
                     'matchType': {'name': 'CustomGameOnline'}, 'map': {'name': 'Bank'},
                     'gamemode': {'name': 'Bomb'}, 'site': 'Lockers',
                     'teams': [{'won': True, 'role': 'Attack'}, {'won': False, 'role': 'Defense'}],
                     'players': [{'username': f'Our{i}', 'profileID': f'our-{i}', 'teamIndex': 0,
                                  'operator': {'name': 'Buck'}} for i in range(5)] +
                                [{'username': f'Enemy{i}', 'profileID': f'enemy-{i}', 'teamIndex': 1,
                                  'operator': {'name': 'Smoke'}} for i in range(5)], 'matchFeedback': []})
    return normalize({'rounds': rows})


def settings():
    return {'team': {'name': 'UAH R6', 'short_name': 'UAH', 'accent': '#0058A4'},
            'stats': {'rating_version': 'collegiate_v1', 'trade_window_seconds': 8},
            'replays': {'path': ''}, 'publishing': {'enabled': False, 'branch': 'main'}}


def seed(db):
    repo.season_create(db, 'Fall 2026', '2026-08-01', '2026-12-31')
    for i in range(5):
        repo.roster_add(db, f'Our{i}', team_id=1)


def test_legacy_migration_preserves_columns_is_atomic_and_idempotent(tmp_path):
    path = tmp_path / 'legacy.sqlite'
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.executescript(repo.SCHEMA)
    db.execute("INSERT INTO players(slug,display_name,username,tracked) VALUES('old','Old','Old',0)")
    db.execute("INSERT INTO seasons(slug,name,active) VALUES('fall-2026','Fall 2026',1)")
    db.execute("INSERT INTO series VALUES('legacy',1,'Opponent','2026-09-29','','','NECC',0)")
    db.execute("""INSERT INTO maps(id,series_id,fingerprint,map_name,match_type,game_mode,our_team,
        our_score,their_score,normalized_json) VALUES('old-map','legacy','old','Bank','CustomGame','Bomb',0,7,3,'{}')""")
    db.commit()
    original = tuple(db.execute('SELECT * FROM players').fetchone())
    teams.migrate(db)
    assert tuple(db.execute('SELECT id,slug,profile_id,display_name,username,tracked FROM players').fetchone()) == original
    assert db.execute('SELECT status FROM players').fetchone()[0] == 'Alumni'
    assert db.execute('SELECT team_id FROM maps WHERE id=\'old-map\'').fetchone()[0] == 1
    assert db.execute('SELECT team_id FROM series WHERE id=\'legacy\'').fetchone()[0] == 1
    assert db.execute('SELECT count(*) FROM team_memberships WHERE team_id=2').fetchone()[0] == 0
    teams.move(db, 1, 2, '2026-10-01')
    rows = [tuple(r) for r in db.execute('SELECT * FROM team_memberships')]
    teams.migrate(db)
    assert [tuple(r) for r in db.execute('SELECT * FROM team_memberships')] == rows
    assert db.execute('PRAGMA foreign_key_check').fetchall() == []
    db.close()
    broken = sqlite3.connect(tmp_path / 'broken.sqlite')
    broken.row_factory = sqlite3.Row
    broken.executescript(repo.SCHEMA)
    broken.execute('DROP TABLE players')
    with pytest.raises(sqlite3.OperationalError):
        teams.migrate(broken)
    assert broken.execute("SELECT name FROM sqlite_master WHERE name='teams'").fetchone() is None
    broken.close()


def test_move_team_career_season_and_alumni_preserve_identity_and_history(tmp_path):
    with closing(repo.connect(tmp_path / 'db.sqlite')) as db:
        seed(db)
        blue = repo.insert_map(db, replay(), 'blue', 0, 'Opponent', organization_team_id=1)
        ids = [r[0] for r in db.execute('SELECT id FROM players')]
        profile_before = [tuple(r) for r in db.execute('SELECT id,slug,profile_id FROM players')]
        for player_id in ids:
            teams.move(db, player_id, 2, '2026-10-01')
        assert repo.choose_team(db, replay(), team_id=1)[0] == 0
        with pytest.raises(ValueError, match='No configured'):
            repo.choose_team(db, replay(), team_id=2)
        white = repo.insert_map(db, replay('white', '2026-10-02T20:00:00Z'), 'white', 0,
                                'Opponent', organization_team_id=2)
        assert [tuple(r) for r in db.execute('SELECT id,slug,profile_id FROM players')] == profile_before
        export(db, settings(), tmp_path / 'public')
        load = lambda path: json.loads((tmp_path / 'public' / path).read_text(encoding='utf-8'))
        a, b = load('teams/blue/career.json'), load('teams/white/career.json')
        assert a['maps'] == b['maps'] == 1
        assert a['rounds'] == b['rounds'] == 2
        before = load('players/our0/career.json')
        assert before['maps'] == 2 and before['rounds'] == 4
        assert sum(t['rounds'] for t in before['team_splits']) == before['rounds']
        repo.roster_update(db, ids[0], status='Alumni')
        export(db, settings(), tmp_path / 'public')
        after = load('players/our0/career.json')
        for key in ('kills', 'deaths', 'kost', 'rating', 'rounds', 'maps', 'operators', 'matches'):
            assert after[key] == before[key]
        assert after['status'] == 'Alumni'
        assert 'our0' not in {p['slug'] for p in load('teams/white/index.json')['roster']}
        assert next(p for p in load('teams/white/career.json')['players'] if p['slug'] == 'our0')['status'] == 'Alumni'
        with pytest.raises(sqlite3.IntegrityError, match='immutable|same team'):
            db.execute('UPDATE maps SET team_id=2 WHERE id=?', (blue,))
        destination = db.execute('SELECT series_id FROM maps WHERE id=?', (white,)).fetchone()[0]
        with pytest.raises(ValueError, match='same team'):
            repo.match_update(db, blue, played_on='2026-09-29', series_id=destination)
        repo.reparse_map(db, blue, replay(), 'blue')
        assert db.execute('SELECT team_id FROM maps WHERE id=?', (blue,)).fetchone()[0] == 1


def test_two_first_connections_can_migrate_the_same_legacy_database(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    path=tmp_path/'concurrent.sqlite'
    with sqlite3.connect(path) as db:
        db.executescript(repo.SCHEMA)
    barrier=Barrier(2)
    class RacingConnection(sqlite3.Connection):
        first=True
        def execute(self, sql, *args):
            cursor=super().execute(sql,*args)
            if "name='team_schema_version'" in sql and self.first:
                self.first=False
                barrier.wait(timeout=5)
            return cursor
    def migrate():
        with closing(sqlite3.connect(path,factory=RacingConnection)) as db:
            db.row_factory=sqlite3.Row
            teams.migrate(db)
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures=[executor.submit(migrate) for _ in range(2)]
        for future in futures:
            future.result(timeout=10)
    with closing(repo.connect(path)) as db:
        assert db.execute('SELECT count(*) FROM teams').fetchone()[0]==2
        assert db.execute('SELECT version FROM team_schema_version').fetchone()[0]==1


def test_team_slug_aliases_arbitrary_colors_and_overlapping_membership(tmp_path):
    with closing(repo.connect(tmp_path / 'db.sqlite')) as db:
        seed(db)
        new_id = teams.save(db, name='UAH Gray', slug='gray', primary_color='#252525')
        teams.save(db, name='UAH Gray Team', slug='gray-team', primary_color='#252525', team_id=new_id)
        with pytest.raises(ValueError, match='reserved'):
            teams.save(db, name='Other', slug='gray', primary_color='#ffffff')
        with pytest.raises(sqlite3.IntegrityError, match='overlap'):
            db.execute('INSERT INTO team_memberships(player_id,team_id,start_date) VALUES(1,2,?)', ('2026-10-01',))
        with pytest.raises(ValueError, match='hex'):
            teams.save(db, name='Invalid', slug='invalid', primary_color='blue')
        export(db, settings(), tmp_path / 'public')
        index = json.loads((tmp_path / 'public/index.json').read_text(encoding='utf-8'))
        gray = next(t for t in index['teams'] if t['id'] == new_id)
        assert gray['aliases'] == ['gray'] and gray['maps'] == 0 and gray['roster_count'] == 0
        assert (tmp_path/'public/teams/gray/career.json').read_bytes() == (tmp_path/'public/teams/gray-team/career.json').read_bytes()
        assert db.execute('PRAGMA foreign_key_check').fetchall() == []


def test_admin_requires_team_and_rejects_stale_preview_context_without_import(tmp_path):
    (tmp_path / 'config').mkdir()
    (tmp_path / 'config/settings.json').write_text(json.dumps(settings()), encoding='utf-8')
    with closing(repo.connect(tmp_path / 'data/r6stats.sqlite')) as db:
        seed(db)
        repo.season_create(db, 'Spring 2027')
    source = tmp_path / 'replay'
    source.mkdir()
    (source / 'Match-test-R01.rec').write_bytes(b'first')
    (source / 'Match-test-R02.rec').write_bytes(b'second')
    with TestClient(create_app(tmp_path)) as client, patch('r6stats.admin.server.parse_match', return_value=replay()):
        headers = {'X-R6-Admin-Token': client.get('/api/admin/session').json()['token']}
        assert client.post('/api/admin/replays/preview', headers=headers, json={'path': str(source)}).status_code == 400
        response = client.post('/api/admin/replays/preview', headers=headers,
                               json={'path': str(source), 'team_id': 1, 'season_slug': 'fall-2026'})
        assert response.status_code == 200, response.text
        preview = response.json()
        assert preview['organization_team'] == 'UAH Blue'
        payload = {'preview_token': preview['preview_token'], 'team_id': 2, 'season_slug': 'fall-2026',
                   'opponent': 'Opponent', 'confirm_necc': True}
        assert 'changed since preview' in client.post('/api/admin/replays/import', headers=headers, json=payload).json()['detail']
        payload.update(team_id=1, season_slug='spring-2027')
        assert client.post('/api/admin/replays/import', headers=headers, json=payload).status_code == 400
        response = client.post('/api/admin/replays/rehost/preview', headers=headers,
                               json={'team_id': 1, 'season_slug': 'fall-2026', 'segments': [
                                   {'path': str(source), 'team_id': 2}, {'path': str(source)}]})
        assert response.status_code == 400 and 'share' in response.json()['detail']
        assert client.get('/api/admin/dashboard?team_id=2&season=fall-2026').json()['maps_imported'] == 0
    with closing(repo.connect(tmp_path / 'data/r6stats.sqlite')) as db:
        assert db.execute('SELECT count(*) FROM maps').fetchone()[0] == 0
        assert db.execute('SELECT count(*) FROM teams').fetchone()[0] == 2
    assert not list((tmp_path / 'data').rglob('manifest.json'))


def test_publishing_validation_rejects_cross_team_generated_data(tmp_path):
    from r6stats.publishing import validate_public_data
    with closing(repo.connect(tmp_path/'db.sqlite')) as db:
        seed(db)
        repo.insert_map(db, replay(), 'blue', 0, 'Opponent', organization_team_id=1)
        export(db, settings(), tmp_path/'web/public/data')
    assert validate_public_data(tmp_path) == 26  # Series plus four team/period analytics documents.
    target=tmp_path/'web/public/data/teams/blue/career.json'
    data=json.loads(target.read_text(encoding='utf-8'))
    data['matches'][0]['team_slug']='white'
    target.write_text(json.dumps(data),encoding='utf-8')
    with pytest.raises(ValueError,match='ownership differs'):
        validate_public_data(tmp_path)




def test_v3_team_and_global_careers_use_eligible_inputs_across_seasons(tmp_path):
    with closing(repo.connect(tmp_path / 'db.sqlite')) as db:
        seed(db)
        first = replay('fall')
        player, victim = first.rounds[0].players[0].key, first.rounds[0].players[5].key
        first.rounds[0].kills = [Kill(0, 90, player, victim, 0, 1)]
        a = repo.insert_map(db, first, 'a', 0, 'Opponent', organization_team_id=1)
        repo.season_create(db, 'Spring 2027', '2027-01-01', '2027-05-31')
        repo.season_activate(db, 'spring-2027')
        second = replay('spring-blue', '2027-02-01T20:00:00Z')
        from copy import deepcopy
        second.rounds.append(deepcopy(second.rounds[-1]))
        second.rounds[-1].number = 3
        for round_ in second.rounds:
            round_.kills = [Kill(0, 90, player, victim, 0, 1)]
        b = repo.insert_map(db, second, 'b', 0, 'Opponent', organization_team_id=1)
        for row in db.execute('SELECT id FROM players').fetchall():
            teams.move(db, row[0], 2, '2027-03-01')
        third = replay('spring-white', '2027-04-01T20:00:00Z')
        c = repo.insert_map(db, third, 'c', 0, 'Opponent', organization_team_id=2)
        excluded = repo.insert_map(db, replay('unsupported', '2027-04-02T20:00:00Z'), 'd',
                                   0, 'Opponent', organization_team_id=2)
        inputs = {a: calculate_match(first), b: calculate_match(second), c: calculate_match(third)}
        def load(_db, map_id, _window):
            return (None, 'fixture unsupported map') if map_id == excluded else (inputs[map_id], None)
        config = settings()
        config['stats']['rating_version'] = 'siege_style_v3'
        with patch('r6stats.export.load_v3', side_effect=load):
            export(db, config, tmp_path / 'public')
        load_json = lambda path: json.loads((tmp_path / 'public' / path).read_text(encoding='utf-8'))
        global_career = load_json('players/our0/career.json')
        blue = next(p for p in load_json('teams/blue/career.json')['players'] if p['slug'] == 'our0')
        white = next(p for p in load_json('teams/white/career.json')['players'] if p['slug'] == 'our0')
        expected = aggregate([inputs[k][player] for k in (a, b, c)], 'siege_style_v3')
        assert global_career['rating'] == expected['rating']
        assert global_career['rounds'] == 9 and global_career['rating_rounds'] == 7
        assert blue['rating'] == aggregate([inputs[a][player], inputs[b][player]], 'siege_style_v3')['rating']
        assert blue['rounds'] == blue['rating_rounds'] == 5
        assert white['rounds'] == 4 and white['rating_rounds'] == 2 and white['rating_maps'] == 1
        assert global_career['rating'] != pytest.approx(sum(
            aggregate([inputs[k][player]], 'siege_style_v3')['rating'] for k in (a, b, c)) / 3)
        spring = load_json('players/our0/spring-2027.json')
        assert len(spring['team_splits']) == 2
        teams.save(db, team_id=1, name='UAH Blue', slug='blue', primary_color='#0058A4', active=False)
        with patch('r6stats.export.load_v3', side_effect=load):
            export(db, config, tmp_path / 'public')
        assert load_json('players/our0/career.json')['rating'] == global_career['rating']
        assert load_json('teams/blue/career.json')['maps'] == 2
