"""One prospective whole-event native-order/clutch study, never a final regrade."""
from collections import defaultdict
from datetime import datetime,timezone
import json
import math
from pathlib import Path
import statistics
import subprocess
import sys

from credited_late_history_development import immutable_write
from fit_baseline import solve
from fit_models import FEATURES,design,predict as v2_predict
from v3_credited_fit import folds,raw_coefficients
from v3_final_reserve import ROOT,sha,source_sha
from v3_native_order_derive import DATA
from v3_objective_fit import metrics

PLAN=ROOT/'research/v3-native-order-plan.json'


def features(row,variant):
    if variant not in ('legacy_count','native_count','native_linear_size','native_triangular_size'):
        raise ValueError('Unplanned feature variant')
    rounds=row['legacy_corrected_rounds'] if variant=='legacy_count' else row['rounds']
    out=design(row|dict(rounds=rounds),{},'raw')
    if variant in ('native_linear_size','native_triangular_size'):
        if any(r['clutches']!=sum(r[f'clutch_1v{x}'] for x in range(1,6)) for r in rounds):
            raise ValueError('Clutch total/breakdown mismatch')
        weight=lambda x:x if variant=='native_linear_size' else x*(x+1)/2
        out[FEATURES.index('clutch')]=sum(weight(x)*r[f'clutch_1v{x}'] for r in rounds for x in range(1,6))/len(rounds)
    return out


def fit(rows,variant):
    if any(r['reserved_for_final_test'] or not r['consumed_development'] or not r['native_event_order_complete'] for r in rows):
        raise ValueError('Only sealed consumed native-order development rows may enter fit')
    xs=[features(r,variant) for r in rows]
    centers=[statistics.mean(x[j] for x in xs) for j in range(len(FEATURES))]
    scales=[max(math.sqrt(statistics.mean((x[j]-centers[j])**2 for x in xs)),1e-9) for j in range(len(FEATURES))]
    matrix=[[1.]+[(x[j]-centers[j])/scales[j] for j in range(len(FEATURES))] for x in xs]
    n=len(FEATURES)+1
    gram=[[sum(x[i]*x[j] for x in matrix)+(1. if i==j and i else 0.) for j in range(n)] for i in range(n)]
    rhs=[sum(x[i]*r['rating'] for x,r in zip(matrix,rows)) for i in range(n)]
    w=solve(gram,rhs)
    return dict(variant=variant,method='native_order_raw',alpha=1,intercept=w[0],
        means=dict(zip(FEATURES,centers)),scales=dict(zip(FEATURES,scales)),weights_standardized=dict(zip(FEATURES,w[1:])))


def predict(model,row):
    return model['intercept']+sum(model['weights_standardized'][k]*(v-model['means'][k])/model['scales'][k]
        for k,v in zip(FEATURES,features(row,model['variant'])))


