"""Inspect every raw state-property occurrence, including non-0x23 layouts.

Discovery only: this deliberately does not classify events or credit actors.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from objective_transition_probe import PARSER, ROOT, replay_file, state_events


def inherited_state_events(data):
    """Discovery grammar: explicit entity followed by contiguous typed fields.

    0x23 introduces a ref64; 0x22 continues the same entity. Stop on every
    unknown encoding rather than carrying an entity across unrelated packets.
    """
    results = {}
    cursor = 0
    while (start := data.find(b'\x23', cursor)) >= 0:
        cursor = start + 1
        if start + 14 > len(data) or data[start+5:start+9] != bytes(4):
            continue
        entity = int.from_bytes(data[start+1:start+5], 'little')
        at = start + 9
        while at + 5 < len(data):
            size = data[at+4]
            if size not in (1, 2, 4, 8) or at+5+size > len(data):
                break
            if data[at:at+4] == bytes.fromhex('ff39f408') and size == 1:
                results[at] = {'offset': at, 'entity': entity,
                               'value': data[at+5], 'inherited': at != start+9,
                               'record_start': start}
            end = at + 5 + size
            if end >= len(data) or data[end] != 0x22:
                break
            at = end + 1
    return sorted(results.values(), key=lambda row: row['offset'])


def dump_round(match_id, number):
    rec, diagnostic = replay_file(match_id, number)
    cache = ROOT / "data/research/diagnostics/objective-encoding"
    cache.mkdir(parents=True, exist_ok=True)
    output = cache / f"{match_id}-R{number:02d}.dump"
    if not output.exists():
        subprocess.run([str(PARSER), "--dump", "-o", str(output), str(rec)],
                       check=True, capture_output=True)
    return output.read_bytes(), diagnostic


def inspect(match_id, number):
    data, diagnostic = dump_round(match_id, number)
    tag = bytes.fromhex("ff39f408")
    rows = []
    cursor = 0
    while (at := data.find(tag, cursor)) >= 0:
        cursor = at + 4
        rows.append({"offset": at, "before": data[max(0, at-32):at].hex(),
                     "after": data[at+4:at+36].hex(),
                     "timer_distance": [at-r['last_offset'] for r in diagnostic['timer_runs']]})
    result = {"match_id": match_id, "round": number,
              "dump_sha256": hashlib.sha256(data).hexdigest(),
              "strict_events": state_events(data), "raw_occurrences": rows}
    result['inherited_events'] = inherited_state_events(data)
    print(json.dumps(result))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('cases', nargs='+', help='MATCH_ID:ROUND')
    args = parser.parse_args()
    for case in args.cases:
        inspect(*map(int, case.split(':')))
