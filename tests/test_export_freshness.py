import json
from contextlib import closing
from datetime import datetime, timezone
from r6stats.db import repository as repo
from r6stats.export import export


def test_generation_timestamp_is_utc_metadata_only_and_export_is_read_only(tmp_path):
    config = {'team': {'name': 'Test', 'short_name': 'T', 'accent': '#0058A4'},
              'stats': {'rating_version': 'collegiate_v1', 'trade_window_seconds': 8}}
    path = tmp_path / 'db.sqlite'
    with closing(repo.connect(path)) as db:
        repo.season_create(db, 'Fall 2026', '2026-08-01', '2026-12-31')
        snapshot = list(db.iterdump())
        start = datetime.now(timezone.utc)
        export(db, config, tmp_path / 'first')
        export(db, config, tmp_path / 'second')
        assert list(db.iterdump()) == snapshot
    for original in (tmp_path / 'first').rglob('*.json'):
        a = json.loads(original.read_text(encoding='utf-8'))
        b = json.loads((tmp_path / 'second' / original.relative_to(tmp_path / 'first')).read_text(encoding='utf-8'))
        if original.name == 'index.json' and original.parent.name == 'first':
            for record in (a, b):
                timestamp = datetime.fromisoformat(record.pop('generated_at'))
                assert timestamp.tzinfo == timezone.utc
                assert start <= timestamp <= datetime.now(timezone.utc)
        else:
            assert 'generated_at' not in a
        assert a == b
