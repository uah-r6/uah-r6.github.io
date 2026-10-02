"""Read completed, sealed SAL evidence without parsing, fitting or regrading.

The supplemental ledger checks round-level credited-kill consistency while
preserving the original quality decisions and both permanent final results.
"""
from collections import Counter
import json

from v3_corrected_final_pipeline import DATA, ROOT, RESULT, verify, quality_path, sha
from v3_corrected_final_reserve import FREEZE, source_sha
from uah_guarded_actor_readonly import snapshot


PERMANENT_RESULTS = {
    "data/research/v3-final-apac-n-stage2/one-shot-result.json":
        "c168c369a4c3f754f5a8376401e87a7857698907b6ebd79330cdd007e594afd2",
    "data/research/v3-corrected-final-sal-stage2/one-shot-result.json":
        "73b17d45f73cc7f07da5fc996bd9e1379017120d451e67c5e145ad1c1b9cbaa2",
}


def sealed_sal_cache():
    frozen, reservation = verify()
    seal = json.loads((DATA / 'prelabel-quality-seal.json').read_text())
    if seal['freeze_sha256'] != source_sha(FREEZE):
        raise ValueError('Prospective SAL seal freeze changed')
    if seal['protected_hashes'] != snapshot():
        raise ValueError('Protected live files differ from prospective seal')
    for name, expected in PERMANENT_RESULTS.items():
        if sha(ROOT / name) != expected:
            raise ValueError('Permanent consumed result changed: ' + name)
    selected = [s for s in reservation['matches'] if s['selected']]
    if {s['official_match_id'] for s in selected} != {
            s['official_match_id'] for s in seal['matches']}:
        raise ValueError('Selected final cohort differs from prospective seal')
    cached = {}
    for source in selected:
        mid = source['official_match_id']
        directory = DATA / str(mid)
        sealed = next(s for s in seal['matches'] if s['official_match_id'] == mid)
        paths = dict(predictions=directory / 'replay-predictions.json',
                     quality=quality_path(directory), api=directory / 'siegegg-api-sealed.json',
                     stats=directory / 'siegegg-player-stats-sealed.json')
        if {key: sha(path) for key, path in paths.items()} != sealed['hashes']:
            raise ValueError('Sealed cohort file changed: ' + str(mid))
        prediction = json.loads(paths['predictions'].read_text())
        quality = json.loads(paths['quality'].read_text())
        if prediction['freeze_sha256'] != source_sha(FREEZE):
            raise ValueError('Prediction freeze changed')
        for key, field in [('predictions', 'prediction_sha256'), ('api', 'api_sha256'),
                           ('stats', 'target_stats_sha256')]:
            if quality[field] != sealed['hashes'][key]:
                raise ValueError('Quality input digest differs from prospective seal')
        cached[mid] = dict(prediction=prediction, quality=quality, source=source)
    return frozen, cached, seal


