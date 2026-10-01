"""Validate the fixed contiguous-property grammar on cached development rounds.

Discovery: 4132 R13. Prior controls: 4139 R7, 3073 R8.
Other rounds are validation of this encoding grammar, not untouched Rating data.
No actor is inferred and no production/research observations are rewritten.
"""
import hashlib
import json
from collections import Counter
from pathlib import Path
import subprocess
import tempfile

from objective_encoding_probe import inherited_state_events
from objective_transition_probe import DEVELOPMENT_MATCHES, PARSER, ROOT, replay_file


def main():
    signature = hashlib.sha256(Path(__file__).with_name('objective_encoding_probe.py').read_bytes()).hexdigest()
    cache = ROOT / 'data/research/diagnostics/objective-encoding-validation'
    cache.mkdir(parents=True, exist_ok=True)
    counts = Counter()
    results = []
    with tempfile.TemporaryDirectory() as temporary:
        dump = Path(temporary) / 'round.dump'
        for match_id in DEVELOPMENT_MATCHES:
            rows = ROOT / 'data/research/diagnostics' / f'objective-timer-{match_id}.jsonl'
            for line in rows.read_text(encoding='utf-8-sig').splitlines():
                row = json.loads(line)
                destination = cache / f'{match_id}-R{row["round"]:02d}.json'
                result = json.loads(destination.read_text()) if destination.exists() else {}
                if result.get('decoder_sha256') != signature:
                    rec, _ = replay_file(match_id, row['round'])
                    subprocess.run([str(PARSER), '--dump', '-o', str(dump), str(rec)],
                                   check=True, capture_output=True)
                    data = dump.read_bytes()
                    result = {'match_id': match_id, 'round': row['round'],
                              'decoder_sha256': signature,
                              'events': inherited_state_events(data)}
                    destination.write_text(json.dumps(result), encoding='utf-8')
                runs = [run for run in row['timer_runs'] if run['min'] <= .10]
                result['terminal_runs'] = []
                matched_offsets = set()
                for index, run in enumerate(runs):
                    flags = [e for e in result['events'] if 0 <= e['offset']-run['last_offset'] <= 1000]
                    kind = row['public_objectives'][index]['type'] if index < len(row['public_objectives']) else 'unlogged_timer'
                    counts[(kind, tuple(e['value'] for e in flags))] += 1
                    result['terminal_runs'].append({'kind': kind, 'terminal_offset': run['last_offset'],
                        'flags': flags, 'all_state_distances': [
                            {'offset': e['offset'], 'value': e['value'],
                             'distance': e['offset']-run['last_offset']} for e in result['events']]})
                    matched_offsets.update(e['offset'] for e in flags)
                if not row['public_objectives']:
                    counts[('objective_free_round', bool(result['events']))] += 1
                result['unmatched_events'] = [e for e in result['events'] if e['offset'] not in matched_offsets]
                result['public_objectives'] = row['public_objectives']
                results.append(result)
            print('completed', match_id, 'rounds', len(results), flush=True)
    output = {'decoder_sha256': signature,
              'parser_sha256': hashlib.sha256(PARSER.read_bytes()).hexdigest(),
              'counts': {str(key): value for key, value in counts.items()}, 'rounds': results}
    (cache / 'summary.json').write_text(json.dumps(output, indent=2), encoding='utf-8')
    lines = ['# Contiguous state-property development validation', '',
             'Discovery: 4132 R13; prior inspected controls: 4139 R7 and 3073 R8. ',
             'The fixed grammar was then scanned across 291 development rounds. No actors are inferred.', '',
             '| Match | Physical round | Logged type | State(s) within unchanged +0..1000 byte window | All state distances from terminal |',
             '| --- | ---: | --- | --- | --- |']
    for result in results:
        for run in result['terminal_runs']:
            lines.append(f"| {result['match_id']} | {result['round']} | {run['kind']} | "
                         f"{','.join(str(e['value']) for e in run['flags']) or 'missing'} | "
                         f"{'; '.join(str(e['value'])+'@'+str(e['distance']) for e in run['all_state_distances']) or 'none'} |")
    lines += ['', '## Whole-round negative controls', '',
              'All objective-free physical rounds scanned (no decoded state events):', '',
              ', '.join(f"{r['match_id']}:R{r['round']:02d}" for r in results if not r['public_objectives'] and not r['events']), '',
              '## State events outside terminal windows', '']
    for result in results:
        for event in result['unmatched_events']:
            lines.append(f"- {result['match_id']}:R{result['round']:02d}: value {event['value']} at {event['offset']}; "
                         f"entity {event['entity']}. No completion is inferred from this alone.")
    report = ROOT / 'research/output/objective-encoding-validation.md'
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text('\n'.join(lines)+'\n', encoding='utf-8')
    print('SUMMARY', output['counts'])


if __name__ == '__main__':
    main()
