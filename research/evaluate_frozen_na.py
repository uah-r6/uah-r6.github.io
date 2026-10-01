"""One-time reserved NA Stage 2 evaluation of the committed frozen model."""
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import statistics
import subprocess

from expanded_fit import ROOT, OBSERVATIONS, PLAN as SPLIT
from fit_models import predict, evaluate

FROZEN = ROOT/'research/frozen-rating-candidate.json'
OUTPUT = ROOT/'research/final-na-evaluation.json'
REPORT = ROOT/'research/output/final-na-rating-evaluation.md'


def metrics(rows, guesses):
    result = evaluate(rows, guesses)
    result['median_abs_error'] = statistics.median(abs(g-r['rating']) for r, g in zip(rows, guesses))
    result['mean_error'] = statistics.mean(g-r['rating'] for r, g in zip(rows, guesses))
    return result


def grouped(rows, guesses):
    buckets = defaultdict(list)
    for row, guess in zip(rows, guesses):
        n = len(row['rounds'])
        trade = sum(r['deaths_traded']+r['kills_traded'] for r in row['rounds'])
        values = {
            'public_objective_credit': 'yes' if row['public']['plants']+row['public']['disables'] else 'no',
            'trade_activity': '>=2' if trade >= 2 else '<2',
            'kpr': '>=0.8' if row['derived']['kills']/n >= .8 else '<0.8',
            'survival': '>=0.3' if row['derived']['survived']/n >= .3 else '<0.3',
            'map': row['map']}
        for key, group in values.items():
            buckets[(key, group)].append((row, guess-row['rating']))
    return [{'dimension': key, 'group': group, 'rows': len(values),
             'maps': len({(r['match_id'], r['game_id']) for r, _ in values}),
             'mae': statistics.mean(abs(e) for _, e in values),
             'bias': statistics.mean(e for _, e in values)}
            for (key, group), values in sorted(buckets.items())]


def main():
    if OUTPUT.exists() or REPORT.exists():
        raise ValueError('Final evaluation already exists; do not repeat or overwrite')
    status = subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True)
    if status:
        raise ValueError('Working tree must be clean before final evaluation')
    subprocess.check_output(['git', 'ls-files', '--error-unmatch', str(FROZEN.relative_to(ROOT))],
                            cwd=ROOT, text=True)
    frozen = json.loads(FROZEN.read_text())
    if frozen['status'] != 'frozen_before_reserved_final_evaluation' or frozen['final_test_evaluated']:
        raise ValueError('Frozen record is not ready for one-time final evaluation')
    content = OBSERVATIONS.read_bytes()
    if hashlib.sha256(content).hexdigest() != frozen['dataset_sha256']:
        raise ValueError('Frozen dataset hash changed')
    # The final target is inspected only after the clean-tree/freeze/hash gates.
    rows = [r for r in map(json.loads, content.splitlines())
            if r['event'] == SPLIT['untouched_final_event'] and r['reserved_for_final_test']
            and r['fit_eligible']]
    if len(rows) != frozen['excluded_event_clean_counts'][SPLIT['untouched_final_event']] or len(rows) != 60:
        raise ValueError('Unexpected reserved cohort')
    if any(r['event'] in frozen['train_events'] for r in rows):
        raise ValueError('Final event overlaps training')
    candidate_predictions = [predict(frozen['model'], r, {}) for r in rows]
    collegiate_predictions = [r['derived']['rating'] for r in rows]
    candidate = metrics(rows, candidate_predictions)
    collegiate = metrics(rows, collegiate_predictions)
    grouped_residuals = grouped(rows, candidate_predictions)
    worst = [{**item, 'public_objective_credit': next(
        (r['public']['plants']+r['public']['disables'] for r in rows
         if r['event'] == item['event'] and r['map'] == item['map'] and r['player'] == item['player']), None)}
             for item in candidate['worst']]
    result = {
        'evaluation_id': datetime.now(timezone.utc).strftime('frozen-na-%Y%m%dT%H%M%SZ'),
        'frozen_candidate_sha256': hashlib.sha256(FROZEN.read_bytes()).hexdigest(),
        'freeze_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'dataset_sha256': frozen['dataset_sha256'],
        'event': SPLIT['untouched_final_event'], 'rows': len(rows),
        'maps': len({(r['match_id'], r['game_id']) for r in rows}),
        'candidate': candidate, 'collegiate_v1': collegiate,
        'candidate_grouped_residuals': grouped_residuals,
        'candidate_worst_with_public_objective_label': worst,
        'final_test_evaluated_once': True,
        'decision_policy': 'Frozen model will not be retuned on this event.'}
    OUTPUT.write_text(json.dumps(result, indent=2)+'\n')
    md = ['# Frozen NA Stage 2 Rating evaluation', '',
          f"Freeze commit `{result['freeze_commit']}`; evaluation `{result['evaluation_id']}`. "
          f"Reserved event contains {len(rows)} clean player-map rows across {result['maps']} maps. "
          'The frozen model was evaluated once; no fit or feature selection used this event.', '',
          '| Model | MAE | RMSE | Median AE | Max AE | Exact rounded | Within .01 | .02 | .03 | .05 | .10 |',
          '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for name, score in [('Frozen raw eight-family', candidate), ('Live collegiate_v1', collegiate)]:
        md.append('| '+name+' | '+' | '.join(
            f"{score[k]:.4f}" for k in ('mae', 'rmse', 'median_abs_error', 'max_abs_error',
                                          'display_exact', 'within_0.01', 'within_0.02',
                                          'within_0.03', 'within_0.05', 'within_0.10'))+' |')
    md += ['', f"Frozen candidate signed bias: {candidate['mean_error']:+.4f}; collegiate_v1: {collegiate['mean_error']:+.4f}.",
           '', '## Largest candidate misses', '',
           '| Player | Map | Actual | Predicted | Error | Public objective credits |',
           '| --- | --- | ---: | ---: | ---: | ---: |']
    for item in worst:
        md.append(f"| {item['player']} | {item['map']} | {item['actual']:.2f} | {item['predicted']:.4f} | {item['error']:+.4f} | {item['public_objective_credit']} |")
    md += ['', '## Descriptive residual groups', '',
           'Groups overlap and rows from the same map are correlated. Public objective credits are analysis labels only; they were never model inputs.', '',
           '| Dimension | Group | Rows | Maps | MAE | Signed bias |',
           '| --- | --- | ---: | ---: | ---: | ---: |']
    for group in grouped_residuals:
        md.append(f"| {group['dimension']} | {group['group']} | {group['rows']} | {group['maps']} | {group['mae']:.4f} | {group['bias']:+.4f} |")
    md += ['', 'The model stays frozen regardless of this result. This event cannot be reused as an untouched final test for a revised model. The live/default Rating and public site remain unchanged.', '']
    REPORT.write_text('\n'.join(md), encoding='utf-8')
    print(json.dumps({'candidate_mae': candidate['mae'], 'collegiate_v1_mae': collegiate['mae'],
                      'n': len(rows), 'maps': result['maps'], 'evaluation_id': result['evaluation_id']}, indent=2))


if __name__ == '__main__':
    main()
