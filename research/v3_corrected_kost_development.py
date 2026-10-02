"""One separate objective-related development study, never consumed final refit."""
from datetime import datetime,timezone
import json
from pathlib import Path

from fit_models import FEATURES,design,fit_ridge,predict
from v3_objective_fit import development_groups,metrics
from v3_final_reserve import ROOT,sha,source_sha
from uah_guarded_actor_readonly import snapshot


def groups(rows,frozen):
    # Apply existing final-exclusion/missing-actor gates first.
    old_train,old_dev=development_groups(rows,frozen)
    eligible=[r for r in rows if r['fit_eligible']]
    train=[r for r in eligible if r['event'] in frozen['train_events']]
    dev=[r for r in eligible if r['event']==frozen['development_event']]
    if (len(train),len(dev))!=(len(old_train),len(old_dev)):raise ValueError('Quality sample changed')
    for r in train+dev:
        paired=r|dict(rounds=r['paired_v2_rounds'])
        a,b=design(paired,{},'raw'),design(r,{},'raw')
        if any(x!=y for i,(x,y) in enumerate(zip(a,b)) if FEATURES[i]!='kost'):
            raise ValueError('Unrelated feature changed')
    return train,dev


def main():
    protected=snapshot()
    original_files=[ROOT/'data/research/experiments/player_maps.jsonl',ROOT/'research/frozen-rating-candidate.json',
        ROOT/'research/v3-frozen-objective-candidate.json',ROOT/'data/research/v3-final-apac-n-stage2/one-shot-result.json',
        ROOT/'data/research/experiments/v3-objective-first-model.json']
    original_hashes={str(p.relative_to(ROOT)):sha(p) for p in original_files}
    data=ROOT/'data/research/experiments/v3-player-maps.jsonl';digest=sha(data)
    log=ROOT/'research/experiment-log.jsonl';kind='siege_style_v3_corrected_kost_development'
    previous=[json.loads(l) for l in log.read_text(encoding='utf-8').splitlines()]
    existing=[r for r in previous if r.get('experiment_kind')==kind and r.get('dataset_sha256')==digest]
    if existing:
        print('Existing separate experiment; no refit:',existing[-1]['experiment_id']);return
    frozen=json.loads((ROOT/'research/frozen-rating-candidate.json').read_text(encoding='utf-8'))
    rows=[json.loads(l) for l in data.read_text(encoding='utf-8').splitlines()]
    train,dev=groups(rows,frozen);baseline=frozen['model'];candidate=fit_ridge(train,{},'raw',alpha=1)
    evaluations={};heavy=[];kost=[]
    for split,group in [('train',train),('development',dev)]:
        a=[predict(baseline,r,{}) for r in group];b=[predict(candidate,r,{}) for r in group]
        evaluations[split]=dict(exact_v2_corrected_inputs=metrics(group,a),v3_corrected_inputs=metrics(group,b))
        for r,ga,gb in zip(group,a,b):
            original_kost=sum(x['kost_rounds'] for x in r['paired_v2_rounds'])
            corrected=sum(x['kost_rounds'] for x in r['rounds'])
            if original_kost!=corrected:kost.append(dict(split=split,player=r['player'],match_id=r['match_id'],game_id=r['game_id'],original=original_kost,corrected=corrected,rounds=len(r['rounds'])))
            n=r['derived']['plants']+r['derived']['disables']
            if n>=2:heavy.append(dict(split=split,player=r['player'],match_id=r['match_id'],game_id=r['game_id'],objectives=n,
                target=r['rating'],v2=ga,v3=gb,absolute_error_change=abs(gb-r['rating'])-abs(ga-r['rating'])))
    drift={n:dict(v2_raw=baseline['weights_standardized'][n]/baseline['scales'][n],
        v3_raw=candidate['weights_standardized'][n]/candidate['scales'][n],
        change=candidate['weights_standardized'][n]/candidate['scales'][n]-baseline['weights_standardized'][n]/baseline['scales'][n]) for n in FEATURES}
    record=dict(experiment_id=datetime.now(timezone.utc).strftime('v3-corrected-kost-%Y%m%dT%H%M%SZ'),
        experiment_kind=kind,status='development_only_new_final_required',dataset_sha256=digest,
        plan_sha256=source_sha(ROOT/'research/v3-corrected-kost-development-plan.json'),
        code_sha256=source_sha(Path(__file__)),model=candidate,baseline=frozen['model'],
        train_rows=len(train),development_rows=len(dev),metrics=evaluations,coefficient_drift=drift,
        corrected_kost_changes=kost,objective_heavy=heavy,final_events_used=False,production_deployed=False,
        original_artifact_hashes=original_hashes,
        limitation='Same small objective-complete subset as the first study; distinct input contract. Cannot compare different-input MAE changes as solely coefficient improvement. Consumed final errors never enter this fit or evaluation.')
    if snapshot()!=protected or any(sha(ROOT/p)!=v for p,v in original_hashes.items()):raise ValueError('Original/live artifact changed')
    (ROOT/'data/research/experiments/v3-corrected-kost-model.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    with log.open('a',encoding='utf-8') as f:f.write(json.dumps(record)+'\n')
    lines=['# Separate v3 development: verified objectives with definition-correct KOST','',
        f"Experiment `{record['experiment_id']}`. Train{len(train)}, EWC development{len(dev)}; fixed ridge alpha1, no search. "
        'A uses exact frozen v2 weights, B fits the same nine-family raw design. Both arms use fully objective-corrected KOST. '
        'No consumed final rows/errors used. The first v3 contract/result and failed APAC gate remain immutable.','',
        '| Split / model | N | MAE | RMSE | Median AE | Max AE | within .01 | .02 | .03 | .05 | .10 |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for split,pair in evaluations.items():
        for name,m in pair.items():lines.append(f"| {split}/{name} | {m['n']} | {m['mae']:.5f} | {m['rmse']:.5f} | {m['median_abs_error']:.5f} | {m['max_abs_error']:.5f} | "+' | '.join(f"{m[f'within_{t:.2f}']:.1%}" for t in (.01,.02,.03,.05,.10))+' |')
    lines+=['','## All coefficient drift','','| Feature | v2 raw | v3 raw | Change |','| --- | ---: | ---: | ---: |']
    for n,d in drift.items():lines.append(f"| {n} | {d['v2_raw']:.8f} | {d['v3_raw']:.8f} | {d['change']:+.8f} |")
    lines+=['','## Every KOST input correction','','| Split / player / match / game | Original | Corrected | Rounds |','| --- | ---: | ---: | ---: |']
    for r in kost:lines.append(f"| {r['split']}/{r['player']}/{r['match_id']}/{r['game_id']} | {r['original']} | {r['corrected']} | {r['rounds']} |")
    lines+=['','## Every objective-heavy residual change','','| Split / player / match / game | Objectives | v2 | v3 | Target | AE change |','| --- | ---: | ---: | ---: | ---: | ---: |']
    for r in heavy:lines.append(f"| {r['split']}/{r['player']}/{r['match_id']}/{r['game_id']} | {r['objectives']} | {r['v2']:.5f} | {r['v3']:.5f} | {r['target']:.2f} | {r['absolute_error_change']:+.5f} |")
    lines+=['',record['limitation'],'','A genuinely new event and another prospective freeze are required before any future final. No automatic deployment; live v2/SQLite/archives/public JSON unchanged. Fit deduplicates the deliberate experiment; do not repeatedly refit.','']
    (ROOT/'research/output/v3-corrected-kost-development.md').write_text('\n'.join(lines),encoding='utf-8')
    print(record['experiment_id'],'devMAE',evaluations['development']['exact_v2_corrected_inputs']['mae'],evaluations['development']['v3_corrected_inputs']['mae'],'objective',drift['objectives']['v3_raw'],'KOSTchanged',len(kost),flush=True)


if __name__=='__main__':main()
