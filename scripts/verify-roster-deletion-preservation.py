"""Verify requested White membership edits and preservation of imported history."""
import json
from pathlib import Path
import sqlite3
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from r6stats.replay_archive import sha256,verify
from r6stats.db import repository as repo,teams
from r6stats.publishing import validate_public_data

OUT=ROOT/'data/research/roster-deletion-20261007'


def main():
    db=sqlite3.connect(ROOT/'data/r6stats.sqlite');db.row_factory=sqlite3.Row
    before=json.loads((OUT/'tables-before.json').read_text(encoding='utf-8'))
    after={r[0]:[dict(x) for x in db.execute(f'SELECT * FROM "{r[0]}" ORDER BY rowid')]
        for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
    assert before.keys()==after.keys()
    for table,rows in before.items():
        if table!='team_memberships':assert rows==after[table],table
    old=[m for m in before['team_memberships'] if m['player_id']!=12]
    new=[m for m in after['team_memberships'] if m['player_id']!=10]
    assert old==new,'Unrelated membership changed'
    assert not [m for m in after['team_memberships'] if m['player_id']==12]
    nacho=repo.roster_identity(db,'nachofries_08');assert nacho['id']==10
    assert nacho['status']=='Active' and nacho['substitute_eligible']==0
    assert teams.member(db,10,2,'2026-10-07') and not teams.member(db,10,2,'2026-10-06')
    assert not teams.member(db,12,2,'2026-10-07')
    assert repo.roster_identity(db,'Nanor555')['id']==12
    assert len([p for p in after['players'] if p['username'].casefold()=='nachofries_08'])==1
    assert len([a for a in after['aliases'] if a['username'].casefold()=='nachofries_08'])==1
    hashes=json.loads((OUT/'hashes-before.json').read_text(encoding='utf-8'))
    for name,digest in hashes.items():assert sha256(ROOT/name)==digest,name
    assert all(verify(db,ROOT/'data/replay-archive',m['id'])['status']=='Healthy' for m in after['maps'])
    assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    assert not db.execute('PRAGMA foreign_key_check').fetchall()
    oldroot=OUT/'public-before';newroot=ROOT/'web/public/data'
    old={p.relative_to(oldroot).as_posix():json.loads(p.read_text(encoding='utf-8')) for p in oldroot.rglob('*.json')}
    new={p.relative_to(newroot).as_posix():json.loads(p.read_text(encoding='utf-8')) for p in newroot.rglob('*.json')}
    assert old.keys()==new.keys(),'Public inventory changed after temporary player cleanup'
    for name,value in old.items():
        current=new[name]
        if name.startswith(('matches/','series/','teams/blue/')) or name.startswith(tuple(f'players/{slug}/' for slug in ('lgon','ohwowjay','azooznewzz','tallman3-14','dinofireking'))):
            assert value==current,name
        if name.startswith('seasons/'):
            for key in value:
                if key!='players':assert value[key]==current[key],(name,key)
            oldplayers={p['slug']:p for p in value['players'] if p['rounds']>0}
            newplayers={p['slug']:p for p in current['players'] if p['rounds']>0}
            assert oldplayers==newplayers,name
        if name.startswith('players/'):
            assert {k:v for k,v in value.items() if k!='memberships'}=={k:v for k,v in current.items() if k!='memberships'},name
    for period in ('index','fall-2026','career'):
        white=new[f'teams/white/{period}.json']
        assert any(p['slug']=='nachofries-08' for p in white['roster'])
        assert not any(p['slug']=='nanor555' for p in white['roster'])
        if period!='index':assert white['players']==[] and white['sub_players']==[]
    profile=new['players/nachofries-08/fall-2026.json']
    assert profile['rounds']==0 and profile['maps']==0 and profile['rating'] is None and profile['kd'] is None
    count=validate_public_data(ROOT)
    report=dict(status='PASS',database_tables=len(before),public_files=count,protected_files=len(hashes),
        healthy_archives=len(after['maps']),maps=len(after['maps']),rounds=len(after['rounds']),
        identities=len(after['players']),unique_nacho_id=10,white_roster=[p['name'] for p in new['teams/white/index.json']['roster']],
        nanor_identity_retained=True,imported_statistics='unchanged',membership_start='2026-10-07')
    (OUT/'preservation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
