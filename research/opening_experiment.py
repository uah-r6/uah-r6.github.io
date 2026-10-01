"""One preregistered opening asymmetry experiment using unchanged raw families."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

from expanded_fit import select_groups, PLAN as SPLIT, OBSERVATIONS, LOG, ROOT
from fit_models import round_features
from multikill_experiment import fit, predict, metrics

PLAN = json.loads((ROOT/'research/opening-plan.json').read_text())


def features(row, variant):
    if variant != 'separate_openings':
        raise ValueError('Unplanned opening variant')
    rounds = row['rounds']
    samples = [round_features(r) for r in rounds]
    names = ('kpr', 'teamkills', 'multikill', 'clutch', 'kost', 'survival', 'trade')
    values = {k: sum(r[i] for r in samples)/len(samples) for k, i in zip(names, (0, 1, 2, 4, 5, 6, 7))}
    for name in ('opening_kills', 'opening_deaths'):
        values[name] = sum(r[name] for r in rounds)/len(rounds)
    return values


def main():
    content = OBSERVATIONS.read_bytes()
    digest = hashlib.sha256(content).hexdigest()
    if digest != PLAN['dataset_sha256']:
        raise ValueError('Dataset changed')
    records = list(map(json.loads, LOG.read_text().splitlines()))
    if any(r.get('experiment_kind') == PLAN['name'] and r.get('dataset_sha256') == digest for r in records):
        raise ValueError('Already recorded; inspect cached results')
    train, dev, held = select_groups(list(map(json.loads, content.splitlines())), SPLIT)
    if (len(train), len(dev)) != (299, 32):
        raise ValueError('Unexpected split')
    prior = next(r for r in records if r['experiment_id'] == PLAN['baseline_id'])
    cv = next(r for r in records if r['experiment_id'] == PLAN['baseline_cv_id'])
    if prior['dataset_sha256'] != digest or cv['dataset_sha256'] != digest:
        raise ValueError('Baseline dataset mismatch')
    folds, rows, guesses = [], [], []
    for event in SPLIT['train_events']:
        training = [r for r in train if r['event'] != event]
        validation = [r for r in train if r['event'] == event]
        model = fit(training, 'separate_openings', features)
        predictions = [predict(model, r, features) for r in validation]
        folds.append({'event': event, 'model': model, 'metrics': metrics(validation, predictions)})
        rows.extend(validation)
        guesses.extend(predictions)
    model = fit(train, 'separate_openings', features)
    old = {k: prior['model']['weights_standardized'][k]/prior['model']['scales'][k] for k in prior['model']['scales']}
    drift = {k: {'prior': old[k], 'new': v, 'absolute_drift': abs(v-old[k]),
                  'relative_drift': abs((v-old[k])/old[k]) if old[k] else None}
             for k, v in model['raw_slopes'].items() if k in old}
    record = {'experiment_id': datetime.now(timezone.utc).strftime('opening-%Y%m%dT%H%M%SZ'),
              'experiment_kind': PLAN['name'], 'dataset_sha256': digest, 'plan': PLAN,
              'code_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              'code_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'helper_sha256': hashlib.sha256((ROOT/'research/multikill_experiment.py').read_bytes()).hexdigest(),
              'train_rows': len(train), 'august_rows': len(dev), 'held_out_clean_rows': held,
              'model': model, 'folds': folds, 'pooled': metrics(rows, guesses),
              'august': metrics(dev, [predict(model, r, features) for r in dev]),
              'baseline_pooled': cv['pooled']['raw'], 'baseline_august': prior['validation'],
              'shared_coefficient_drift': drift, 'prior_opening_slope': old['opening'],
              'fold_slope_ranges': {k: [min(f['model']['raw_slopes'][k] for f in folds),
                                       max(f['model']['raw_slopes'][k] for f in folds)] for k in model['raw_slopes']},
              'final_test_evaluated': False, 'objectives': 'unavailable/excluded'}
    with LOG.open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(record)+'\n')
    (ROOT/'data/research/experiments/separate-openings-v1.json').write_text(json.dumps(record, indent=2))
    print(json.dumps({k: record[k] for k in ('experiment_id', 'pooled', 'august', 'fold_slope_ranges')}, indent=2))


if __name__ == '__main__':
    main()