def main():
    output=DATA/'experiment.json'
    if output.exists():raise ValueError('Study already completed; do not fit again')
    if subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip():
        raise ValueError('Commit prospective plan/code/tests and clean tree before fitting')
    plan=json.loads(PLAN.read_text(encoding='utf-8'));dataset=DATA/'dataset.json'
    rows=json.loads(dataset.read_text(encoding='utf-8'))['rows'];arms=plan['variants']
    baseline=json.loads((ROOT/'research/frozen-rating-candidate.json').read_text(encoding='utf-8'))['model']
    marker=dict(plan_sha256=source_sha(PLAN),dataset_sha256=sha(dataset),source_sha256=source_sha(Path(__file__)),
        source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        new_final_targets_opened=False,cnl_is_consumed_development=True)
    immutable_write(DATA/'fit-reservation.json',marker)
    pooled=defaultdict(list);pooled_rows=[];fold_reports=[];fold_models=[]
    for event,train,validation in folds(rows):
        models={arm:fit(train,arm) for arm in arms}
        guesses={'exact_frozen_v2_original':[v2_predict(baseline,r|dict(rounds=r['original_v2_rounds']),{}) for r in validation]}
        guesses.update({arm:[predict(model,r) for r in validation] for arm,model in models.items()})
        summary={name:metrics(validation,p) for name,p in guesses.items()}
        fold_reports.append(dict(event=event,train_rows=len(train),validation_rows=len(validation),metrics=summary))
        fold_models.append(dict(event=event,models=models,raw_coefficients={arm:raw_coefficients(m) for arm,m in models.items()}))
        pooled_rows+=validation
        for name,p in guesses.items():pooled[name]+=p
        print('EVENT',event,{name:(round(m['mae'],5),round(m['within_0.05'],3)) for name,m in summary.items()},flush=True)
    summary={name:metrics(pooled_rows,p) for name,p in pooled.items()};models={arm:fit(rows,arm) for arm in arms}
    subgroups={};residuals={};drift={};baseline_raw=raw_coefficients(baseline)
    for name,guesses in pooled.items():
        indices={'objective_positive':[i for i,r in enumerate(pooled_rows) if any(x['plants'] or x['disables'] for x in r['rounds'])],
            'kill_credit_affected':[i for i,r in enumerate(pooled_rows) if r['kill_credit_affected']],
            'clutch_positive':[i for i,r in enumerate(pooled_rows) if any(x['clutches'] for x in r['rounds'])]}
        subgroups[name]={group:metrics([pooled_rows[i] for i in ids],[guesses[i] for i in ids]) for group,ids in indices.items() if ids}
        errors=[g-r['rating'] for g,r in zip(guesses,pooled_rows)];ordered=sorted(errors)
        residuals[name]=dict(mean=statistics.mean(errors),median=statistics.median(errors),
            quantiles={str(p):ordered[int((len(ordered)-1)*p)] for p in (.05,.10,.25,.50,.75,.90,.95)},
            rows=[dict(event=r['event'],map=r['map'],player=r['player'],target=r['rating'],prediction=g,error=e,
                objective_positive=any(x['plants'] or x['disables'] for x in r['rounds']),kill_credit_affected=r['kill_credit_affected'])
                for r,g,e in zip(pooled_rows,guesses,errors)])
    for arm,model in models.items():
        raw=raw_coefficients(model)
        drift[arm]={k:dict(full_raw=raw['coefficients'][k],v2_raw=baseline_raw['coefficients'][k],
            fold_min=min(f['raw_coefficients'][arm]['coefficients'][k] for f in fold_models),
            fold_max=max(f['raw_coefficients'][arm]['coefficients'][k] for f in fold_models)) for k in FEATURES}
    gate=plan['development_qualification'];qualifications={};a=summary['exact_frozen_v2_original'];control=summary['native_count']
    for arm in arms[1:]:
        m=summary[arm];checks=dict(events=len(fold_reports)>=gate['minimum_events'],rows=len(rows)>=gate['minimum_clean_rows'],
            mae_improvement=(a['mae']-m['mae'])/a['mae']>=gate['relative_mae_improvement_vs_exact_v2'],
            within_005=m['within_0.05']>=gate['within_0_05'],rmse=m['rmse']<=a['rmse'],max_error=m['max_abs_error']<=gate['max_absolute_error'])
        for group in ('objective_positive','kill_credit_affected'):
            s=subgroups[arm][group];checks[group]=s['n']<gate['subgroup_minimum_rows'] or s['mae']<=gate['subgroup_max_mae']
        if 'size' in arm:
            checks['mae_vs_native_count']=(control['mae']-m['mae'])/control['mae']>=gate['size_arm_relative_mae_improvement_vs_native_count']
            checks['broad_event_wins']=sum(f['metrics'][arm]['mae']<f['metrics']['native_count']['mae'] for f in fold_reports)>=gate['size_arm_event_wins_minimum']
        qualifications[arm]=dict(checks=checks,qualified=all(checks.values()))
    qualified=[arm for arm,q in qualifications.items() if q['qualified']]
    selected=min(qualified,key=lambda arm:summary[arm]['mae']) if qualified else None
    result=dict(experiment_id=datetime.now(timezone.utc).strftime('v3-native-order-%Y%m%dT%H%M%SZ'),
        experiment_kind=plan['version'],reservation=marker,rows=len(rows),maps=len({(r['match_id'],r['game_id']) for r in rows}),
        events=len(fold_reports),folds=fold_reports,pooled=summary,models=models,fold_models=fold_models,
        raw_coefficients={a:raw_coefficients(m) for a,m in models.items()},coefficient_drift=drift,
        subgroups=subgroups,residuals=residuals,qualifications=qualifications,selected_arm=selected,
        final_test_evaluated=False,production_deployed=False,limits=plan['feature_limits']+' '+plan['historical_studies'])
    immutable_write(output,result)
    compact=result|dict(residuals={n:{k:v for k,v in s.items() if k!='rows'} for n,s in residuals.items()},private_result_sha256=sha(output))
    with (ROOT/'research/experiment-log.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(compact)+'\n')
    if selected:
        immutable_write(ROOT/'research/v3-native-order-candidate.json',dict(version='siege_style_v3',status='development_qualified_not_final_tested',
            variant=selected,model=models[selected],experiment_id=result['experiment_id'],plan_sha256=source_sha(PLAN),
            dataset_sha256=sha(dataset),acceptance=plan['prospective_final_gate'],feature_policy=plan['feature_limits']))
    lines=['# Native event order and clutch-size development','',result['experiment_id'],'',result['limits'],'',
        f"{result['rows']} clean rows, {result['maps']} maps, {result['events']} whole-event folds. CNL is permanently consumed development.",'',
        '| Arm | MAE | RMSE | Median AE | Max AE | .01 | .02 | .03 | .05 | .10 |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for arm,m in summary.items():lines.append(f"| {arm} | {m['mae']:.6f} | {m['rmse']:.6f} | {m['median_abs_error']:.6f} | {m['max_abs_error']:.6f} | "+' | '.join(f"{m[f'within_{t:.2f}']:.1%}" for t in (.01,.02,.03,.05,.10))+' |')
    lines+=['','## Whole-event validation','','| Event | Rows | '+' | '.join(summary)+' |','| --- | ---: | '+' | '.join('---:' for _ in summary)+' |']
    for f in fold_reports:lines.append(f"| {f['event']} | {f['validation_rows']} | "+' | '.join(f"{f['metrics'][a]['mae']:.5f} / {f['metrics'][a]['within_0.05']:.1%}" for a in summary)+' |')
    lines+=['','## Qualification','',json.dumps(qualifications,indent=2),'',f'Selected: {selected}. No new final target opened.',
        '','## Raw coefficients and whole-event drift','','| Arm / feature | Full | v2 | Fold min | Fold max |','| --- | ---: | ---: | ---: | ---: |']
    for arm,terms in drift.items():
        lines.append(f"\n{arm} raw intercept: {raw_coefficients(models[arm])['intercept']:.10f}\n")
        for k,d in terms.items():lines.append(f"| {arm}/{k} | {d['full_raw']:.8f} | {d['v2_raw']:.8f} | {d['fold_min']:.8f} | {d['fold_max']:.8f} |")
    lines+=['','Subgroup, residual quantiles, all fold coefficients, all row errors and immutable input hashes are preserved in the private experiment and compact public experiment log. Fixed size transforms have sparse 1v4/5 support; no individual size coefficients were fitted.','']
    (ROOT/'research/output/v3-native-order-development.md').write_text('\n'.join(lines),encoding='utf-8')
    print('QUALIFICATION',json.dumps(qualifications),'SELECTED',selected,flush=True)


if __name__=='__main__':main()
