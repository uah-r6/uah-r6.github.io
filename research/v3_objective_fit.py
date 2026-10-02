"""One deduplicated development comparison: frozen v2 versus +verified objectives."""
from datetime import datetime, timezone
import hashlib
import json
from statistics import median

from fit_models import FEATURES, design, evaluate, fit_ridge, predict
from objective_transition_probe import ROOT
from uah_guarded_actor_readonly import snapshot


def paired_input(row):
    return row|dict(rounds=row['paired_v2_rounds'])


def development_groups(rows,frozen):
    allowed=set(frozen['train_events'])|{frozen['development_event']}
    if any(r['event'] not in allowed or r['reserved_for_final_test'] for r in rows):
        raise ValueError('Final/reserved data must never enter this development dataset')
    if any(r['fit_eligible'] and not r['objective_map_complete'] for r in rows):
        raise ValueError('Missing objective actors cannot be encoded as verified zero')
    train=[paired_input(r) for r in rows if r['fit_eligible'] and r['event'] in frozen['train_events']]
    dev=[paired_input(r) for r in rows if r['fit_eligible'] and r['event']==frozen['development_event']]
    if not train or not dev:raise ValueError('Clean objective-complete train and development rows required')
    return train,dev


def metrics(rows,guesses):
    result=evaluate(rows,guesses)
    result['median_abs_error']=median(abs(g-r['rating']) for r,g in zip(rows,guesses))
    return result


