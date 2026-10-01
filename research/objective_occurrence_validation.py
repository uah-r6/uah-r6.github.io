"""Validate a replay-only occurrence hypothesis; no player objective credit.

Frozen before running: exactly one state1 on one entity establishes a candidate
plant. If the score-derived round winner is Defense, it additionally implies a
completed disable under Bomb rules. A later state0 with Attack winning is not
a disable. No timer threshold, public label, or parser winCondition is used.
This remains research until independently validated beyond the discovery maps.
"""
import json

from objective_transition_probe import ROOT, replay_file


def occurrences(events, winner_side, game_mode):
    if game_mode != 'Bomb' or winner_side not in ('Attack', 'Defense'):
        return {'plant': False, 'disable': False, 'status': 'unsupported_round'}
    plants = [e for e in events if e['value'] == 1]
    if not plants:
        return {'plant': False, 'disable': False, 'status': 'no_plant_state'}
    if len(plants) != 1 or len({e['entity'] for e in events}) != 1:
        return {'plant': False, 'disable': False, 'status': 'ambiguous_state_sequence'}
    if any(e['value'] not in (0, 1) or e['offset'] < plants[0]['offset'] for e in events):
        return {'plant': False, 'disable': False, 'status': 'ambiguous_state_sequence'}
    return {'plant': True, 'disable': winner_side == 'Defense',
            'status': 'candidate_only', 'actor': None,
            'disable_source': 'plant_state_and_defense_score_win' if winner_side == 'Defense' else None}


def main():
    path = ROOT / 'data/research/diagnostics/objective-encoding-validation/summary.json'
    rows = json.loads(path.read_text())['rounds']
    reports, mismatches = [], []
    derived = {}
    for row in rows:
        rec, _ = replay_file(row['match_id'], row['round'])
        if rec.parent.name not in derived:
            derived[rec.parent.name] = json.loads((ROOT / 'data/research/derived' / (rec.parent.name+'.json')).read_text())
        match = derived[rec.parent.name]
        round_ = next(r for r in match['rounds'] if r['number'] == row['round'])
        sides = {p['side'] for p in round_['players'] if p['team'] == round_['winner']}
        side = next(iter(sides)) if len(sides) == 1 else None
        result = occurrences(row['events'], side, match['game_mode'])
        expected = {kind: any(e['type'] == kind for e in row['public_objectives']) for kind in ['plant','disable']}
        report = {'match_id': row['match_id'], 'round': row['round'], 'winner_side': side,
                  'result': result, 'expected': expected}
        reports.append(report)
        if any(result[k] != expected[k] for k in expected):
            mismatches.append(report)
    output = {'rounds': len(reports), 'plant_candidates': sum(r['result']['plant'] for r in reports),
              'disable_candidates': sum(r['result']['disable'] for r in reports),
              'mismatches': mismatches, 'results': reports}
    (path.parent / 'occurrence-validation.json').write_text(json.dumps(output, indent=2))
    print(json.dumps({k:v for k,v in output.items() if k != 'results'},indent=2))


if __name__ == '__main__':
    main()
