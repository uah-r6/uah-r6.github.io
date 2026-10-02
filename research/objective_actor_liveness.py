"""Read-only packet-ordered liveness and score audit on consumed actor cases.

Uses the parser's existing kill offsets; no new low-level kill decoder. Cached
raw evidence and private paths stay under data/research/diagnostics.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess

from objective_transition_probe import ROOT, replay_file
from objective_timer_audit import runs
from objective_score_delta_validation import grade
from objective_production_check import candidate_raw


def interaction_span(timers, center, previous_state):
    entries = [{'offset': t['offset'], 'timer': float(t['value']), 'player_id': ''}
               for t in timers if t['value']]
    eligible = [r for r in runs(entries) if 6.5 <= r['first'] <= 7.1 and r['last'] <= .1
                and r['n'] > 1
                and previous_state < r['first_offset'] <= r['last_offset'] < center]
    return eligible[-1] if eligible else None


def sole_interval_candidate(at_start, at_end):
    if not at_start or {p['player'] for p in at_start} != {p['player'] for p in at_end}:
        return None
    if any(p['alive_at_completion'] is None for p in at_start + at_end):
        return None
    first = [p['player'] for p in at_start if p['alive_at_completion'] is True]
    last = [p['player'] for p in at_end if p['alive_at_completion'] is True]
    return first[0] if len(first) == 1 and first == last else None


def feedback(rec):
    executable = ROOT / '.local-tools/bin/actor-feedback-probe.exe'
    signature = hashlib.sha256(executable.read_bytes() + rec.read_bytes()).hexdigest()
    cache = ROOT / 'data/research/diagnostics/actor-feedback'
    cache.mkdir(parents=True, exist_ok=True)
    dest = cache / (signature + '.json')
    if not dest.exists():
        run = subprocess.run([str(executable), str(rec.resolve())], check=True,
                             capture_output=True, text=True)
        dest.write_text(json.dumps(json.loads(run.stdout)[0]), encoding='utf-8')
    return json.loads(dest.read_text())


def player_ledger(header, feed, scores, binding, center, side):
    mapped = {int(k): names[0] for k, names in binding['entity_names'].items() if len(names) == 1}
    result = []
    for player in header['players']:
        if header['teams'][player['teamIndex']]['role'] != side:
            continue
        name = player['username']
        entities = [entity for entity, bound in mapped.items() if bound == name]
        deaths = [row for row in feed if
                  (row['feedback']['type']['name'] == 'Kill' and row['feedback'].get('target') == name)
                  or (row['feedback']['type']['name'] == 'Death' and row['feedback'].get('username') == name)]
        unresolved_death_offset = any(row['offset'] <= 0 for row in deaths)
        dead = any(0 < row['offset'] <= center for row in deaths)
        updates = [e for e in scores if e['entity'] in entities and e['counter'] == 'score']
        before = [e for e in updates if e['offset'] < center]
        score_before = before[-1]['value'] if before else updates[0]['previous'] if updates else None
        related = [row for row in feed if name in
                   (row['feedback'].get('username'), row['feedback'].get('target'))]
        result.append({'player': name, 'numeric_uid': player.get('id'),
                       'score_entities': entities, 'side': side,
                       'alive_at_completion': None if unresolved_death_offset else not dead,
                       'liveness_source': 'existing_parser_feedback_offsets',
                       'dbno_state': 'unavailable',
                       'score_before_completion': score_before,
                       'score_final': updates[-1]['value'] if updates else None,
                       'score_updates': [{**e, 'distance_from_completion': e['offset'] - center}
                                         for e in updates],
                       'kill_death_feedback': [{**e, 'distance_from_completion': e['offset'] - center}
                                               for e in related],
                       'counter_updates': [e for e in scores if e['entity'] in entities
                                           and e['counter'] in ('kills', 'assists')],
                       'actor': None})
    return result


def main():
    base = ROOT / 'data/research/diagnostics'
    validation = json.loads((base / 'objective-score-delta-validation/summary.json').read_text())['events']
    occurrence = json.loads((base / 'objective-occurrence-holdout/summary.json').read_text())['results']
    reports = []
    raw_by_folder = {}
    parity_rounds = set()
    sources = {s['siegegg_match_id']: s for s in json.loads((ROOT / 'research/sources.json').read_text())['matches']
               if s.get('siegegg_match_id')}
    for event in validation:
        folder, n = event['folder'], event['round']
        folders = [p for p in (ROOT / 'data/research/extracted').rglob(folder) if p.is_dir()]
        if len(folders) != 1:
            raise ValueError(f'Ambiguous replay folder: {folder}')
        physical = folders[0]
        recs = list(physical.glob(f'*-R{n:02d}.rec'))
        if len(recs) != 1:
            raise ValueError(f'Ambiguous physical round: {folder} R{n:02d}')
        rec = recs[0]
        parsed = feedback(rec)
        if folder not in raw_by_folder:
            raw_by_folder[folder] = candidate_raw(physical)
        baseline = raw_by_folder[folder]['rounds'][n - 1]
        expected = [e for e in baseline['matchFeedback'] if e['type']['name'] in ('Kill', 'Death')]
        if [e['feedback'] for e in parsed['events']] != expected:
            raise ValueError(f'Probe altered cached kill/death feedback: {folder} R{n:02d}')
        parity_rounds.add((folder, n))
        row = next(r for r in occurrence if r['folder'] == folder and r['round'] == n)
        states = row['events'] if event['kind'] == 'plant' else reversed(row['events'])
        center = next(e['offset'] for e in states if e['value'] == (1 if event['kind'] == 'plant' else 0))
        evidence = json.loads((base / f'objective-score-delta-validation/{folder}-R{n:02d}.json').read_text())
        side = 'Attack' if event['kind'] == 'plant' else 'Defense'
        players = player_ledger(parsed['header'], parsed['events'], evidence['ledger']['events'],
                                evidence['bindings'], center, side)
        previous = max((e['offset'] for e in row['events'] if e['offset'] < center), default=0)
        span = interaction_span(parsed['timers'], center, previous)
        sole = None
        at_start = []
        if span:
            at_start = player_ledger(parsed['header'], parsed['events'], evidence['ledger']['events'],
                                     evidence['bindings'], span['first_offset'], side)
            sole = sole_interval_candidate(at_start, players)
        target = json.loads((ROOT / f"data/research/targets/siegegg-match-{event['match_id']}-api.json").read_text())
        verdict = grade(sole, event['public_actor'] + ' plants defuser', sources[event['match_id']], target)
        reports.append({**event, 'center': center, 'players': players, 'interaction_span': span,
                        'players_at_interaction_start': at_start,
                        'sole_interval_candidate': sole, 'sole_interval_verdict': verdict})
    # Mandatory discovery control is separate from the consumed extension.
    rec, _ = replay_file(4139, 7)
    parsed = feedback(rec)
    evidence = json.loads((base / 'objective-score-batch-cohort/4139-R07.json').read_text())
    binding = json.loads((base / 'objective-score-identity/4139-R07.json').read_text())
    mandatory = player_ledger(parsed['header'], parsed['events'], evidence['events'], binding, 61871641, 'Attack')
    dest = base / 'objective-player-ledger-v2.json'
    dest.write_text(json.dumps({'consumed_events': reports, 'mandatory_4139_r07': mandatory,
                               'feedback_parity_rounds': len(parity_rounds)}, indent=2))
    lines = ['# Objective completion liveness audit', '',
             'Research only. Liveness uses existing parser kill/death feedback offsets. It is not an independent confirmation of victim identity, and DBNO/interaction ability is unavailable. No actors are credited.', '',
             '| Match / game / round | Kind | Alive eligible players at completion | Frozen score result | Sole throughout timer-run diagnostic |',
             '| --- | --- | --- | --- | --- |']
    for event in reports:
        alive = [p['player'] for p in event['players'] if p['alive_at_completion']]
        lines.append(f"| {event['match_id']} / {event['game_id']} / R{event['round']:02d} | {event['kind']} | {', '.join(alive) or 'none'} | {event['verdict']} | {event['sole_interval_candidate'] or 'unresolved'} ({event['sole_interval_verdict']}) |")
    counts = {kind: dict(Counter(e['sole_interval_verdict'] for e in reports if e['kind'] == kind))
              for kind in ('plant', 'disable')}
    lines += ['', f'Consumed-set sole-survivor diagnostic counts: `{json.dumps(counts)}`.', '',
              'The candidate must be the sole living eligible player both at the start of the last completed timer run and at the validated state packet, with no unknown death offsets. A timer run must start at 6.5-7.1 seconds and end at or below 0.1 seconds; a fragment containing only late timer packets cannot establish liveness throughout the interaction. Timer runs reuse the existing diagnostic reset grouping; this is a research association, not a new production completion detector. These results are development only. The fresh actor reserve remains unopened.', '',
              f'Probe kill/death feedback exactly matched cached parser feedback for all {len(parity_rounds)} physical consumed-set rounds.']
    lines += ['', '3579 / 6706 R04 illustrates why completion-only liveness is weaker: Ape is the only survivor at completion, but Reeps is still alive when the timer starts (75,935,559) and dies at 75,936,557. The diagnostic abstains.']
    lines += ['', '## Counterexamples', '',
              '4139 R07: Aiden and Raid are both alive at the plant-state packet. Aiden dies 2,987 decompressed bytes later; Raid kills SpiriTz 14,137 bytes after state. Liveness does not exclude the wrong close-score candidate Aiden.', '',
              '3563 / 6675 R02: J9O and njr are both alive at disable completion. The earlier three teammate deaths exclude Fultz, kyno, and Nuers but do not distinguish the public disabler J9O from the wrong score-residual candidate njr.', '',
              'The ignored player ledger retains stable numeric identity, score component, all ordered score updates, score at completion and final score, kill/death offsets, and kill/assist counter updates. A death with no positive parser offset yields unknown liveness rather than an alive assumption. Score reasons, DBNO and gadget-credit causes remain unknown.', '']
    (ROOT / 'research/output/objective-liveness.md').write_text('\n'.join(lines), encoding='utf-8')
    print('events', len(reports), 'mandatory players', len(mandatory), 'output', dest)
    print('eligible survivor counts', Counter(sum(p['alive_at_completion'] is True for p in e['players']) for e in reports))


if __name__ == '__main__':
    main()
