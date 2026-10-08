"""Read-only production v3 audit and checkpoint preservation verification.

Usage: python scripts/verify-rating-production.py [--verify]
Diagnostics containing private evidence stay under ignored data/research.
"""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from r6stats.rating_evidence import audit_map
from r6stats.rating_inputs_v3 import load_inputs
from r6stats.replay_archive import sha256
from r6stats.stats.calculate import aggregate

OUT = ROOT/'data/research/rating-evidence-production-20261008'
WHITE = '035ff71d4884'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(name, value):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/name).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')


def tables(db):
    return {r[0]:[dict(row) for row in db.execute(f'SELECT * FROM "{r[0]}" ORDER BY rowid')]
        for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}


def public_comparison():
    allowed = {'generated_at','rating','rating_maps','rating_rounds','rating_eligible','rating_exclusion','partial'}
    def strip(value):
        if isinstance(value,dict):return {k:strip(v) for k,v in value.items() if k not in allowed}
        if isinstance(value,list):
            rows=[strip(v) for v in value]
            # Leaderboard order may change as newly eligible inputs contribute.
            return sorted(rows,key=lambda r:r['slug']) if rows and all(isinstance(r,dict) and 'slug' in r for r in rows) else rows
        return value
    old_root=OUT/'public-before';new_root=ROOT/'web/public/data'
    old={str(p.relative_to(old_root)):read(p) for p in old_root.rglob('*.json')}
    new={str(p.relative_to(new_root)):read(p) for p in new_root.rglob('*.json')}
    assert old.keys()==new.keys(),'Public inventory changed'
    for name,value in old.items():
        assert strip(value)==strip(new[name]),f'Unrelated public statistics changed: {name}'
        if name.startswith('matches/') and value['rating_eligible']:
            assert value==new[name],f'Already eligible map changed: {name}'
        if name=='series/40bf93b16f97.json':assert value==new[name],'UCF changed'
    return len(old)


def series_inputs(db):
    results=[]
    for path in sorted((ROOT/'web/public/data/series').glob('*.json')):
        doc=read(path)
        for player in doc['players']:
            pid=db.execute('SELECT id FROM players WHERE slug=?',(player['slug'],)).fetchone()[0]
            inputs=[];rated_maps=[];played_maps=[];rounds=0
            for row in db.execute('SELECT id FROM maps WHERE series_id=?',(doc['id'],)):
                participation=db.execute('SELECT DISTINCT rp.player_key,r.number FROM round_players rp JOIN rounds r ON r.id=rp.round_id WHERE r.map_id=? AND rp.player_id=?',(row['id'],pid)).fetchall()
                if not participation:continue
                played_maps.append(row['id']);rounds+=len({r['number'] for r in participation})
                values,_=load_inputs(db,row['id'])
                if values is None:continue
                rows=[values[key] for key in {r['player_key'] for r in participation} if key in values]
                if rows:inputs.extend(rows);rated_maps.append(row['id'])
            combined=aggregate(inputs,'siege_style_v3') if inputs else None
            assert player['maps']==len(played_maps) and player['rounds']==rounds
            assert player['rating_maps']==len(rated_maps)
            assert player['rating_rounds']==sum(r['rounds'] for r in inputs)
            assert abs(player['rating']-combined['rating'])<1e-12 if combined else player['rating'] is None
            weighted=sum(r['rating']*r['rounds'] for r in inputs)/sum(r['rounds'] for r in inputs) if inputs else None
            assert abs(combined['rating']-weighted)<1e-12 if combined else weighted is None
            results.append(dict(series_id=doc['id'],opponent=doc['opponent'],team=doc['team_name'],player=player['name'],
                role=player['appearance_role'],maps=player['maps'],rating_maps=player['rating_maps'],rounds=rounds,
                rating_rounds=player['rating_rounds'],rating=player['rating'],weighted=weighted))
    write('series-input-verification.json',results)
    white=read(ROOT/'web/public/data/teams/white/fall-2026.json')
    assert len(white['players'])==4 and len(white['sub_players'])==1
    assert all((p['rating_maps'],p['rating_rounds'])==(2,21) for p in white['players']+white['sub_players'])
    normal=read(ROOT/'web/public/data/players/dinoted11/career.json')
    assert normal['rounds']==0 and normal['maps']==0 and not normal['series_ratings']
    assert normal['sub_teams'][0]['rounds']==21
    return results


