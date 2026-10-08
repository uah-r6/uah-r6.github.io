"""Private baseline/audit for the historical evidence repair; never imports maps."""
import argparse
import json
from pathlib import Path
import shutil
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from r6stats.rating_inputs_v3 import load_inputs
from r6stats.replay_archive import verify, sha256
from r6stats.kill_credit import validate_map_credit
from r6stats.stats.calculate import aggregate

OUT = ROOT / 'data/research/series-evidence-repair-20261007'


def write(name, value):
    (OUT/name).write_text(json.dumps(value, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')


def tables(db):
    return {r[0]: [dict(row) for row in db.execute(f'SELECT * FROM "{r[0]}" ORDER BY rowid')]
            for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")}


def hashes():
    paths = list((ROOT/'data/replay-archive').rglob('*'))
    paths += list((ROOT/'r6stats/stats').rglob('*.py'))
    paths += list((ROOT/'r6stats/parser').rglob('*.py'))
    paths += list((ROOT/'third_party/siege-dissect').rglob('*.go'))
    paths += list((ROOT/'.local-tools/bin').glob('*.exe'))
    return {str(p.relative_to(ROOT)): sha256(p) for p in sorted(paths) if p.is_file()}


def audit(db):
    result = []
    for row in db.execute('SELECT m.*,s.opponent FROM maps m JOIN series s ON s.id=m.series_id ORDER BY m.id'):
        stats, reason = load_inputs(db, row['id'])
        credit = db.execute('SELECT * FROM map_kill_credit WHERE map_id=?', (row['id'],)).fetchone()
        objective = db.execute('SELECT * FROM map_v3_objective_evidence WHERE map_id=?', (row['id'],)).fetchone()
        result.append(dict(map_id=row['id'], series_id=row['series_id'], opponent=row['opponent'], map=row['map_name'],
            rounds=len(json.loads(row['normalized_json'])['rounds']), archive=verify(db, ROOT/'data/replay-archive', row['id']),
            credited_status='complete' if credit and validate_map_credit(json.loads(credit['evidence_json']))['complete'] else 'incomplete' if credit else 'absent',
            credited_issues=validate_map_credit(json.loads(credit['evidence_json']))['issues'] if credit else [],
            objective_status='sidecar present' if objective else 'normalized only', eligible=stats is not None, exclusion=reason))
    return result


def series():
    return [dict(series=d['id'], opponent=d['opponent'], player=p['name'], maps=p['maps'], rating_maps=p['rating_maps'],
                 rounds=p['rounds'], rating_rounds=p['rating_rounds'], rating=p['rating'])
            for f in sorted((ROOT/'web/public/data/series').glob('*.json'))
            for d in [json.loads(f.read_text(encoding='utf-8'))] for p in d['players']]


def compare_public():
    allowed = {'generated_at', 'rating', 'rating_maps', 'rating_rounds', 'rating_eligible', 'rating_exclusion'}
    def strip(v):
        if isinstance(v, dict): return {k: strip(x) for k, x in v.items() if k not in allowed}
        if isinstance(v, list): return [strip(x) for x in v]
        return v
    old_root = OUT/'public-before'
    old = {str(p.relative_to(old_root)): json.loads(p.read_text(encoding='utf-8')) for p in old_root.rglob('*.json')}
    new_root = ROOT/'web/public/data'
    new = {str(p.relative_to(new_root)): json.loads(p.read_text(encoding='utf-8')) for p in new_root.rglob('*.json')}
    assert old.keys() == new.keys(), 'Public file inventory differs'
    for name, value in old.items():
        assert strip(value) == strip(new[name]), f'Ordinary public statistics changed: {name}'
        if name.startswith('matches/') and value['rating_eligible']:
            assert value == new[name], f'Already valid map changed: {name}'
        if name == 'series/40bf93b16f97.json':
            assert value == new[name], 'UCF series changed'
    return len(old)


def verify_series_inputs(db):
    results=[]
    for f in sorted((ROOT/'web/public/data/series').glob('*.json')):
        doc=json.loads(f.read_text(encoding='utf-8'))
        for player in doc['players']:
            pid=db.execute('SELECT id FROM players WHERE slug=?',(player['slug'],)).fetchone()[0]
            inputs=[];rated_maps=[]
            for row in db.execute('SELECT id FROM maps WHERE series_id=?',(doc['id'],)):
                values,_=load_inputs(db,row['id'])
                if values is None:continue
                keys={r[0] for r in db.execute('SELECT DISTINCT player_key FROM round_players rp JOIN rounds r ON r.id=rp.round_id WHERE r.map_id=? AND rp.player_id=?',(row['id'],pid))}
                rows=[values[k] for k in keys if k in values]
                if rows:
                    inputs.extend(rows);rated_maps.append(row['id'])
            combined=aggregate(inputs,'siege_style_v3') if inputs else None
            assert player['rating_maps']==len(rated_maps)
            assert player['rating_rounds']==sum(r['rounds'] for r in inputs)
            assert abs(player['rating']-combined['rating'])<1e-12 if combined else player['rating'] is None
            weighted=sum(r['rating']*r['rounds'] for r in inputs)/sum(r['rounds'] for r in inputs) if inputs else None
            assert abs(combined['rating']-weighted)<1e-12 if combined else weighted is None
            results.append(dict(series_id=doc['id'],player=player['name'],input_maps=rated_maps,
                rating_maps=player['rating_maps'],rating_rounds=player['rating_rounds'],rating=player['rating'],weighted=weighted))
    write('series-input-verification.json',results)
    return len(results)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['baseline', 'audit', 'verify'])
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(ROOT/'data/r6stats.sqlite'); db.row_factory = sqlite3.Row
    if args.mode == 'baseline':
        assert not (OUT/'before.sqlite').exists(), 'Baseline already exists; refusing overwrite'
        with sqlite3.connect(OUT/'before.sqlite') as target: db.backup(target)
        shutil.copytree(ROOT/'web/public/data', OUT/'public-before')
        write('tables-before.json', tables(db)); write('hashes-before.json', hashes())
        write('series-before.json', series()); write('audit-before.json', audit(db))
        print('Baseline saved. SQLite backup SHA256:', sha256(OUT/'before.sqlite'))
    elif args.mode == 'verify':
        before = json.loads((OUT/'tables-before.json').read_text(encoding='utf-8'))
        after = tables(db)
        for table, rows in before.items():
            if table in ('map_kill_credit', 'map_v3_objective_evidence'): continue
            assert after[table] == rows, f'Historical database table changed: {table}'
        assert hashes() == json.loads((OUT/'hashes-before.json').read_text(encoding='utf-8')), 'Protected files changed'
        n = compare_public()
        assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        assert not db.execute('PRAGMA foreign_key_check').fetchall()
        observed = audit(db)
        assert all(m['archive']['status'] == 'Healthy' for m in observed)
        write('audit-after.json', observed); write('series-after.json', series())
        assert verify_series_inputs(db)==15
        write('preservation.json', dict(status='PASS', public_files=n, historical_tables=len(before), protected_files=len(hashes()), maps=len(observed)))
        print('Preservation PASS:', n, 'public files;', len(before), 'historical tables;', len(observed), 'Healthy archives')
    for item in audit(db):
        print(item['map_id'], item['map'], item['rounds'], item['archive']['status'], item['credited_status'], item['objective_status'], item['eligible'], item['exclusion'])
    for item in series(): print(json.dumps(item))


if __name__ == '__main__': main()
