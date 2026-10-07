"""Compare the substitute migration against the private pre-change checkpoint."""
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from r6stats import replay_archive
from r6stats.publishing import validate_public_data


def compare(before, after, path=''):
    if isinstance(before, dict):
        for k, value in before.items():
            if path == 'index.json' and k == 'generated_at':
                continue
            assert k in after, (path, k)
            compare(value, after[k], path+'/'+k)
    elif isinstance(before, list):
        assert len(before) == len(after), (path, len(before), len(after))
        for i, (a, b) in enumerate(zip(before, after)):
            compare(a, b, path+'/'+str(i))
    else:
        assert before == after, (path, before, after)


def verify(evidence):
    original = json.loads((evidence/'tables-before.json').read_text(encoding='utf8'))
    # Read only: validation itself must never migrate or recalculate.
    db = sqlite3.connect(f'file:{ROOT / "data/r6stats.sqlite"}?mode=ro', uri=True)
    db.row_factory = sqlite3.Row
    for table, rows in original.items():
        if rows:
            after = [dict(r) for r in db.execute('SELECT '+','.join(rows[0])+' FROM '+table)]
            assert rows == after, table
        else:
            assert db.execute('SELECT count(*) FROM '+table).fetchone()[0] == 0, table
    assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
    assert db.execute('PRAGMA foreign_key_check').fetchall() == []
    assert db.execute('SELECT count(*) FROM players WHERE substitute_eligible!=0').fetchone()[0] == 0
    appearances = [dict(r) for r in db.execute('SELECT * FROM map_player_appearances')]
    assert len(appearances) == 35 and all(r['appearance_role'] == 'roster' for r in appearances)
    expected = {(r['map_id'], p['player_id']) for r in original['rounds'] for p in original['round_players']
                if p['round_id'] == r['id'] and p['player_id'] is not None}
    assert {(r['map_id'], r['player_id']) for r in appearances} == expected
    archives = {r['id']: replay_archive.verify(db, ROOT/'data/replay-archive', r['id'])['status'] for r in original['maps']}
    assert all(s == 'Healthy' for s in archives.values()), archives
    db.close()
    documents = list((evidence/'head-public-before').rglob('*.json'))
    for path in documents:
        relative = path.relative_to(evidence/'head-public-before')
        compare(json.loads(path.read_text(encoding='utf8')),
                json.loads((ROOT/'web/public/data'/relative).read_text(encoding='utf8')), str(relative))
    protected = json.loads((evidence/'protected-before.json').read_text(encoding='utf8'))
    for name, digest in protected.items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == digest, name
    report = {'status':'PASS', 'original_tables_unchanged':len(original), 'public_documents_preserved':len(documents),
              'protected_files_unchanged':len(protected), 'appearance_rows':len(appearances), 'archives':archives,
              'public_validation_count':validate_public_data(ROOT)}
    (evidence/'preservation.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--evidence',type=Path,default=ROOT/'data/research/substitutes-20261007')
    verify(ap.parse_args().evidence)
