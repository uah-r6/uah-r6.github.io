"""Resumable current archive counter audit; historical studies stay immutable.

Read-only until a separate, explicit apply step is implemented. No target APIs,
replay reparse, original cache replacement, or production export occurs here.
"""
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from credited_round_dataset import archive_sources, cached_index, cached_observation
from r6stats.kill_credit import validate_map_credit, project_credited_counts
from r6stats.parser.models import Match
from r6stats.replay_archive import verify
from v3_final_reserve import ROOT, sha

DATA = ROOT / 'data/research/production-kill-migration-20261006'
EXE = ROOT / '.local-tools/bin/siege-kill-credit.exe'


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, indent=2, sort_keys=True) + '\n'
    if path.exists() and path.read_text(encoding='utf-8') != text:
        raise ValueError(f'Existing audit differs: {path.name}')
    if not path.exists():
        path.write_text(text, encoding='utf-8')


def main():
    DATA.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect((ROOT/'data/r6stats.sqlite').resolve().as_uri()+'?mode=ro', uri=True) as db:
        db.row_factory = sqlite3.Row
        # Snapshot BEFORE schema additions. Table contents are the rollback and
        # nonregression reference; private evidence never enters public output.
        tables = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        state = {t: [dict(r) for r in db.execute(f'SELECT * FROM {t} ORDER BY rowid')] for t in tables}
        state['head'] = subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip()
        state['sqlite_sha256'] = sha(ROOT/'data/r6stats.sqlite')
        state['public_hashes'] = {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted((ROOT/'web/public/data').rglob('*.json'))}
        state['archive_hashes'] = {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted((ROOT/'data/replay-archive').rglob('*')) if p.is_file()}
        save(DATA/'before.json', state)
        if not (DATA/'before.sqlite').exists():
            with sqlite3.connect(DATA/'before.sqlite') as backup:
                db.backup(backup)
                if backup.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                    raise ValueError('Backup integrity check failed')
        if db.execute('SELECT COUNT(*) FROM map_kd_corrections').fetchone()[0]:
            raise ValueError('Manual overrides require separate reconciliation')
        rows = list(db.execute('''SELECT m.id,m.normalized_json,se.slug FROM maps m
            JOIN series s ON s.id=m.series_id JOIN seasons se ON se.id=s.season_id
            WHERE s.demo=0 ORDER BY m.id'''))
        index = cached_index()
        results = []
        for row in rows:
            status = verify(db, ROOT/'data/replay-archive', row['id'])
            if status['status'] != 'Healthy':
                raise ValueError(f"Unhealthy archive: {row['id']}")
            records = []
            for source in sorted(archive_sources(row['id'],row['slug']), key=lambda r:r['logical_round']):
                if sha(source['path']) != source['replay_sha256']:
                    raise ValueError('Replay hash differs')
                cached = DATA/'raw'/(source['replay_sha256']+'.json')
                if cached.exists():
                    observation = json.loads(cached.read_text(encoding='utf-8'))
                elif index.get(source['replay_sha256']):
                    _, observation = cached_observation(index, source['replay_sha256'])
                    save(cached, observation)
                else:
                    run = subprocess.run([str(EXE),str(source['path'])], capture_output=True, text=True, check=True)
                    observation = json.loads(run.stdout)
                    observation.update(replay_sha256=source['replay_sha256'], executable_sha256=sha(EXE), mode='actual-replay-current-migration')
                    save(cached, observation)
                if observation['replay_sha256'] != source['replay_sha256'] or observation['executable_sha256'] != sha(EXE):
                    raise ValueError('Counter provenance differs')
                records.append({k:source[k] for k in ('logical_round','physical_round','segment')} | {'credit':observation['credit']})
                print(row['id'],source['logical_round'],observation['credit']['complete'],flush=True)
            credit = validate_map_credit(records)
            match = Match.from_dict(json.loads(row['normalized_json']))
            projected = project_credited_counts(match,credit) if credit['complete'] else None
            result = dict(map_id=row['id'],map=match.map_name,rounds=len(match.rounds),credit=credit,records=records,projection=projected)
            save(DATA/'maps'/(row['id']+'.json'),result)
            results.append(result)
            print('MAP COMPLETE',row['id'],credit['complete'],credit['issues'],flush=True)
        save(DATA/'audit.json',dict(maps=results,baseline_sha256=sha(DATA/'before.json'),binary_sha256=sha(EXE)))


if __name__ == '__main__':
    main()
