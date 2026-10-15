"""Read-only production baseline/verification for the opening + embed pass."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from r6stats.publishing import validate_public_data
from r6stats.replay_archive import verify as verify_archive
from r6stats.rating_inputs_v3 import load_inputs

OUT = ROOT / 'data/research/opening-embed-20261015'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def tables(db):
    return {r[0]: [dict(row) for row in db.execute(f'SELECT * FROM "{r[0]}" ORDER BY rowid')]
            for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}


def protected():
    paths = list((ROOT/'r6stats/parser').rglob('*.py'))
    paths += list((ROOT/'r6stats/stats').rglob('*.py'))
    paths += [ROOT/'r6stats'/name for name in ('rating_inputs_v3.py', 'credited_refresh.py', 'objective_refresh.py', 'manual_kd.py', 'series_export.py')]
    paths += list((ROOT/'data/replay-archive').rglob('*'))
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in paths if p.is_file()}


def without_new(value):
    if isinstance(value, dict):
        return {k: without_new(v) for k, v in value.items() if k not in ('opening_engagements', 'opening', 'generated_at')}
    if isinstance(value, list):
        return [without_new(v) for v in value]
    return value


def run(baseline):
    OUT.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect((ROOT/'data/r6stats.sqlite').as_uri()+'?mode=ro', uri=True) as db:
        db.row_factory = sqlite3.Row
        current = tables(db)
        if baseline:
            assert not (OUT/'tables-before.json').exists(), 'Baseline already exists; never overwrite it.'
            with sqlite3.connect(OUT/'before.sqlite') as backup:
                db.backup(backup)
            (OUT/'tables-before.json').write_text(json.dumps(current), encoding='utf-8')
            shutil.copytree(ROOT/'web/public/data', OUT/'public-before')
            (OUT/'hashes-before.json').write_text(json.dumps(protected()), encoding='utf-8')
            print('Baseline saved; production database opened read-only.')
            return
        assert current == read(OUT/'tables-before.json'), 'Production rows/schema changed.'
        assert protected() == read(OUT/'hashes-before.json'), 'Protected statistics/parser/archive changed.'
        archives = {}
        ratings = {}
        for row in db.execute('SELECT id FROM maps'):
            archives[row['id']] = verify_archive(db, ROOT/'data/replay-archive', row['id'])['status']
            inputs, reason = load_inputs(db, row['id'], 8)
            ratings[row['id']] = {'eligible': inputs is not None, 'reason': reason}
        assert set(archives.values()) == {'Healthy'}
    paths = list((OUT/'public-before').rglob('*.json'))
    for path in paths:
        relative = path.relative_to(OUT/'public-before')
        assert without_new(read(path)) == without_new(read(ROOT/'web/public/data'/relative)), relative
    report = dict(status='PASS', tables_unchanged=len(current), existing_json_preserved=len(paths),
                  archives=archives, rating_eligibility=ratings, public_documents=validate_public_data(ROOT))
    (OUT/'preservation.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', action='store_true')
    run(parser.parse_args().baseline)
