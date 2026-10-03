"""Cached-only death-order/countdown scope audit; no elapsed-time repair."""
from collections import Counter
import hashlib
import json
import math
from pathlib import Path

from uah_guarded_actor_readonly import snapshot
from v3_final_reserve import ROOT, sha, source_sha


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def phase(offset, anchors):
    if len(anchors) != 1:
        return 'no_unique_plant_anchor'
    return 'before_plant_state' if offset < anchors[0] else 'after_plant_state'


def analyze(events, teams, anchors):
    if any(type(a) is not int or a <= 0 for a in anchors) or len(set(anchors)) != len(anchors):
        raise ValueError('Plant anchors must be unique positive physical offsets')
    if any(type(e['offset']) is not int or e['offset'] <= 0 for e in events):
        raise ValueError('Exact unique feedback offsets are required')
    if len({e['offset'] for e in events}) != len(events):
        raise ValueError('Duplicated physical death source')
    for e in events:
        seconds = e['feedback']['timeInSeconds']
        if type(seconds) not in (int, float) or not math.isfinite(seconds) or not 0 <= seconds <= 600:
            raise ValueError('Unsupported coarse feedback clock')
    packet = sorted(events, key=lambda e: e['offset'])
    timer = sorted(events, key=lambda e: (-e['feedback']['timeInSeconds'], e['offset']))
    reversals = []; candidate_trades = []
    for i, earlier in enumerate(packet):
        a = earlier['feedback']
        for later in packet[i+1:]:
            b = later['feedback']
            cross = (len(anchors) == 1 and earlier['offset'] < anchors[0] <= later['offset'])
            delta = a['timeInSeconds'] - b['timeInSeconds']
            context = dict(earlier=earlier, later=later, earlier_phase=phase(earlier['offset'], anchors),
                           later_phase=phase(later['offset'], anchors), cross_plant_state=cross,
                           remaining_seconds_difference=delta)
            if delta < 0:
                reversals.append(context)
            if (a['type']['name'] == b['type']['name'] == 'Kill'
                    and a['username'] in teams and b['username'] in teams
                    and a['target'] in teams and b['target'] in teams
                    and teams[a['username']] != teams[a['target']]
                    and teams[b['username']] != teams[b['target']]
                    and a['username'] == b['target'] and teams[a['target']] == teams[b['username']]):
                candidate_trades.append(dict(context,
                    legacy_8s_numeric_predicate=0 <= delta <= 8,
                    elapsed_time_status='unresolved_phase_transition' if cross else
                    'unresolved_missing_or_ambiguous_plant_epoch' if len(anchors) != 1 else
                    'unresolved_zero_remaining_or_overtime' if 0 in (a['timeInSeconds'], b['timeInSeconds']) else
                    'same_phase_coarse_clock_only_not_precise_elapsed_time'))
    return dict(full_order_changed=[e['offset'] for e in packet] != [e['offset'] for e in timer],
                reversals=reversals, raw_finisher_refrag_candidates=candidate_trades,
                zero_remaining_events=[e for e in packet if e['feedback']['timeInSeconds'] == 0])


