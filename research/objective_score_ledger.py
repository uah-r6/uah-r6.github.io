"""Discovery ledger with literal username properties, never nearest-ID joins.

No score increment is classified as an objective and no actor is credited.
Public logs are attached after parsing solely for validation.
"""
import argparse
from collections import defaultdict
import json

from objective_encoding_probe import dump_round
from objective_transition_probe import ROOT

NAME = bytes.fromhex('5be84728')
COUNTERS = {'ecda4f80': 'score', '1cd2b19d': 'kills', '4d737f9e': 'assists'}


def ledger(data):
    fields = {}
    cursor = 0
    while (start := data.find(b'\x23', cursor)) >= 0:
        cursor = start + 1
        if start+14 > len(data) or data[start+5:start+9] != bytes(4):
            continue
        entity = int.from_bytes(data[start+1:start+5], 'little')
        at = start+9
        while at+5 <= len(data):
            tag, size = data[at:at+4], data[at+4]
            if size not in (1, 2, 4, 8) and not (tag == NAME and size <= 64):
                break
            end = at+5+size
            if end > len(data):
                break
            if tag == NAME or (tag.hex() in COUNTERS and size == 4):
                fields[at] = (entity, tag.hex(), data[at+5:end])
            if end >= len(data) or data[end] != 0x22:
                break
            at = end+1
    names = defaultdict(set)
    for entity, tag, value in fields.values():
        if tag == NAME.hex() and value:
            try:
                name = value.decode('utf-8')
            except UnicodeDecodeError:
                continue
            if name.isprintable():
                names[entity].add(name)
    previous = {}
    events = []
    for at, (entity, tag, raw) in sorted(fields.items()):
        if tag not in COUNTERS:
            continue
        value = int.from_bytes(raw, 'little')
        key = entity, tag
        old = previous.get(key)
        previous[key] = value
        if old is not None and value != old:
            events.append({'offset': at, 'entity': entity, 'names': sorted(names[entity]),
                           'counter': COUNTERS[tag], 'previous': old,
                           'value': value, 'delta': value-old})
    return {'entity_names': {str(k): sorted(v) for k,v in names.items()}, 'events': events}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('cases', nargs='+')
    args = parser.parse_args()
    for case in args.cases:
        match, number = map(int, case.split(':'))
        data, diagnostic = dump_round(match, number)
        result = ledger(data)
        result['match_id'], result['round'] = match, number
        result['runs'] = []
        for run in diagnostic['timer_runs']:
            if run['min'] <= .1:
                center = run['last_offset']
                result['runs'].append({'terminal_offset': center, 'events': [
                    {**e, 'terminal_distance': e['offset']-center} for e in result['events']
                    if -5000 <= e['offset']-center <= 10000]})
        result['public_objectives'] = diagnostic['public_objectives']
        destination = ROOT / f'data/research/diagnostics/objective-encoding/{match}-R{number:02d}-ledger.json'
        destination.write_text(json.dumps(result, indent=2), encoding='utf-8')
        print(json.dumps({k: result[k] for k in ['match_id','round','entity_names','runs']}))


if __name__ == '__main__':
    main()
