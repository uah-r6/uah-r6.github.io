from contextlib import closing
from copy import deepcopy
from dataclasses import replace
import json

import pytest

from r6stats.db import repository as repo, teams
from r6stats.export import export
from r6stats.map_analytics import build_analytics
from r6stats.opening_engagements import round_facts, summarize, summarize_maps
from r6stats.parser.models import Kill, Match, Player, Round
from r6stats.publishing import validate_public_data
from r6stats.stats.calculate import calculate_match
from tests.test_teams import replay, seed, settings


def fixture_round(number=1, side='Attack', opener='kill', won=True):
    other = 'Defense' if side == 'Attack' else 'Attack'
    players = [Player('a', 'A', 0, side=side), Player('b', 'B', 0, side=side),
               Player('c', 'C', 1, side=other), Player('d', 'D', 1, side=other)]
    kills = [] if opener is None else [Kill(1, 100, 'a' if opener == 'kill' else 'c',
                                           'c' if opener == 'kill' else 'a',
                                           0 if opener == 'kill' else 1, 1 if opener == 'kill' else 0)]
    return Round(number, 'Site', 0 if won else 1, 'DefuserExploded', players, kills)


def fixture(rounds):
    return Match('fixture', '2026-10-01T00:00:00Z', 'Border', 'CustomGame', 'Bomb', rounds)


def test_weighted_combined_counts_conversion_recovery_and_sides():
    # Uneven samples deliberately distinguish pooled rates from mean side rates.
    rounds = [fixture_round(1, 'Attack', 'kill', True), fixture_round(2, 'Attack', 'death', False)]
    rounds += [fixture_round(i+3, 'Defense', 'kill' if i < 8 else 'death', i < 6 or i == 8) for i in range(10)]
    report = summarize(round_facts(fixture(rounds), 0).values())
    a, d, total = report['attack'], report['defense'], report['overall']
    assert (a['opening_kills'], a['eligible_rounds'], a['opening_kill_pct']) == (1, 2, .5)
    assert (d['opening_kills'], d['eligible_rounds'], d['opening_kill_pct']) == (8, 10, .8)
    assert (total['opening_kills'], total['eligible_rounds'], total['opening_kill_pct']) == (9, 12, .75)
    assert total['opening_kill_pct'] != (a['opening_kill_pct'] + d['opening_kill_pct']) / 2
    assert (total['opening_kill_wins'], total['conversion_pct']) == (7, 7/9)
    assert (total['opening_deaths'], total['opening_death_wins'], total['recovery_pct']) == (3, 1, 1/3)
    assert a['conversion_pct'] == 1 and a['recovery_pct'] == 0
    assert d['conversion_pct'] == .75 and d['recovery_pct'] == .5


@pytest.mark.parametrize(('opener','won'), [('kill', True), ('kill', False), ('death', True), ('death', False), (None, True), (None, False)])
def test_one_round_definition_and_objective_winner(opener, won):
    match = fixture([fixture_round(opener=opener, won=won)])
    before = deepcopy(match.to_dict())
    stats_before = calculate_match(match)
    result = summarize(round_facts(match, 0).values())['overall']
    assert result['eligible_rounds'] == int(opener is not None)
    assert result['opening_kills'] == int(opener == 'kill')
    assert result['opening_deaths'] == int(opener == 'death')
    assert result['opening_kill_wins'] == int(opener == 'kill' and won)
    assert result['opening_death_wins'] == int(opener == 'death' and won)
    assert match.to_dict() == before and calculate_match(match) == stats_before


def test_exact_public_entry_eligibility_order_dead_victims_and_unknown_identities():
    round_ = fixture_round()
    # The clock chronology intentionally differs from native sequence. Entry's
    # original policy remains authoritative here; Rating's native policy is untouched.
    round_.kills = [Kill(0, 80, 'c', 'a', 1, 0), Kill(9, 120, 'b', 'c', 0, 1)]
    match = fixture([round_])
    before = calculate_match(match)
    assert before['b']['opening_kills'] == 1
    assert round_facts(match, 0)[1]['opening'] == 'kill'
    round_.kills = [Kill(0, 150, 'a', 'a', 0, 0),  # suicide affects alive set
                    Kill(1, 140, 'b', 'a', 0, 0),  # already dead victim
                    Kill(2, 130, '', 'd', -1, 1),  # environmental death
                    Kill(3, 120, 'missing', 'b', 1, 0),  # invalid identity
                    Kill(4, 110, 'c', 'd', 1, 1),  # already dead, teamkill
                    Kill(5, 100, 'b', 'c', 0, 1)]
    stats = calculate_match(match)
    assert stats['b']['opening_kills'] == 1
    assert round_facts(match, 0)[1]['opening'] == 'kill'
    round_.kills = round_.kills[:5]
    assert round_facts(match, 0)[1]['opening'] is None


def test_unknown_side_stays_overall_and_no_sample_is_null():
    stats = summarize(round_facts(fixture([fixture_round(side='Unknown')]), 0).values())
    assert stats['overall']['opening_kill_pct'] == 1
    assert stats['unknown_side']['eligible_rounds'] == 1
    for scope in ('attack', 'defense'):
        assert all(stats[scope][key] is None for key in ('opening_kill_pct', 'conversion_pct', 'recovery_pct'))
    assert summarize([])['overall']['conversion_pct'] is None


