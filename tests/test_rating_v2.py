"""Frozen research formula parity and versioned public aggregation."""
from contextlib import closing
import json
from pathlib import Path
import sys

import pytest

from r6stats.db import repository as repo
from r6stats.export import export
from r6stats.manual_kd import save as save_kd
from r6stats.parser.models import Kill, Match, Player, Round
from r6stats.publishing import validate_public_data
from r6stats.stats.calculate import (RatingEngine, SiegeStyleRating, aggregate,
                                     calculate_match)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'research'))
from fit_models import predict as research_predict  # noqa: E402


def fixture(replay_id='v2-map'):
    players = [Player(f'ours-{i}', f'Player{i}', 0, 'Buck', 'Attack') for i in range(5)]
    players += [Player(f'foe-{i}', f'Enemy{i}', 1, 'Wamai', 'Defense') for i in range(5)]
    first = [Kill(0, 100, 'ours-0', 'foe-0', 0, 1),
             Kill(1, 98, 'ours-0', 'foe-1', 0, 1),
             Kill(2, 95, 'foe-2', 'ours-0', 1, 0),
             Kill(3, 94, 'ours-1', 'foe-2', 0, 1)]
    second = [Kill(0, 100, 'foe-0', 'ours-1', 1, 0),
              Kill(1, 96, 'ours-0', 'foe-0', 0, 1)]
    return Match(replay_id, '2026-09-29T20:00:00Z', 'Bank', 'Custom Game', 'Bomb',
                 [Round(1, 'Lockers', 0, 'KilledOpponents', players, first),
                  Round(2, 'Lockers', 0, 'KilledOpponents', players, second)])


def research_row(match, key):
    names = ('kills', 'teamkills', 'opening_kills', 'opening_deaths', 'clutches',
             'kost_rounds', 'survived', 'deaths_traded', 'kills_traded', 'plants', 'disables')
    rounds = []
    for one in match.rounds:
        stats = calculate_match(Match(match.replay_id, match.timestamp, match.map_name,
                                      match.match_type, match.game_mode, [one]),
                                rating_version='collegiate_v1')[key]
        rounds.append({name: stats[name] for name in names})
    return {'rounds': rounds}


def test_frozen_exact_coefficients_and_prediction_parity():
    frozen = json.loads((ROOT/'research/frozen-rating-candidate.json').read_text())['model']
    assert SiegeStyleRating.intercept == frozen['intercept']
    for name, weight, mean, scale in SiegeStyleRating.terms:
        assert (weight, mean, scale) == (frozen['weights_standardized'][name],
                                         frozen['means'][name], frozen['scales'][name])
    assert frozen['weights_standardized']['objectives'] == 0
    match = fixture()
    runtime = calculate_match(match, rating_version='siege_style_v2')['ours-0']
    expected = research_predict(frozen, research_row(match, 'ours-0'), {})
    assert runtime['rating'] == pytest.approx(expected, abs=1e-12)
    assert runtime['multikill_extra'] == 1
    assert runtime['rounds'] == 2


def test_aggregation_participation_and_frozen_trade_window():
    match = fixture()
    first = Match('one', match.timestamp, match.map_name, match.match_type,
                  match.game_mode, [match.rounds[0]])
    second = Match('two', match.timestamp, match.map_name, match.match_type,
                   match.game_mode, [match.rounds[1]])
    one = calculate_match(first, rating_version='siege_style_v2')['ours-0']
    two = calculate_match(second, rating_version='siege_style_v2')['ours-0']
    joined = aggregate([one, two], 'siege_style_v2')
    assert joined['rating'] == pytest.approx(calculate_match(match, rating_version='siege_style_v2')['ours-0']['rating'])
    assert joined['rounds'] == 2 and joined['multikill_extra'] == 1
    with pytest.raises(ValueError, match='8-second'):
        calculate_match(match, 7, 'siege_style_v2')
    # The historical formula remains callable and numerically unchanged.
    old = calculate_match(match, rating_version='collegiate_v1')['ours-0']
    assert old['rating'] == pytest.approx(RatingEngine.calculate(old))


def test_public_export_keeps_partial_map_unrated_and_private_data_out(tmp_path):
    with closing(repo.connect(tmp_path/'data/r6stats.sqlite')) as db:
        repo.season_create(db, 'Fall 2026')
        for i in range(5):
            repo.roster_add(db, f'Player{i}')
        complete = fixture('complete')
        partial = fixture('partial')
        complete_id = repo.insert_map(db, complete, 'hash-complete', 0, 'Opponent')
        partial_id = repo.insert_map(db, partial, 'hash-partial', 0, 'Opponent')
        player_id = db.execute("SELECT id FROM players WHERE username='Player0'").fetchone()[0]
        save_kd(db, partial_id, player_id, 8, 4, 'Missing physical replay rounds', '', 8)
        config = {'team': {'name': 'Test', 'short_name': 'T', 'accent': '#82e3db'},
                  'stats': {'trade_window_seconds': 8, 'rating_version': 'siege_style_v2'}}
        export(db, config, tmp_path/'web/public/data')
    def read(name):
        return json.loads((tmp_path/'web/public/data'/name).read_text())
    assert validate_public_data(tmp_path) > 0
    assert read('index.json')['rating_version'] == 'siege_style_v2'
    assert read('methodology.json')['rating_version'] == 'siege_style_v2'
    complete_player = next(p for p in read(f'matches/{complete_id}.json')['players'] if p['slug'] == 'player0')
    partial_player = next(p for p in read(f'matches/{partial_id}.json')['players'] if p['slug'] == 'player0')
    assert complete_player['rating'] == pytest.approx(calculate_match(complete, rating_version='siege_style_v2')['ours-0']['rating'])
    assert partial_player['rating'] is None
    assert (partial_player['kills'], partial_player['deaths']) == (8, 4)
    season = read('players/player0/fall-2026.json')
    career = read('players/player0/career.json')
    assert season['rating'] == career['rating'] == pytest.approx(complete_player['rating'])
    assert season['rounds'] == 4  # Partial map still contributes genuine round statistics.
    assert 'normalized_json' not in (tmp_path/'web/public/data/methodology.json').read_text()
