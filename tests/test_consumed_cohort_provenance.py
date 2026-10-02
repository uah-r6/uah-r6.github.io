"""Supplemental audits must reject mutated frozen inputs without regrading."""
import importlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'research'))
audit = importlib.import_module('v3_consumed_cohort_integrity')


@pytest.fixture
def sealed_cache(tmp_path, monkeypatch):
    data = tmp_path / 'cohort'
    directory = data / '1'
    directory.mkdir(parents=True)
    freeze = tmp_path / 'freeze.json'
    freeze.write_text('{}')
    final = tmp_path / 'permanent.json'
    final.write_text('{"pass": false}')
    monkeypatch.setattr(audit, 'ROOT', tmp_path)
    monkeypatch.setattr(audit, 'DATA', data)
    monkeypatch.setattr(audit, 'FREEZE', freeze)
    monkeypatch.setattr(audit, 'PERMANENT_RESULTS', {'permanent.json': audit.sha(final)})
    monkeypatch.setattr(audit, 'verify', lambda: ({}, {'matches': [
        {'official_match_id': 1, 'selected': True}]}))
    monkeypatch.setattr(audit, 'snapshot', lambda: {'database': 'unchanged'})
    monkeypatch.setattr(audit, 'quality_path', lambda folder: folder / 'quality.json')
    prediction = directory / 'replay-predictions.json'
    prediction.write_text(json.dumps({'freeze_sha256': audit.source_sha(freeze)}))
    api, stats = directory / 'siegegg-api-sealed.json', directory / 'siegegg-player-stats-sealed.json'
    api.write_text('{}')
    stats.write_text('{}')
    quality = directory / 'quality.json'
    quality.write_text(json.dumps(dict(prediction_sha256=audit.sha(prediction),
                                      api_sha256=audit.sha(api), target_stats_sha256=audit.sha(stats))))
    seal = dict(freeze_sha256=audit.source_sha(freeze), protected_hashes={'database': 'unchanged'},
                matches=[dict(official_match_id=1, hashes=dict(predictions=audit.sha(prediction),
                              quality=audit.sha(quality), api=audit.sha(api), stats=audit.sha(stats)))])
    (data / 'prelabel-quality-seal.json').write_text(json.dumps(seal))
    return directory, final


def test_sealed_cache_can_be_read_without_regrading(sealed_cache):
    _, cached, _ = audit.sealed_sal_cache()
    assert set(cached) == {1}


@pytest.mark.parametrize('name', ['replay-predictions.json', 'quality.json',
                                  'siegegg-api-sealed.json', 'siegegg-player-stats-sealed.json'])
def test_any_mutated_sealed_input_is_rejected(sealed_cache, name):
    directory, final = sealed_cache
    permanent = final.read_bytes()
    (directory / name).write_text('changed')
    with pytest.raises(ValueError, match='Sealed cohort file changed'):
        audit.sealed_sal_cache()
    assert final.read_bytes() == permanent


def test_consumed_result_cannot_be_replaced(sealed_cache):
    _, final = sealed_cache
    final.write_text('{"pass": true}')
    with pytest.raises(ValueError, match='Permanent consumed result changed'):
        audit.sealed_sal_cache()


def test_live_snapshot_must_match_prospective_seal(sealed_cache, monkeypatch):
    monkeypatch.setattr(audit, 'snapshot', lambda: {'database': 'altered'})
    with pytest.raises(ValueError, match='Protected live files differ'):
        audit.sealed_sal_cache()