def test_logical_map_dedup_round_protection_and_map_aggregate():
    def public(mid, rounds):
        return dict(id=mid, series_id='series', season='fall-2026', team_slug='blue',
                    opponent='Opponent', date='2026-10-01', map='Border',
                    our_score=1, their_score=0, result='WIN',
                    rounds=list(round_facts(fixture(rounds), 0).values()))
    a = public('one', [fixture_round()])
    b = public('two', [fixture_round(1, 'Defense', 'death'), fixture_round(2, 'Defense', 'death', False)])
    total = summarize_maps([a, b, deepcopy(a)])
    assert (total['overall']['opening_kills'], total['overall']['eligible_rounds']) == (1, 3)
    assert total['overall']['opening_kill_pct'] == 1/3
    border = next(m for m in build_analytics('blue', 'fall-2026', 'Fall', [a, b, a])['maps'] if m['slug'] == 'border')
    assert border['opening_engagements'] == total
    changed = deepcopy(a); changed['rounds'][0]['opening'] = 'death'
    with pytest.raises(ValueError, match='Conflicting duplicate'):
        summarize_maps([a, changed])
    a['rounds'] *= 2
    with pytest.raises(ValueError, match='Duplicate logical round'):
        summarize_maps([a])


def test_selected_rehost_rounds_swapped_indices_and_sides_count_once(tmp_path):
    from tests.test_confirmed_rehost import segment
    from r6stats.parser.confirmed_rehost import stitch_confirmed
    first = segment(tmp_path, 'segment1', [0, 1, 0])
    second = segment(tmp_path, 'segment2', [1, 0], swapped=True, ours_side='Defense')
    logical = stitch_confirmed([first, second],
        excluded={('segment-01', 3): 'abandoned'}, expected_final_scores=(2, 2))
    result = summarize(round_facts(logical.match, 0).values())
    assert result['overall']['eligible_rounds'] == result['overall']['opening_kills'] == 4
    assert result['overall']['opening_kill_wins'] == 2
    assert result['overall']['conversion_pct'] == .5
    assert result['attack']['eligible_rounds'] == result['defense']['eligible_rounds'] == 2
    assert calculate_match(logical.match)['ours-0']['opening_kills'] == 4


def test_equal_side_denominators_still_sum_raw_counts():
    rounds = [fixture_round(i+1, 'Attack', 'kill' if i < 4 else 'death') for i in range(10)]
    rounds += [fixture_round(i+11, 'Defense', 'kill' if i < 8 else 'death') for i in range(10)]
    report = summarize(round_facts(fixture(rounds), 0).values())
    assert report['attack']['opening_kill_pct'] == .4
    assert report['defense']['opening_kill_pct'] == .8
    assert report['overall']['opening_kills'] == 12
    assert report['overall']['eligible_rounds'] == 20
    assert report['overall']['opening_kill_pct'] == .6


def test_exports_scopes_team_season_history_and_public_validator(tmp_path):
    def match(mid, opener, timestamp):
        value = replay(mid, timestamp)
        for round_ in value.rounds:
            round_.kills = [Kill(0, 100, 'our-0' if opener == 'kill' else 'enemy-0',
                                'enemy-0' if opener == 'kill' else 'our-0',
                                0 if opener == 'kill' else 1, 1 if opener == 'kill' else 0)]
        return value
    root = tmp_path/'web/public/data'
    with closing(repo.connect(tmp_path/'fixture.sqlite')) as db:
        seed(db)
        first = repo.insert_map(db, match('a', 'kill', '2026-09-29T20:00:00Z'), 'a', 0, 'Opponent', organization_team_id=1)
        sid = db.execute('SELECT series_id FROM maps WHERE id=?', (first,)).fetchone()[0]
        repo.insert_map(db, match('b', 'death', '2026-09-29T21:00:00Z'), 'b', 0, 'Opponent', series_id=sid, organization_team_id=1)
        repo.season_create(db, 'Spring 2027', '2027-01-01', '2027-05-31')
        repo.season_activate(db, 'spring-2027')
        repo.insert_map(db, match('c', 'death', '2027-02-01T20:00:00Z'), 'c', 0, 'Other', organization_team_id=1)
        for row in db.execute('SELECT id FROM players').fetchall():
            teams.move(db, row[0], 2, '2027-03-01')
        repo.insert_map(db, match('d', 'kill', '2027-04-01T20:00:00Z'), 'd', 0, 'Other', organization_team_id=2)
        before = db.total_changes
        export(db, settings(), root)
        assert db.total_changes == before
    load = lambda name: json.loads((root/name).read_text(encoding='utf-8'))
    report = lambda name: load(name)['opening_engagements']['overall']
    assert report('teams/blue/fall-2026.json')['opening_kill_pct'] == .5
    assert report('teams/blue/spring-2027.json')['opening_kill_pct'] == 0
    assert report('teams/blue/career.json')['opening_kill_pct'] == 1/3
    assert report('teams/white/fall-2026.json')['opening_kill_pct'] is None
    assert report('teams/white/spring-2027.json')['opening_kill_pct'] == 1
    assert report(f'series/{sid}.json')['opening_kill_pct'] == .5
    assert report(f'matches/{first}.json')['opening_kill_pct'] == 1
    assert load(f'matches/{first}.json')['players'][0]['opening_kills'] == 2
    maps = load('teams/blue/maps/career.json')
    bank = next(m for m in maps['maps']+maps['historical_maps'] if m['slug'] == 'bank')
    assert bank['opening_engagements']['overall'] == report('teams/blue/career.json')
    assert validate_public_data(tmp_path) > 0
    path = root/'teams/blue/career.json'
    damaged = load('teams/blue/career.json')
    damaged['opening_engagements']['overall']['opening_kill_pct'] = .99
    path.write_text(json.dumps(damaged), encoding='utf-8')
    with pytest.raises(ValueError, match='opening engagements are inconsistent'):
        validate_public_data(tmp_path)
