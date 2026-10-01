"""Single preregistered size-weighted clutch comparison on current clean cohort."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

from expanded_fit import select_groups, PLAN as SPLIT, OBSERVATIONS, LOG, ROOT
from fit_models import design as baseline_design, FEATURES, predict as baseline_predict
from multikill_experiment import fit, predict, metrics

PLAN = json.loads((ROOT/'research/clutch-plan.json').read_text())


def features(row, variant):
    if variant != 'linear_size':
        raise ValueError('Unplanned clutch variant')
    values = {k: v for k, v in zip(FEATURES, baseline_design(row, {}, 'raw')) if k != 'objectives'}
    for round_ in row['rounds']:
        if round_['clutches'] != sum(round_[f'clutch_1v{x}'] for x in range(1, 6)):
            raise ValueError('Clutch total/breakdown mismatch')
    values['clutch'] = sum(x*r[f'clutch_1v{x}'] for r in row['rounds'] for x in range(1, 6))/len(row['rounds'])
    return values


def main():
    content = OBSERVATIONS.read_bytes()
    digest = hashlib.sha256(content).hexdigest()
    if digest != PLAN['dataset_sha256']:
        raise ValueError('Dataset changed')
    logs = list(map(json.loads, LOG.read_text().splitlines()))
    if any(r.get('experiment_kind') == PLAN['name'] and r.get('dataset_sha256') == digest for r in logs):
        raise ValueError('Already recorded')
    train, dev, held = select_groups(list(map(json.loads, content.splitlines())), SPLIT)
    if (len(train), len(dev)) != (299, 32):
        raise ValueError('Unexpected split')
    prior = next(r for r in logs if r['experiment_id'] == PLAN['baseline_id'])
    cv = next(r for r in logs if r['experiment_id'] == PLAN['baseline_cv_id'])
    if prior['dataset_sha256'] != digest or cv['dataset_sha256'] != digest:
        raise ValueError('Baseline dataset mismatch')
    variant = 'linear_size'
    folds, pooled_rows, guesses = [], [], []
    for event in SPLIT['train_events']:
        training = [r for r in train if r['event'] != event]
        validation = [r for r in train if r['event'] == event]
        model = fit(training, variant, features)
        preds = [predict(model, r, features) for r in validation]
        folds.append({'event': event, 'metrics': metrics(validation, preds),
                      'clutch_slope': model['raw_slopes']['clutch']})
        pooled_rows.extend(validation)
        guesses.extend(preds)
    model = fit(train, variant, features)
    old = {k: prior['model']['weights_standardized'][k]/prior['model']['scales'][k]
           for k in prior['model']['scales'] if k != 'objectives'}
    record = {'experiment_id': datetime.now(timezone.utc).strftime('clutch-%Y%m%dT%H%M%SZ'),
              'experiment_kind': PLAN['name'], 'dataset_sha256': digest, 'plan': PLAN,
              'code_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              'code_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'train_rows': len(train), 'august_rows': len(dev), 'held_out_clean_rows': held,
              'train_clutch_sizes': {str(x): sum(r[f'clutch_1v{x}'] for p in train for r in p['rounds'])
                                     for x in range(1, 6)},
              'model': model, 'folds': folds, 'pooled': metrics(pooled_rows, guesses),
              'august': metrics(dev, [predict(model, r, features) for r in dev]),
              'baseline_pooled': cv['pooled']['raw'],
              'baseline_august': metrics(dev, [baseline_predict(prior['model'], r, {}) for r in dev]),
              'coefficient_drift': {k: {'baseline': old[k], 'new': model['raw_slopes'][k],
                                       'absolute': abs(model['raw_slopes'][k]-old[k])} for k in old},
              'final_test_evaluated': False}
    with LOG.open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(record)+'\n')
    (ROOT/'data/research/experiments/clutch-linear-v1.json').write_text(json.dumps(record, indent=2))
    print(json.dumps({k: record[k] for k in ('experiment_id', 'train_clutch_sizes')}
                     | {'pooled_mae': record['pooled']['mae'], 'august_mae': record['august']['mae'],
                        'clutch_slope': model['raw_slopes']['clutch']}, indent=2))


if __name__ == '__main__':
    main()
