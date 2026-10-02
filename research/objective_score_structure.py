"""Read-only score record grouping on consumed rounds, without actor selection."""
from bisect import bisect_right
import hashlib
import json
from pathlib import Path
import subprocess

from objective_production_check import candidate_raw
from objective_transition_probe import replay_file

ROOT = Path(__file__).resolve().parents[1]


def observe(rec):
    executable = ROOT / '.local-tools/bin/score-structure-probe.exe'
    key = hashlib.sha256(executable.read_bytes() + rec.read_bytes()).hexdigest()
    cache = ROOT / 'data/research/diagnostics/score-structure'
    cache.mkdir(parents=True, exist_ok=True)
    path = cache / f'{key}.json'
    if not path.exists():
        result = subprocess.run([str(executable), str(rec.resolve())], capture_output=True, text=True, check=True)
        path.write_text(json.dumps(json.loads(result.stdout)[0]), encoding='utf-8')
    return json.loads(path.read_text(encoding='utf-8'))


def annotate(fields, mapping, canonical_changes=()):
    previous = {}
    ticks = [e for e in fields if e['kind'] == 'clock' and e['value'] <= 600]
    offsets = [e['offset'] for e in ticks]
    result = []
    by_offset = {e['offset']: e for e in canonical_changes}
    for e in fields:
        if e['kind'] == 'clock':
            continue
        index = bisect_right(offsets, e['offset']) - 1
        key = e['entity'], e['kind']
        old = previous.get(key)
        previous[key] = e['value']
        change = by_offset.get(e['offset'])
        # The direct observer omits inherited continuation fields. Never infer
        # an increment across them: use the existing complete ledger's delta.
        result.append({**e, 'player': mapping.get(str(e['entity'])),
                       'previous': change['previous'] if change else None,
                       'delta': change['delta'] if change else None,
                       'clock_tick_offset': offsets[index] if index >= 0 else None,
                       'clock_value': ticks[index]['value'] if index >= 0 else None})
    return result


