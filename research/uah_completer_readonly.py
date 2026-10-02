"""Direct completing-owner proposals on verified UAH archives; SQLite read-only."""
from collections import Counter
import hashlib
import json
import sqlite3

from objective_production_check import candidate_raw
from r6stats.parser.siege_dissect import normalize
from objective_transition_probe import ROOT
from uah_guarded_actor_readonly import snapshot, physical_rounds


def main():
    before=snapshot()
    executable=ROOT/'.local-tools/bin/siege-dissect-actors.exe'
    with sqlite3.connect((ROOT/'data/r6stats.sqlite').resolve().as_uri()+'?mode=ro',uri=True) as db:
        db.row_factory=sqlite3.Row
        maps=[dict(r) for r in db.execute('''SELECT m.id,m.map_name,se.slug,m.normalized_json
            FROM maps m JOIN series s ON s.id=m.series_id JOIN seasons se ON se.id=s.season_id WHERE s.demo=0''')]
        tracked={r['profile_id']:r['display_name'] for r in db.execute('SELECT profile_id,display_name FROM players WHERE tracked=1') if r['profile_id']}
    events,parity,counts,tracked_counts=[],[],Counter(),Counter()
    lgon_attack=Counter(); original38_lgon=Counter();parsed_folders={}
    for map_ in maps:
        archive=ROOT/'data/replay-archive'/map_['slug']/map_['id']
        manifest=json.loads((archive/'manifest.json').read_text(encoding='utf-8'))
        stored=json.loads(map_['normalized_json'])
        for number,rec,oldraw in physical_rounds(archive,manifest):
            if rec.parent not in parsed_folders:parsed_folders[rec.parent]=candidate_raw(rec.parent,executable)
            physical=int(rec.stem.rsplit('-R',1)[1])
            raw=parsed_folders[rec.parent]['rounds'][physical-1]
            header=raw.get('header',raw)
            port=normalize([raw],round_numbers=[number]).rounds[0]
            baseline=normalize([oldraw],round_numbers=[number]).rounds[0]
            fields=('players','kills','winner','win_condition','site','starting_scores','ending_scores')
            changed=[k for k in fields if getattr(port,k)!=getattr(baseline,k)]
            if changed:parity.append(dict(map_id=map_['id'],round=number,changed=changed))
            old=next(r for r in stored['rounds'] if r['number']==number)
            counts['rounds']+=1
            for p in port.players:
                if (tracked.get(p.profile_id) or '').casefold()=='lgon' and p.side=='Attack':
                    lgon_attack[p.operator]+=1
                    if map_['id'] in ('d64d5478cdb3','8a6357ff307c','5adc26f7a402'):original38_lgon[p.operator]+=1
            for o in header.get('objectiveOccurrences',[]):
                kind=o['kind'];actor=o.get('actor')
                credits=[c for c in port.objectives if c.kind==kind]
                if bool(actor)!=bool(credits) or len(credits)>1:raise ValueError('Go/Python objective adapter mismatch')
                prior=[]
                for c in old['objectives']:
                    if c['kind']!=kind:continue
                    p=next((p for p in old['players'] if (p['profile_id'] or p['username'].casefold())==c['player']),None)
                    prior.append(dict(username=p['username'] if p else c['player'],side=p['side'] if p else 'unknown'))
                player=next((p for p in port.players if p.username==actor),None)
                display=tracked.get(player.profile_id) if player else None
                if display:tracked_counts[display,kind]+=1
                events.append(dict(map_id=map_['id'],map=map_['map_name'],round=number,physical_round=physical,
                    kind=kind,completing_owner=actor,source=o.get('actorSource'),
                    confidence='verified_structural_completion_owner_not_independent_UAH_truth' if actor else 'unresolved',
                    reason=o.get('actorReason'),prior_stored_actors=prior,tracked_player=display,
                    proposed_correction=actor if actor and [p['username'] for p in prior]!=[actor] else None))
                counts[kind]+=1;counts[kind+'_resolved' if actor else kind+'_unresolved']+=1
        print('readonly',map_['id'],map_['map_name'],flush=True)
    if snapshot()!=before:raise ValueError('SQLite/archive/public files changed')
    result=dict(status='readonly_proposals_not_historical_corrections',maps=len(maps),counts=dict(counts),
        events=events,existing_gameplay_parity_failures=parity,protected_files=len(before),
        database_sha256=before['data/r6stats.sqlite'],binary_sha256=hashlib.sha256(executable.read_bytes()).hexdigest(),
        tracked_proposals=[dict(player=p,kind=k,count=n) for (p,k),n in sorted(tracked_counts.items())],
        lgon_attack_all_archives=dict(lgon_attack),lgon_attack_original38=dict(original38_lgon))
    (ROOT/'data/research/diagnostics/uah-completer-readonly.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    lines=['# UAH completing-owner proposals: read-only','',
        f'Maps{len(maps)}, counts`{dict(counts)}`. Gameplay parity failures`{parity}`. '
        'SQLite opened mode=ro; every source archive file hash verified against its manifest. '
        'Old stored actors are comparison context, not target labels. Proposed corrections are not applied.','',
        '| Map/ID | Round | Kind | Completing owner | Evidence / unresolved reason | Prior stored actor | Proposed correction |',
        '| --- | ---: | --- | --- | --- | --- | --- |']
    for e in events:
        prior='; '.join(f"{p['username']}({p['side']})" for p in e['prior_stored_actors']) or 'none'
        lines.append(f"| {e['map']}/{e['map_id']} | {e['round']} | {e['kind']} | {e['completing_owner'] or 'unresolved'} | "
                     f"{e['source'] or e['reason']} | {prior} | {e['proposed_correction'] or 'none'} |")
    lines+=['','## Tracked proposals, not applied','','| Player | Kind | Count |','| --- | --- | ---: |']
    for r in result['tracked_proposals']:lines.append(f"| {r['player']} | {r['kind']} | {r['count']} |")
    lines+=['',f'Lgon Attack original38rounds: `{dict(original38_lgon)}`. All archived rounds: `{dict(lgon_attack)}`. '
        'Every parsed player/operator/kill/death/winner/site/physical-score field matches the previous binary. '
        'Completion clocks are not invented: new normalized credits carry0.0 as unknown timing; statistics '
        'use round/actor counts. Structural confidence means all replay guards pass, not externally labeled '
        'UAH accuracy. Unsupported/missing identity remains unresolved.','',
        f'{len(before)} database/archive/public file hashes unchanged; SQLite SHA256`{before["data/r6stats.sqlite"]}`. '
        'No recalculation, import, archive mutation, website JSON regeneration, Rating change or publish.','',
        'Reproduce `.venv/Scripts/python.exe research/uah_completer_readonly.py`. Separate actor candidate binary '
        'is used explicitly; this script does not install it or alter configured live paths.','']
    (ROOT/'research/output/uah-completer-readonly.md').write_text('\n'.join(lines),encoding='utf-8')
    print('UAH READONLY',dict(counts),'parity',parity,'Lgon original38',dict(original38_lgon),flush=True)
    if parity:raise SystemExit(1)


if __name__=='__main__':main()
