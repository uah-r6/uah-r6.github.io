"""Read-only frozen A actor evidence on verified private UAH archives.

Never imports or replaces a match. SQLite opens mode=ro. Archive, database and
public JSON digests are checked before/after; all diagnostic caches are ignored.
Historical credits and recollection are not ground truth for new predictions.
"""
from collections import Counter
import hashlib
import json
import sqlite3

from objective_cached_map_validation import inputs
from objective_combined_candidate import combine, declared_body_states
from objective_production_check import candidate_raw
from objective_transition_probe import ROOT


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot():
    files = [ROOT / 'data/r6stats.sqlite']
    files += sorted((ROOT / 'data/replay-archive').rglob('*'))
    files += sorted((ROOT / 'web/public/data').rglob('*.json'))
    return {p.relative_to(ROOT).as_posix(): digest(p) for p in files if p.is_file()}


def physical_rounds(archive, manifest):
    if manifest['archive_format_version'] == 1:
        segments = [(archive, manifest['files'])]
        mapping = None
    else:
        segments = [(archive / f"segment-{s['segment']:02d}", s['files']) for s in manifest['segments']]
        mapping = manifest['source_manifest']['mapping']
    seen = set()
    for segment, (folder, files) in enumerate(segments, 1):
        raw = candidate_raw(folder)
        for f in sorted(files, key=lambda f: f['physical_round_number']):
            physical = f['physical_round_number']
            rec = folder / f['filename']
            if digest(rec) != f['sha256']:
                raise ValueError('Archive SHA256 mismatch')
            logical = physical if mapping is None else next(
                m['logical_number'] for m in mapping if m['segment'] == segment and m['physical_number'] == physical)
            if logical is None:
                continue
            if logical in seen:
                raise ValueError('Duplicate logical archive round')
            seen.add(logical)
            r = raw['rounds'][physical-1]
            if 'header' not in r:
                r = dict(header=r, matchFeedback=r['matchFeedback'])
            yield logical, rec, r


def main():
    before = snapshot()
    database = ROOT / 'data/r6stats.sqlite'
    with sqlite3.connect(database.resolve().as_uri() + '?mode=ro', uri=True) as db:
        db.row_factory = sqlite3.Row
        maps = [dict(m) for m in db.execute('''SELECT m.id,m.map_name,se.slug,m.normalized_json
            FROM maps m JOIN series s ON s.id=m.series_id JOIN seasons se ON se.id=s.season_id WHERE s.demo=0''')]
        tracked = {r['profile_id']: r['display_name'] for r in db.execute('SELECT profile_id,display_name FROM players WHERE tracked=1') if r['profile_id']}
    reports, counts, player_counts = [], Counter(), Counter()
    for map_ in maps:
        archive = ROOT / 'data/replay-archive' / map_['slug'] / map_['id']
        manifest = json.loads((archive / 'manifest.json').read_text(encoding='utf-8'))
        old = json.loads(map_['normalized_json'])
        rounds = list(physical_rounds(archive, manifest))
        if {n for n,_,_ in rounds} != {r['number'] for r in old['rounds']}:
            raise ValueError('Stored/archive logical round mismatch')
        for number, rec, raw in rounds:
            counts['rounds'] += 1
            stored = next(r for r in old['rounds'] if r['number'] == number)
            for occurrence in raw['header'].get('objectiveOccurrences', []):
                kind = occurrence['kind']
                row, feed, state, previous = inputs(rec, raw, kind)
                if row is None:
                    actor, mode, context = None, 'missing_completion_anchor', {}
                else:
                    actor, mode, context = combine(row, feed['events'], feed['timers'],
                                                   declared_body_states(state), state['feedback'], previous)
                selected = next((p for p in raw['header']['players'] if p['username'] == actor), None)
                display = tracked.get(selected.get('profileID')) if selected else None
                historical = []
                for o in stored['objectives']:
                    if o['kind'] != kind:
                        continue
                    p = next((p for p in stored['players'] if (p['profile_id'] or p['username'].casefold()) == o['player']), None)
                    historical.append(dict(username=p['username'] if p else o['player'], side=p['side'] if p else 'unknown'))
                reports.append(dict(map_id=map_['id'], map=map_['map_name'], round=number, kind=kind,
                                    build=raw['header']['codeVersion'], candidate=actor, mode=mode,
                                    context=context, tracked_player=display, historical_context_only=historical))
                counts[kind] += 1
                counts[kind+'_resolved' if actor else kind+'_unresolved'] += 1
                if display:
                    player_counts[display, kind] += 1
            print('inspected', map_['id'], number, flush=True)
    if snapshot() != before:
        raise ValueError('Protected database/archive/public files changed during read-only research')
    result = dict(counts=dict(counts), events=reports,
                  tracked_candidate_counts=[dict(player=p, kind=k, n=n) for (p,k),n in sorted(player_counts.items())],
                  database_sha256=before['data/r6stats.sqlite'], protected_files_checked=len(before))
    path = ROOT / 'data/research/diagnostics/uah-guarded-actor-readonly.json'
    path.write_text(json.dumps(result, indent=2), encoding='utf-8')
    lines = ['# UAH guarded actor evidence — read-only', '',
             'Original frozen cd28f76 candidate A, unchanged. Predictions are research evidence, '
             'not historical corrections or independently labeled UAH accuracy. Stored credits and recollection '
             'never supply target actors. No SQLite, archive, public export or live Rating writes.', '',
             f"Five maps; counts: `{dict(counts)}`. Protected file digests unchanged: {len(before)}. "
             f"SQLite SHA256 `{before['data/r6stats.sqlite']}`.", '',
             '| Map / ID | Round | Kind | Candidate | Tracked player | Evidence mode / abstention | Historical context only |',
             '| --- | ---: | --- | --- | --- | --- | --- |']
    for r in reports:
        historical = '; '.join(f"{h['username']} ({h['side']})" for h in r['historical_context_only']) or 'none'
        lines.append(f"| {r['map']} / {r['map_id']} | {r['round']} | {r['kind']} | {r['candidate'] or 'unresolved'} | "
                     f"{r['tracked_player'] or '—'} | {r['mode']} | {historical} |")
    lines += ['', '## Tracked candidate counts (not applied)', '', '| Player | Kind | Candidate events |', '| --- | --- | ---: |']
    for r in result['tracked_candidate_counts']:
        lines.append(f"| {r['player']} | {r['kind']} | {r['n']} |")
    lines += ['', 'Unresolved data stays unresolved. Named candidates need user review and broader independent actor validation '
              'before runtime credit or historical corrections. Unchanged operators, kills, deaths, KOST and Rating are '
              'protected by the identical whole-database digest. All archive files and public JSON are also unchanged.', '']
    (ROOT / 'research/output/uah-guarded-actor-readonly.md').write_text('\n'.join(lines), encoding='utf-8')
    print(dict(counts), result['tracked_candidate_counts'])


if __name__ == '__main__':
    main()