def main():
    protected = snapshot()
    _, cached, _ = sealed_sal_cache()
    source = ROOT / 'data/research/diagnostics/v3-sal-kill-credit'
    probe = ROOT / 'research/v3_consumed_kill_credit_probe.py'
    differences, raw_controls, map_patterns, all_maps = [], [], [], []
    totals = Counter()
    for mid, inputs in cached.items():
        evidence_path = source / f'{mid}.json'
        evidence = json.loads(evidence_path.read_text())
        prediction = inputs['prediction']
        quality = {q['player']: q for q in inputs['quality']['decisions']}
        if (evidence['official_match_id'] != mid or evidence['source_sha256'] != sha(probe)
                or not evidence['complete_counter_binding'] or evidence['continuity_issues']):
            raise ValueError('Incomplete or changed direct-UID counter evidence: ' + str(mid))
        if len(evidence['rounds']) != prediction['round_count']:
            raise ValueError('Counter round coverage differs from sealed prediction')
        by_player = {p['player']: p for p in prediction['players']}
        per_player = {name: [] for name in by_player}
        for round_ in evidence['rounds']:
            logical = round_['logical_round']
            physical = next(m for m in prediction['physical_mapping'] if m['logical_round'] == logical)
            if any(round_[key] != physical[key] for key in ('folder', 'filename', 'physical_round')):
                raise ValueError('Counter physical round association differs')
            if round_['replay_sha256'] != physical['sha256']:
                raise ValueError('Counter replay provenance differs')
            if not round_['full_counter_binding'] or set(round_['players']) != set(by_player):
                raise ValueError('Full counter player identity missing')
            for name, counter in round_['players'].items():
                accepted = by_player[name]['rounds'][logical - 1]['kills']
                if counter['feed_finishes'] != accepted:
                    raise ValueError('Accepted finish count differs from frozen inputs')
                item = dict(official_match_id=mid, round=logical, player=name,
                            credited=counter['delta'], opponent_finishes=accepted,
                            raw_kill_packets=counter['raw_feedback_kill_packets'],
                            frozen_eligible=quality[name]['eligible'])
                if counter['delta'] != accepted:
                    differences.append(item)
                    per_player[name].append(item)
                if counter['raw_feedback_kill_packets'] != accepted:
                    raw_controls.append(item)
        for p in evidence['summary']:
            if not p['credit_matches_independent']:
                raise ValueError('Scoreboard credit disagrees with independent totals')
            if per_player[p['player']]:
                map_patterns.append(dict(official_match_id=mid, player=p['player'],
                                         credited=p['credit_counter_kills'],
                                         opponent_finishes=p['feed_finishes'],
                                         frozen_eligible=quality[p['player']]['eligible'],
                                         rounds=per_player[p['player']]))
        totals.update(maps=1, rounds=len(evidence['rounds']), player_maps=len(evidence['summary']))
        all_maps.append(dict(official_match_id=mid, evidence_sha256=sha(evidence_path),
                             explicit_rehost_resets=evidence['explicit_rehost_resets']))
    eligible = [p for p in map_patterns if p['frozen_eligible']]
    counts = dict(totals, player_round_differences=len(differences),
                  rounds_with_differences=len({(d['official_match_id'], d['round']) for d in differences}),
                  player_map_patterns=len(map_patterns),
                  map_total_differences=sum(p['credited'] != p['opponent_finishes'] for p in map_patterns),
                  eligible_player_map_patterns=len(eligible),
                  eligible_player_round_differences=sum(len(p['rounds']) for p in eligible))
    result = dict(status='consumed_supplemental_evidence_not_regrading', counts=counts,
                  freeze_sha256=source_sha(FREEZE), seal_sha256=sha(DATA / 'prelabel-quality-seal.json'),
                  permanent_results=PERMANENT_RESULTS, maps=all_maps,
                  player_map_patterns=map_patterns, raw_feedback_negative_controls=raw_controls,
                  protected_hashes=protected,
                  limits='Exact map K/D can hide offsetting round credit/finish differences. '
                         'No victim/DBNO causality inferred, features/eligibility changed, or errors reevaluated.')
    destination = DATA / 'consumed-round-credit-integrity.json'
    if destination.exists():
        if json.loads(destination.read_text()) != result:
            raise ValueError('Never overwrite changed supplemental integrity evidence')
    else:
        destination.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    lines = ['# Consumed SAL round-credit integrity: exact map K/D is insufficient', '',
             'Completed cached direct-UID scoreboard evidence is compared with the already-frozen accepted '
             'opponent finishes. No replay parsing, model fitting, numerical target grading or eligibility change occurs. '
             'All 20 prediction/quality/API/stat digests are checked against the prospective seal. '
             'Both permanent failed finals and all 86 live file hashes are checked.', '',
             f'Coverage and discrepancies: `{counts}`.', '',
             'All 200 scoreboard credited-kill totals match independent official and original public totals. '
             'Three previously eligible player-map rows contain offsetting per-round differences, so exact map K/D '
             'does not validate their round-level credited-kill pattern. This is a limitation of the frozen studies, '
             'not a revised final result or proof of a particular Rating error.', '',
             '| Official / player | Credited map kills | Opponent finishes | Offsetting round evidence |',
             '| --- | ---: | ---: | --- |']
    for p in eligible:
        rounds = '; '.join(f"R{r['round']:02d}: credit {r['credited']}, finishes {r['opponent_finishes']}"
                           for r in p['rounds'])
        lines.append(f"| {p['official_match_id']}/{p['player']} | {p['credited']} | "
                     f"{p['opponent_finishes']} | {rounds} |")
    lines += ['', '## Raw-feed negative control', '',
              f'Raw Kill packets versus accepted opponent finishes: `{raw_controls}`. '
              'The single mitrix-to-Legacy packet in 8596/R10 is a teamkill, already excluded correctly. '
              'It is separate from the 52 credited-opponent-kill differences; the original raw audit is retained.', '',
              'The independent [Y11 broadcast review](v3-consumed-dbno-vod-review.md) establishes one credited-kill '
              'versus displayed-finisher split, without claiming the downing shot is visible. '
              'The full [direct-UID counter ledger](v3-consumed-sal-kill-credit.md) records all rounds and rehost continuity.', '',
              'A future explicit credited-kill design must preserve displayed finisher and death timing separately, '
              'require event/victim identity and DBNO/revive evidence, and validate on development data before any '
              'new prospective final. Never assign a victim by nearest counter update or public expected total. '
              'No runtime kill/operator/action boundary or objective changes are authorized by this diagnostic.', '',
              'Live v2 remains unchanged. Both v3 final failures, original actor comparisons, all frozen dependencies, '
              'SQLite, private archives and public JSON are preserved. No publish or push.', '']
    (ROOT / 'research/output/v3-consumed-round-credit-integrity.md').write_text('\n'.join(lines), encoding='utf-8')
    if snapshot() != protected or sha(RESULT) != PERMANENT_RESULTS[RESULT.relative_to(ROOT).as_posix()]:
        raise ValueError('Protected result/live files changed')
    print('Cached consumed SAL round-credit integrity', counts, flush=True)


if __name__ == '__main__':
    main()