def preservation(db):
    before=read(OUT/'tables-before.json');after=tables(db)
    allowed={'maps','objective_events','rating_evidence_audit'}
    for name,rows in before.items():
        if name not in allowed:assert after[name]==rows,f'Unrelated DB table changed: {name}'
    for old,new in zip(before['maps'],after['maps']):
        if old['id']!=WHITE:assert old==new;continue
        prior=deepcopy(old);updated=deepcopy(new)
        a=json.loads(prior.pop('normalized_json'));b=json.loads(updated.pop('normalized_json'))
        assert prior==updated,'Map metadata changed'
        assert len(a['rounds'])==len(b['rounds'])==14
        for r,s in zip(a['rounds'],b['rounds']):
            if r['number']!=6:assert r==s;continue
            assert r['objectives']==[]
            assert len(s['objectives'])==len(s['objective_occurrences'])==1
            occurrence=s['objective_occurrences'][0]
            assert occurrence['actor']=='b26e89ec-86d2-4bde-b1a8-54d424b007f6'
            assert occurrence['actor_uid']==5319349670349841180
            assert occurrence['actor_source']==occurrence['actor_reason']=='completing_timer_owner_v1'
            assert occurrence['plant_state_offset']==104858758
            assert {k:v for k,v in r.items() if k not in ('objectives','objective_occurrences')}=={k:v for k,v in s.items() if k not in ('objectives','objective_occurrences')}
        assert {k:v for k,v in a.items() if k!='rounds'}=={k:v for k,v in b.items() if k!='rounds'}
    old_events=before['objective_events'];new_events=after['objective_events']
    assert all(row in new_events for row in old_events)
    delta=[row for row in new_events if row not in old_events]
    rid=db.execute('SELECT id FROM rounds WHERE map_id=? AND number=6',(WHITE,)).fetchone()[0]
    assert len(delta)==1 and delta[0]['round_id']==rid and delta[0]['kind']=='plant'
    assert delta[0]['player_key']=='b26e89ec-86d2-4bde-b1a8-54d424b007f6'
    protected=read(OUT/'protected-hashes-before.json')
    assert all(sha256(ROOT/name)==value for name,value in protected.items()),'Protected archive/formula/validator file changed'
    assert all(row in after['rating_evidence_audit'] for row in before['rating_evidence_audit'])
    for row in after['rating_evidence_audit'][len(before['rating_evidence_audit']):]:
        explanation=json.loads(row['after_json']) if row['operation']=='objective_actor_correction' else json.loads(row['explanation'])
        assert explanation['parser_sha256'] and explanation['archive_manifest_sha256'],row['operation']
    inputs=read(OUT/'inputs-before.json')
    for mid,values in inputs.items():
        if values['values'] is not None:assert load_inputs(db,mid)[0]==values['values'],f'Existing v3 inputs changed: {mid}'
    assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    assert not db.execute('PRAGMA foreign_key_check').fetchall()
    return dict(status='PASS',historical_tables=len(before),protected_files=len(protected),public_files=public_comparison(),
        existing_eligible_maps=sum(v['values'] is not None for v in inputs.values()),supported_objective_event_delta=delta,
        series_players=len(series_inputs(db)))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    db=sqlite3.connect((ROOT/'data/r6stats.sqlite').as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
    audit=[audit_map(db,ROOT/'data/replay-archive',row[0]) for row in db.execute('SELECT id FROM maps ORDER BY id')]
    write('audit-after.json',audit)
    for item in audit:
        # No private archive paths are printed or included in tracked artifacts.
        print(item['map_id'],item['team'],item['map'],item['rounds'],item['archive']['status'],item['credited_status'],item['eligible'],item['exclusion'])
    if args.verify:
        result=preservation(db);write('preservation.json',result);print(json.dumps(result))
    db.close()


if __name__=='__main__':main()
