import json
import re
from contextlib import closing
from copy import deepcopy
from pathlib import Path

import pytest

from r6stats.map_catalog import CATALOG, identity
from r6stats.map_analytics import build_analytics
from r6stats.db import repository as repo, teams
from r6stats.export import export
from r6stats.publishing import validate_public_data
from tests.test_teams import replay, seed, settings


def match(mid='logical', team='blue', season='fall-2026', name='NighthavenLabsY10'):
    return {'id': mid, 'series_id': 'series', 'season': season, 'team_slug': team,
            'opponent': 'UCF', 'date': '2026-10-06', 'map': name,
            'our_score': 7, 'their_score': 2, 'result': 'WIN',
            'rounds': [{'number': i + 1, 'side': 'Defense' if i < 6 else 'Attack',
                        'result': 'Loss' if i in (2, 4) else 'Win',
                        'site': ['Command, Servers', 'Storage, Control', 'Assembly, Tank'][i % 3]}
                       for i in range(9)]}


def find(document, name='Nighthaven Labs'):
    return next(m for m in document['maps'] + document.get('historical_maps', []) if m['name'] == name)


def test_exact_rounds_sides_sites_and_map_order():
    data = build_analytics('blue', 'fall-2026', 'Fall 2026', [match()])
    m = find(data)
    assert (m['maps_played'], m['map_wins'], m['map_losses']) == (1, 1, 0)
    assert (m['rounds'], m['wins'], m['losses']) == (9, 7, 2)
    assert m['attack'] == {'rounds': 3, 'wins': 3, 'losses': 0}
    assert m['defense'] == {'rounds': 6, 'wins': 4, 'losses': 2}
    assert [(s['site'], s['rounds'], s['wins']) for s in m['sites']['Defense']] == [
        ('Command, Servers', 2, 2), ('Assembly, Tank', 2, 1), ('Storage, Control', 2, 1)]
    assert data['maps'][0]['name'] == 'Nighthaven Labs'
    assert [x['name'] for x in data['maps'][1:]] == sorted(x['name'] for x in data['maps'][1:])


def test_logical_map_dedup_and_duplicate_round_rejection():
    m = match()
    assert find(build_analytics('blue', 'career', 'Career', [m, deepcopy(m)]))['rounds'] == 9
    changed = deepcopy(m)
    changed['rounds'][0]['result'] = 'Loss'
    with pytest.raises(ValueError, match='Conflicting duplicate logical map'):
        build_analytics('blue', 'career', 'Career', [m, changed])
    m['rounds'].append(deepcopy(m['rounds'][0]))
    with pytest.raises(ValueError, match='Duplicate logical round'):
        build_analytics('blue', 'career', 'Career', [m])


def test_unknown_site_and_side_remain_in_totals_and_raw_label_is_preserved():
    m = match()
    m['rounds'][0]['site'] = ''
    m['rounds'][1]['site'] = 'Unknown'
    m['rounds'][2]['side'] = 'Unknown'
    data = find(build_analytics('blue', 'career', 'Career', [m]))
    assert data['rounds'] == 9
    assert data['defense']['rounds'] == 5
    assert data['unknown_side'] == {'rounds': 1, 'wins': 0, 'losses': 1}
    assert sum(s['rounds'] for sites in data['sites'].values() for s in sites) == 9
    unknown = [s for s in data['sites']['Defense'] if s['unknown']]
    assert {s['site'] for s in unknown} == {'', 'Unknown'}


def test_scope_guards_career_and_empty_catalog():
    empty = build_analytics('future', 'career', 'Career', [])
    assert len(empty['maps']) == len(CATALOG) == 26
    assert all(m['rounds'] == m['maps_played'] == 0 and not m['matches'] for m in empty['maps'])
    spring = match('spring', season='spring-2027')
    spring['result'] = 'LOSS'
    spring['date'] = '2027-02-02'
    career = find(build_analytics('blue', 'career', 'Career', [match(), spring]))
    assert (career['maps_played'], career['map_wins'], career['map_losses'], career['rounds']) == (2, 1, 1, 18)
    assert [m['id'] for m in career['matches']] == ['spring', 'logical']
    with pytest.raises(ValueError, match='ownership/period'):
        build_analytics('blue', 'fall-2026', 'Fall', [spring])
    with pytest.raises(ValueError, match='ownership/period'):
        build_analytics('white', 'career', 'Career', [match()])


@pytest.mark.parametrize(('raw', 'name'), [
    ('ClubHouseY10', 'Clubhouse'), ('ClubHouse', 'Clubhouse'),
    ('KafeDostoyevskyY10', 'Kafe Dostoyevsky'), ('KafeDostoyevsky', 'Kafe Dostoyevsky'),
    ('ConsulateY7', 'Consulate'), ('BorderY10', 'Border'),
    ('NighthavenLabsY10', 'Nighthaven Labs'), ('Chalet', 'Chalet'),
    ('Fortress', 'Fortress'), ('HerefordBase', 'Hereford Base')])
def test_catalog_aliases(raw, name):
    assert identity(raw)['name'] == name
    assert identity(raw)['supported']