def main():
    protected = snapshot(); rows = []; counts = Counter(); inputs = {}
    state_exe = ROOT / '.local-tools/bin/state-component-probe.exe'
    exe_bytes = state_exe.read_bytes()
    inputs[state_exe.relative_to(ROOT).as_posix()] = sha(state_exe)
    for path in sorted((ROOT / 'data/research/diagnostics/v3-sal-kill-credit').glob('*.json')):
        if not path.stem.isdigit():
            continue
        old = read(path); mid = old['official_match_id']
        prediction_path = ROOT / f'data/research/v3-corrected-final-sal-stage2/{mid}/replay-predictions.json'
        prediction = read(prediction_path)
        teams = {p['player']: p['team'] for p in prediction['players']}
        inputs[path.relative_to(ROOT).as_posix()] = sha(path)
        inputs[prediction_path.relative_to(ROOT).as_posix()] = sha(prediction_path)
        for row in old['rounds']:
            sources = [p for p in (ROOT / f'data/research/extracted/v3-corrected-final-sal-{mid}').rglob(row['filename'])
                       if p.parent.name == row['folder']]
            if len(sources) != 1:
                raise ValueError('Consumed physical replay identity ambiguous')
            replay_bytes = sources[0].read_bytes()
            if hashlib.sha256(replay_bytes).hexdigest() != row['replay_sha256']:
                raise ValueError('Consumed replay changed')
            key = hashlib.sha256(exe_bytes + replay_bytes).hexdigest()
            cached = ROOT / 'data/research/diagnostics/state-components' / (key + '.json')
            if not cached.exists():
                raise ValueError('Cached-only diagnostic refuses new parsing: ' + str(mid))
            state = read(cached)
            inputs[cached.relative_to(ROOT).as_posix()] = sha(cached)
            anchors = [o['plantStateOffset'] for o in state['header'].get('objectiveOccurrences', [])
                       if o['kind'] == 'plant' and o.get('source') == 'defuser_state_v1'
                       and type(o.get('plantStateOffset')) is int and o['plantStateOffset'] > 0]
            result = analyze(row['feed'], teams, anchors)
            rows.append(dict(official_match_id=mid, round=row['logical_round'],
                replay_sha256=row['replay_sha256'], cached_header_sha256=sha(cached),
                plant_state_anchors=anchors, **result))
            counts['rounds'] += 1; counts['rounds_with_unique_plant_state'] += len(anchors) == 1
            counts['rounds_with_full_order_change'] += result['full_order_changed']
            counts['inverted_pairs'] += len(result['reversals'])
            counts['cross_plant_inverted_pairs'] += sum(e['cross_plant_state'] for e in result['reversals'])
            counts['other_inverted_pairs'] += sum(not e['cross_plant_state'] for e in result['reversals'])
            counts['zero_remaining_feedback_events'] += len(result['zero_remaining_events'])
            counts['raw_finisher_refrag_candidate_pairs'] += len(result['raw_finisher_refrag_candidates'])
            counts['candidate_pairs_crossing_plant'] += sum(e['cross_plant_state'] for e in result['raw_finisher_refrag_candidates'])
        print('cached clock-epoch audit', mid, flush=True)
    record = dict(status='consumed_cached_clock_scope_diagnostic_no_event_feature_repair',
        counts=dict(counts), rounds=rows, input_hashes=inputs,
        helper_sha256=source_sha(Path(__file__)), protected_hashes=protected,
        limits='Plant state byte anchors distinguish serialization epochs, not exact elapsed-time boundaries. Clock0 can span planting overtime and round end. Coarse remaining differences across a reset are invalid elapsed time; within a phase they are only coarse observations. No generic credited-victim join, subsecond timestamp, trade policy or live ordering change is derived.')
    destination = ROOT / 'data/research/credited-kills-v1' / ('clock-epoch-audit-' + source_sha(Path(__file__))[:12] + '.json')
    if destination.exists() and read(destination) != record:
        raise ValueError('Never overwrite changed consumed clock diagnostic')
    destination.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    lines = ['# Consumed countdown scope and full death ordering', '', str(dict(counts)), '',
        'Uses only cached parser headers, explicit defuser-state plant anchors, raw death offsets and '
        'sealed replay identities. No downloads, parsing jobs, targets, fits or original derivation is repeated. '
        'The two independent official HUD controls corroborate the plant-reset explanation. '
        'No actor credit is needed to identify the occurrence anchor.', '',
        '| Map / round | Plant state anchor | Inverted pairs across plant / other | Raw refrag candidates across plant | Zero-clock deaths |',
        '| --- | --- | --- | --- | --- |']
    for r in rows:
        if r['full_order_changed']:
            cross = sum(e['cross_plant_state'] for e in r['reversals'])
            trades = sum(e['cross_plant_state'] for e in r['raw_finisher_refrag_candidates'])
            lines.append(f'| {r["official_match_id"]}/R{r["round"]:02d} | {r["plant_state_anchors"]} | '
                         f'{cross} / {len(r["reversals"])-cross} | {trades} | {len(r["zero_remaining_events"])} |')
    lines += ['', record['limits'], '',
        'A later generic event model needs sequence/physical source, explicit clock epoch, separate raw '
        'remaining time and an unresolved elapsed-time field where overtime/terminal clocks cannot be '
        'calibrated. A scoreboard counter increment is a credited count observation, not a victim-linked '
        'timed elimination. Do not replace the live chronological helper or original v2 inputs from this '
        'descriptive inventory. Final-death ordering, generic credited ownership and trade elapsed time '
        'need separate validation and versioning.', '']
    (ROOT / 'research/output/credited-kill-clock-epochs.md').write_text('\n'.join(lines), encoding='utf-8')
    if snapshot() != protected:
        raise ValueError('Protected state changed')
    print(dict(counts))


if __name__ == '__main__':
    main()
