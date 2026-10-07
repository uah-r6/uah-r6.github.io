import json
from pathlib import Path
import shutil

import pytest

from r6stats.publishing import validate_public_data

PUBLIC = Path(__file__).resolve().parents[1] / 'web/public/data'


def candidate(tmp_path):
    root = tmp_path / 'web/public/data'
    shutil.copytree(PUBLIC, root)
    return root


def edit(root, name, change):
    path = root / name
    data = json.loads(path.read_text(encoding='utf-8'))
    change(data)
    path.write_text(json.dumps(data), encoding='utf-8')


def test_all_actual_series_highlights_and_profile_references_validate(tmp_path):
    candidate(tmp_path)
    assert validate_public_data(tmp_path) == 30


@pytest.mark.parametrize('change,reason', [
    (lambda d: d.update(team_slug='white'), 'metadata'),
    (lambda d: d['maps'].append(d['maps'][0]), 'inventory'),
    (lambda d: d['recorded_maps'].update(wins=9), 'result'),
    (lambda d: d['players'][0].update(rating_rounds=999), 'coverage'),
    (lambda d: d['players'][0].update(rating=None), 'coverage'),
    (lambda d: d.update(archive_path='private'), 'private'),
])
def test_rejects_series_inconsistency_and_private_fields(tmp_path, change, reason):
    root = candidate(tmp_path)
    edit(root, 'series/40bf93b16f97.json', change)
    with pytest.raises(ValueError, match=reason):
        validate_public_data(tmp_path)


def test_rejects_frontend_series_rating_drift_and_missing_series(tmp_path):
    root = candidate(tmp_path)
    edit(root, 'players/lgon/career.json', lambda d: d['series_ratings'][0].update(rating=0))
    with pytest.raises(ValueError, match='reference differs'):
        validate_public_data(tmp_path)
    shutil.copyfile(PUBLIC / 'players/lgon/career.json', root / 'players/lgon/career.json')
    (root / 'series/40bf93b16f97.json').unlink()
    with pytest.raises(ValueError, match='reference'):
        validate_public_data(tmp_path)


@pytest.mark.parametrize('labels', [['2K'], ['Opening'], ['3K', 'Plant', 'Disable'], ['3K', '3K']])
def test_rejects_highlight_clutter_and_unsupported_labels(tmp_path, labels):
    root = candidate(tmp_path)
    group = {'player_slug': 'lgon', 'player_name': 'Lgon', 'labels': labels, 'emphasis': 'notable'}
    edit(root, 'matches/9db26f1b6ca7.json', lambda d: d['rounds'][0].update(highlights=[group]))
    with pytest.raises(ValueError, match='highlight'):
        validate_public_data(tmp_path)


def test_rejects_third_highlight_group_and_opponent_or_private_metadata(tmp_path):
    root = candidate(tmp_path)
    group = lambda slug: {'player_slug': slug, 'player_name': slug, 'labels': ['3K'], 'emphasis': 'notable'}
    for groups in ([group(s) for s in ('lgon', 'ohwowjay', 'azooznewzz')],
                   [group('opponent')], [{**group('lgon'), 'offset': 2000}]):
        edit(root, 'matches/9db26f1b6ca7.json', lambda d: d['rounds'][0].update(highlights=groups))
        with pytest.raises(ValueError, match='highlight'):
            validate_public_data(tmp_path)