def score_runs(fields):
    groups = []
    for e in fields:
        if e['kind'] != 'score':
            continue
        if not groups or groups[-1][-1]['record_end'] != e['record_start']:
            groups.append([])
        groups[-1].append(e)
    return [{'id': i, 'start': g[0]['record_start'], 'end': g[-1]['record_end'], 'records': g}
            for i, g in enumerate(groups)]


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--extension', action='store_true')
    parser.add_argument('--development', action='store_true')
    args = parser.parse_args()
    base = ROOT / 'data/research/diagnostics'
    consumed = json.loads((base / 'objective-player-ledger-v2.json').read_text())['consumed_events']
    if args.development:
        selected = []
        for row in json.loads((base / 'objective-encoding-validation/summary.json').read_text())['rounds']:
            if not row['public_objectives']:
                continue
            rec, _ = replay_file(row['match_id'], row['round'])
            for kind in ('plant', 'disable'):
                if not any(e['type'] == kind for e in row['public_objectives']):
                    continue
                centers = row['events'] if kind == 'plant' else reversed(row['events'])
                center = next((e['offset'] for e in centers if e['value'] == (1 if kind == 'plant' else 0)), None)
                if center is None:
                    continue  # Old disable lacks this mode's required state anchor.
                selected.append(dict(match_id=row['match_id'], game_id=None, round=row['round'],
                                     kind=kind, center=center, folder=rec.parent.name, development=True))
    elif args.extension:
        selected = consumed
    else:
        selected = [e for e in consumed if (e['match_id'], e['game_id'], e['round']) in
                    {(3579, 6707, 2), (3563, 6675, 2), (3563, 6675, 10), (6157, 10430, 12)}]
    # The disputed discovery control is always included, with its frozen center.
    rec, _ = replay_file(4139, 7)
    if not args.development:
        selected = selected + [{'match_id': 4139, 'game_id': None, 'round': 7, 'kind': 'plant',
                               'center': 61871641, 'folder': rec.parent.name, 'discovery': True}]
    reports, observed, raw_by_folder = [], {}, {}
    for e in selected:
        folder = next((ROOT / 'data/research/extracted').rglob(e['folder']))
        rec = next(folder.glob(f"*-R{e['round']:02d}.rec"))
        if rec not in observed:
            observed[rec] = observe(rec)
        parsed = observed[rec]
        if folder not in raw_by_folder:
            raw_by_folder[folder] = candidate_raw(folder)
        baseline = raw_by_folder[folder]['rounds'][e['round'] - 1]
        if parsed['feedback'] != baseline['matchFeedback']:
            raise ValueError(f'Observer feedback changed: {folder.name} R{e["round"]}')
        if e.get('discovery') or e.get('development'):
            stem = f"{e['match_id']}-R{e['round']:02d}.json"
            binding = json.loads((base / 'objective-score-identity' / stem).read_text())
            changes = json.loads((base / 'objective-score-batch-cohort' / stem).read_text())['events']
        else:
            saved = json.loads((base / f"objective-score-delta-validation/{folder.name}-R{e['round']:02d}.json").read_text())
            binding, changes = saved['bindings'], saved['ledger']['events']
        mapping = {k: v[0] for k, v in binding['entity_names'].items() if len(v) == 1}
        fields = annotate(parsed['fields'], mapping, changes)
        groups = score_runs(fields)
        before = [g for g in groups if g['end'] <= e['center']]
        after = [g for g in groups if g['start'] >= e['center']]
        crossing = [g for g in groups if g['start'] < e['center'] < g['end']]
        reports.append({k: v for k, v in e.items() if k in ('match_id','game_id','round','kind','center')}
                       | {'build': parsed['header']['codeVersion'], 'groups': before[-3:] + crossing + after[:3],
                          'folder': folder.name, 'header': parsed['header'],
                          'clock_ticks': [r for r in parsed['fields'] if r['kind'] == 'clock' and r['value'] <= 600],
                          'all_changes': changes, 'identity': binding, 'feedback': parsed['feedback'],
                          'last_before': before[-1]['id'] if before else None,
                          'first_after': after[0]['id'] if after else None,
                          'crossing': [g['id'] for g in crossing]})
        print('checked', e['match_id'], e['round'], e['kind'], flush=True)
    name = 'development' if args.development else 'extension' if args.extension else 'controls'
    (base / f'objective-score-structure-{name}.json').write_text(json.dumps(reports, indent=2))
    lines = ['# Score serialization runs: ' + name, '',
             'Read-only consumed-data diagnostic. A group is an exact contiguous run of complete 18-byte '
             '0x23 score records, with no intervening byte. It is not a decoded network packet, frame or '
             'causal scoring transaction. Parser clock ticks annotate each record; same displayed clock '
             'does not imply the same frame. All feedback matched the cached parser output.', '',
             '| Match/game/round/type | Build | State offset | Run start distance | Score records (delta; latest clock tick) |',
             '| --- | --- | --- | --- | --- |']
    for e in reports:
        for g in e['groups']:
            values = '; '.join(f"{r['player'] or r['entity']}: {r['previous']}->{r['value']} ({r['delta']}); clock {r['clock_value']}@{r['clock_tick_offset']}" for r in g['records'])
            lines.append(f"| {e['match_id']}/{e['game_id']}/R{e['round']:02d}/{e['kind']} | {e['build']} | {e['center']} | {g['start'] - e['center']:+} | {values} |")
    lines += ['', 'Only direct validated 0x23-prefixed score records are included by this observer. '
              'Inherited continuation fields are not treated as new records; increments come from the complete cached ledger, '
              'not differences between incomplete direct snapshots. No actor is selected; '
              'serialization adjacency must not be promoted to causal score grouping without further evidence.', '']
    (ROOT / f'research/output/objective-score-structure-{name}.md').write_text('\n'.join(lines), encoding='utf-8')


if __name__ == '__main__':
    main()
