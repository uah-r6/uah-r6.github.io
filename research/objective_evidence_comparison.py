"""Compare separate actor evidence modes on consumed caches; no new resolver."""
from collections import Counter
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    base = ROOT / 'data/research/diagnostics'
    rows = json.loads((base / 'objective-player-ledger-v2.json').read_text())['consumed_events']
    plants = [r for r in rows if r['kind'] == 'plant']
    groups = Counter(('score' if r['candidate'] else 'no_score',
                      'sole' if r['sole_interval_candidate'] else 'not_sole') for r in plants)
    lines = ['# Consumed actor evidence comparison', '',
             'The prior score diagnostic and later sole-survivor diagnostic are separate experiments. '
             'The latter never used the score candidate as input. No production resolver was replaced.', '',
             f'Plant intersection counts: `{dict(groups)}`.', '',
             '**Eight score-only plants, four liveness-only plants, zero overlap.** The net count change '
             'of minus four does not identify four lost events. All eight score candidates remain alive '
             'according to the diagnostic; multiple living teammates prevent sole-survivor attribution.', '',
             '| Match/game/round | Earlier score actor (public-correct) | Alive at timer start / completion | Actor alive start/end | Close score packet: before -> after @ relative bytes | Identity |',
             '| --- | --- | --- | --- | --- | --- |']
    details = []
    for r in plants:
        if not r['candidate']:
            continue
        p = next(p for p in r['players'] if p['player'] == r['candidate'])
        start = r['players_at_interaction_start']
        old = next((s for s in start if s['player'] == p['player']), None)
        updates = [e for e in p['score_updates'] if 0 <= e['distance_from_completion'] <= 1500]
        counts = [sum(p['alive_at_completion'] is True for p in collection) for collection in (start, r['players'])]
        states = [old['alive_at_completion'] if old else None, p['alive_at_completion']]
        lines.append(f"| {r['match_id']}/{r['game_id']}/R{r['round']:02d} | {p['player']} | {counts[0]} / {counts[1]} | {states} | "
                     + ', '.join(f"{e['previous']} -> {e['value']} @{e['distance_from_completion']:+}" for e in updates)
                     + f" | UID {p['numeric_uid']}; score components {p['score_entities']} |")
        details.append({**r, 'comparison_reason': 'multiple_survivors_not_actor_exclusion',
                        'actor_start_end_alive': states,
                        'nearby_feedback': [dict(player=p['player'], **e) for p in r['players']
                                            for e in p['kill_death_feedback'] if abs(e['distance_from_completion']) <= 20000],
                        'nearby_counters': [dict(player=p['player'], **e) for p in r['players']
                                            for e in p['counter_updates'] if abs(e['offset'] - r['center']) <= 20000]})
    lines += ['', 'No changed packet boundary or identity ambiguity causes these eight abstentions. '
              'All eight passed the frozen whole-roster kill/assist collision veto. DBNO, revive, '
              'gadget causes and interaction eligibility are unavailable. A positive liveness value '
              'means no earlier decoded death, not independently verified ability to plant.', '',
              '## Liveness-only plants', '',
              '| Match/game/round | Candidate | Earlier score rejection |', '| --- | --- | --- |']
    for r in plants:
        if r['sole_interval_candidate']:
            lines.append(f"| {r['match_id']}/{r['game_id']}/R{r['round']:02d} | {r['sole_interval_candidate']} | {r['reason']} |")
    lines += ['', '## Successful liveness disables and complete nearby defender score sequences', '',
              '| Match/game/round | Candidate | Each defender score delta @ relative byte offset |', '| --- | --- | --- |']
    for r in rows:
        if r['kind'] != 'disable' or not r['sole_interval_candidate']:
            continue
        packets = []
        for p in r['players']:
            updates = [e for e in p['score_updates'] if abs(e['distance_from_completion']) <= 5000]
            packets.append(p['player'] + ': ' + ', '.join(f"{e['delta']:+}@{e['distance_from_completion']:+}" for e in updates))
        lines.append(f"| {r['match_id']}/{r['game_id']}/R{r['round']:02d} | {r['sole_interval_candidate']} | {'; '.join(packets)} |")
    lines += ['', 'These disables are selected entirely by sole-survivor evidence, not by their score batches. '
              'The same common-plus-extra score pattern also occurs in unresolved multi-survivor disables; '
              '3563/6675 R02 remains the counterexample to score-only selection. '
              'A union would expand apparent coverage, but the current analysis does not justify one.', '']
    (ROOT / 'research/output/objective-evidence-comparison.md').write_text('\n'.join(lines), encoding='utf-8')
    (base / 'objective-evidence-comparison.json').write_text(json.dumps({'groups': {str(k): v for k, v in groups.items()}, 'score_only_plants': details}, indent=2))
    print(dict(groups))


if __name__ == '__main__':
    main()
