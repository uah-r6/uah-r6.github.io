"""The old prospective APAC seal intentionally normalizes quality newlines."""
import importlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'research'))
probe = importlib.import_module('v3_consumed_apac_credit_probe')


@pytest.fixture
def original_apac_seal(tmp_path, monkeypatch):
    directory = tmp_path / '1'
    directory.mkdir()
    freeze = tmp_path / 'freeze.json'
    freeze.write_text('{}')
    monkeypatch.setattr(probe, 'DATA', tmp_path)
    monkeypatch.setattr(probe, 'FREEZE', freeze)
    monkeypatch.setattr(probe, 'verify', lambda: ({}, {'matches': [
        {'official_match_id': 1, 'selected': True}]}))
    monkeypatch.setattr(probe, 'quality_path', lambda folder: folder / 'quality.json')
    prediction = directory / 'replay-predictions.json'
    api = directory / 'siegegg-api-sealed.json'
    stats = directory / 'siegegg-player-stats-sealed.json'
    for file in [prediction, api, stats]:
        file.write_bytes(b'{}\n')
    quality = directory / 'quality.json'
    text = json.dumps(dict(prediction_sha256=probe.sha(prediction), api_sha256=probe.sha(api),
                           target_stats_sha256=probe.sha(stats)), indent=2) + '\n'
    quality.write_bytes(text.replace('\n', '\r\n').encode())
    (tmp_path / 'prelabel-quality-seal.json').write_text(json.dumps(dict(
        freeze_sha256=probe.source_sha(freeze), matches=[dict(official_match_id=1,
        prediction_sha256=probe.sha(prediction), quality_sha256=probe.source_sha(quality),
        target_stats_sha256=probe.sha(stats))])))
    return quality


def test_original_lf_quality_seal_accepts_identical_windows_crlf_json(original_apac_seal):
    quality = original_apac_seal
    assert probe.sha(quality) != probe.source_sha(quality)
    _, cached = probe.sealed_apac_cache()
    assert set(cached) == {1}


def test_newline_normalization_does_not_accept_changed_quality(original_apac_seal):
    quality = original_apac_seal
    changed = json.loads(quality.read_text())
    changed['decisions'] = 'altered'
    quality.write_text(json.dumps(changed, indent=2))
    with pytest.raises(ValueError, match='Original APAC sealed input changed'):
        probe.sealed_apac_cache()
