"""Consumed-data test of a standalone plant score inside clock-tick boundaries.

This is an unfrozen hypothesis. Clock ticks are not network frames. Public
actor labels only grade the returned candidate, never define its interval.
"""
from bisect import bisect_right
from collections import Counter
import json

from objective_actor_liveness import feedback
from objective_score_delta_validation import grade
from objective_transition_probe import ROOT


def epochs(ticks):
    result = []
    for t in ticks:
        if not result or result[-1]['value'] != t['value']:
            result.append(t)
    return result


def candidate(row, deaths):
    if row['kind'] != 'plant':
        return None, 'disable_not_supported', {}
    mapping = {int(k): v[0] for k, v in row['identity']['entity_names'].items() if len(v) == 1}
    eligible = {p['username'] for p in row['header']['players']
                if row['header']['teams'][p['teamIndex']]['role'] == 'Attack'}
    bound = [p for p in mapping.values() if p in eligible]
    if len(bound) != len(eligible) or len(set(bound)) != len(eligible):
        return None, 'incomplete_identity', {}
    ticks = epochs(row['clock_ticks'])
    offsets = [t['offset'] for t in ticks]
    state_index = bisect_right(offsets, row['center']) - 1
    scores = [e for e in row['all_changes'] if e['counter'] == 'score' and e['delta'] > 0
              and mapping.get(e['entity']) in eligible and e['offset'] >= row['center']]
    if not scores or state_index < 0:
        return None, 'missing_score_or_clock', {}
    first_index = bisect_right(offsets, scores[0]['offset']) - 1
    if first_index not in (state_index, state_index + 1) or first_index + 1 >= len(ticks):
        return None, 'not_immediate_complete_clock_interval', {}
    start, end = ticks[state_index]['offset'], ticks[first_index + 1]['offset']
    interval = dict(start=start, end=end, state_tick=ticks[state_index]['value'],
                    score_tick=ticks[first_index]['value'])
    # Death lacking an offset cannot be placed before/after this interval.
    if any(d['offset'] <= 0 for d in deaths):
        return None, 'unknown_death_offset', interval
    if any(start <= d['offset'] < end for d in deaths):
        return None, 'kill_or_death_in_interval', interval
    if any(e['counter'] in ('kills', 'assists') and e['delta'] > 0 and start <= e['offset'] < end
           for e in row['all_changes']):
        return None, 'counter_in_interval', interval
    found = [e for e in scores if e['offset'] < end]
    if len(found) != 1 or found[0]['delta'] != 100:
        return None, 'not_single_standalone_increment', interval
    return mapping[found[0]['entity']], 'standalone_clock_interval', interval


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--development', action='store_true')
    args = parser.parse_args()
    base = ROOT / 'data/research/diagnostics'
    name = 'development' if args.development else 'extension'
    rows = json.loads((base / f'objective-score-structure-{name}.json').read_text())
    old = json.loads((base / 'objective-score-delta-validation/summary.json').read_text())['events']
    source = {s['siegegg_match_id']: s for s in json.loads((ROOT / 'research/sources.json').read_text())['matches']
              if s.get('siegegg_match_id')}
    records = []
    development = json.loads((base / 'objective-encoding-validation/summary.json').read_text())['rounds'] if args.development else []
    for row in rows:
        folder = next((ROOT / 'data/research/extracted').rglob(row['folder']))
        rec = next(folder.glob(f"*-R{row['round']:02d}.rec"))
        actor, reason, interval = candidate(row, feedback(rec)['events'])
        if args.development:
            reference = next(e for e in development if (e['match_id'], e['round']) == (row['match_id'], row['round']))
            reference = next(e for e in reference['public_objectives'] if e['type'] == row['kind'])
            label = reference.get('description', reference.get('html', ''))
        elif row['match_id'] == 4139:
            label = 'Raid plants defuser'
        else:
            reference = next(e for e in old if all(e[k] == row[k] for k in ('match_id', 'game_id', 'round', 'kind')))
            label = reference['public_actor'] + (' plants ' if row['kind'] == 'plant' else ' disables ') + 'defuser'
        target = json.loads((ROOT / f"data/research/targets/siegegg-match-{row['match_id']}-api.json").read_text())
        verdict = grade(actor, label, source[row['match_id']], target)
        records.append({k: row[k] for k in ('match_id','game_id','round','kind','build')}
                       | dict(candidate=actor, reason=reason, interval=interval, verdict=verdict))
    if args.development:
        for row in development:
            for event in row['public_objectives']:
                if not any((e['match_id'], e['round'], e['kind']) ==
                           (row['match_id'], row['round'], event['type']) for e in records):
                    records.append(dict(match_id=row['match_id'], game_id=None, round=row['round'],
                                        kind=event['type'], build=None, candidate=None,
                                        reason='no_completion_state_anchor', interval={}, verdict='unresolved'))
    counts = {kind: dict(Counter(e['verdict'] for e in records if e['kind'] == kind and (args.development or e['match_id'] != 4139)))
              for kind in ('plant','disable')}
    (base / f'objective-clock-candidate-{name}.json').write_text(json.dumps({'counts': counts, 'events': records}, indent=2))
    lines = ['# Standalone score / clock interval development experiment', '',
             'Consumed cases only. Unfrozen hypothesis; no production actor credit. See source function for exact logic. '
             'A candidate needs one +100 eligible score change before the first score tick ends, with that tick '
             'at completion or immediately next. Kill/death or positive kill/assist counter inside the interval '
             'vetoes the candidate. Unknown death offsets abstain. Disables are not selected by this plant-only mode.', '',
             f'{name.title()} counts: `{json.dumps(counts)}`.', '',
             '| Match/game/round/kind | Candidate | Verdict | Reason | Clock interval |', '| --- | --- | --- | --- | --- |']
    for e in records:
        lines.append(f"| {e['match_id']}/{e['game_id']}/R{e['round']:02d}/{e['kind']} | {e['candidate'] or 'unresolved'} | {e['verdict']} | {e['reason']} | {e['interval']} |")
    lines += ['', 'This experiment tests boundaries derived from replay clock changes rather than fixed byte gaps. '
              'It does not prove that the score is objective credit: gadget scores and delayed earlier scoring remain competing causes. '
              'The fresh reserve remains sealed. Every wrong result must be analyzed before any candidate freeze.', '']
    (ROOT / f'research/output/objective-clock-candidate-{name}.md').write_text('\n'.join(lines), encoding='utf-8')
    print(counts)
    print('wrong', [r for r in records if r['verdict'] == 'incorrect'])


if __name__ == '__main__':
    main()
