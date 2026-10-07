"""One predeclared broad event-fold experiment; no new final event is opened."""
from collections import defaultdict
from copy import deepcopy
from datetime import datetime,timezone
import json
from pathlib import Path
import statistics
import subprocess
import sys

from fit_models import FEATURES,fit_ridge,predict
from v3_objective_fit import metrics
from v3_credited_derive import DATA
from v3_final_reserve import ROOT,sha,source_sha
from credited_late_history_development import immutable_write


def fit(rows, objectives):
    prepared=deepcopy(rows)
    if not objectives:
        for r in prepared:
            for round_ in r['rounds']:
                round_['plants']=round_['disables']=0
    return fit_ridge(prepared,{},'raw',alpha=1)


def baseline_row(row):
    return row|dict(rounds=row['original_v2_rounds'])


def raw_coefficients(model):
    values={n:model['weights_standardized'][n]/model['scales'][n] for n in FEATURES}
    return dict(coefficients=values,intercept=model['intercept']-sum(values[n]*model['means'][n] for n in FEATURES))


def folds(rows):
    events=sorted({r['event'] for r in rows})
    for event in events:
        train=[r for r in rows if r['event']!=event]
        validation=[r for r in rows if r['event']==event]
        if not train or not validation:raise ValueError('Whole-event folds require training and validation')
        yield event,train,validation


