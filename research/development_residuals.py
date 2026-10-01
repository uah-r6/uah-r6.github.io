"""Describe development errors from saved models without refitting or final access."""
from collections import defaultdict
import hashlib
import json
import statistics

from expanded_fit import select_groups, PLAN as SPLIT, OBSERVATIONS, LOG, ROOT
from fit_models import predict as baseline_predict
from multikill_experiment import predict
from opening_experiment import features


def summary(values):
    errors = [e for _, e in values]
    return {'n': len(values), 'maps': len({(r['match_id'], r['game_id']) for r, _ in values}),
            'mae': statistics.mean(abs(e) for e in errors), 'bias': statistics.mean(errors)}


def describe(rows, guesses):
    groups = defaultdict(list)
    for r, g in zip(rows, guesses):
        rounds = r['rounds']
        n = len(rounds)
        total = lambda k: sum(p[k] for p in rounds)
        dominant = lambda side: max(sorted({p['operator'] for p in rounds if p['side'] == side}),
                                   key=lambda op: sum(p['operator'] == op and p['side'] == side for p in rounds), default='none')
        values = {
            'event': r['event'], 'roster_id': str(r['roster_id']), 'player': str(r['player_id']),
            'length': 'short <=9' if n <= 9 else 'regulation 10-12' if n <= 12 else 'overtime 13+',
            'kost': '<0.5' if total('kost_rounds')/n < .5 else '0.5-0.75' if total('kost_rounds')/n < .75 else '>=0.75',
            'survival': '<0.25' if total('survived')/n < .25 else '>=0.25',
            'opening_activity': 'none' if total('opening_kills')+total('opening_deaths') == 0 else 'present',
            'trades': 'none' if total('deaths_traded')+total('kills_traded') == 0 else 'present',
            'clutch': 'present' if total('clutches') else 'none',
            'multikill': 'present' if any(p['kills'] >= 2 for p in rounds) else 'none',
            'public_objective_label': 'present' if r['public']['plants']+r['public']['disables'] else 'none',
            'dominant_attack_operator': dominant('Attack'),
            'dominant_defense_operator': dominant('Defense')}
        for k, v in values.items():
            groups[(k, v)].append((r, g-r['rating']))
    return [{'dimension': k, 'group': v, **summary(samples)} for (k, v), samples in sorted(groups.items())]


def main():
    content = OBSERVATIONS.read_bytes()
    saved = json.loads((ROOT/'data/research/experiments/separate-openings-v1.json').read_text())
    if hashlib.sha256(content).hexdigest() != saved['dataset_sha256']:
        raise ValueError('Saved model/data mismatch')
    train, dev, _ = select_groups(list(map(json.loads, content.splitlines())), SPLIT)
    records = list(map(json.loads, LOG.read_text().splitlines()))
    prior = next(r for r in records if r['experiment_id'] == saved['plan']['baseline_id'])
    baseline = describe(dev, [baseline_predict(prior['model'], r, {}) for r in dev])
    rows, guesses = [], []
    for fold in saved['folds']:
        validation = [r for r in train if r['event'] == fold['event']]
        rows.extend(validation)
        guesses.extend(predict(fold['model'], r, features) for r in validation)
    pooled = describe(rows, guesses)
    result = {'baseline_august': baseline, 'separate_openings_event_held_out': pooled,
              'final_test_evaluated': False, 'dataset_sha256': saved['dataset_sha256'],
              'note': 'Public objective labels are diagnostic groups only, never model inputs. Each row is a player-map; within-map rows are correlated. Operator groups use modal operator, not side-specific rating targets. Roster ID denotes team grouping, not verified team name. No region/role labels are inferred.'}
    (ROOT/'data/research/experiments/development-residuals.json').write_text(json.dumps(result, indent=2))
    text = ['# Development residual review - 2026-10-01', '', result['note'], '',
            'Saved models only; no refits. Both September events excluded. Small cells are descriptive and are not grounds for player/team/operator adjustments.', '']
    for title, groups in [('Existing baseline: August development', baseline), ('Separate-opening diagnostic: seven held-out event folds', pooled)]:
        text += [f'## {title}', '', '| Dimension | Group | Player-maps | Maps | MAE | Signed bias |', '| --- | --- | ---: | ---: | ---: | ---: |']
        for g in groups:
            if g['dimension'] in {'player', 'roster_id', 'dominant_attack_operator', 'dominant_defense_operator'}:
                continue
            text.append(f"| {g['dimension']} | {g['group']} | {g['n']} | {g['maps']} | {g['mae']:.4f} | {g['bias']:+.4f} |")
        text.append('')
    text += ['Full player/roster/operator group diagnostics are cached privately in `data/research/experiments/development-residuals.json`. No side-level rating or role target exists in these observations, so those effects cannot be separately estimated from map-level errors.', '']
    (ROOT/'research/output/development-residuals.md').write_text('\n'.join(text), encoding='utf-8')
    print('Saved development residual report; no final ratings evaluated.')


if __name__ == '__main__':
    main()