def test_catalog_covers_native_enum_without_claiming_current_pool():
    header = Path('third_party/siege-dissect/dissect/header.go').read_text(encoding='utf-8')
    names = re.findall(r'^\s+(\w+)\s+Map\s+=', header, re.M)
    assert names and all(identity(name)['supported'] for name in names)
    assert {identity(name)['slug'] for name in names} == {m['slug'] for m in CATALOG}
    assert len({m['slug'] for m in CATALOG}) == len(CATALOG)
    unknown = identity('Map(99999)')
    assert unknown['name'] == 'Map(99999)' and not unknown['supported']
    assert identity('Map(99999)') == unknown


def test_export_multiple_seasons_teams_aliases_future_team_and_validation(tmp_path):
    root = tmp_path / 'web/public/data'
    with closing(repo.connect(tmp_path / 'db.sqlite')) as db:
        seed(db)
        repo.insert_map(db, replay(), 'fall', 0, 'UCF', organization_team_id=1)
        repo.season_create(db, 'Spring 2027', '2027-01-01', '2027-05-31')
        repo.season_activate(db, 'spring-2027')
        repo.insert_map(db, replay('spring', '2027-02-01T20:00:00Z'), 'spring', 0, 'UCF', organization_team_id=1)
        for row in db.execute('SELECT id FROM players').fetchall():
            teams.move(db, row[0], 2, '2027-03-01')
        repo.insert_map(db, replay('white', '2027-04-01T20:00:00Z'), 'white', 0, 'UCF', organization_team_id=2)
        future = teams.save(db, name='Future', slug='future', primary_color='#111111')
        teams.save(db, name='Future renamed', slug='future-new', primary_color='#111111', team_id=future)
        export(db, settings(), root)
    load = lambda p: json.loads((root / p).read_text(encoding='utf-8'))
    assert find(load('teams/blue/maps/career.json'), 'Bank')['rounds'] == 4
    assert find(load('teams/blue/maps/fall-2026.json'), 'Bank')['rounds'] == 2
    assert find(load('teams/white/maps/career.json'), 'Bank')['rounds'] == 2
    assert all(m['rounds'] == 0 for m in load('teams/future-new/maps/career.json')['maps'])
    assert load('teams/future/maps/career.json') == load('teams/future-new/maps/career.json')
    assert validate_public_data(tmp_path) > 0
    path = root / 'teams/blue/maps/career.json'
    data = load('teams/blue/maps/career.json')
    find(data, 'Bank')['attack']['wins'] += 1
    path.write_text(json.dumps(data), encoding='utf-8')
    with pytest.raises(ValueError, match='analytics.*inconsistent'):
        validate_public_data(tmp_path)


def test_export_rehost_counts_selected_logical_rounds_once(tmp_path):
    from tests.test_confirmed_rehost import segment
    from r6stats.parser.confirmed_rehost import stitch_confirmed
    first = segment(tmp_path, 'segment1', [0, 1, 0])
    second = segment(tmp_path, 'segment2', [0, 0], ours_side='Defense')
    logical = stitch_confirmed([first, second],
        excluded={('segment-01', 3): 'abandoned'}, expected_final_scores=(3, 1))
    root = tmp_path / 'public'
    with closing(repo.connect(tmp_path / 'db.sqlite')) as db:
        seed(db)
        repo.insert_map(db, logical.match, 'logical-rehost', 0, 'Opponent', organization_team_id=1)
        export(db, settings(), root)
    data = json.loads((root / 'teams/blue/maps/career.json').read_text(encoding='utf-8'))
    border = find(data, 'Border')
    assert border['maps_played'] == 1 and len(border['matches']) == 1
    assert border['rounds'] == 4 and border['wins'] == 3 and border['losses'] == 1
    assert border['attack'] == {'rounds': 2, 'wins': 1, 'losses': 1}
    assert border['defense'] == {'rounds': 2, 'wins': 2, 'losses': 0}


def test_substitutes_do_not_change_owner_round_analytics(tmp_path):
    root = tmp_path / 'public'
    with closing(repo.connect(tmp_path / 'db.sqlite')) as db:
        seed(db)
        from r6stats.db import map_pool
        map_pool.save(db, 'fall-2026', ['bank'])
        for pid in range(1, 6):
            repo.roster_update(db, pid, substitute_eligible=True)
        repo.insert_map(db, replay(), 'sub-white', 0, 'Opponent', organization_team_id=2)
        assert all(r[0] == 'sub' for r in db.execute('SELECT appearance_role FROM map_player_appearances'))
        export(db, settings(), root)
    load = lambda p: json.loads((root / p).read_text(encoding='utf-8'))
    bank = find(load('teams/white/maps/career.json'), 'Bank')
    assert bank['maps_played'] == 1 and bank['rounds'] == bank['wins'] == 2
    assert bank['attack'] == {'rounds': 2, 'wins': 2, 'losses': 0}
    assert find(load('teams/blue/maps/career.json'), 'Bank')['maps_played'] == 0
    assert not load('teams/white/career.json')['players']
    assert len(load('teams/white/career.json')['sub_players']) == 5
