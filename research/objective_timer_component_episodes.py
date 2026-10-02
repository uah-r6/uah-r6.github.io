"""Consumed research: split timers by explicit component state records.

This observer emits ownership evidence, never an objective actor. It does not
use byte gaps, score values or public labels to split interactions. State 0/1
starts an observed run; state 2 terminates it, including properties serialized
in that same record. These meanings remain hypotheses requiring validation.
"""
from collections import Counter, defaultdict
import json
import math
import struct

from objective_player_component_fields import observe, bindings_at, controls
from objective_transition_probe import ROOT

SLOT = '27c08dca'
CLASS = 'b2216bf3'
STATE = 'e58c06e9'
PROGRESS = 'e9a37feb'
TIMER = 'a9c858d9'


def component_episodes(owners, slots, fields):
    records = defaultdict(list)
    for field in fields:
        if field['hash'] in (STATE, PROGRESS, TIMER):
            records[field['record_start'], field['entity']].append(field)
    observed_entities = {entity for _,entity in records}
    # Retain complete histories for every slot that EVER references an observed
    # entity, including unknown owners, clears and replacements. Other slots
    # cannot affect these components' bindings. This reduces repeated joins.
    slots = {key:ds for key,ds in slots.items() if any(d['component'] in observed_entities for d in ds)}
    active, completed, orphan = {}, [], []
    declaration_offsets = sorted({d['offset'] for ds in slots.values() for d in ds})
    declaration_index = 0

    def close(entity, reason, end_record, source='property_record'):
        episode = active.pop(entity)
        episode.update(end_reason=reason, end_record=end_record if source=='property_record' else None,
                       end_offset=end_record, end_source=source)
        completed.append(episode)

    def declaration_boundary(offset):
        current = bindings_at(owners, slots, offset)
        for entity in list(active):
            binding = current.get(entity)
            route = [binding[k] for k in ('owner','player','slot','class_hash','declaration_offset')] if binding else None
            if route != active[entity]['route']:
                close(entity, 'ownership_declaration_boundary', offset, 'slot_declaration')

    for (record_start, entity), properties in sorted(records.items()):
        while declaration_index < len(declaration_offsets) and declaration_offsets[declaration_index] < record_start:
            declaration_boundary(declaration_offsets[declaration_index])
            declaration_index += 1
        properties.sort(key=lambda f: f['offset'])
        links = [bindings_at(owners, slots, f['offset']).get(entity) for f in properties]
        routes = {(b['owner'], b['player'], b['slot'], b['class_hash'], b['declaration_offset'])
                  for b in links if b}
        bound = (all(links) and len(routes) == 1 and links[0]['slot'] == SLOT
                 and links[0]['class_hash'] == CLASS)
        if not bound:
            if entity in active:
                close(entity, 'ownership_missing_or_changed', record_start)
            if any(f['hash'] == TIMER and f['value'] for f in properties):
                orphan.append(dict(record_start=record_start, entity=entity,
                                   reason='unknown_or_non_timer_component_route', fields=properties))
            continue
        binding = links[0]
        route = next(iter(routes))
        if entity in active and active[entity]['route'] != list(route):
            close(entity, 'ownership_changed', record_start)
        state_fields = [f for f in properties if f['hash'] == STATE]
        state = state_fields[-1]['value'] if len(state_fields) == 1 and state_fields[0]['size'] == 4 else None
        if len(state_fields) > 1:
            if entity in active:
                close(entity, 'multiple_state_writes_same_record', record_start)
            orphan.append(dict(record_start=record_start, entity=entity,
                               reason='multiple_state_writes_same_record', fields=properties))
            continue
        if state_fields and state is None:
            if entity in active:
                close(entity, 'unsupported_state_width', record_start)
            orphan.append(dict(record_start=record_start, entity=entity,
                               reason='unsupported_state_width', fields=properties))
            continue
        if state in (0, 1):
            if entity in active:
                close(entity, 'explicit_restart', record_start)
            active[entity] = dict(entity=entity, route=list(route), binding=binding,
                                  start_record=record_start, state=state, records=[], samples=[])
        if entity in active:
            active[entity]['records'].append(dict(record_start=record_start, fields=properties))
            for field in properties:
                if field['hash'] == TIMER and field['value']:
                    try:
                        number = float(field['value'])
                    except ValueError:
                        number = None
                    active[entity]['samples'].append(dict(offset=field['offset'], text=field['value'],
                                                         seconds=number if number is not None and math.isfinite(number) else None))
            if state == 2:
                close(entity, 'explicit_state_2', record_start)
            elif state is not None and state not in (0, 1):
                close(entity, 'unknown_state', record_start)
        elif any(f['hash'] == TIMER and f['value'] for f in properties):
            orphan.append(dict(record_start=record_start, entity=entity,
                               reason='timer_without_explicit_start', fields=properties, binding=binding))
    while declaration_index < len(declaration_offsets):
        declaration_boundary(declaration_offsets[declaration_index])
        declaration_index += 1
    for entity in list(active):
        close(entity, 'round_ended_without_explicit_terminal', None, 'round_end')
    for episode in completed:
        samples = episode['samples']
        episode['first_timer'] = samples[0]['seconds'] if samples else None
        episode['last_timer'] = samples[-1]['seconds'] if samples else None
        values = [s['seconds'] for s in samples]
        episode['monotonic_timer'] = bool(values) and all(v is not None for v in values) and all(a >= b for a,b in zip(values, values[1:]))
        progress = [f for r in episode['records'] for f in r['fields'] if f['hash'] == PROGRESS and f['size'] == 4]
        episode['progress_float_observation'] = []
        for field in progress:
            value = struct.unpack('<f', bytes.fromhex(field['raw_hex']))[0]
            episode['progress_float_observation'].append(dict(offset=field['offset'], raw_hex=field['raw_hex'],
                                                               float_value=value if math.isfinite(value) else None))
        episode.update(actor=None, actor_reason='unvalidated_component_state_semantics')
    return dict(episodes=sorted(completed, key=lambda e:e['start_record']), orphan_records=orphan)


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--all-consumed', action='store_true')
    args = parser.parse_args()
    structures = []
    for name in ('development', 'extension'):
        structures += json.loads((ROOT/f'data/research/diagnostics/objective-score-structure-{name}.json').read_text(encoding='utf-8'))
    selected = structures if args.all_consumed else controls()+[next(r for r in structures if r['match_id']==4150 and r['round']==11)]
    # Predeclared negative control: earlier consumed incomplete timers, no plant.
    if not args.all_consumed:
        selected += [dict(match_id=4141, game_id=8331, round=6, kind='negative',
                          folder='Match-2026-07-03_18-43-07-12240', center=None)]
    results, seen = [], set()
    for row in selected:
        key = row['folder'], row['round']
        if key in seen:
            continue
        seen.add(key)
        folders = [p for p in (ROOT/'data/research/extracted').rglob(row['folder']) if p.is_dir()]
        if len(folders) != 1:
            raise ValueError('Ambiguous physical replay folder')
        recs = list(folders[0].glob(f"*-R{row['round']:02d}.rec"))
        if len(recs) != 1:
            raise ValueError('Ambiguous physical round')
        raw, owners, slots, fields = observe(recs[0])
        record = {k:row.get(k) for k in ('match_id', 'game_id', 'round', 'folder', 'build')}
        record['completion_anchors'] = [{k:r[k] for k in ('kind','center')} for r in structures if (r['folder'],r['round']) == key]
        record.update(component_episodes(owners, slots, fields))
        results.append(record)
        print(row['match_id'],row['round'],len(record['episodes']),'episodes',len(record['orphan_records']),'orphan records',flush=True)
    suffix = '-all-consumed' if args.all_consumed else '-controls'
    dest = ROOT/f'data/research/diagnostics/player-component-fields/timer-episodes{suffix}.json'
    dest.write_text(json.dumps(results, indent=2, allow_nan=False), encoding='utf-8')
    lines = ['# Explicit timer component state runs - consumed research', '',
             'No actor selector, byte-gap segmentation, score threshold, target-based splitting or production change. '
             'Temporal direct slot27c08dca/classb2216bf3 ownership is checked at each field. '
             'State0/1 starts and state2 terminates observed runs; state2 also occurs after cancellations, '
             'so it is not objective completion by itself. All labels are already consumed.', '',
             '| Match/game/round | Owner observation | State | Start / terminal record | Timer first / last | Samples | Terminal |',
             '| --- | --- | --- | --- | --- | --- | --- |']
    for result in results:
        for ep in result['episodes']:
            lines.append(f"| {result['match_id']}/{result['game_id']}/R{result['round']:02d} | {ep['binding']['player']} | {ep['state']} | "
                         f"{ep['start_record']} / {ep['end_record']} | {ep['first_timer']} / {ep['last_timer']} | {len(ep['samples'])} | {ep['end_reason']} |")
    lines += ['', f"Terminal counts: `{dict(Counter(ep['end_reason'] for r in results for ep in r['episodes']))}`.", '',
              'A decreasing timer and state2 are not sufficient actor proof. No mandatory disputed control receives actor credit. '
              'The original frozen resolver and immutable results remain unchanged. Compare cancellations, completion anchors, '
              'same-record progress and build-specific routes before formalizing any new resolver.', '']
    (ROOT/f'research/output/objective-timer-component-episodes{suffix}.md').write_text('\n'.join(lines), encoding='utf-8')


if __name__ == '__main__':
    main()
