"""Consumed SAL residual/contribution audit; never fits or revises a model."""
from collections import defaultdict
import json
import random

from v3_corrected_final_pipeline import DATA, RESULT, ROOT, verify, sha
from fit_models import FEATURES
from uah_comparison import contribution
from uah_guarded_actor_readonly import snapshot


def summarize(rows):
    a = [abs(r['v2'] - r['rating']) for r in rows]
    b = [abs(r['v3'] - r['rating']) for r in rows]
    return dict(n=len(rows), baseline_mae=sum(a) / len(a), candidate_mae=sum(b) / len(b),
                baseline_bias=sum(r['v2']-r['rating'] for r in rows)/len(rows),
                candidate_bias=sum(r['v3']-r['rating'] for r in rows)/len(rows),
                baseline_within005=sum(v <= .05 for v in a)/len(a),
                candidate_within005=sum(v <= .05 for v in b)/len(b),
                improved=sum(y < x for x,y in zip(a,b)), worsened=sum(y > x for x,y in zip(a,b)))


def main():
    before = snapshot()
    frozen, _ = verify()
    permanent_sha = sha(RESULT)
    result = json.loads(RESULT.read_text())
    rows, groups = [], defaultdict(list)
    for d in result['details']:
        pred = json.loads((DATA / str(d['official_match_id']) / 'replay-predictions.json').read_text())
        player = next(r for r in pred['players'] if r['player'] == d['player'])
        feature = dict(rounds=player['rounds'])
        ca, cb = contribution(frozen['baseline_model'], feature), contribution(frozen['model'], feature)
        changes = {name: cb[name] - ca[name] for name in FEATURES}
        intercept = frozen['model']['intercept'] - frozen['baseline_model']['intercept']
        if abs(sum(changes.values()) + intercept - (d['v3'] - d['v2'])) > 1e-10:
            raise ValueError('Feature decomposition does not sum to frozen prediction delta')
        raw_objective = d['objectives'] / pred['round_count'] * frozen['model']['weights_standardized']['objectives'] / frozen['model']['scales']['objectives']
        row = d | dict(ae_v2=abs(d['v2'] - d['rating']), ae_v3=abs(d['v3'] - d['rating']),
                       delta_ae=abs(d['v3'] - d['rating']) - abs(d['v2'] - d['rating']),
                       contribution_changes=changes, raw_objective_addition=raw_objective,
                       round_count=pred['round_count'])
        rows.append(row)
        groups[d['official_match_id']].append(row)
    if len(rows) != result['evidence']['clean_rows']:
        raise ValueError('Final cohort changed')
    strata = {'all': summarize(rows),
              'verified_objective_positive': summarize([r for r in rows if r['objectives']]),
              'verified_objective_zero': summarize([r for r in rows if not r['objectives']])}
    for n in sorted({r['objectives'] for r in rows}):
        strata['objective_count_' + str(n)] = summarize([r for r in rows if r['objectives'] == n])
    roster = {str(rid): summarize([r for r in rows if r['roster_id'] == rid])
              for rid in sorted({r['roster_id'] for r in rows})}
    rng = random.Random(20261002)
    keys = sorted(groups)
    bootstrap = []
    for _ in range(2000):
        sampled = [r for key in rng.choices(keys, k=len(keys)) for r in groups[key]]
        m = summarize(sampled)
        bootstrap.append(m['candidate_mae'] - m['baseline_mae'])
    bootstrap.sort()
    interval = [bootstrap[49], bootstrap[1949]]
    diagnostics = dict(status='consumed_descriptive_only_no_refit_no_revised_gates',
                       permanent_result_sha256=permanent_sha, strata=strata, roster_strata=roster,
                       map_cluster_bootstrap=dict(resamples=2000, seed=20261002,
                                                  mae_delta_percentile_95_interval=interval,
                                                  limitation='Small regional cohort; descriptive paired uncertainty, not a new acceptance gate or independent validation'),
                       rows=rows)
    (DATA/'consumed-diagnostics.json').write_text(json.dumps(diagnostics, indent=2)+'\n', encoding='utf-8')
    lines = ['# Corrected-KOST SAL consumed final diagnostics', '',
             'The permanent one-shot result fails its 80% within0.05 gate. '
             'This report describes the already-consumed fixed cohort; it fits nothing, changes no gate, '
             'and does not admit excluded rows or revise historical metrics.', '',
             '## Verified objective strata', '',
             '| Stratum | N | v2 MAE | v3 MAE | v2 signed bias | v3 signed bias | v2 within .05 | v3 within .05 | Improved / worsened |',
             '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |']
    for name,m in strata.items():
        lines.append(f"| {name} | {m['n']} | {m['baseline_mae']:.5f} | {m['candidate_mae']:.5f} | "
                     f"{m['baseline_bias']:+.5f} | {m['candidate_bias']:+.5f} | {m['baseline_within005']:.1%} | "
                     f"{m['candidate_within005']:.1%} | {m['improved']} / {m['worsened']} |")
    lines += ['', f'Paired map-cluster bootstrap (2000 draws, seed20261002, {len(groups)} maps): '
              f'95% percentile interval for v3 minus v2 MAE [{interval[0]:+.5f}, {interval[1]:+.5f}]. '
              'Descriptive uncertainty only: no new gate, tuning or claim of a fresh evaluation.', '',
              '## Every objective-positive player-map residual', '',
              'Raw objective addition is coefficient times objectives/round, without centering. '
              'Total prediction change also includes all frozen coefficient/intercept drift. '
              'These observational strata cannot isolate a causal effect of objectives.', '',
              '| Official / player | Objectives | Target | v2 | v3 | AE change | Raw objective addition |',
              '| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    for r in sorted((r for r in rows if r['objectives']), key=lambda r:(r['official_match_id'],r['player'])):
        lines.append(f"| {r['official_match_id']}/{r['player']} | {r['objectives']} | {r['rating']:.3f} | "
                     f"{r['v2']:.3f} | {r['v3']:.3f} | {r['delta_ae']:+.5f} | {r['raw_objective_addition']:+.5f} |")
    lines += ['', '## Largest 15 candidate errors', '',
              '| Official / player | Target | v2 | v3 | v3 AE | Objectives |',
              '| --- | ---: | ---: | ---: | ---: | ---: |']
    largest = sorted(rows, key=lambda r:r['ae_v3'], reverse=True)[:15]
    for r in largest:
        lines.append(f"| {r['official_match_id']}/{r['player']} | {r['rating']:.3f} | {r['v2']:.3f} | "
                     f"{r['v3']:.3f} | {r['ae_v3']:.5f} | {r['objectives']} |")
    lines += ['', '## Frozen feature contribution changes for the largest errors', '',
              '| Official / player | ' + ' | '.join(FEATURES) + ' |',
              '| --- | ' + ' | '.join(['---:']*len(FEATURES)) + ' |']
    for r in largest:
        lines.append(f"| {r['official_match_id']}/{r['player']} | " +
                     ' | '.join(f"{r['contribution_changes'][n]:+.4f}" for n in FEATURES) + ' |')
    lines += ['', f'Intercept drift {intercept:+.8f}. All141 full decompositions are cached separately. '
              'The unchanged nine-family feature contract is not an operator-relative model; unresolved professional operators '
              'remain a compatibility limitation and were not guessed or introduced into this candidate.', '',
              f'Permanent result SHA256 `{permanent_sha}` and all{len(before)} protected local hashes unchanged. '
              'Live v2, SQLite, private archives and public JSON remain unchanged. No fit, deployment or publishing.', '']
    (ROOT/'research/output/v3-corrected-final-sal-diagnostics.md').write_text('\n'.join(lines), encoding='utf-8')
    if sha(RESULT) != permanent_sha or snapshot() != before:
        raise ValueError('Permanent result or protected live data changed')
    print('Consumed descriptive strata', strata, 'MAE delta interval', interval, flush=True)


if __name__ == '__main__':
    main()
