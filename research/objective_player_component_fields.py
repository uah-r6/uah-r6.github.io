"""Research-only temporal direct component fields during consumed interactions.

Uses explicit typed UID owners and their declared slots. Ownership is resolved
at each property offset; a changing slot is not unioned across the round. No
nearest-ID, drone assumption, score attribution or production parsing change.
Unknown field hashes are observations, not decoded interaction semantics.
"""
from bisect import bisect_right
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

from objective_actor_liveness import feedback, interaction_span
from objective_clock_candidate import epochs
from objective_state_components import probe
from objective_transition_probe import ROOT, PARSER


def primitive_fields(data, entities):
    fields, cursor = {}, 0
    while (start := data.find(b'\x23', cursor)) >= 0:
        cursor = start+1
        if start+14 > len(data) or data[start+5:start+9] != bytes(4):
            continue
        entity = int.from_bytes(data[start+1:start+5], 'little')
        if entity not in entities:
            continue
        at = start+9
        while at+5 <= len(data):
            size = data[at+4]
            tag = data[at:at+4].hex()
            is_name = tag == '5be84728'
            is_timer = tag == 'a9c858d9'
            if size not in (1,2,4,8) and not ((is_name or is_timer) and size <= 64):
                break
            end = at+5+size
            if end > len(data):
                break
            raw = data[at+5:end]
            value = raw.decode('utf-8',errors='replace') if is_name or is_timer else int.from_bytes(raw, 'little')
            fields[at] = dict(offset=at, entity=entity, hash=tag, size=size,
                              value=value, interpretation='utf8_name' if is_name else 'ascii_timer' if is_timer else 'unsigned_bits_only', raw_hex=raw.hex(),
                              record_start=start, inherited=at != start+9)
            if end >= len(data) or data[end] != 0x22:
                break
            at = end+1
    return [fields[k] for k in sorted(fields)]


def owners_and_slots(raw):
    names = {p['id']: p['username'] for p in raw['header']['players'] if p.get('id')}
    uids = defaultdict(set)
    for p in raw['properties']:
        if p['kind'] == 'numeric_uid':
            uids[p['entity']].add(p['value'])
    owners = {owner:names[next(iter(values))] for owner,values in uids.items()
              if len(values) == 1 and next(iter(values)) in names}
    # Repeated numeric UID owners are uncertain; do not choose by proximity.
    duplicated = {name for name in owners.values() if list(owners.values()).count(name) > 1}
    owners = {owner:name for owner,name in owners.items() if name not in duplicated}
    slots = defaultdict(list)
    for d in raw['declarations']:
        # Keep unknown owners too: their active route may share a component.
        slots[d['owner'],d['slot_hash']].append(d)
    for declarations in slots.values():
        declarations.sort(key=lambda d:d['offset'])
    return owners, slots


def bindings_at(owners, slots, offset):
    result = defaultdict(list)
    for owner, name in owners.items():
        result[owner].append(dict(player=name, owner=owner, slot='uid_owner', class_hash='uid_owner', declaration_offset=0))
    for (owner,slot), declarations in slots.items():
        index = bisect_right([d['offset'] for d in declarations], offset)-1
        if index < 0:
            continue
        d = declarations[index]
        if d['component'] and d['class_hash'] != '00000000':
            result[d['component']].append(dict(player=owners.get(owner), owner=owner, slot=slot,
                                               class_hash=d['class_hash'], declaration_offset=d['offset']))
    # Multiple active ownership routes remain ambiguous even if names agree.
    return {entity: links[0] for entity,links in result.items() if len(links) == 1 and links[0]['player'] is not None}


def observe(rec):
    state = probe(rec)
    owners,slots = owners_and_slots(state)
    entities = set(owners) | {d['component'] for (owner,_),ds in slots.items() if owner in owners for d in ds if d['component']}
    cache = ROOT / 'data/research/diagnostics/player-component-fields'
    cache.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256(rec.read_bytes()+PARSER.read_bytes()+Path(__file__).read_bytes()).hexdigest()
    dest = cache / (key+'.json')
    if not dest.exists():
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'round.dump'
            subprocess.run([str(PARSER), '--dump', '-o', str(path), str(rec)], check=True, capture_output=True)
            fields = primitive_fields(path.read_bytes(), entities)
        dest.write_text(json.dumps(fields), encoding='utf-8')
    return state,owners,slots,json.loads(dest.read_text(encoding='utf-8'))


