"""Controlled eight-second trade representation comparison, research only."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

from expanded_fit import select_groups, PLAN as SPLIT, OBSERVATIONS, LOG, ROOT
from fit_models import design as baseline_design, FEATURES, predict as baseline_predict
from multikill_experiment import fit, predict, metrics

PLAN = json.loads((ROOT/'research/trade-definition-plan.json').read_text())


def features(row, variant):
    if variant not in PLAN['variants']:
        raise ValueError('Unplanned trade variant')
    values = {k: v for k, v in zip(FEATURES, baseline_design(row, {}, 'raw')) if k != 'objectives'}
    field = 'deaths_traded' if variant == 'deaths_traded_rate' else 'kills_traded'
    values['trade'] = sum(r[field] for r in row['rounds'])/len(row['rounds'])
    return values


def main():
    content = OBSERVATIONS.read_bytes()
    digest = hashlib.sha256(content).hexdigest()
    if digest != PLAN['dataset_sha256']:
        raise ValueError('Dataset changed')
    records = list(map(json.loads, LOG.read_text().splitlines()))
    if any(r.get('experiment_kind') == PLAN['name'] and r.get('dataset_sha256') == digest for r in records):
        raise ValueError('Already recorded')
    train, dev, held = select_groups(list(map(json.loads, content.splitlines())), SPLIT)
    if (len(train), len(dev)) != (299, 32):
        raise ValueError('Unexpected split')
    prior = next(r for r in records if r['experiment_id'] == PLAN['baseline_id'])
    cv = next(r for r in records if r['experiment_id'] == PLAN['baseline_cv_id'])
    if prior['dataset_sha256'] != digest or cv['dataset_sha256'] != digest:
        raise ValueError('Baseline dataset mismatch')
    old = {k: prior['model']['weights_standardized'][k]/prior['model']['scales'][k]
           for k in prior['model']['scales'] if k != 'objectives'}
    variants = []
    for variant in PLAN['variants']:
        folds, pooled_rows, guesses = [], [], []
        for event in SPLIT['train_events']:
            training = [r for r in train if r['event'] != event]
            validation = [r for r in train if r['event'] == event]
            model = fit(training, variant, features)
            preds = [predict(model, r, features) for r in validation]
            folds.append({'event': event, 'metrics': metrics(validation, preds),
                          'trade_slope': model['raw_slopes']['trade']})
            pooled_rows.extend(validation)
            guesses.extend(preds)
        model = fit(train, variant, features)
        variants.append({'variant': variant, 'model': model, 'folds': folds,
                         'pooled': metrics(pooled_rows, guesses),
                         'august': metrics(dev, [predict(model, r, features) for r in dev]),
                         'coefficient_drift': {k: {'baseline': old[k], 'new': model['raw_slopes'][k],
                                                  'absolute': abs(model['raw_slopes'][k]-old[k])}
                                               for k in old}})
    record = {'experiment_id': datetime.now(timezone.utc).strftime('trade-def-%Y%m%dT%H%M%SZ'),
              'experiment_kind': PLAN['name'], 'dataset_sha256': digest, 'plan': PLAN,
              'code_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              'code_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'train_rows': len(train), 'august_rows': len(dev), 'held_out_clean_rows': held,
              'baseline_pooled': cv['pooled']['raw'],
              'baseline_august': metrics(dev, [baseline_predict(prior['model'], r, {}) for r in dev]),
              'variants': variants, 'final_test_evaluated': False}
    with LOG.open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(record)+'\n')
    (ROOT/'data/research/experiments/trade-definition-v1.json').write_text(json.dumps(record, indent=2))
    print(json.dumps({v['variant']: {'pooled_mae': v['pooled']['mae'],
                                    'august_mae': v['august']['mae'],
                                    'trade_slope': v['model']['raw_slopes']['trade']}
                      for v in variants}, indent=2))


if __name__ == '__main__':
    main()