def main():
    subprocess.run([sys.executable,str(ROOT/'research/verify_production_kill_checkpoint.py')],check=True)
    result_path=DATA/'experiment.json'
    if result_path.exists():
        print('Deliberate experiment already preserved; no refit or log append');return
    dataset_path=DATA/'dataset.json';dataset=json.loads(dataset_path.read_text(encoding='utf-8'))
    rows=[r for r in dataset['rows'] if r['fit_eligible']]
    if any(not r['consumed_development'] or r['reserved_for_final_test'] for r in rows):raise ValueError('New final or UAH rows in development')
    if any(not r['credited_map_complete'] or not r['objective_map_complete'] for r in rows):raise ValueError('Missing features encoded as zero')
    if len({(r['match_id'],r['game_id'],r['player_id']) for r in rows})!=len(rows):raise ValueError('Duplicate development identities')
    plan_path=ROOT/'research/v3-credited-development-plan.json';plan=json.loads(plan_path.read_text(encoding='utf-8'))
    baseline=json.loads((ROOT/'research/frozen-rating-candidate.json').read_text(encoding='utf-8'))['model']
    marker=dict(dataset_sha256=sha(dataset_path),plan_sha256=source_sha(plan_path),source_sha256=source_sha(Path(__file__)),
        source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        models=plan['models'],folds=sorted({r['event'] for r in rows}),new_final_targets_opened=False)
    immutable_write(DATA/'fit-reservation.json',marker)
    pooled=defaultdict(list);fold_reports=[];pooled_rows=[];fold_models=[]
    for event,train,validation in folds(rows):
        models={'corrected_eight':fit(train,False),'corrected_nine_objectives':fit(train,True)}
        guesses={'exact_frozen_v2_original':[predict(baseline,baseline_row(r),{}) for r in validation],
                 'frozen_v2_corrected':[predict(baseline,r,{}) for r in validation]}
        guesses.update({name:[predict(model,r,{}) for r in validation] for name,model in models.items()})
        scored={name:metrics(validation,p) for name,p in guesses.items()}
        fold_reports.append(dict(event=event,train_rows=len(train),validation_rows=len(validation),metrics=scored))
        fold_models.append(dict(event=event,models=models,raw_coefficients={n:raw_coefficients(m) for n,m in models.items()}))
        pooled_rows+=validation
        for name,p in guesses.items():pooled[name]+=p
        print('EVENT',event,'N',len(validation),{n:(round(m['mae'],5),round(m['within_0.05'],3)) for n,m in scored.items()},flush=True)
    summary={name:metrics(pooled_rows,p) for name,p in pooled.items()}
    models={'corrected_eight':fit(rows,False),'corrected_nine_objectives':fit(rows,True)}
    subgroups={};residuals={}
    for name,guesses in pooled.items():
        groups={'objective_positive':[i for i,r in enumerate(pooled_rows) if any(x['plants'] or x['disables'] for x in r['rounds'])],
                'kill_credit_affected':[i for i,r in enumerate(pooled_rows) if r['kill_credit_affected']]}
        subgroups[name]={group:metrics([pooled_rows[i] for i in indices],[guesses[i] for i in indices]) if indices else None for group,indices in groups.items()}
        errors=[g-r['rating'] for r,g in zip(pooled_rows,guesses)];ordered=sorted(errors)
        residuals[name]=dict(mean=statistics.mean(errors),median=statistics.median(errors),
            quantiles={str(p):ordered[min(len(ordered)-1,int((len(ordered)-1)*p))] for p in (.05,.10,.25,.50,.75,.90,.95)},
            rows=[dict(event=r['event'],map=r['map'],player=r['player'],target=r['rating'],prediction=g,residual=e,
                       kill_credit_affected=r['kill_credit_affected']) for r,g,e in zip(pooled_rows,guesses,errors)])
    drift={}
    for name,model in models.items():
        raw=raw_coefficients(model);base=raw_coefficients(baseline)
        drift[name]={n:dict(full_raw=raw['coefficients'][n],v2_raw=base['coefficients'][n],
            change=raw['coefficients'][n]-base['coefficients'][n],
            fold_min=min(f['raw_coefficients'][name]['coefficients'][n] for f in fold_models),
            fold_max=max(f['raw_coefficients'][name]['coefficients'][n] for f in fold_models)) for n in FEATURES}
    gate=plan['development_qualification'];qualifications={}
    a=summary['exact_frozen_v2_original']
    for name in models:
        m=summary[name]
        checks=dict(events=len(fold_reports)>=gate['minimum_events'],rows=len(rows)>=gate['minimum_clean_rows'],
            mae_improvement=(a['mae']-m['mae'])/a['mae']>=gate['relative_mae_improvement_vs_exact_v2'],
            within_005=m['within_0.05']>=gate['within_0_05'],rmse=m['rmse']<=a['rmse'],max_error=m['max_abs_error']<=gate['max_absolute_error'])
        qualifications[name]=dict(checks=checks,qualified=all(checks.values()))
    result=dict(experiment_id=datetime.now(timezone.utc).strftime('v3-credited-event-folds-%Y%m%dT%H%M%SZ'),
        experiment_kind='corrected_counts_core_objectives_whole_event_development_v1',reservation=marker,
        rows=len(rows),maps=len({(r['match_id'],r['game_id']) for r in rows}),events=len(fold_reports),folds=fold_reports,
        pooled=summary,models=models,raw_coefficients={n:raw_coefficients(m) for n,m in models.items()},
        coefficient_drift=drift,fold_models=fold_models,subgroups=subgroups,residuals=residuals,qualifications=qualifications,
        final_test_evaluated=False,production_deployed=False,
        limits='Frozen v2 reference has seen some earlier development rows; candidate predictions leave the entire event out. Consumed APAC/SAL finals are broad development only, not new final accuracy. Event features retain documented legacy semantics. No individual final residual tuning or coefficient search.')
    immutable_write(result_path,result)
    compact=result|dict(residuals={n:{k:v for k,v in d.items() if k!='rows'} for n,d in residuals.items()},
        private_result_sha256=sha(result_path))
    with (ROOT/'research/experiment-log.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(compact)+'\n')
    lines=['# Corrected-count whole-event Rating development','',result['experiment_id'],'',result['limits'],'',
        f"{result['rows']} clean player-map rows, {result['maps']} maps, {result['events']} whole-event folds.",
        '', '| Model | MAE | RMSE | Median AE | Max AE | within .01 | .02 | .03 | .05 | .10 |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for name,m in summary.items():
        lines.append(f"| {name} | {m['mae']:.5f} | {m['rmse']:.5f} | {m['median_abs_error']:.5f} | {m['max_abs_error']:.5f} | "+' | '.join(f"{m[f'within_{t:.2f}']:.1%}" for t in (.01,.02,.03,.05,.10))+' |')
    lines+=['','## Predeclared development qualification','',json.dumps(qualifications,indent=2),'',
        '## Coefficients and whole-event drift','','| Model / feature | Raw | v2 raw | Fold min | Fold max |','| --- | ---: | ---: | ---: | ---: |']
    for name,terms in drift.items():
        for n,d in terms.items():lines.append(f"| {name}/{n} | {d['full_raw']:.8f} | {d['v2_raw']:.8f} | {d['fold_min']:.8f} | {d['fold_max']:.8f} |")
    lines+=['','Exact per-event metrics, all thresholds, fold models, residual quantiles, objective-positive and kill-credit-affected residuals are preserved in the private experiment. No new final event was selected or opened.','']
    (ROOT/'research/output/v3-credited-event-development.md').write_text('\n'.join(lines),encoding='utf-8')
    print('QUALIFICATION',qualifications,flush=True)
    subprocess.run([sys.executable,str(ROOT/'research/verify_production_kill_checkpoint.py')],check=True)


if __name__=='__main__':main()
