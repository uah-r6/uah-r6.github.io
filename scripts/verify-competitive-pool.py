"""Read-only preservation checks against the pre-migration production backup."""
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from r6stats.db import map_pool
from r6stats.publishing import validate_public_data
from r6stats.rating_inputs_v3 import load_inputs
from r6stats.replay_archive import verify as verify_archive

OUT=ROOT/'data/research/competitive-map-pool-20261008'


def read(path):return json.loads(path.read_text(encoding='utf-8'))


def verify():
    original=read(OUT/'tables-before.json')
    allowed={'map_pool_catalog','season_map_pool','season_map_pool_config','map_pool_schema_version'}
    with sqlite3.connect((ROOT/'data/r6stats.sqlite').as_uri()+'?mode=ro',uri=True) as db:
        db.row_factory=sqlite3.Row
        current={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
        assert current-set(original)==allowed
        for table,rows in original.items():
            assert [dict(r) for r in db.execute(f'SELECT * FROM "{table}" ORDER BY rowid')]==rows,table
        assert not db.execute('PRAGMA foreign_key_check').fetchall()
        pools=[map_pool.load(db,r[0]) for r in db.execute('SELECT slug FROM seasons')]
        archive={}
        for row in db.execute('SELECT id FROM maps'):
            archive[row['id']]=verify_archive(db,ROOT/'data/replay-archive',row['id'])['status']
            inputs,reason=load_inputs(db,row['id'],8)
            assert inputs is not None and reason is None
        assert len(archive)==9 and set(archive.values())=={'Healthy'}
    changed={'r6stats/export.py','r6stats/publishing.py','r6stats/admin/server.py',
             'r6stats/db/repository.py','r6stats/map_analytics.py'}
    for name,digest in read(OUT/'hashes-before.json').items():
        if name not in changed:assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
    stats_docs=analytics_docs=0
    for path in (OUT/'public-before').rglob('*.json'):
        relative=path.relative_to(OUT/'public-before')
        before,after=read(path),read(ROOT/'web/public/data'/relative)
        if '/maps/' in relative.as_posix():
            originals={m['slug']:m for m in before['maps']}
            actual={m['slug']:m for m in after['maps']+after['historical_maps']}
            for slug,old in originals.items():
                if old['maps_played'] or slug in actual:assert actual[slug]==old,(relative,slug)
            analytics_docs+=1
        else:
            if relative.as_posix()=='index.json':before.pop('generated_at');after.pop('generated_at')
            assert before==after,relative
            stats_docs+=1
    report=dict(status='PASS',original_tables_preserved=len(original),added_tables=sorted(allowed),
                statistical_documents_preserved=stats_docs,analytics_counts_preserved=analytics_docs,
                archives=archive,rating_eligible_maps=9,public_documents=validate_public_data(ROOT),
                pools=[{k:p[k] for k in ('season','configured','origin','maps')} for p in pools],
                backup_sha256=hashlib.sha256((OUT/'before.sqlite').read_bytes()).hexdigest())
    (OUT/'verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='pools'},indent=2))


if __name__=='__main__':verify()
