"""Read-only occurrence audit of archived UAH maps using the candidate binary.

Neither historical player credit nor the user's recollection supplies actors.
Version-2 archive mappings are read as stored; rehost behavior is not changed.
"""
from collections import Counter
import hashlib
import json
import sqlite3

from objective_production_check import candidate
from objective_transition_probe import ROOT

PRE_OBJECTIVES = ROOT/'.local-tools/bin/siege-dissect-before-objectives.exe'


def archived_rounds(archive, manifest, executable=None):
    if manifest['archive_format_version'] == 1:
        segments = [(archive, manifest['files'])]
        mapping = None
    else:
        segments = [(archive/f"segment-{s['segment']:02d}",s['files']) for s in manifest['segments']]
        mapping = manifest['source_manifest']['mapping']
    result = {}
    for index,(folder,files) in enumerate(segments,1):
        for f in files:
            if hashlib.sha256((folder/f['filename']).read_bytes()).hexdigest()!=f['sha256']:
                raise ValueError('Archive digest mismatch')
        parsed = candidate(folder, executable) if executable else candidate(folder)
        for round_ in parsed.rounds:
            if mapping is None:
                logical = round_.number
            else:
                logical = next(m['logical_number'] for m in mapping
                               if m['segment']==index and m['physical_number']==round_.number)
            if logical is not None:
                if logical in result: raise ValueError('Duplicate logical round')
                result[logical] = round_
    return result


def main():
    database = ROOT/'data/r6stats.sqlite'
    before = hashlib.sha256(database.read_bytes()).hexdigest()
    with sqlite3.connect(database.resolve().as_uri()+'?mode=ro',uri=True) as db:
        maps = db.execute('''SELECT m.id,m.map_name,se.slug,m.normalized_json FROM maps m
            JOIN series s ON s.id=m.series_id JOIN seasons se ON se.id=s.season_id WHERE s.demo=0''').fetchall()
        tracked = {r[0] for r in db.execute('SELECT profile_id FROM players WHERE tracked=1') if r[0]}
    lines = ['# UAH objective occurrence audit - read-only', '',
             'Occurrence parser; no historical corrections applied. All new actors remain unresolved.',
             'Stored actor side/operator are historical context, not evidence of newly resolved credit.', '',
             '| Map / ID | Round | Kind | Stored actor (side; operator) | New occurrence | New actor | Evidence / discrepancy |',
             '| --- | ---: | --- | --- | --- | --- | --- |']
    reports, totals, historical_operator_differences = [], Counter(), []
    tracked_usage = Counter()
    for map_id,name,season,encoded in maps:
        old = json.loads(encoded)
        archive = ROOT/'data/replay-archive'/season/map_id
        manifest = json.loads((archive/'manifest.json').read_text())
        parsed = archived_rounds(archive,manifest)
        installed = None
        if set(parsed)!={r['number'] for r in old['rounds']}: raise ValueError('Logical round mismatch')
        for stored in old['rounds']:
            r = parsed[stored['number']]
            # Canonical team indices can change during rehost; physical side and
            # stable identity/operator must remain identical.
            old_ops = Counter((p['profile_id'] or p['username'].casefold(),p['side'],p['operator']) for p in stored['players'])
            new_ops = Counter((p.profile_id or p.username.casefold(),p.side,p.operator) for p in r.players)
            if old_ops != new_ops:
                if installed is None:
                    if not PRE_OBJECTIVES.is_file():
                        raise ValueError('Pre-objective baseline binary is required to verify historical operator differences')
                    installed = archived_rounds(archive,manifest,PRE_OBJECTIVES)
                base_ops = Counter((p.profile_id or p.username.casefold(),p.side,p.operator)
                                   for p in installed[stored['number']].players)
                if base_ops != new_ops: raise ValueError(f'Candidate operator regression {map_id} R{r.number}')
                display = {p['profile_id'] or p['username'].casefold():p['username'] for p in stored['players']}
                old_diff = [(display.get(key,'unknown'),side,op) for key,side,op in (old_ops-new_ops).elements()]
                new_diff = [(display.get(key,'unknown'),side,op) for key,side,op in (new_ops-old_ops).elements()]
                historical_operator_differences.append(f"{name} / {map_id} R{stored['number']:02d}: stored {old_diff}, current installed and candidate {new_diff}")
            old_tracked = Counter({k:v for k,v in old_ops.items() if k[0] in tracked})
            new_tracked = Counter({k:v for k,v in new_ops.items() if k[0] in tracked})
            if old_tracked != new_tracked: raise ValueError('Tracked operator change')
            tracked_usage.update(new_tracked)
            totals['operator_player_rounds_checked'] += len(r.players)
            totals['rounds'] += 1
            occurrences = {o.kind:o for o in r.objective_occurrences}
            old_kinds = {o['kind'] for o in stored['objectives']}
            for kind in sorted(set(occurrences)|old_kinds):
                credited = [o for o in stored['objectives'] if o['kind']==kind]
                actors=[]
                for o in credited:
                    p = next((p for p in stored['players'] if (p['profile_id'] or p['username'].casefold())==o['player']),None)
                    actors.append(f"{p['username']} ({p['side']}; {p['operator']})" if p else o['player'])
                event = occurrences.get(kind)
                totals[kind] += bool(event)
                evidence = (event.source if event else 'No supported occurrence; historical credit disagrees')
                if event and credited: evidence += '; historical actor remains unverified'
                lines.append(f"| {name} / {map_id} | {stored['number']} | {kind} | {'; '.join(actors) or 'none'} | {'yes' if event else 'unresolved / absent'} | unresolved | {evidence} |")
                reports.append({'map_id':map_id,'round':stored['number'],'kind':kind,'detected':bool(event),'stored_actors':actors,'actor':None})
        print('checked',map_id,name,len(parsed),flush=True)
    after = hashlib.sha256(database.read_bytes()).hexdigest()
    if before!=after: raise ValueError('Database changed during read-only audit')
    lines += ['',f"Maps: {len(maps)}. Rounds: {totals['rounds']}. Detected plants: {totals['plant']}; disables: {totals['disable']}. Resolved actors: 0.",
              f"Checked {totals['operator_player_rounds_checked']} player-round identity/side/operator tuples. All {sum(tracked_usage.values())} tracked player-rounds / {len(tracked_usage)} tracked operator usage groups match stored data. SQLite SHA-256 unchanged.", '',
              'Occurrence does not establish who acted. The known personal disable remains unattributed; no player is selected from recollection. Historical changes require review.']
    lines += ['', '## Pre-existing operator differences', '']
    lines += historical_operator_differences or ['None.']
    (ROOT/'research/output/uah-objective-audit.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    (ROOT/'data/research/diagnostics/uah-objective-occurrence-audit.json').write_text(json.dumps({'totals':totals,'rows':reports,'database_sha256':before},indent=2))
    print(dict(totals))


if __name__=='__main__':
    main()
