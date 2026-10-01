"""Preregistered research-only multikill comparison; no final-event evaluation."""
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import statistics
import subprocess

from expanded_fit import select_groups, PLAN as SPLIT, OBSERVATIONS, LOG, ROOT
from fit_baseline import solve
from fit_models import round_features, evaluate, predict as baseline_predict

PLAN = json.loads((ROOT / 'research/multikill-plan.json').read_text())
SHARED = ('kpr', 'teamkills', 'opening', 'clutch', 'kost', 'survival', 'trade')


def features(row, variant):
    if variant not in PLAN['variants']:
        raise ValueError('Unplanned variant')
    rounds = row['rounds']
    samples = [round_features(r) for r in rounds]
    indices = (0, 1, 3, 4, 5, 6, 7)
    values = {k: sum(s[i] for s in samples) / len(samples) for k, i in zip(SHARED, indices)}
    if variant == 'multi_round_rate':
        values['multi_round_rate'] = sum(r['kills'] >= 2 for r in rounds) / len(rounds)
    else:
        for k in (2, 3, 4, 5):
            values[f'kills_{k}'] = sum(min(r['kills'], 5) == k for r in rounds) / len(rounds)
    return values


def fit(rows, variant, feature_builder=features):
    if any(r['reserved_for_final_test'] or r['event'] not in SPLIT['train_events'] for r in rows):
        raise ValueError('Only pre-August training events may enter fit')
    xs = [feature_builder(r, variant) for r in rows]
    names = list(xs[0])
    centers = {k: statistics.mean(x[k] for x in xs) for k in names}
    scales = {k: max(math.sqrt(statistics.mean((x[k]-centers[k])**2 for x in xs)), 1e-9) for k in names}
    matrix = [[1.] + [(x[k]-centers[k])/scales[k] for k in names] for x in xs]
    n = len(names)+1
    gram = [[sum(x[i]*x[j] for x in matrix)+(1. if i == j and i else 0.) for j in range(n)] for i in range(n)]
    rhs = [sum(x[i]*r['rating'] for x, r in zip(matrix, rows)) for i in range(n)]
    weights = solve(gram, rhs)
    slopes = {k: w/scales[k] for k, w in zip(names, weights[1:])}
    return {'variant': variant, 'alpha': 1., 'means': centers, 'scales': scales,
            'weights_standardized': dict(zip(names, weights[1:])), 'intercept': weights[0],
            'raw_slopes': slopes, 'raw_intercept': weights[0]-sum(slopes[k]*centers[k] for k in names)}


def predict(model, row, feature_builder=features):
    if row['reserved_for_final_test'] or row['event'] not in SPLIT['train_events'] + [SPLIT['development_validation_event']]:
        raise ValueError('Final/historical event prediction is forbidden')
    return model['raw_intercept'] + sum(model['raw_slopes'][k]*v for k, v in feature_builder(row, model['variant']).items())


def metrics(rows, guesses):
    return {**evaluate(rows, guesses),
            'median_abs_error': statistics.median(abs(g-r['rating']) for r, g in zip(rows, guesses)),
            'mean_error': statistics.mean(g-r['rating'] for r, g in zip(rows, guesses))}


def main():
    content = OBSERVATIONS.read_bytes()
    digest = hashlib.sha256(content).hexdigest()
    if digest != PLAN['dataset_sha256']:
        raise ValueError('Dataset changed since preregistration')
    records = list(map(json.loads, LOG.read_text().splitlines()))
    if any(r.get('experiment_kind') == PLAN['name'] and r.get('dataset_sha256') == digest for r in records):
        raise ValueError('Experiment already recorded; inspect cached result instead')
    train, dev, held = select_groups(list(map(json.loads, content.splitlines())), SPLIT)
    if (len(train), len(dev)) != (299, 32):
        raise ValueError('Unexpected split size')
    prior = next(r for r in records if r['experiment_id'] == PLAN['baseline_id'])
    prior_cv = next(r for r in records if r['experiment_id'] == PLAN['baseline_cv_id'])
    if prior['dataset_sha256'] != digest or prior_cv['dataset_sha256'] != digest:
        raise ValueError('Baseline dataset differs')
    if prior['model']['weights_standardized']['objectives'] != 0:
        raise ValueError('Cannot compare baseline with credited objectives')
    old_slopes = {k: prior['model']['weights_standardized'][k]/prior['model']['scales'][k] for k in SHARED}
    variants = []
    for variant in PLAN['variants']:
        folds, pooled_rows, pooled_predictions = [], [], []
        for event in SPLIT['train_events']:
            training = [r for r in train if r['event'] != event]
            validation = [r for r in train if r['event'] == event]
            model = fit(training, variant)
            guesses = [predict(model, r) for r in validation]
            folds.append({'event': event, 'model': model, 'metrics': metrics(validation, guesses)})
            pooled_rows.extend(validation)
            pooled_predictions.extend(guesses)
        model = fit(train, variant)
        drift = {k: {'prior': old_slopes[k], 'new': model['raw_slopes'][k],
                     'absolute_drift': abs(model['raw_slopes'][k]-old_slopes[k]),
                     'relative_drift': abs((model['raw_slopes'][k]-old_slopes[k])/old_slopes[k]) if old_slopes[k] else None}
                 for k in SHARED}
        variants.append({'variant': variant, 'model': model, 'folds': folds,
                         'pooled': metrics(pooled_rows, pooled_predictions),
                         'august': metrics(dev, [predict(model, r) for r in dev]),
                         'shared_coefficient_drift': drift,
                         'fold_slope_ranges': {k: [min(f['model']['raw_slopes'][k] for f in folds),
                                                  max(f['model']['raw_slopes'][k] for f in folds)] for k in model['raw_slopes']}})
    record = {'experiment_id': datetime.now(timezone.utc).strftime('multikill-%Y%m%dT%H%M%SZ'),
              'experiment_kind': PLAN['name'], 'dataset_sha256': digest, 'plan': PLAN,
              'code_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              'code_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'parser_sha256': hashlib.sha256((ROOT/'.local-tools/bin/siege-dissect.exe').read_bytes()).hexdigest(),
              'train_rows': len(train), 'august_rows': len(dev), 'held_out_clean_rows': held,
              'baseline_pooled': prior_cv['pooled']['raw'],
              'baseline_august': metrics(dev, [baseline_predict(prior['model'], r, {}) for r in dev]),
              'variants': variants, 'final_test_evaluated': False,
              'objective_status': 'Unavailable; omitted, not imputed from team occurrences.'}
    with LOG.open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(record)+'\n')
    out = ROOT/'data/research/experiments/multikill-definition-v1.json'
    out.write_text(json.dumps(record, indent=2))
    print(json.dumps({v['variant']: {'pooled': v['pooled']['mae'], 'august': v['august']['mae']} for v in variants}, indent=2))


if __name__ == '__main__':
    main()
