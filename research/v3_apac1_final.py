"""Freeze APAC North Stage1 before targets and permanently evaluate ONCE."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
from urllib.parse import unquote,urlparse

from credited_late_history_development import immutable_write
from fit_models import predict as baseline_predict
from r6stats.kill_credit import validate_map_credit
from r6stats.parser.models import Match
from uah_comparison import player_rounds
from v3_apac1_pipeline import DATA,ALIASES,ADDITIONAL_ALIASES,EXTRA_ALIASES,PARSER,BASELINE,COUNTER
from v3_apac1_reserve import RESERVE
from v3_cnl_final import clean_tree,source_files,coverage,accuracy_checks,re_kd
from v3_cnl_metadata import DATA as METADATA,fetch
from v3_credited_derive import bind_lan_counts
from v3_final_reserve import ROOT,sha,source_sha
from v3_native_order_derive import updated_rows
from v3_native_order_fit import predict
from v3_objective_fit import metrics

FREEZE=ROOT/'research/v3-native-final-apac1-freeze.json'
RESULT=DATA/'one-shot-result.json'
CANDIDATE=ROOT/'research/v3-native-order-candidate.json'
PLAN=ROOT/'research/v3-native-order-plan.json'


def freeze():
    if FREEZE.exists() or (DATA/'rating-targets-opened.json').exists():raise ValueError('Final freeze/consumption already exists')
    clean_tree();subprocess.run([sys.executable,str(ROOT/'research/verify_production_kill_checkpoint.py')],check=True)
    reservation=json.loads(RESERVE.read_text(encoding='utf-8'));candidate=json.loads(CANDIDATE.read_text(encoding='utf-8'))
    baseline=json.loads((ROOT/'research/frozen-rating-candidate.json').read_text(encoding='utf-8'))['model']
    if reservation['candidate_sha256']!=source_sha(CANDIDATE) or reservation['plan_sha256']!=source_sha(PLAN):raise ValueError('Prospectively reserved candidate/plan differs')
    rows=[];maps=[];inputs={}
    for source in reservation['matches']:
        if not source['selected']:continue
        mid=source['official_match_id'];path=DATA/str(mid)/'prelabel-replays-v3.json'
        if not path.exists():raise ValueError('Every selected source needs a terminal decision')
        payload=json.loads(path.read_text(encoding='utf-8'));inputs[path.relative_to(ROOT).as_posix()]=sha(path)
        for filename,digest in payload['previous_prelabel_decisions'].items():
            old=path.with_name(filename)
            if sha(old)!=digest:raise ValueError('Earlier prelabel refusal changed')
            inputs[old.relative_to(ROOT).as_posix()]=digest
        archive=ROOT/'data/research/pro-replays'/unquote(Path(urlparse(source['archive_url']).path).name)
        if sha(archive)!=payload['archive_sha256']:raise ValueError('Selected archive changed')
        inputs[archive.relative_to(ROOT).as_posix()]=payload['archive_sha256']
        for p,d in ((METADATA/f"apac1-metadata-{source['siegegg_match_id']}.json",payload['metadata_sha256']),
                    (METADATA/f'apac1-primary-{mid}.html',payload['primary_sha256'])):
            if sha(p)!=d:raise ValueError('Independent metadata changed')
            inputs[p.relative_to(ROOT).as_posix()]=d
        expected_aliases=[source_sha(p) for p in (ALIASES,ADDITIONAL_ALIASES,EXTRA_ALIASES)]
        if [payload[k] for k in ('aliases_sha256','additional_aliases_sha256','extra_aliases_sha256')]!=expected_aliases:raise ValueError('Independent alias evidence revision differs')
        if [payload[k] for k in ('parser_sha256','baseline_parser_sha256','counter_sha256')]!=[sha(p) for p in (PARSER,BASELINE,COUNTER)]:raise ValueError('Parser binary changed')
        # Hash all source files and both raw-parser caches, including rejected
        # maps/unfinished attempts. A missing source is never silently skipped.
        extraction=ROOT/'data/research/extracted'/f'v3-native-apac1-{mid}'
        for folder in sorted({p.parent for p in extraction.rglob('*.rec')}):
            digests=[]
            for p in sorted(folder.glob('*.rec')):
                digest=sha(p);digests.append(bytes.fromhex(digest));inputs[p.relative_to(ROOT).as_posix()]=digest
            for executable in (PARSER,BASELINE):
                key=hashlib.sha256(executable.read_bytes()+b''.join(digests)).hexdigest()
                raw=ROOT/'data/research/diagnostics/objective-production-check'/(key+'.json')
                if not raw.exists():raise ValueError('Saved raw parser cache missing')
                inputs[raw.relative_to(ROOT).as_posix()]=sha(raw)
        for m in payload['maps']:
            inputs.update(m['inputs'])
            eligible=[r for r in m['rows'] if r['fit_eligible']]
            if eligible:
                match=Match.from_dict(m['normalized']);original=Match.from_dict(m['original_normalized']);records=[];observations={}
                for physical in m['physical_mapping']:
                    obs_path=DATA/'raw'/(physical['sha256']+'.json');obs=json.loads(obs_path.read_text(encoding='utf-8'))
                    if obs['replay_sha256']!=physical['sha256'] or obs['executable_sha256']!=sha(COUNTER):raise ValueError('Counter provenance differs')
                    observations[physical['logical_round']]=obs
                    records.append(dict(logical_round=physical['logical_round'],physical_round=physical['physical_round'],segment=physical['folder'],credit=obs['credit']))
                credit=validate_map_credit(records)
                counts=bind_lan_counts(match,credit)
                control=[]
                for row in m['rows']:
                    key=next(p.key for p in match.rounds[0].players if p.username==row['player'])
                    rounds=player_rounds(match,key)
                    for r in rounds:
                        r['kills']=counts[r['number']][key]
                        r['kost_rounds']=int(bool(r['kills'] or r['plants'] or r['disables'] or r['survived'] or r['deaths_traded']))
                    if rounds!=row['legacy_corrected_rounds'] or player_rounds(original,key)!=row['original_v2_rounds']:raise ValueError('Frozen legacy/original baseline reconstruction differs')
                    control.append(row|dict(rounds=rounds))
                native,_=updated_rows(match,control,observations)
                for expected,observed in zip(m['rows'],native):
                    if expected['rounds']!=observed['rounds'] or predict(candidate['model'],expected)!=expected['v3_prediction'] or baseline_predict(baseline,expected|dict(rounds=expected['original_v2_rounds']),{})!=expected['v2_prediction']:raise ValueError('Frozen native features/predictions differ')
            rows+=eligible
            maps.append(dict(official_match_id=mid,game_id=m['game_id'],map=m['map'],clean_rows=len(eligible),
                issues=sorted({i for r in m['rows'] for i in r['quality_issues']}|({m['whole_map_refusal']} if m.get('whole_map_refusal') else set()))))
        print('SEAL INPUTS',mid,'clean',sum(m['clean_rows'] for m in payload['maps']),flush=True)
    for p in (ALIASES,ADDITIONAL_ALIASES,EXTRA_ALIASES,METADATA/'apac1-independent-profile-bindings.json',
        METADATA/'apac1-identity-db3adff9-afd1-4e16-a201-e9d044a4a799-browser.json'):
        inputs[p.relative_to(ROOT).as_posix()]=sha(p)
    evidence,checks=coverage(rows,candidate['acceptance'])
    result=dict(event=reservation['event'],created_at=datetime.now(timezone.utc).isoformat(),source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        working_tree_clean=True,candidate_sha256=source_sha(CANDIDATE),candidate=candidate['model'],baseline=baseline,
        reservation_sha256=source_sha(RESERVE),plan_sha256=source_sha(PLAN),acceptance=candidate['acceptance'],
        coverage_evidence=evidence,coverage_checks=checks,qualified=all(checks.values()),
        source_hashes={p:source_sha(ROOT/p) for p in source_files()},binary_hashes={p.relative_to(ROOT).as_posix():sha(p) for p in (PARSER,BASELINE,COUNTER)},
        input_hashes=inputs,maps=maps,rows=rows,ratings_opened=False,
        exposure=reservation['exposure'],target_policy='All terminal source decisions and exact eligible rows sealed before any Rating target values. Public K/D/round discrepancy fails quality without row replacement; no final refit or gate changes.',
        feature_policy=candidate['feature_policy'],historical_failure_policy='CNL/APACStage2/SAL failures remain permanently consumed and unchanged.')
    private=DATA/'prelabel-quality-seal.json';immutable_write(private,result)
    identities=[dict(match_id=r['match_id'],game_id=r['game_id'],player_id=r['player_id'],player=r['player'],
        row_sha256=hashlib.sha256(json.dumps(r,sort_keys=True,separators=(',',':')).encode()).hexdigest()) for r in rows]
    immutable_write(FREEZE,result|dict(rows=identities,private_seal_sha256=sha(private)))
    print('FROZEN PRELABEL',evidence,checks,'qualified',result['qualified'],flush=True)


def read_frozen():
    public=json.loads(FREEZE.read_text(encoding='utf-8'));private_path=DATA/'prelabel-quality-seal.json'
    if sha(private_path)!=public['private_seal_sha256']:raise ValueError('Private feature seal changed')
    private=json.loads(private_path.read_text(encoding='utf-8'))
    if len(public['rows'])!=len(private['rows']):raise ValueError('Frozen row inventory changed')
    for k in private:
        if k!='rows' and public[k]!=private[k]:raise ValueError('Public/private freeze differs')
    for r,p in zip(private['rows'],public['rows']):
        if hashlib.sha256(json.dumps(r,sort_keys=True,separators=(',',':')).encode()).hexdigest()!=p['row_sha256']:raise ValueError('Frozen feature row changed')
    return private


def prepare_targets():
    if (DATA/'rating-targets-opened.json').exists() or RESULT.exists():raise ValueError('Final already consumed')
    clean_tree();frozen=read_frozen()
    if not frozen['qualified']:raise ValueError('Insufficient prospective coverage; targets stay unopened')
    targets={}
    for mid in sorted({r['match_id'] for r in frozen['rows']}):
        p=DATA/'targets'/f'{mid}.json';fetch(f'https://siege.gg/api/stats/matches/{mid}/player-stats',p);targets[str(mid)]=sha(p)
        print('Sealed raw target bytes',mid,flush=True);time.sleep(2)
    immutable_write(DATA/'target-byte-seal.json',dict(freeze_sha256=source_sha(FREEZE),targets=targets,ratings_projected=False))


def evaluate():
    marker=DATA/'rating-targets-opened.json'
    if RESULT.exists() or marker.exists():raise ValueError('Final already consumed; never reopen/refit/regrade')
    clean_tree();frozen=read_frozen()
    if not frozen['qualified']:raise ValueError('Insufficient prospective coverage; targets stay unopened')
    for p,d in frozen['source_hashes'].items():
        if source_sha(ROOT/p)!=d:raise ValueError('Frozen source changed: '+p)
    for group in ('binary_hashes','input_hashes'):
        for p,d in frozen[group].items():
            if sha(ROOT/p)!=d:raise ValueError('Frozen input changed: '+p)
    if source_sha(CANDIDATE)!=frozen['candidate_sha256'] or source_sha(RESERVE)!=frozen['reservation_sha256'] or source_sha(PLAN)!=frozen['plan_sha256']:raise ValueError('Frozen model/plan/reservation changed')
    subprocess.run(['git','merge-base','--is-ancestor',frozen['source_commit'],'HEAD'],cwd=ROOT,check=True)
    byte_seal=json.loads((DATA/'target-byte-seal.json').read_text(encoding='utf-8'))
    if byte_seal['freeze_sha256']!=source_sha(FREEZE) or {int(mid) for mid in byte_seal['targets']}!={r['match_id'] for r in frozen['rows']}:raise ValueError('Target inventory differs')
    for mid,d in byte_seal['targets'].items():
        if sha(DATA/'targets'/f'{mid}.json')!=d:raise ValueError('Target bytes changed')
    immutable_write(marker,dict(opened_at=datetime.now(timezone.utc).isoformat(),freeze_sha256=source_sha(FREEZE),
        source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()))
    targets={int(mid):json.loads((DATA/'targets'/f'{mid}.json').read_text(encoding='utf-8')) for mid in byte_seal['targets']}
    rows=[];details=[];quality=[]
    for row in frozen['rows']:
        t=targets[row['match_id']][str(row['game_id'])].get(str(row['player_id']))
        if t is None:quality.append(dict(game_id=row['game_id'],player=row['player'],reason='Missing sealed player target'));continue
        expected=tuple(sum(r[k] for r in row['rounds']) for k in ('kills','deaths'))
        if re_kd(t['kd'])!=expected or t['rounds']!=len(row['rounds']):quality.append(dict(game_id=row['game_id'],player=row['player'],reason='Public exact K/D or rounds differs from frozen primary quality'))
        rating=float(t['rating']);rows.append(row|dict(rating=rating))
        details.append(dict(match_id=row['match_id'],game_id=row['game_id'],player=row['player'],rating=rating,v2=row['v2_prediction'],v3=row['v3_prediction']))
    if not rows:raise ValueError('Consumed final has no evaluable targets; consumption marker retained')
    a=metrics(rows,[r['v2_prediction'] for r in rows]);b=metrics(rows,[r['v3_prediction'] for r in rows]);subgroups={}
    for name in ('objective_positive','kill_credit_affected'):
        subset=[r for r in rows if r[name]]
        subgroups[name]=dict(rows=len(subset),metrics=metrics(subset,[r['v3_prediction'] for r in subset]) if subset else None)
    checks=accuracy_checks(a,b,frozen['acceptance'],subgroups)|dict(public_quality=not quality and len(rows)==len(frozen['rows']))
    result=dict(event=frozen['event'],freeze_sha256=source_sha(FREEZE),target_hashes=byte_seal['targets'],rows=len(rows),baseline=a,candidate=b,
        subgroups=subgroups,checks=checks,passed=all(checks.values()),public_quality_issues=quality,details=details,final_event_consumed=True,production_deployed=False)
    immutable_write(RESULT,result)
    compact=result|dict(details='private',experiment_id='v3-native-apac-n-stage1-one-shot',result_sha256=sha(RESULT))
    with (ROOT/'research/experiment-log.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(compact)+'\n')
    (ROOT/'research/output/v3-native-final-apac1-result.md').write_text('# APAC North Stage1 one-shot Rating final\n\n'+json.dumps(compact,indent=2)+'\n',encoding='utf-8')
    print('ONE SHOT FINAL',result['passed'],'N',len(rows),'V2 MAE',a['mae'],'V3',json.dumps({k:v for k,v in b.items() if k!='worst'}),'CHECKS',checks,flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=('freeze','targets','evaluate'));args=ap.parse_args()
    {'freeze':freeze,'targets':prepare_targets,'evaluate':evaluate}[args.action]()
