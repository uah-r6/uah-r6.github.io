"""Extend the liveness diagnostic to the already-consumed discovery cohort."""
from collections import Counter
import json

from objective_actor_liveness import (feedback, interaction_span, player_ledger,
                                      sole_interval_candidate)
from objective_production_check import candidate_raw
from objective_score_delta_validation import grade
from objective_transition_probe import ROOT, replay_file


def main():
    base = ROOT / 'data/research/diagnostics'
    sources = {s['siegegg_match_id']: s for s in json.loads((ROOT / 'research/sources.json').read_text())['matches']
               if s.get('siegegg_match_id')}
    rows = json.loads((base / 'objective-encoding-validation/summary.json').read_text())['rounds']
    records, raw_by_folder = [], {}
    for row in rows:
        if not row['public_objectives']:
            continue
        match_id, number = row['match_id'], row['round']
        rec, _ = replay_file(match_id, number)
        parsed = feedback(rec)
        if rec.parent not in raw_by_folder:
            raw_by_folder[rec.parent] = candidate_raw(rec.parent)
        baseline = raw_by_folder[rec.parent]['rounds'][number - 1]
        expected = [e for e in baseline['matchFeedback'] if e['type']['name'] in ('Kill', 'Death')]
        if expected != [e['feedback'] for e in parsed['events']]:
            raise ValueError(f'Feedback parity failed: {match_id} R{number:02d}')
        stem = f'{match_id}-R{number:02d}.json'
        scores = json.loads((base / 'objective-score-batch-cohort' / stem).read_text())['events']
        binding = json.loads((base / 'objective-score-identity' / stem).read_text())
        target = json.loads((ROOT / f'data/research/targets/siegegg-match-{match_id}-api.json').read_text())
        for kind in ('plant', 'disable'):
            states = row['events'] if kind == 'plant' else reversed(row['events'])
            center = next((e['offset'] for e in states if e['value'] == (1 if kind == 'plant' else 0)), None)
            # Occurrences are already independently validated. Labels only grade
            # the candidate below, never select its identity or timer run.
            labels = [e for e in row['public_objectives'] if e['type'] == kind]
            if not labels:
                continue
            if len(labels) != 1:
                raise ValueError(f'Ambiguous validated occurrence: {match_id} R{number:02d} {kind}')
            if center is None:
                # Older builds can validate completion by outcome/terminal timer
                # without this state packet. Do not substitute a label-derived
                # position for the present diagnostic's required anchor.
                records.append({'match_id': match_id, 'round': number, 'kind': kind,
                                'center': None, 'candidate': None, 'verdict': 'unresolved',
                                'reason': 'no_completion_state_anchor'})
                continue
            previous = max((e['offset'] for e in row['events'] if e['offset'] < center), default=0)
            span = interaction_span(parsed['timers'], center, previous)
            side = 'Attack' if kind == 'plant' else 'Defense'
            end = player_ledger(parsed['header'], parsed['events'], scores, binding, center, side)
            start = player_ledger(parsed['header'], parsed['events'], scores, binding,
                                  span['first_offset'], side) if span else []
            candidate = sole_interval_candidate(start, end)
            label = labels[0].get('description', labels[0].get('html', ''))
            verdict = grade(candidate, label, sources[match_id], target)
            records.append({'match_id': match_id, 'round': number, 'kind': kind,
                            'center': center, 'interaction_span': span, 'candidate': candidate,
                            'verdict': verdict, 'players_at_start': start, 'players_at_completion': end})
        print('checked', match_id, number, flush=True)
    counts = {kind: dict(Counter(e['verdict'] for e in records if e['kind'] == kind))
              for kind in ('plant', 'disable')}
    (base / 'objective-liveness-development.json').write_text(json.dumps({'counts': counts, 'events': records}, indent=2))
    lines = ['# Liveness diagnostic: original development cohort', '',
             'Consumed development evidence only. Same diagnostic as `objective_actor_liveness.py`; '
             'no production credit, no fresh reserve labels, no SQLite changes.', '',
             f'Results: `{json.dumps(counts)}`.', '',
             '| Match / physical round | Kind | Sole throughout complete timer-run candidate | Verdict |',
             '| --- | --- | --- | --- |']
    for e in records:
        lines.append(f"| {e['match_id']} / R{e['round']:02d} | {e['kind']} | {e['candidate'] or 'unresolved'} | {e['verdict']} |")
    lines += ['', 'Kill/death feedback from the research observer matched the cached parser feedback in every inspected physical round. '
              'DBNO and player interaction ability remain unavailable. A sole living player is a development candidate, not a validated production actor.', '']
    (ROOT / 'research/output/objective-liveness-development.md').write_text('\n'.join(lines), encoding='utf-8')
    print(json.dumps(counts))


if __name__ == '__main__':
    main()
