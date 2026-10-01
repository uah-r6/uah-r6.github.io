"""Isolated trade-window experiment from cached normalized matches only."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import statistics
import subprocess

from expanded_fit import select_groups, PLAN as SPLIT, OBSERVATIONS, LOG, ROOT
from fit_models import design as baseline_design, predict as baseline_predict
from multikill_experiment import fit, predict, metrics
from r6stats.parser.models import Match
from r6stats.stats.calculate import calculate_match

PLAN = json.loads((ROOT/'research/trade-window-plan.json').read_text())
DERIVED = ROOT/'data/research/derived'


def load_trade_counts(rows, windows):
    """Only open the development rows' maps; never touch sealed-event target ratings."""
    if any(r['reserved_for_final_test'] or r['event'] not in
           SPLIT['train_events'] + [SPLIT['development_validation_event']] for r in rows):
        raise ValueError('Final/historical event entered trade derivation')
    folders = sorted({r['replay_folder'] for r in rows})
    result = {}
    provenance = {}
    for folder in folders:
        data = (DERIVED/(folder+'.json')).read_bytes()
        provenance[folder] = hashlib.sha256(data).hexdigest()
        match = Match.from_dict(json.loads(data))
        for seconds in windows:
            for round_ in match.rounds:
                one = Match(match.replay_id, match.timestamp, match.map_name,
                            match.match_type, match.game_mode, [round_])
                stat = calculate_match(one, seconds)
                for player in round_.players:
                    value = stat[player.key]
                    key = (folder, seconds, round_.number, player.username.casefold())
                    if key in result:
                        raise ValueError(f'Duplicate normalized round/player: {key}')
                    result[key] = (value['deaths_traded'], value['kills_traded'], value['kost_rounds'])
    return result, provenance


def trade_features(row, variant, values):
    seconds = int(variant.removeprefix('trade_'))
    if seconds not in PLAN['windows_seconds']:
        raise ValueError('Unplanned window')
    # Keep all non-trade families exactly as in the cached 8-second baseline.
    vector = baseline_design(row, {}, 'raw')
    from fit_models import FEATURES
    features = {k: v for k, v in zip(FEATURES, vector) if k != 'objectives'}
    differences = [values[(row['replay_folder'], seconds, r['number'], row['player'].casefold())]
                   for r in row['rounds']]
    features['trade'] = sum(deaths-kills for deaths, kills, _ in differences)/len(differences)
    return features


def distribution(rows, seconds, values):
    pairs = [values[(row['replay_folder'], seconds, r['number'], row['player'].casefold())]
             for row in rows for r in row['rounds']]
    by_row = [sum(values[(row['replay_folder'], seconds, r['number'], row['player'].casefold())][0] -
                  values[(row['replay_folder'], seconds, r['number'], row['player'].casefold())][1]
                  for r in row['rounds'])/len(row['rounds']) for row in rows]
    return {'player_rounds': len(pairs), 'deaths_traded': sum(p[0] for p in pairs),
            'kills_traded': sum(p[1] for p in pairs),
            'differential_min': min(by_row), 'differential_median': statistics.median(by_row),
            'differential_max': max(by_row),
            'differential_nonzero_rows': sum(v != 0 for v in by_row),
            'differential_sign_counts': dict(Counter('positive' if v > 0 else 'negative' if v < 0 else 'zero'
                                                    for v in by_row))}


