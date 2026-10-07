"""Current-state audited preview, then separately authorized atomic sidecars.

Run without --apply first. Rollback: stop the local server, restore the verified
before.sqlite backup to data/r6stats.sqlite and restore before-public/. Raw
archives, identities, normalized events, and existing Rating snapshots never move.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from current_kill_migration import DATA, save
from r6stats.credited_refresh import store
from r6stats.db import repository as repo
from r6stats.export import export
from r6stats.publishing import validate_public_data
from v3_final_reserve import ROOT, sha, source_sha

ALLOWED = {'kills','kd','kpr','kd_diff','kost','kost_rounds','multikill_extra',
           'kill_source','kill_source_rounds','finisher_kills','multikill_sizes',
           'headshot_source','event_feature_source'}


def compare(old, new, path=''):
    if isinstance(old,dict) and isinstance(new,dict):
        for key in old.keys() | new.keys():
            if key in ALLOWED or path=='methodology.json' and key=='kill_methodology':
                continue
            if key not in old or key not in new:
                raise ValueError(f'Unexpected field inventory difference: {path}/{key}')
            compare(old[key],new[key],path+'/'+key)
    elif isinstance(old,list) and isinstance(new,list):
        if len(old)!=len(new):raise ValueError(f'Changed public inventory: {path}')
        for i,(a,b) in enumerate(zip(old,new)):compare(a,b,path+f'/{i}')
    elif old!=new:
        raise ValueError(f'Unrelated public change: {path}: {old!r} -> {new!r}')


def state_matches(db,before):
    for table,rows in before.items():
        if not isinstance(rows,list):continue
        actual=[dict(r) for r in db.execute(f'SELECT * FROM {table} ORDER BY rowid')]
        if table=='rating_input_snapshots':
            index={(r['map_id'],r['version']):r for r in actual}
            if any(index.get((r['map_id'],r['version']))!=r for r in rows):
                raise ValueError('Existing Rating snapshot changed')
        elif actual!=rows:
            raise ValueError(f'Protected table changed: {table}')
    if db.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('SQLite integrity failure')


def main():
    args=argparse.ArgumentParser();args.add_argument('--apply',action='store_true');opt=args.parse_args()
    before=json.loads((DATA/'before.json').read_text(encoding='utf-8'))
    audit=json.loads((DATA/'audit.json').read_text(encoding='utf-8'))
    if audit['baseline_sha256']!=sha(DATA/'before.json'):raise ValueError('Baseline seal differs')
    config=json.loads((ROOT/'config/settings.json').read_text(encoding='utf-8'))
    for name,digest in before['archive_hashes'].items():
        if sha(ROOT/name)!=digest:raise ValueError('Archive changed')
    backup=DATA/'before-public'
    if not backup.exists():shutil.copytree(ROOT/'web/public/data',backup)
    candidate_db=DATA/'candidate.sqlite'
    if not candidate_db.exists():shutil.copy2(DATA/'before.sqlite',candidate_db)
    db=repo.connect(candidate_db)
    for m in audit['maps']:store(db,m['map_id'],m['records'],audit['binary_sha256'])
    state_matches(db,before)
    candidate=DATA/'candidate-public';export(db,config,candidate/'web/public/data')
    validate_public_data(candidate)
    diffs=[];totals=[]
    for path in sorted(backup.rglob('*.json')):
        relative=path.relative_to(backup)
        old=json.loads(path.read_text(encoding='utf-8'))
        new=json.loads((candidate/'web/public/data'/relative).read_text(encoding='utf-8'))
        compare(old,new,relative.as_posix())
        if old!=new:diffs.append(relative.as_posix())
        if relative.parts[0]=='players' and relative.name=='career.json':
            totals.append({'player':new['name'],'before':old,'after':new})
    # Per-map preview retains every old/new statistic and its whole-map status.
    maps=[]
    for m in audit['maps']:
        relative=Path('matches')/(m['map_id']+'.json')
        maps.append(dict(map_id=m['map_id'],map=m['map'],whole_map_ready=m['credit']['complete'],
            before=json.loads((backup/relative).read_text(encoding='utf-8')),
            after=json.loads((candidate/'web/public/data'/relative).read_text(encoding='utf-8')),
            unresolved_notes=m['credit']['issues']))
    result=dict(baseline_sha256=sha(DATA/'before.json'),audit_sha256=sha(DATA/'audit.json'),
        maps=maps,totals=totals,public_changed_files=diffs,
        source_hashes={n:source_sha(ROOT/n) for n in ('r6stats/credited_refresh.py','r6stats/export.py','research/apply_current_kill_migration.py')},
        candidate_hashes={p.relative_to(candidate/'web/public/data').as_posix():sha(p) for p in (candidate/'web/public/data').rglob('*.json')})
    save(DATA/'preview.json',result)
    for r in totals:
        print(r['player'],r['before']['kills'],'->',r['after']['kills'],
              'D',r['after']['deaths'],'KOST',r['after']['kost_rounds'],
              'coverage',r['after']['kill_source_rounds'],'Rating delta',r['after']['rating']-r['before']['rating'],flush=True)
    if opt.apply:
        live=repo.connect(ROOT/'data/r6stats.sqlite')
        state_matches(live,before)
        # Use one outer transaction: store uses savepoints via the small proxy,
        # preventing its context manager from committing each map individually.
        class Transaction:
            def __init__(self, connection):self.connection=connection
            def execute(self,*a):return self.connection.execute(*a)
            def __enter__(self):self.connection.execute('SAVEPOINT credit_map');return self
            def __exit__(self,kind,value,trace):
                if kind:self.connection.execute('ROLLBACK TO credit_map')
                self.connection.execute('RELEASE credit_map')
        with live:
            live.execute('BEGIN IMMEDIATE')
            state_matches(live,before)
            for m in audit['maps']:store(Transaction(live),m['map_id'],m['records'],audit['binary_sha256'])
            state_matches(live,before)
        export(live,config,ROOT/'web/public/data')
        validate_public_data(ROOT)
        for relative,digest in result['candidate_hashes'].items():
            if sha(ROOT/'web/public/data'/relative)!=digest:raise ValueError('Applied public output differs from reviewed candidate')
        save(DATA/'applied.json',dict(preview_sha256=sha(DATA/'preview.json'),sqlite_sha256=sha(ROOT/'data/r6stats.sqlite'),
            original_tables_preserved=True,original_snapshots_preserved=True,new_snapshot_count=live.execute('SELECT COUNT(*) FROM rating_input_snapshots').fetchone()[0]))
        print('APPLIED: original tables, archives, objectives, and v2 inputs preserved',flush=True)


if __name__=='__main__':main()
