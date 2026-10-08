"""Read-only independent production analytics and preservation verification."""
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from r6stats.publishing import validate_public_data
from r6stats.rating_inputs_v3 import load_inputs
from r6stats.replay_archive import verify as verify_archive

OUT = ROOT / 'data/research/match-map-analytics-20261008'
PUBLIC = ROOT / 'web/public/data'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def verify():
    preserved = []
    for path in (OUT / 'public-before').rglob('*.json'):
        relative = path.relative_to(OUT / 'public-before')
        before, after = read(path), read(PUBLIC / relative)
        if str(relative) == 'index.json':
            before.pop('generated_at'); after.pop('generated_at')
        assert before == after, relative
        preserved.append(relative.as_posix())
    before_hashes = read(OUT / 'hashes-before.json')
    # Only these two existing Python modules may change in this presentation pass.
    changed = {'r6stats/export.py', 'r6stats/publishing.py'}
    for name, digest in before_hashes.items():
        if name not in changed:
            assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    with sqlite3.connect((ROOT / 'data/r6stats.sqlite').as_uri() + '?mode=ro', uri=True) as db:
        db.row_factory = sqlite3.Row
        expected_tables = read(OUT / 'tables-before.json')
        tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
        assert tables == set(expected_tables)
        for table, expected in expected_tables.items():
            actual = [dict(r) for r in db.execute(f'SELECT * FROM "{table}" ORDER BY rowid')]
            assert actual == expected, table
        archive_status = {}
        for row in db.execute('SELECT id FROM maps'):
            archive_status[row['id']] = verify_archive(db, ROOT / 'data/replay-archive', row['id'])['status']
            inputs, reason = load_inputs(db, row['id'], 8)
            assert inputs is not None and reason is None, (row['id'], reason)
        assert len(archive_status) == 9 and set(archive_status.values()) == {'Healthy'}
    index = read(PUBLIC / 'index.json')
    maps = [read(p) for p in (PUBLIC / 'matches').glob('*.json')]
    report = []
    # Independent loop over current public round projections. No analytics helper.
    for team in index['teams']:
        for period in [s['slug'] for s in index['seasons']] + ['career']:
            records = defaultdict(list)
            for match in maps:
                if match['team_slug'] == team['slug'] and (period == 'career' or match['season'] == period):
                    records[match['map']].append(match)
            data = read(PUBLIC / 'teams' / team['slug'] / 'maps' / f'{period}.json')
            for name, matches in records.items():
                target = next(m for m in data['maps'] if m['name'] == name)
                assert target['maps_played'] == len(matches)
                assert target['map_wins'] == sum(m['result'] == 'WIN' for m in matches)
                rounds = [r for m in matches for r in m['rounds']]
                assert (target['rounds'], target['wins'], target['losses']) == (
                    len(rounds), sum(r['result'] == 'Win' for r in rounds), sum(r['result'] == 'Loss' for r in rounds))
                for side, field in [('Attack', 'attack'), ('Defense', 'defense')]:
                    selected = [r for r in rounds if r['side'] == side]
                    wins = sum(r['result'] == 'Win' for r in selected)
                    assert target[field] == dict(rounds=len(selected), wins=wins, losses=len(selected)-wins)
                    counters = Counter((r['site'], r['result']) for r in selected)
                    for site in target['sites'][side]:
                        assert site['wins'] == counters[site['site'], 'Win']
                        assert site['losses'] == counters[site['site'], 'Loss']
                    assert sum(s['rounds'] for s in target['sites'][side]) == len(selected)
                report.append(dict(team=team['slug'], period=period, map=name,
                    maps=target['maps_played'], record=[target['map_wins'], target['map_losses']],
                    rounds=target['rounds'], wins=target['wins'], losses=target['losses'],
                    attack=target['attack'], defense=target['defense'], sites=target['sites']))
    ucf = next(m for m in maps if m['id'] == '9db26f1b6ca7')
    assert ucf['opponent'] == 'UCF' and ucf['map'] == 'Nighthaven Labs'
    assert [(r['side'], r['result']) for r in ucf['rounds']] == [
        ('Defense', 'Win'), ('Defense', 'Win'), ('Defense', 'Loss'),
        ('Defense', 'Win'), ('Defense', 'Loss'), ('Defense', 'Win'),
        ('Attack', 'Win'), ('Attack', 'Win'), ('Attack', 'Win')]
    result = dict(status='PASS', documents=validate_public_data(ROOT),
        preserved_documents=len(preserved), database_tables=len(expected_tables),
        rating_eligible_maps=9, archives=archive_status, results=report)
    (OUT / 'verification.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k != 'results'}, indent=2))


if __name__ == '__main__':
    verify()