def controls():
    base = ROOT / 'data/research/diagnostics'
    structures = []
    for name in ('development','extension'):
        structures += json.loads((base / f'objective-score-structure-{name}.json').read_text(encoding='utf-8'))
    wanted = [(4139,None,7,'plant'), (3563,6675,2,'disable'), (3563,6675,10,'disable')]
    rows = [next(r for r in structures if (r['match_id'],r['game_id'],r['round'],r['kind']) == case) for case in wanted]
    record = json.loads((base / 'objective-cached-map-validation/false-credit-diagnosis.json').read_text(encoding='utf-8'))[0]
    rows.append(record['row'] | {k:record['event'][k] for k in ('folder','round','match_id','game_id','build')})
    return rows


def main():
    reports = []
    for row in controls():
        folder = next((ROOT / 'data/research/extracted').rglob(row['folder']))
        rec = next(folder.glob(f"*-R{row['round']:02d}.rec"))
        raw,owners,slots,fields = observe(rec)
        feed = feedback(rec)
        previous = 0
        if row['kind'] == 'disable':
            # Completion of the preceding plant is the independent lower bound.
            plants = [r['center'] for r in json.loads((ROOT / 'data/research/diagnostics/objective-score-structure-extension.json').read_text())
                      if r['folder'] == row['folder'] and r['round'] == row['round'] and r['kind'] == 'plant']
            previous = max(plants,default=0)
        span = interaction_span(feed['timers'],row['center'],previous)
        if not span:
            raise ValueError('Control lacks complete interaction')
        ticks = epochs(row['clock_ticks'])
        offsets = [t['offset'] for t in ticks]
        start,end = span['first_offset'],row['center']
        start_bindings = bindings_at(owners,slots,start)
        center_bindings = bindings_at(owners,slots,end)
        initial,changes = {},[]
        prior = {}
        for field in fields:
            key = field['entity'],field['hash'],field['size']
            value_before = prior.get(key)
            prior[key] = field['value']
            if field['offset'] <= start:
                if field['entity'] in start_bindings:
                    initial[key] = field
            elif field['offset'] <= end and field['value'] != value_before:
                binding = bindings_at(owners,slots,field['offset']).get(field['entity'])
                if binding:
                    clock_index = bisect_right(offsets,field['offset'])-1
                    changes.append(field | binding | dict(previous=value_before, clock=ticks[clock_index]['value'] if clock_index >= 0 else None))
        initial = [field | start_bindings[field['entity']] for field in initial.values()]
        reports.append(dict(match_id=row['match_id'],game_id=row['game_id'],round=row['round'],kind=row['kind'],
                            build=row['build'],span=span,center=end,fields=len(fields),
                            typed_players=len(owners),slots=len(slots),
                            start_bindings=start_bindings,center_bindings=center_bindings,initial=initial,changes=changes))
        print(row['match_id'],row['round'],row['kind'],'properties',len(fields),'interaction_changes',len(changes),flush=True)
    path = ROOT / 'data/research/diagnostics/player-component-fields/controls.json'
    path.write_text(json.dumps(reports,indent=2),encoding='utf-8')
    lines = ['# Direct declared player-component interaction fields', '',
             'Consumed semantic discovery only. Temporal explicit UID/slot declarations supply ownership. '
             'Unknown primitive payloads are shown as unsigned bit patterns, not decoded numeric semantics. '
             'Known UTF-8 name payloads remain text even at width4/8. Changes do not establish objective actors. '
             'No score, timer, actor or production code changed. Direct slots only, no guessed pawn graph or numeric proximity.', '']
    for r in reports:
        lines += [f"## {r['match_id']}/{r['game_id']}/R{r['round']:02d}/{r['kind']} build{r['build']}", '',
                  f"UID players{r['typed_players']}; all owner/slot histories{r['slots']}; observed fields{r['fields']}. "
                  f"Interaction `{r['span']}` to completion{r['center']}.", '',
                  '| Offset | Clock | Player | Slot / class | Field / width | Previous -> value |',
                  '| --- | --- | --- | --- | --- | --- |']
        for field in r['changes']:
            lines.append(f"| {field['offset']} | {field['clock']} | {field['player']} | {field['slot']} / {field['class_hash']} | "
                         f"{field['hash']} / {field['size']} | {field['previous']} -> {field['value']} |")
    lines += ['', 'Missing or ambiguous routes remain unknown. A slot can change or clear; historical components are '
              'not all active at once. Candidate field semantics need independent video and non-objective controls across '
              'builds before any actor selector. No reserve reused as fresh evidence.', '']
    (ROOT / 'research/output/objective-player-component-fields.md').write_text('\n'.join(lines),encoding='utf-8')


if __name__ == '__main__':
    main()
