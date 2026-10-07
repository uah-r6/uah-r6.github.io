"""Freeze the complete prospective CNL cohort, then evaluate exactly once."""
import argparse
from collections import Counter
from datetime import datetime,timezone
import json
from pathlib import Path
import subprocess
import sys
import time

from credited_late_history_development import immutable_write
from fit_models import predict
from r6stats.kill_credit import validate_map_credit
from r6stats.parser.models import Match
from uah_comparison import player_rounds
from v3_cnl_metadata import DATA as METADATA,fetch
from v3_cnl_pipeline import DATA,PARSER,BASELINE,COUNTER,official_primary
from v3_cnl_reserve import RESERVE
from v3_credited_derive import bind_lan_counts
from v3_final_reserve import ROOT,sha,source_sha
from v3_objective_fit import metrics

FREEZE=ROOT/'research/v3-credited-final-cnl-freeze.json'
RESULT=DATA/'one-shot-result.json'


def source_files():
    files=subprocess.check_output(['git','ls-files'],cwd=ROOT,text=True).splitlines()
    return [p for p in files if Path(p).suffix in ('.py','.go') or p in ('third_party/siege-dissect/go.mod','third_party/siege-dissect/go.sum')]


def clean_tree():
    if subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip():raise ValueError('Clean committed working tree required')


def coverage(rows,gate):
    evidence=dict(clean_rows=len(rows),clean_maps=len({(r['match_id'],r['game_id']) for r in rows}),
        distinct_rosters=len({r['roster_id'] for r in rows}),objective_positive_rows=sum(r['objective_positive'] for r in rows))
    checks={k:evidence[k]>=gate['minimum_'+k] for k in evidence}
    return evidence,checks


