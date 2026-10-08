"""Compare the correction to the ignored production baseline, with SQLite read-only."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from r6stats import replay_archive
from r6stats.publishing import validate_public_data


def verify():
    evidence = ROOT / 'data/research/series-completeness-20261008'
    tables = json.loads((evidence / 'tables-before.json').read_text())
    with sqlite3.connect(f'file:{(ROOT / "data/r6stats.sqlite").as_posix()}?mode=ro', uri=True) as db:
        db.row_factory = sqlite3.Row
        for table, rows in tables.items():
            assert [dict(r) for r in db.execute('SELECT * FROM "' + table + '"')] == rows, table
        assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        assert not list(db.execute('PRAGMA foreign_key_check'))
        archives = [replay_archive.verify(db, ROOT / 'data/replay-archive', r['id']) for r in db.execute('SELECT id FROM maps')]
        assert len(archives) == 9 and all(a['status'] == 'Healthy' for a in archives)
    protected = json.loads((evidence / 'protected-before.json').read_text())
    for name, sha in protected.items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == sha, name

    changed_ratings = []
    def abstain(track, label):
        if (track['maps'] == 0 or track['rounds'] == 0 or
                track['rating_maps'] != track['maps'] or track['rating_rounds'] != track['rounds']):
            if track['rating'] is not None:
                changed_ratings.append(label)
            track['rating'] = None

    before_root = evidence / 'public-before'
    paths = list(before_root.rglob('*.json'))
    assert len(paths) == len(list((ROOT / 'web/public/data').rglob('*.json'))) == 49
    for path in paths:
        name = path.relative_to(before_root).as_posix()
        before = json.loads(path.read_text(encoding='utf-8'))
        after = json.loads((ROOT / 'web/public/data' / name).read_text(encoding='utf-8'))
        expected = deepcopy(before)
        if name.startswith('series/'):
            for p in expected['players']:
                abstain(p, name + '/' + p['slug'])
                if 'roster_stats' in p:
                    abstain(p['roster_stats'], name + '/' + p['slug'] + '/roster_stats')
            # Sorting follows the changed Rating. Compare identities/counts exactly.
            expected['players'].sort(key=lambda p: p['slug'])
            ratings = [p['rating'] for p in after['players']]
            assert ratings == sorted(ratings, key=lambda r: r if r is not None else -float('inf'), reverse=True)
            after['players'].sort(key=lambda p: p['slug'])
        elif name.startswith('players/'):
            for s in expected.get('series_ratings', []):
                abstain(s, name + '/' + s['id'])
        if 'generated_at' in expected:
            expected['generated_at'] = after['generated_at']  # Export freshness only.
        assert after == expected, name
        if name.startswith('matches/'):
            assert path.read_bytes() == (ROOT / 'web/public/data' / name).read_bytes(), name
    assert len(changed_ratings) == 30
    assert validate_public_data(ROOT) == 49
    report = dict(status='PASS', tables=len(tables), protected_files=len(protected), public_json=len(paths),
                  healthy_archives=len(archives), incomplete_ratings_now_null=len(changed_ratings),
                  map_ratings_raw_stats_season_career_roles_coverage_unchanged=True,
                  permitted_changes='incomplete Series Ratings become null, series Rating sorting, export freshness',
                  changed_rating_fields=changed_ratings)
    (evidence / 'preservation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k:v for k,v in report.items() if k!='changed_rating_fields'}, indent=2))


if __name__ == '__main__':
    verify()
