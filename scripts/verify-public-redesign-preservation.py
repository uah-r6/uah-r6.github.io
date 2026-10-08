"""Read-only comparison against the ignored pre-redesign backup."""
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from r6stats import replay_archive


def verify():
    evidence = ROOT / 'data/research/public-redesign-20261008'
    before = json.loads((evidence / 'tables-before.json').read_text(encoding='utf-8'))
    with sqlite3.connect(f'file:{(ROOT / "data/r6stats.sqlite").as_posix()}?mode=ro', uri=True) as db:
        db.row_factory = sqlite3.Row
        for table, rows in before.items():
            assert [dict(r) for r in db.execute('SELECT * FROM "' + table + '"')] == rows, table
        assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        assert not list(db.execute('PRAGMA foreign_key_check'))
        archives = [replay_archive.verify(db, ROOT / 'data/replay-archive', r['id']) for r in db.execute('SELECT id FROM maps')]
        assert len(archives) == 9 and all(a['status'] == 'Healthy' for a in archives)
    protected = json.loads((evidence / 'protected-before.json').read_text(encoding='utf-8'))
    for name, sha in protected.items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == sha, name
    public = list((evidence / 'public-before').rglob('*.json'))
    assert len(public) == len(list((ROOT / 'web/public/data').rglob('*.json')))
    for path in public:
        assert path.read_bytes() == (ROOT / 'web/public/data' / path.relative_to(evidence / 'public-before')).read_bytes(), str(path)
    report = dict(status='PASS', tables=len(before), protected_files=len(protected), public_json=len(public), healthy_archives=len(archives), logo_assets_unchanged=True, integrity='ok', foreign_keys='ok', unchanged=True)
    (evidence / 'preservation.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    verify()
