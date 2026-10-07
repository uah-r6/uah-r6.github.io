"""Compare team metadata migration with a private, pre-migration SQLite backup.

Run from the repo root. The backup directory must contain before.sqlite,
before.json (HEAD/archive hashes), and before-public/. Nothing is rewritten.
"""
import argparse
import hashlib
import json
import sqlite3
import subprocess
from pathlib import Path


def verify(backup, database, public):
    seal = json.loads((backup / 'before.json').read_text(encoding='utf-8'))
    old = sqlite3.connect(backup / 'before.sqlite')
    current = sqlite3.connect(f'{database.resolve().as_uri()}?mode=ro', uri=True)
    try:
        for (table,) in old.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall():
            columns = [r[1] for r in old.execute(f'PRAGMA table_info("{table}")')]
            select = ','.join('"' + c + '"' for c in columns)
            query = f'SELECT {select} FROM "{table}" ORDER BY rowid'
            assert old.execute(query).fetchall() == current.execute(query).fetchall(), f'Historical table changed: {table}'
        assert current.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        assert current.execute('PRAGMA foreign_key_check').fetchall() == []
        assert current.execute('SELECT count(*) FROM maps WHERE team_id!=1 OR team_id IS NULL').fetchone()[0] == 0
        assert current.execute('SELECT count(*) FROM team_memberships WHERE team_id=2').fetchone()[0] == 0
        assert current.execute('SELECT count(*) FROM maps').fetchone()[0] == 7
        assert current.execute('SELECT count(*) FROM rounds').fetchone()[0] == 82
    finally:
        old.close()
        current.close()

    def preserved(a, b, location):
        if isinstance(a, dict):
            for key, value in a.items():
                assert key in b, (location, key)
                preserved(value, b[key], location + '/' + key)
        elif isinstance(a, list):
            assert len(a) == len(b), location
            for i, (x, y) in enumerate(zip(a, b)):
                preserved(x, y, location + '/' + str(i))
        else:
            assert a == b, (location, a, b)

    for path in (backup / 'before-public').rglob('*.json'):
        relative = path.relative_to(backup / 'before-public')
        preserved(json.loads(path.read_text(encoding='utf-8')),
                  json.loads((public / relative).read_text(encoding='utf-8')), str(relative))
    white = json.loads((public / 'teams/white/career.json').read_text(encoding='utf-8'))
    assert white['maps'] == white['rounds'] == 0 and white['players'] == white['roster'] == []
    blue = json.loads((public / 'teams/blue/career.json').read_text(encoding='utf-8'))
    for player in blue['players']:
        career = json.loads((public / 'players' / player['slug'] / 'career.json').read_text(encoding='utf-8'))
        for key, value in player.items():
            assert career[key] == value, ('Blue career scope differs from preserved global career', player['slug'], key)
    assert blue['maps'] == 7 and blue['rounds'] == 82 and len(blue['players']) == 5
    for name, expected in seal['archive_hashes'].items():
        assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == expected, name
    assert {p.as_posix() for p in Path('data/replay-archive').rglob('*') if p.is_file()} == set(seal['archive_hashes'])
    protected = [*Path('r6stats/parser').rglob('*.py'), *Path('r6stats/stats').rglob('*.py'),
                 *map(Path, ['r6stats/replay_archive.py', 'r6stats/credited_refresh.py',
                             'r6stats/objective_refresh.py', 'r6stats/rating_inputs_v3.py'])]
    for path in protected:
        original = subprocess.check_output(['git', 'show', seal['head'] + ':' + path.as_posix()]).decode('utf-8')
        assert path.read_text(encoding='utf-8') == original, f'Protected semantics changed: {path}'
    private_keys = {'profile_id', 'profileID', 'fingerprint', 'normalized_json', 'rehost_json',
                    'source_name', 'archive', 'archive_path', 'database_path', 'player_id'}

    def privacy(value):
        if isinstance(value, dict):
            assert not private_keys.intersection(value), private_keys.intersection(value)
            for child in value.values():
                privacy(child)
        elif isinstance(value, list):
            for child in value:
                privacy(child)
        elif isinstance(value, str):
            assert 'data/research/' not in value and 'data/replay-archive/' not in value and 'C:\\Users\\' not in value
    for path in public.rglob('*.json'):
        privacy(json.loads(path.read_text(encoding='utf-8')))
    return {'status': 'PASS', 'baseline_head': seal['head'], 'maps': 7, 'rounds': 82,
            'public_documents': len(list(public.rglob('*.json'))),
            'archives_unchanged': len(seal['archive_hashes']), 'historical_fields': 'exactly preserved'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--backup', type=Path, required=True)
    parser.add_argument('--database', type=Path, default=Path('data/r6stats.sqlite'))
    parser.add_argument('--public', type=Path, default=Path('web/public/data'))
    args = parser.parse_args()
    print(json.dumps(verify(args.backup, args.database, args.public), indent=2))