def main():
    protected=snapshot()
    dataset=ROOT/'data/research/experiments/v3-player-maps.jsonl'
    dataset_sha=hashlib.sha256(dataset.read_bytes()).hexdigest()
    frozen_path=ROOT/'research/frozen-rating-candidate.json'
    frozen_sha=hashlib.sha256(frozen_path.read_bytes()).hexdigest()
    frozen=json.loads(frozen_path.read_text());baseline=frozen['model']
    plan_path=ROOT/'research/v3-objective-development-plan.json'
    plan_sha=hashlib.sha256(plan_path.read_bytes().replace(b'\r\n',b'\n')).hexdigest()
    log=ROOT/'research/experiment-log.jsonl'
    kind='siege_style_v3_verified_objectives_first_development'
    previous=[json.loads(l) for l in log.read_text(encoding='utf-8').splitlines()]
    duplicate=[r for r in previous if r.get('experiment_kind')==kind and r.get('dataset_sha256')==dataset_sha]
    if duplicate:
        print('Existing deliberate experiment; no refit/log append:',duplicate[-1]['experiment_id'])
        return
    rows=[json.loads(l) for l in dataset.read_text(encoding='utf-8').splitlines()]
    train,dev=development_groups(rows,frozen)
    original_path=ROOT/'data/research/experiments/player_maps.jsonl'
    original_sha=hashlib.sha256(original_path.read_bytes()).hexdigest()
    original={(r['match_id'],r['game_id'],r['player_id']):r for r in
              [json.loads(l) for l in original_path.read_text(encoding='utf-8').splitlines()]}
    # Prove the frozen eight inputs are identical, not merely similarly named.
    for r in train+dev:
        old=original[r['match_id'],r['game_id'],r['player_id']]
        if design(r,{},'raw')[:-1]!=design(old,{},'raw')[:-1]:raise ValueError('A second v2 feature changed')
        if abs(predict(baseline,r,{})-predict(baseline,old,{}))>1e-12:raise ValueError('Frozen v2 prediction changed')
    candidate=fit_ridge(train,{},'raw',alpha=1.0)
    evaluations={}
    heavy=[]
    for group,data in (('train',train),('development',dev)):
        a=[predict(baseline,r,{}) for r in data];b=[predict(candidate,r,{}) for r in data]
        evaluations[group]=dict(frozen_v2=metrics(data,a),v3_objectives=metrics(data,b))
        for r,ga,gb in zip(data,a,b):
            n=r['derived']['plants']+r['derived']['disables']
            if n>=2:
                heavy.append(dict(group=group,match_id=r['match_id'],game_id=r['game_id'],player=r['player'],
                    map=r['map'],objectives=n,rounds=r['derived']['rounds'],target=r['rating'],
                    v2=ga,v3=gb,v2_residual=ga-r['rating'],v3_residual=gb-r['rating'],
                    absolute_error_change=abs(gb-r['rating'])-abs(ga-r['rating'])))
    drift={name:dict(v2_standardized=baseline['weights_standardized'][name],
        v3_standardized=candidate['weights_standardized'][name],
        v2_raw=baseline['weights_standardized'][name]/baseline['scales'][name],
        v3_raw=candidate['weights_standardized'][name]/candidate['scales'][name],
        raw_change=candidate['weights_standardized'][name]/candidate['scales'][name]-baseline['weights_standardized'][name]/baseline['scales'][name]) for name in FEATURES}
    now=datetime.now(timezone.utc)
    record=dict(experiment_id=now.strftime('v3-objectives-%Y%m%dT%H%M%SZ'),experiment_kind=kind,
        created_at=now.isoformat(),status='development_only_no_final_evaluation',dataset_sha256=dataset_sha,
        original_dataset_sha256=original_sha,frozen_v2_sha256=frozen_sha,plan_sha256=plan_sha,
        train_rows=len(train),development_rows=len(dev),train_events=frozen['train_events'],
        development_event=frozen['development_event'],original_v2_train_rows=frozen['train_rows'],
        original_v2_development_rows=frozen['development_rows'],candidate_model=candidate,
        baseline_model_unchanged=baseline,metrics=evaluations,coefficient_drift=drift,
        intercept_drift=dict(v2=baseline['intercept'],v3=candidate['intercept'],change=candidate['intercept']-baseline['intercept']),
        objective_raw_coefficient=drift['objectives']['v3_raw'],objective_heavy_player_residuals=heavy,
        eight_feature_input_parity_verified=True,corrected_kost_in_first_comparison=False,
        final_test_evaluated=False,new_final_event_reserved=False,production_deployed=False,
        limitations=['Development EWC previously consumed; only objective-complete subset evaluated.',
            'Candidate train subset differs from original v2 train; coefficient drift is not purely feature effect.',
            'Reviewed actor labels are mixed-source; structural resolved does not mean independent VOD verification.',
            'A NEW untouched event and a new freeze are mandatory before any final v3 decision.'])
    if snapshot()!=protected or hashlib.sha256(original_path.read_bytes()).hexdigest()!=original_sha or hashlib.sha256(frozen_path.read_bytes()).hexdigest()!=frozen_sha:
        raise ValueError('Live data or frozen v2 changed')
    output=ROOT/'data/research/experiments/v3-objective-first-model.json'
    output.write_text(json.dumps(record,indent=2),encoding='utf-8')
    with log.open('a',encoding='utf-8') as f:f.write(json.dumps(record)+'\n')
    lines=['# First v3 verified-objective development comparison','',
        f'Experiment`{record["experiment_id"]}`. Fixed raw standardized ridge alpha1, no parameter search. '
        f'Train{len(train)} rows versus original v2{frozen["train_rows"]}; EWC development{len(dev)} versus original{frozen["development_rows"]}. '
        'Both September final events excluded. Maps with unresolved objective actors excluded, not treated as zero.','',
        'A is the exact frozen v2 model and coefficients. B fits the exact same raw family plus verified '
        'plants+disables/round. Every eight-feature input and baseline prediction is checked against '
        'the original observation. Recomputed KOST is reported in the derivation report and kept out of '
        'this one-feature experiment. The candidate train subset differs, so drift can also reflect '
        'sample selection. Deployed v2 and its final MAE0.03623 are unchanged.','',
        '| Split / model | N | MAE | RMSE | Median AE | Max AE | within .01 | .02 | .03 | .05 | .10 |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for group,pair in evaluations.items():
        for name,m in pair.items():
            lines.append(f"| {group}/{name} | {m['n']} | {m['mae']:.5f} | {m['rmse']:.5f} | {m['median_abs_error']:.5f} | {m['max_abs_error']:.5f} | "+
                ' | '.join(f"{m[f'within_{t:.2f}']:.1%}" for t in (.01,.02,.03,.05,.10))+' |')
    lines+=['','## Every coefficient drift','','| Feature | v2 standardized | v3 standardized | v2 raw | v3 raw | Raw change |',
        '| --- | ---: | ---: | ---: | ---: | ---: |']
    for name,d in drift.items():lines.append(f"| {name} | {d['v2_standardized']:.8f} | {d['v3_standardized']:.8f} | {d['v2_raw']:.8f} | {d['v3_raw']:.8f} | {d['raw_change']:.8f} |")
    lines+=[f"\nStandardized intercept: {baseline['intercept']:.8f} -> {candidate['intercept']:.8f}.",
        '', '## Objective-heavy player-map residual changes','',
        'Objective-heavy means at least2 verified objectives on the map; selected from replay features, not errors. '
        'Residual is prediction minus target; negative AE change improves. Every qualifying row is listed.','',
        '| Split / match / game / player | Objectives | v2 residual | v3 residual | AE change |',
        '| --- | ---: | ---: | ---: | ---: |']
    for r in heavy:lines.append(f"| {r['group']}/{r['match_id']}/{r['game_id']}/{r['player']} | {r['objectives']} | {r['v2_residual']:.5f} | {r['v3_residual']:.5f} | {r['absolute_error_change']:.5f} |")
    lines+=['','## Interpretation and next gate','',
        'This is one deliberate development experiment, not a final result or deployment approval. '
        'Inspect objective coefficient stability and sample exclusion before choosing a new frozen candidate. '
        'A different untouched event must be metadata-reserved before its objective/Rating outcomes are examined. '
        'Never use the old NA Stage2 set as a new final holdout. No v3 runtime model/default is installed.','',
        f'{len(protected)} protected live file hashes, original dataset/frozenv2 hashes unchanged. '
        'Reproduce `.venv/Scripts/python.exe research/v3_objective_fit.py`; a matching dataset/experiment '
        'is deduplicated and never refit or appended twice.','']
    (ROOT/'research/output/v3-objective-first-development.md').write_text('\n'.join(lines),encoding='utf-8')
    print(record['experiment_id'],'train',len(train),'dev',len(dev),
        'MAE',evaluations['development']['frozen_v2']['mae'],evaluations['development']['v3_objectives']['mae'],
        'objective_raw',record['objective_raw_coefficient'],flush=True)


if __name__=='__main__':main()
