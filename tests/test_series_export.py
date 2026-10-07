from copy import deepcopy
import json

import pytest

from r6stats.export import export
from r6stats.series_export import SeriesProjection, player_total
from r6stats.stats.calculate import empty, aggregate
from r6stats.stats.rating_v3 import SiegeStyleV3Rating
from r6stats.credited_refresh import store
from r6stats.rating_inputs_v3 import store_objective_evidence
from r6stats.db import repository as repo
from test_credited_production import make_db
from test_rating_v3 import evidence


def counts(rounds, kills):
    s = empty()
    s.update(rounds=rounds, kills=kills, deaths=rounds//2,
             survived=rounds-rounds//2, kost_rounds=rounds-1,
             opening_kills=2, opening_deaths=1, multikill_extra=max(kills-rounds, 0))
    s['sides']['Attack'].update(rounds=rounds, kills=kills, deaths=rounds//2)
    return aggregate([s], 'siege_style_v3')


def record(mid, rounds, kills, eligible=True):
    s = counts(rounds, kills)
    return {'map_id': mid, 'display': deepcopy(s), 'rating': s if eligible else None, 'delta': (0, 0)}


@pytest.mark.parametrize('sizes', [(12,), (12, 15), (12, 15, 9)])
def test_same_frozen_formula_on_aggregate_counts_equals_round_weighted_exact_ratings(sizes):
    records = [record(str(i), n, (i+1)*5) for i, n in enumerate(sizes)]
    result = player_total(records, 'siege_style_v3')
    weighted = sum(SiegeStyleV3Rating.calculate(r['rating'])*r['rating']['rounds'] for r in records)/sum(sizes)
    assert result['rating'] == pytest.approx(weighted, abs=1e-12)
    assert result['rating_rounds'] == result['rounds'] == sum(sizes)
    assert result['rating_maps'] == result['maps'] == len(sizes)
    if len(sizes) > 1:
        unweighted = sum(r['rating']['rating'] for r in records)/len(records)
        assert result['rating'] != pytest.approx(unweighted, abs=1e-5)
    # Cached/rounded Rating fields are never the authoritative calculation.
    for r in records:
        r['rating']['rating'] = 999
    assert player_total(records, 'siege_style_v3')['rating'] == pytest.approx(weighted, abs=1e-12)


def test_partial_coverage_preserves_every_display_count_and_manual_adjustment():
    a, b = record('rated', 12, 20), record('unrated', 15, 3, False)
    b['delta'] = (2, -1)
    before = deepcopy([a, b])
    total = player_total([a, b], 'siege_style_v3')
    assert (total['maps'], total['rounds'], total['rating_maps'], total['rating_rounds']) == (2, 27, 1, 12)
    assert total['kills'] == 25 and total['deaths'] == a['display']['deaths'] + b['display']['deaths'] - 1
    assert total['kost_rounds'] == a['display']['kost_rounds'] + b['display']['kost_rounds']
    assert total['rating'] == a['rating']['rating']
    assert [a, b] == before
    assert player_total([b], 'siege_style_v3')['rating'] is None
    assert player_total([], 'siege_style_v3')['rating'] is None


def metadata():
    return dict(id='series', series_id='series', team_slug='blue', team_name='UAH Blue', season='fall-2026',
                season_name='Fall 2026', date='2026-10-06', opponent='Opponent', week='', notes='', demo=False)


def map_public(mid):
    return {**metadata(), 'id': mid, 'map': 'Border', 'our_score': 7, 'their_score': 5, 'result': 'WIN'}


def test_internal_identity_username_changes_substitution_and_logical_rehost_map_once():
    projection = SeriesProjection('siege_style_v3')
    projection.add(metadata(), map_public('logical-rehost'), {42: record('logical-rehost', 12, 10), 43: record('logical-rehost', 6, 2)})
    projection.add(metadata(), map_public('second'), {42: record('second', 15, 12)})
    projection.add(metadata(), map_public('third'), {43: record('third', 9, 3, False)})
    identities = {42: {'slug': 'same-player', 'name': 'New username', 'status': 'Alumni'},
                  43: {'slug': 'substitute', 'name': 'Other', 'status': 'Active'}}
    doc = projection.documents(identities)[0]
    assert len(doc['maps']) == 3 and doc['recorded_maps']['wins'] == 3
    by_slug = {p['slug']: p for p in doc['players']}
    assert by_slug['same-player']['name'] == 'New username'
    assert (by_slug['same-player']['maps'], by_slug['same-player']['rounds']) == (2, 27)
    substitute = by_slug['substitute']
    assert (substitute['maps'], substitute['rounds'], substitute['rating_maps'], substitute['rating_rounds']) == (2, 15, 1, 6)
    with pytest.raises(ValueError, match='Duplicate logical'):
        projection.add(metadata(), map_public('logical-rehost'), {})
    with pytest.raises(ValueError, match='Duplicate logical'):
        player_total([record('same', 2, 1), record('same', 2, 1)], 'siege_style_v3')


@pytest.mark.parametrize('field', ['team_slug', 'team_name', 'season', 'opponent', 'week', 'notes'])
def test_inconsistent_series_metadata_fails_safely(field):
    projection = SeriesProjection('siege_style_v3')
    bad = map_public('map'); bad[field] = 'different'
    with pytest.raises(ValueError, match='metadata differs'):
        projection.add(metadata(), bad, {})
    projection.add(metadata(), map_public('first'), {})
    altered = metadata(); altered['date'] = '2026-10-07'
    with pytest.raises(ValueError, match='metadata differs'):
        projection.add(altered, map_public('second'), {})


def test_export_reuses_sealed_inputs_without_changing_sqlite_or_map_ratings(tmp_path):
    db, mid, match, records = make_db(tmp_path)
    evidence(match, records); store(db, mid, records, 'binary'); store_objective_evidence(db, mid, match)
    sid = db.execute('SELECT series_id FROM maps').fetchone()[0]
    second = deepcopy(match); second.replay_id = 'second'
    mid2 = repo.insert_map(db, second, 'second-fingerprint', 0, 'Opponent', series_id=sid, organization_team_id=1)
    store(db, mid2, deepcopy(records), 'binary'); store_objective_evidence(db, mid2, second)
    snapshot = list(db.iterdump())
    config = {'team': {}, 'stats': {'rating_version': 'siege_style_v3', 'trade_window_seconds': 8}}
    export(db, config, tmp_path/'public')
    assert list(db.iterdump()) == snapshot
    load = lambda file: json.loads((tmp_path/'public'/file).read_text(encoding='utf-8'))
    doc = load(f'series/{sid}.json')
    assert len(doc['maps']) == 2 and all(p['rating_maps'] == 2 for p in doc['players'])
    for p in doc['players']:
        a = next(s for s in load(f'matches/{mid}.json')['players'] if s['slug'] == p['slug'])
        b = next(s for s in load(f'matches/{mid2}.json')['players'] if s['slug'] == p['slug'])
        assert p['rating'] == pytest.approx((a['rating'] + b['rating'])/2, abs=1e-12)
        profile = load(f"players/{p['slug']}/career.json")
        assert profile['series_ratings'][0]['rating'] == p['rating']
        assert len(profile['matches']) == 2
    assert all('profile_id' not in p for p in doc['players'])
    db.close()
