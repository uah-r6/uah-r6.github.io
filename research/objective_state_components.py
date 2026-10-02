"""Test explicit component declaration paths to health entities; consumed controls."""
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import subprocess

from objective_production_check import candidate_raw
from objective_transition_probe import ROOT, replay_file


def probe(rec):
    exe = ROOT / '.local-tools/bin/state-component-probe.exe'
    key = hashlib.sha256(exe.read_bytes() + rec.read_bytes()).hexdigest()
    cache = ROOT / 'data/research/diagnostics/state-components'
    cache.mkdir(parents=True, exist_ok=True)
    path = cache / (key + '.json')
    if not path.exists():
        result = subprocess.run([str(exe), str(rec.resolve())], check=True, capture_output=True, text=True)
        path.write_text(json.dumps(json.loads(result.stdout)[0]), encoding='utf-8')
    return json.loads(path.read_text(encoding='utf-8'))


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--all-consumed', action='store_true')
    args = parser.parse_args()
    base = ROOT / 'data/research/diagnostics'
    controls = [(4139, 7), (4139, 4), (3639, 3)]
    reports = []
    recs = [replay_file(m, n)[0] for m, n in controls]
    folder = next((ROOT / 'data/research/extracted').rglob('Match-2026-05-17_18-07-03-14704'))
    recs += [next(folder.glob('*-R02.rec')), next(folder.glob('*-R10.rec'))]
    if args.all_consumed:
        structures = []
        for name in ('development', 'extension'):
            structures += json.loads((base / f'objective-score-structure-{name}.json').read_text())
        recs = sorted({next(next((ROOT / 'data/research/extracted').rglob(r['folder'])).glob(f"*-R{r['round']:02d}.rec"))
                       for r in structures})
    for rec in recs:
        raw = probe(rec)
        baseline = candidate_raw(rec.parent)
        number = int(rec.stem.rsplit('-R', 1)[1])
        if raw['feedback'] != baseline['rounds'][number - 1]['matchFeedback']:
            raise ValueError('State observer altered feedback')
        names = {p['id']: p['username'] for p in raw['header']['players'] if p.get('id')}
        uid_entities = defaultdict(set)
        for p in raw['properties']:
            if p['kind'] == 'numeric_uid' and p['value'] in names:
                uid_entities[p['entity']].add(names[p['value']])
        graph = defaultdict(set)
        for d in raw['declarations']:
            graph[d['owner']].add(d['component'])
        health = defaultdict(list)
        for p in raw['properties']:
            if p['kind'] == 'health':
                health[p['entity']].append(p)
        links = []
        for owner, players in uid_entities.items():
            if len(players) != 1:
                continue
            seen, frontier = {owner}, [[owner]]
            for depth in range(4):
                following = []
                for path in frontier:
                    if path[-1] in health:
                        links.append({'player': next(iter(players)), 'path': path,
                                      'health_samples': health[path[-1]]})
                    for child in graph[path[-1]]:
                        if child not in seen:
                            seen.add(child)
                            following.append(path + [child])
                frontier = following
        reports.append({'folder': rec.parent.name, 'round': number,
                        'declaration_records': len(raw['declarations']),
                        'uid_entities': {str(k): sorted(v) for k,v in uid_entities.items()},
                        'health_entities': len(health), 'candidate_links': links,
                        'players_with_paths': sorted({p['player'] for p in links})})
        print(rec.parent.name, number, 'health', len(health), 'linked_players', len({p['player'] for p in links}), flush=True)
    suffix = '-all-consumed' if args.all_consumed else ''
    (base / f'objective-state-components{suffix}.json').write_text(json.dumps(reports, indent=2))
    lines = ['# Explicit component paths to health: consumed controls', '',
             'Research only. Generic 0x1b record candidates have owner/slot/component/class fields. '
             'Their framing matches the verified scoreboard declaration grammar, but arbitrary classes '
             'are not semantically verified. Paths do not establish pawn identity. No nearest-ID, drone '
             'spawn-counter or objective-to-player adjacency join is used. All feedback matched cached output.', '',
             '| Folder / physical round | Declaration candidates | UID-bearing entities | Health entities | Players with candidate paths |',
             '| --- | --- | --- | --- | --- |']
    for r in reports:
        lines.append(f"| {r['folder']} / R{r['round']:02d} | {r['declaration_records']} | {len(r['uid_entities'])} | {r['health_entities']} | {', '.join(r['players_with_paths']) or 'none'} |")
    lines += ['', 'A linked health entity still requires independent body/player and DBNO/revive validation '
              'before it can constrain eligibility. Zero paths rejects this specific declaration-route hypothesis, '
              'not the existence of replay eligibility evidence. Fresh reserve remains sealed.', '']
    (ROOT / f'research/output/objective-state-components{suffix}.md').write_text('\n'.join(lines), encoding='utf-8')


if __name__ == '__main__':
    main()
