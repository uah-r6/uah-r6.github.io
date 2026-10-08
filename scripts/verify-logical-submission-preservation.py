"""Read-only comparison with the ignored pre-intake-overhaul checkpoint."""
import argparse
import hashlib
import json
import sqlite3
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from r6stats import replay_archive
from r6stats.submissions import Client


def verify(cloud=False):
    evidence=ROOT/'data/research/logical-submissions-20261008'
    before=json.loads((evidence/'tables-before.json').read_text(encoding='utf8'))
    with sqlite3.connect(f'file:{(ROOT/"data/r6stats.sqlite").as_posix()}?mode=ro',uri=True) as db:
        db.row_factory=sqlite3.Row
        for table,rows in before.items():
            assert [dict(r) for r in db.execute('SELECT * FROM "'+table+'"')]==rows,table
        assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        assert not list(db.execute('PRAGMA foreign_key_check'))
        archives=[replay_archive.verify(db,ROOT/'data/replay-archive',r['id']) for r in db.execute('SELECT id FROM maps')]
        assert len(archives)==9 and all(a['status']=='Healthy' for a in archives)
    protected=json.loads((evidence/'protected-before.json').read_text(encoding='utf8'))
    for name,sha in protected.items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==sha,name
    public=list((evidence/'public-before').rglob('*.json'))
    assert len(public)==len(list((ROOT/'web/public/data').rglob('*.json')))
    for file in public:
        assert file.read_bytes()==(ROOT/'web/public/data'/file.relative_to(evidence/'public-before')).read_bytes(),str(file)
    report=dict(tables=len(before),protected_files=len(protected),public_json=len(public),archives=len(archives),integrity='ok',foreign_keys='ok',unchanged=True)
    if cloud:
        client=Client(ROOT)
        baseline=json.loads((evidence/'cloud-before.json').read_text(encoding='utf8'))
        current=dict(submissions=client.call('/submissions?status=all'),pending=client.call('/submissions'),storage=client.call('/storage'))
        assert current['pending']==baseline['pending']
        assert len(current['submissions'])==len(baseline['submissions'])
        lookup={s['id']:s for s in current['submissions']}
        for old in baseline['submissions']:
            new=lookup[old['id']]
            for key,value in old.items():
                if key=='folders':
                    folders={f['id']:f for f in new['folders']}
                    for original in value:
                        assert all(folders[original['id']][k]==v for k,v in original.items()),'Legacy folder changed'
                else:assert new[key]==value,'Legacy submission field changed: '+key
        for key in ('stored_bytes','reserved_bytes','pending_count','pending_bytes','terminal_bytes','cap_bytes','enabled'):
            assert current['storage'][key]==baseline['storage'][key],key
        (evidence/'cloud-after.json').write_text(json.dumps(current,indent=2),encoding='utf8')
        report.update(cloud_legacy_records=len(current['submissions']),cloud_pending=len(current['pending']),cloud_storage_unchanged=True)
    (evidence/'preservation.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print('Preservation PASS:',json.dumps(report))
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--cloud',action='store_true');args=parser.parse_args();verify(args.cloud)