def freeze():
    if FREEZE.exists():raise ValueError('Final freeze already exists; never replace')
    if (DATA/'rating-targets-opened.json').exists():raise ValueError('Rating already consumed')
    clean_tree();subprocess.run([sys.executable,str(ROOT/'research/verify_production_kill_checkpoint.py')],check=True)
    candidate_path=ROOT/'research/v3-credited-candidate.json';candidate=json.loads(candidate_path.read_text(encoding='utf-8'))
    baseline=json.loads((ROOT/'research/frozen-rating-candidate.json').read_text(encoding='utf-8'))['model']
    plan=json.loads((ROOT/'research/v3-credited-development-plan.json').read_text(encoding='utf-8'));gate=plan['prospective_final_gate']
    reservation=json.loads(RESERVE.read_text(encoding='utf-8'));rows=[];maps=[];inputs={};issues=Counter()
    for source in [s for s in reservation['matches'] if s['selected']]:
        path=DATA/str(source['official_match_id'])/'prelabel-replays.json'
        record=json.loads(path.read_text(encoding='utf-8'));inputs[path.relative_to(ROOT).as_posix()]=sha(path)
        if record['reservation_sha256']!=source_sha(RESERVE) or record['parser_sha256']!=sha(PARSER) or record['baseline_parser_sha256']!=sha(BASELINE) or record['counter_sha256']!=sha(COUNTER):raise ValueError('Collection provenance changed')
        primary,primary_path=official_primary(source)
        if sha(primary_path)!=record['primary_sha256']:raise ValueError('Primary evidence changed')
        inputs[primary_path.relative_to(ROOT).as_posix()]=sha(primary_path)
        metadata_path=METADATA/f"cnl1-metadata-{source['siegegg_match_id']}.json"
        if sha(metadata_path)!=record['metadata_sha256']:raise ValueError('Metadata changed')
        inputs[metadata_path.relative_to(ROOT).as_posix()]=sha(metadata_path)
        for m in record['maps']:
            extra=[]
            if m['rows']:
                match=Match.from_dict(m['normalized']);original=Match.from_dict(m['original_normalized'])
                inputs.update(m['inputs']);credit_records=[]
                for item in m['physical_mapping']:
                    rec=ROOT/item['replay_path']
                    if sha(rec)!=item['sha256']:raise ValueError('Physical replay changed')
                    inputs[item['replay_path']]=item['sha256']
                    raw_path=DATA/'raw'/(item['sha256']+'.json');obs=json.loads(raw_path.read_text(encoding='utf-8'))
                    if obs['executable_sha256']!=sha(COUNTER) or obs['replay_sha256']!=item['sha256']:raise ValueError('Counter evidence changed')
                    credit_records.append(dict(logical_round=item['logical_round'],physical_round=item['physical_round'],segment=item['folder'],credit=obs['credit']))
                credit=validate_map_credit(credit_records);counts=bind_lan_counts(match,credit) if credit['complete'] else None
                occurrence_counts=Counter(o.kind for r in match.rounds for o in r.objective_occurrences)
                trusted_counts=Counter(o.kind for r in match.rounds for o in r.objective_occurrences if o.actor and o.actor_source==o.actor_reason=='completing_timer_owner_v1')
                actual_counts=Counter(o.kind for r in match.rounds for o in r.objectives)
                if actual_counts!=trusted_counts or occurrence_counts!=trusted_counts:extra.append('Entire map lacks exclusively complete core objective credits')
                primary_games=[g for g in primary['games'] if g['rounds'] and len(g['rounds'])==m['rounds'] and g['map']['name'].lower().replace(' ','').replace('kafedostoyevsky','kafe')==m['map'].lower().replace(' ','').replace('kafedostoyevsky','kafe')]
                if len(primary_games)!=1:raise ValueError('Unique independently completed primary map missing')
                people={p['id']:p for t in primary_games[0]['teams'] for p in t['players']}
                for row in m['rows']:
                    player=next(p for p in match.rounds[0].players if p.username==row['player'])
                    derived=player_rounds(match,player.key)
                    if counts is not None:
                        for r in derived:
                            r['kills']=counts[r['number']][player.key]
                            r['kost_rounds']=int(bool(r['kills'] or r['plants'] or r['disables'] or r['survived'] or r['deaths_traded']))
                    if derived!=row['rounds'] or player_rounds(original,player.key)!=row['original_v2_rounds']:raise ValueError('Frozen feature reconstruction differs')
                    if predict(candidate['model'],row,{})!=row['v3_prediction'] or predict(baseline,row|dict(rounds=row['original_v2_rounds']),{})!=row['v2_prediction']:raise ValueError('Candidate/exact-v2 prediction changed')
                if all(r['primary_player_id'] for r in m['rows']) and m['objective_complete']:
                    for kind,field in (('plants','diffuserPlanted'),('disables','diffuserDisabled')):
                        # Stronger prelabel objective audit; mismatch refuses the
                        # whole map, never changes a replay actor from labels.
                        for row in m['rows']:
                            expected=people[row['primary_player_id']]['stats'][field]['count']
                            if sum(r[kind] for r in row['rounds'])!=expected:extra.append('Independent primary objective totals mismatch');break
            eligible=[r for r in m['rows'] if r['fit_eligible'] and not extra]
            rows+=eligible
            map_issues=sorted(set(extra+[i for r in m['rows'] for i in r['quality_issues']]+([m['whole_map_refusal']] if m.get('whole_map_refusal') else [])))
            issues.update(map_issues)
            maps.append(dict(official_match_id=source['official_match_id'],game_id=m['game_id'],map=m['map'],clean_rows=len(eligible),issues=map_issues))
    evidence,checks=coverage(rows,gate)
    result=dict(event=reservation['event'],created_at=datetime.now(timezone.utc).isoformat(),
        source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),working_tree_clean=True,
        candidate_sha256=source_sha(candidate_path),candidate=candidate['model'],baseline=baseline,
        reservation_sha256=source_sha(RESERVE),plan_sha256=source_sha(ROOT/'research/v3-credited-development-plan.json'),
        acceptance=gate,coverage_evidence=evidence,coverage_checks=checks,qualified=all(checks.values()),
        source_hashes={p:source_sha(ROOT/p) for p in source_files()},
        binary_hashes={p.relative_to(ROOT).as_posix():sha(p) for p in (PARSER,BASELINE,COUNTER)},
        input_hashes=inputs,maps=maps,rows=rows,ratings_opened=False,
        target_policy='All eligible primary-KD-verified rows frozen before player-stat downloads; any public exact-KD/round discrepancy fails final quality without selecting replacement rows. No target-dependent alias or eligibility changes.',
        baseline_policy='Exact e7c2 v2 occurrence-era Go binary; original finisher KPR/MK/KOST/objective inputs retained. Candidate uses current supported core actors/credited counts and corrected KOST; other event features identical.',
        exposure='CNLStage1 schedules and metadata only; no Rating targets opened. CNLStage2 excluded due known search exposure.')
    immutable_write(DATA/'prelabel-quality-seal.json',result);immutable_write(FREEZE,result)
    lines=['# Prospective CNL Stage 1 corrected-count final seal','',f'All27selected BO3 archives have terminal decisions. Coverage: {evidence}; gates: {checks}.','',
        'Candidate, exact-v2 baseline, all rows, excluded maps, source commit and input/binary hashes are sealed before any player-stat targets. Strong independent primary objective audit refuses entire mismatched maps. No Rating values opened.','',
        '| Official / game | Map | Clean rows | Reasons |','| --- | --- | ---: | --- |']
    lines += [f"| {m['official_match_id']}/{m['game_id']} | {m['map']} | {m['clean_rows']} | {'; '.join(m['issues'])} |" for m in maps]
    (ROOT/'research/output/v3-credited-final-cnl-prelabel.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('FROZEN PRELABEL',evidence,checks,'qualified',result['qualified'],flush=True)


def accuracy_checks(a,b,gate,subgroups):
    checks=dict(mae=b['mae']<=gate['max_mae'],relative_mae_improvement=(a['mae']-b['mae'])/a['mae']>=gate['relative_mae_improvement_vs_exact_v2'],
        within_005=b['within_0.05']>=gate['within_0_05'],rmse=b['rmse']<=a['rmse'],max_error=b['max_abs_error']<=gate['max_absolute_error'])
    for name,group in subgroups.items():checks[name]=group['rows']<10 or group['metrics']['mae']<=.05
    return checks


def prepare_targets():
    """Stage complete raw targets after the row freeze, without decoding them.

    HTTP failures are retryable collection problems, not a consumed one-shot
    evaluation. The scientific consumption marker is written only once every
    frozen target file has been successfully cached and hashed.
    """
    frozen=json.loads(FREEZE.read_text(encoding='utf-8'))
    if not frozen['qualified']:raise ValueError('Insufficient prelabel coverage; keep targets unopened')
    if (DATA/'rating-targets-opened.json').exists():raise ValueError('Final already consumed')
    clean_tree();targets={}
    for mid in sorted({r['match_id'] for r in frozen['rows']}):
        path=DATA/'targets'/f'{mid}.json'
        fetch(f'https://siege.gg/api/stats/matches/{mid}/player-stats',path)
        targets[str(mid)]=sha(path)
        print('Cached sealed target bytes',mid,flush=True);time.sleep(3)
    immutable_write(DATA/'target-byte-seal.json',dict(freeze_sha256=source_sha(FREEZE),targets=targets,ratings_projected=False))


def evaluate():
    marker=DATA/'rating-targets-opened.json'
    if RESULT.exists() or marker.exists():raise ValueError('Final event already consumed; never reopen/refit/regrade')
    clean_tree();frozen=json.loads(FREEZE.read_text(encoding='utf-8'))
    if not frozen['qualified']:raise ValueError('Prospective coverage insufficient; keep Ratings unopened')
    for p,d in frozen['source_hashes'].items():
        if source_sha(ROOT/p)!=d:raise ValueError('Frozen source changed: '+p)
    for group in ('binary_hashes','input_hashes'):
        for p,d in frozen[group].items():
            if sha(ROOT/p)!=d:raise ValueError('Frozen input changed: '+p)
    if source_sha(ROOT/'research/v3-credited-candidate.json')!=frozen['candidate_sha256'] or source_sha(RESERVE)!=frozen['reservation_sha256']:raise ValueError('Candidate/reservation changed')
    subprocess.run(['git','merge-base','--is-ancestor',frozen['source_commit'],'HEAD'],cwd=ROOT,check=True)
    byte_seal=json.loads((DATA/'target-byte-seal.json').read_text(encoding='utf-8'))
    if byte_seal['freeze_sha256']!=source_sha(FREEZE) or {int(mid) for mid in byte_seal['targets']}!={r['match_id'] for r in frozen['rows']}:raise ValueError('Target byte seal differs')
    for mid,digest in byte_seal['targets'].items():
        if sha(DATA/'targets'/f'{mid}.json')!=digest:raise ValueError('Sealed target bytes changed')
    immutable_write(marker,dict(opened_at=datetime.now(timezone.utc).isoformat(),freeze_sha256=source_sha(FREEZE),source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()))
    targets={int(mid):json.loads((DATA/'targets'/f'{mid}.json').read_text(encoding='utf-8')) for mid in byte_seal['targets']}
    hashes=byte_seal['targets']
    rows=[];details=[];quality=[]
    for row in frozen['rows']:
        target=targets[row['match_id']][str(row['game_id'])].get(str(row['player_id']))
        if target is None:quality.append(dict(player=row['player'],game_id=row['game_id'],reason='Missing frozen public identity target'));continue
        kd=re_kd(target['kd'])
        expected=tuple(sum(r[k] for r in row['rounds']) for k in ('kills','deaths'))
        if kd!=expected or target['rounds']!=len(row['rounds']):quality.append(dict(player=row['player'],game_id=row['game_id'],reason='Public exact K/D or rounds differs from frozen primary quality',expected=list(expected),public=target['kd']))
        value=float(target['rating']);rows.append(row|dict(rating=value))
        details.append(dict(match_id=row['match_id'],game_id=row['game_id'],player=row['player'],rating=value,v2=row['v2_prediction'],v3=row['v3_prediction']))
    a=metrics(rows,[r['v2_prediction'] for r in rows]);b=metrics(rows,[r['v3_prediction'] for r in rows])
    subgroups={}
    for name in ('objective_positive','kill_credit_affected'):
        subset=[r for r in rows if r[name]]
        subgroups[name]=dict(rows=len(subset),metrics=metrics(subset,[r['v3_prediction'] for r in subset]) if subset else None)
    checks=accuracy_checks(a,b,frozen['acceptance'],subgroups)|dict(public_quality=not quality and len(rows)==len(frozen['rows']))
    result=dict(event=frozen['event'],freeze_sha256=source_sha(FREEZE),target_hashes=hashes,rows=len(rows),
        baseline=a,candidate=b,subgroups=subgroups,checks=checks,passed=all(checks.values()),
        public_quality_issues=quality,details=details,final_event_consumed=True,production_deployed=False)
    immutable_write(RESULT,result)
    with (ROOT/'research/experiment-log.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(result|dict(details='private',experiment_id='v3-credited-cnl-stage1-one-shot',result_sha256=sha(RESULT)))+'\n')
    (ROOT/'research/output/v3-credited-final-cnl-result.md').write_text('# CNL Stage 1 one-shot Rating final\n\n'+json.dumps({k:v for k,v in result.items() if k!='details'},indent=2)+'\n',encoding='utf-8')
    print('ONE SHOT FINAL',result['passed'],'N',len(rows),'V2',a,'V3',b,'CHECKS',checks,flush=True)


def re_kd(value):
    import re
    match=re.fullmatch(r'(\d+)-(\d+)(?:\s+\([+-]?\d+\))?',value)
    return tuple(map(int,match.groups())) if match else None


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=('freeze','targets','evaluate'));args=ap.parse_args()
    {'freeze':freeze,'targets':prepare_targets,'evaluate':evaluate}[args.action]()
