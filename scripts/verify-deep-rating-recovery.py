"""Private v3 recovery verifier: read-only production, repairs only trial copies.

Never imports/reparses into production SQLite. Baselines cannot be overwritten.
"""
import argparse
import json
from pathlib import Path
import shutil
import sqlite3
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from r6stats.rating_evidence import audit_map
from r6stats.rating_inputs_v3 import load_inputs, prepare
from r6stats.parser.models import Match
from r6stats.replay_archive import sha256
from r6stats import credited_refresh, objective_refresh, rating_evidence
from r6stats.stats.calculate import COUNTS, calculate_match, aggregate

OUT = ROOT / 'data/research/deep-rating-recovery-20261008'
TARGETS = {'5adc26f7a402':9,'8a6357ff307c':6,'b595ffaaec57':10}


def write(name, value):
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')


def tables(db):
    return {r[0]: [dict(row) for row in db.execute(f'SELECT * FROM "{r[0]}" ORDER BY rowid')]
            for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")}


def hashes():
    paths = list((ROOT/'data/replay-archive').rglob('*'))
    paths += list((ROOT/'.local-tools/bin').glob('*.exe'))
    paths += list((ROOT/'r6stats').rglob('*.py'))
    paths += list((ROOT/'third_party/siege-dissect').rglob('*.go'))
    paths += list((ROOT/'web/src').rglob('*'))
    paths += list((ROOT/'cloudflare').rglob('*')) if (ROOT/'cloudflare').exists() else []
    return {str(p.relative_to(ROOT)): sha256(p) for p in sorted(paths)
            if p.is_file() and not {'node_modules', '.wrangler', '__pycache__'} & set(p.parts)}


def inputs(db):
    result = {}
    for row in db.execute('SELECT * FROM maps ORDER BY id'):
        values, reason = load_inputs(db, row['id'])
        entry = dict(values=values, reason=reason, audit=audit_map(db, ROOT/'data/replay-archive', row['id']))
        if values is not None:
            match = Match.from_dict(json.loads(row['normalized_json']))
            sidecar = db.execute('SELECT evidence_json FROM map_v3_objective_evidence WHERE map_id=?', (row['id'],)).fetchone()
            if sidecar:
                match = Match.from_dict(json.loads(sidecar[0]))
            from r6stats.rating_credit_evidence import load
            credit, stale = load(db, row['id'])
            assert not stale
            if credit is None:
                credit = json.loads(db.execute('SELECT evidence_json FROM map_kill_credit WHERE map_id=?', (row['id'],)).fetchone()[0])
            entry['features'] = prepare(match, credit)[1]
        result[row['id']] = entry
    return result


def reextract(db):
    baseline = json.loads((OUT/'inputs-before.json').read_text(encoding='utf-8'))
    binary = OUT/'siege-kill-credit-candidate.exe'
    with patch('r6stats.parser.siege_dissect.parser_executable',return_value=str(OUT/'siege-dissect-candidate.exe')):
        for row in db.execute('SELECT * FROM maps ORDER BY id'):
            mid = row['id']
            fresh = objective_refresh.parse_archive(db,ROOT/'data/replay-archive',mid)
            records, digest = credited_refresh.read_archive(db,ROOT/'data/replay-archive',mid,binary)
            write(f'fresh/{mid}-credit.json',dict(records=records,binary_sha256=digest))
            write(f'fresh/{mid}-objectives.json',fresh.to_dict())
            if baseline[mid]['values'] is not None:
                original = Match.from_dict(json.loads(row['normalized_json']))
                candidate = rating_evidence.objective_candidate(original,fresh)
                values,features = prepare(candidate,records)
                assert values == baseline[mid]['values'], f'Already eligible Rating drift: {mid}'
                assert features == baseline[mid]['features'], f'Already eligible feature drift: {mid}'
            print('Fresh extraction PASS',mid,flush=True)
    write('fresh/regression.json',dict(status='PASS',maps=9,eligible_feature_rows_exact=6,
        parser_sha256=sha256(OUT/'siege-dissect-candidate.exe'),credit_sha256=sha256(binary)))


def trial(filename):
    assert Path(filename).name == filename and filename.endswith('.sqlite')
    path=OUT/filename
    assert not path.exists(), 'Trial exists; refusing overwrite'
    shutil.copy2(OUT/'before.sqlite',path)
    original_reader=credited_refresh.read_archive
    def reader(db,archive,mid,executable=None):
        return original_reader(db,archive,mid,OUT/'siege-kill-credit-candidate.exe')
    with sqlite3.connect(path) as db, patch('r6stats.credited_refresh.read_archive',side_effect=reader), patch('r6stats.parser.siege_dissect.parser_executable',return_value=str(OUT/'siege-dissect-candidate.exe')), patch('r6stats.rating_evidence.parser_executable',return_value=str(OUT/'siege-dissect-candidate.exe')):
        db.row_factory=sqlite3.Row
        result=rating_evidence.repair_all(db,ROOT/'data/replay-archive')
        write('trial-repair.json',result)
        assert result['repaired']==3 and result['blocked']==0,result
        write('trial-inputs.json',inputs(db))
        write('trial-tables.json',tables(db))
        before=json.loads((OUT/'inputs-before.json').read_text(encoding='utf-8'))
        for mid,entry in inputs(db).items():
            if before[mid]['values'] is not None:
                assert entry['values']==before[mid]['values'] and entry['features']==before[mid]['features'],mid
        print('Trial repair PASS: 9 eligible, 3 repaired, six original feature/Ratings exact')


def verify_repair(db):
    before=json.loads((OUT/'tables-before.json').read_text(encoding='utf-8'))
    trial=json.loads((OUT/'trial-tables.json').read_text(encoding='utf-8'))
    current=tables(db)
    assert set(current)==set(before)|{'map_v3_kill_evidence'}
    changed={'maps','objective_events','rating_evidence_audit','map_v3_kill_evidence'}
    for name in set(before)-changed:
        assert current[name]==before[name],f'Unrelated database table changed: {name}'
    # The real maintenance transaction must exactly reproduce the reviewed copy.
    assert current['maps']==trial['maps'],'Map payload/metadata differs from reviewed trial'
    canonical=lambda rows:sorted(rows,key=lambda r:json.dumps(r,sort_keys=True))
    assert canonical(current['objective_events'])==canonical(trial['objective_events'])
    assert current['map_v3_kill_evidence']==trial['map_v3_kill_evidence']
    assert current['rating_evidence_audit'][:len(before['rating_evidence_audit'])]==before['rating_evidence_audit']
    added=current['rating_evidence_audit'][len(before['rating_evidence_audit']):]
    assert len(added)==7 and all(r['map_id'] in TARGETS for r in added)
    deltas=[]
    oldmaps={r['id']:r for r in before['maps']}
    for row in current['maps']:
        mid=row['id'];old=Match.from_dict(json.loads(oldmaps[mid]['normalized_json']))
        new=Match.from_dict(json.loads(row['normalized_json']))
        a,b=calculate_match(old),calculate_match(new)
        assert set(a)==set(b)
        for key in a:
            for field in (*COUNTS,'operators','sides'):
                if a[key][field]==b[key][field]:continue
                assert mid in TARGETS and field in ('plants','disables','kost_rounds'),(mid,key,field)
                deltas.append(dict(map_id=mid,player=next(p.username for r in old.rounds for p in r.players if p.key==key),
                                   field=field,before=a[key][field],after=b[key][field]))
        for r,s in zip(old.rounds,new.rounds):
            assert r.number==s.number and r.players==s.players and r.kills==s.kills
            if r.objectives!=s.objectives:assert r.number==TARGETS[mid]
    assert {(d['map_id'],d['player'],d['field'],d['after']-d['before']) for d in deltas}=={
        ('5adc26f7a402','Kenbot.USU','plants',1),
        ('8a6357ff307c','Lxgacy.MAV','disables',-1),('8a6357ff307c','Lxgacy.MAV','kost_rounds',-1),
        ('b595ffaaec57','Ophanbear.UMich','plants',1)},deltas
    oldhash=json.loads((OUT/'hashes-before.json').read_text(encoding='utf-8'));now=hashes()
    preserved=('data/replay-archive/','web/src/','cloudflare/')
    for name,digest in oldhash.items():
        if name.startswith(preserved) or name=='r6stats/stats/rating_v3.py':
            assert now[name]==digest,f'Preserved source/archive changed: {name}'
    observed=inputs(db);baseline=json.loads((OUT/'inputs-before.json').read_text(encoding='utf-8'))
    assert all(e['values'] is not None and e['audit']['archive']['status']=='Healthy' for e in observed.values())
    for mid,e in baseline.items():
        if e['values'] is not None:
            assert observed[mid]['values']==e['values'] and observed[mid]['features']==e['features'],mid
    assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    assert not db.execute('PRAGMA foreign_key_check').fetchall()
    write('inputs-after.json',observed)
    write('preservation.json',dict(status='PASS',eligible_maps=9,healthy_archives=9,
        original_six_features_and_ratings='EXACT',immutable_tables=sorted(set(before)-changed),
        display_sidecars_and_v2_snapshots='EXACT',normalized_objective_deltas=deltas,
        archives_manifests_frontend_worker_formula='EXACT',audits_added=len(added)))


def verify_public(db):
    from r6stats.publishing import validate_public_data
    assert validate_public_data(ROOT)==49
    public=ROOT/'web/public/data'
    ignored={'rating','rating_rounds','rating_maps','rating_eligible','rating_exclusion','generated_at'}
    def canonical(value):
        if isinstance(value,dict):return {k:canonical(v) for k,v in value.items() if k not in ignored}
        if isinstance(value,list):return sorted([canonical(v) for v in value],key=lambda v:json.dumps(v,sort_keys=True))
        return value
    changed=[]
    before=OUT/'public-before'
    assert {p.relative_to(public) for p in public.rglob('*.json')}=={p.relative_to(before) for p in before.rglob('*.json')}
    for p in before.rglob('*.json'):
        name=p.relative_to(before)
        a=json.loads(p.read_text(encoding='utf-8'));b=json.loads((public/name).read_text(encoding='utf-8'))
        assert canonical(a)==canonical(b),f'Unrelated public value changed: {name}'
        if a!=b:changed.append(name.as_posix())
        if name.parts[0]=='matches' and name.stem not in TARGETS:assert a==b
        if name.parts[0]=='series' and name.stem in ('40bf93b16f97','ada4becd7c74'):assert a==b
    cached={r['id']:load_inputs(db,r['id'])[0] for r in db.execute('SELECT id FROM maps')}
    identities={r['slug']:r['id'] for r in db.execute('SELECT id,slug FROM players')}
    def player_inputs(mid,slug):
        keys={r[0] for r in db.execute('SELECT DISTINCT rp.player_key FROM round_players rp JOIN rounds r ON r.id=rp.round_id WHERE r.map_id=? AND rp.player_id=?',(mid,identities[slug]))}
        assert len(keys)==1,(mid,slug,keys)
        return cached[mid][next(iter(keys))]
    results=[]
    for p in sorted((public/'series').glob('*.json')):
        doc=json.loads(p.read_text(encoding='utf-8'))
        for player in doc['players']:
            mids=[r[0] for r in db.execute('SELECT m.id FROM maps m JOIN map_player_appearances a ON a.map_id=m.id WHERE m.series_id=? AND a.player_id=?',(doc['id'],identities[player['slug']]))]
            rows=[player_inputs(mid,player['slug']) for mid in mids]
            expected=aggregate(rows,'siege_style_v3')
            assert player['rating']==expected['rating'],(doc['id'],player['slug'])
            assert player['rating_maps']==player['maps']==len(mids)
            assert player['rating_rounds']==player['rounds']==expected['rounds']
            results.append(dict(series_id=doc['id'],opponent=doc['opponent'],player=player['name'],rating=player['rating'],
                                maps=len(mids),rounds=expected['rounds']))
    for path in (public/'players').glob('*/*.json'):
        doc=json.loads(path.read_text(encoding='utf-8'));slug=path.parent.name
        mids=[r[0] for r in db.execute("SELECT map_id FROM map_player_appearances WHERE player_id=? AND appearance_role='roster'",(identities[slug],))]
        if mids:
            expected=aggregate([player_inputs(mid,slug) for mid in mids],'siege_style_v3')
            assert doc['rating']==expected['rating'],path
            assert doc['rating_maps']==len(mids) and doc['rating_rounds']==expected['rounds']
    write('public-verification.json',dict(status='PASS',documents=49,changed_documents=changed,
        all_public_counts_highlights_roles_metadata='EXACT',six_map_documents='EXACT',ucf_white_series='EXACT',
        series_players_aggregate_once=results,normal_season_career='INDEPENDENT TRUSTED AGGREGATION'))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('mode', choices=['baseline', 'audit', 'verify', 'reextract', 'trial'])
    ap.add_argument('--trial-file',default='trial.sqlite')
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if args.mode == 'trial':
        trial(args.trial_file)
        return
    with sqlite3.connect((ROOT/'data/r6stats.sqlite').resolve().as_uri()+'?mode=ro', uri=True) as db:
        db.row_factory = sqlite3.Row
        if args.mode == 'baseline':
            assert not (OUT/'before.sqlite').exists(), 'Baseline exists; refusing overwrite'
            with sqlite3.connect(OUT/'before.sqlite') as target:
                db.backup(target)
            shutil.copytree(ROOT/'web/public/data', OUT/'public-before')
            write('tables-before.json', tables(db))
            write('hashes-before.json', hashes())
            write('inputs-before.json', inputs(db))
            write('baseline.json', dict(database_sha256=sha256(OUT/'before.sqlite'), maps=9))
        elif args.mode == 'reextract':
            reextract(db)
        elif args.mode == 'verify':
            verify_repair(db)
            verify_public(db)
        else:
            write('audit-current.json', inputs(db))
        for key, entry in inputs(db).items():
            print(key, entry['audit']['map'], entry['audit']['rounds'], entry['audit']['archive']['status'], entry['reason'] or 'ELIGIBLE')


if __name__ == '__main__':
    main()