def main():
    source = OBSERVATIONS.read_bytes()
    digest = hashlib.sha256(source).hexdigest()
    if digest != PLAN['dataset_sha256']:
        raise ValueError('Dataset changed since preregistration')
    logs = list(map(json.loads, LOG.read_text().splitlines()))
    if any(r.get('experiment_kind') == PLAN['name'] and r.get('dataset_sha256') == digest for r in logs):
        raise ValueError('Experiment already recorded')
    train, dev, held = select_groups(list(map(json.loads, source.splitlines())), SPLIT)
    if (len(train), len(dev)) != (299, 32):
        raise ValueError('Unexpected fixed split')
    old = next(r for r in logs if r['experiment_id'] == PLAN['baseline_id'])
    cv = next(r for r in logs if r['experiment_id'] == PLAN['baseline_cv_id'])
    if old['dataset_sha256'] != digest or cv['dataset_sha256'] != digest:
        raise ValueError('Baseline dataset mismatch')
    if old['model']['weights_standardized']['objectives'] != 0:
        raise ValueError('Baseline objective feature is not inert')
    values, provenance = load_trade_counts(train+dev, PLAN['windows_seconds'])
    mismatches = []
    for row in train+dev:
        for r in row['rounds']:
            death, kill, kost = values[(row['replay_folder'], 8, r['number'], row['player'].casefold())]
            if (death, kill, kost) != (r['deaths_traded'], r['kills_traded'], r['kost_rounds']):
                mismatches.append((row['replay_folder'], r['number'], row['player']))
    if mismatches:
        raise ValueError(f'Cached 8-second parity failed: {mismatches[:5]} ({len(mismatches)} total)')
    slopes = {k: old['model']['weights_standardized'][k]/old['model']['scales'][k]
              for k in old['model']['scales'] if k != 'objectives'}
    results = []
    for seconds in PLAN['windows_seconds']:
        entry = {'seconds': seconds, 'train_distribution': distribution(train, seconds, values),
                 'august_distribution': distribution(dev, seconds, values)}
        if seconds == 8:
            entry.update({'pooled': cv['pooled']['raw'],
                          'august': metrics(dev, [baseline_predict(old['model'], r, {}) for r in dev]),
                          'folds': [{'event': f['event'], 'metrics': f['models']['raw']}
                                    for f in cv['folds']],
                          'model': old['model'], 'raw_slopes': slopes,
                          'source': 'saved_baseline_no_refit'})
        else:
            variant = f'trade_{seconds}'
            builder = lambda row, v: trade_features(row, v, values)
            folds, pooled_rows, pooled_guesses = [], [], []
            for event in SPLIT['train_events']:
                training = [r for r in train if r['event'] != event]
                validation = [r for r in train if r['event'] == event]
                fitted = fit(training, variant, builder)
                guesses = [predict(fitted, r, builder) for r in validation]
                folds.append({'event': event, 'metrics': metrics(validation, guesses),
                              'trade_slope': fitted['raw_slopes']['trade']})
                pooled_rows.extend(validation)
                pooled_guesses.extend(guesses)
            fitted = fit(train, variant, builder)
            entry.update({'pooled': metrics(pooled_rows, pooled_guesses),
                          'august': metrics(dev, [predict(fitted, r, builder) for r in dev]),
                          'folds': folds, 'model': fitted, 'raw_slopes': fitted['raw_slopes'],
                          'source': 'new_isolated_fit'})
        entry['coefficient_drift'] = {k: {'baseline': slopes[k], 'candidate': entry['raw_slopes'][k],
                                          'absolute': abs(entry['raw_slopes'][k]-slopes[k])}
                                      for k in slopes}
        results.append(entry)
    record = {'experiment_id': datetime.now(timezone.utc).strftime('trade-window-%Y%m%dT%H%M%SZ'),
              'experiment_kind': PLAN['name'], 'dataset_sha256': digest, 'plan': PLAN,
              'code_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              'code_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'normalized_map_hashes': provenance, 'baseline_parity_mismatches': 0,
              'train_rows': len(train), 'august_rows': len(dev), 'held_out_clean_rows': held,
              'windows': results, 'final_test_evaluated': False}
    with LOG.open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(record)+'\n')
    (ROOT/'data/research/experiments/trade-window-isolated-v1.json').write_text(json.dumps(record, indent=2))
    print(json.dumps([{k: row[k] for k in ('seconds', 'train_distribution')}
                      | {'pooled_mae': row['pooled']['mae'], 'august_mae': row['august']['mae']}
                      for row in results], indent=2))


if __name__ == '__main__':
    main()
