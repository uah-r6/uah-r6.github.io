"""Separate trusted-objective derivation without rewriting frozen v2 datasets."""
from collections import Counter, defaultdict
import copy
import hashlib
import json

from objective_production_check import candidate_raw
from objective_transition_probe import ROOT
from r6stats.parser.models import Match, Objective, ObjectiveOccurrence
from r6stats.parser.siege_dissect import normalize
from r6stats.stats.calculate import calculate_match
from uah_comparison import player_rounds
from uah_guarded_actor_readonly import snapshot


def physical_mapping(source,mapping,old):
    if 'segments' not in mapping:
        return [dict(folder=mapping['folder'],physical_number=r.number,logical_number=r.number) for r in old.rounds]
    path=ROOT/'data/research/diagnostics/rehost'/str(source['rehost_official_match_id'])/'pipeline-mapping.json'
    audit=json.loads(path.read_text(encoding='utf-8'))
    return [r for r in audit['physical_to_logical'] if r['logical_number'] is not None]


def derive_map(source,mapping,rows,executable,folders,parsed):
    original_path=ROOT/'data/research/derived'/f"{mapping['folder']}.json"
    old=Match.from_dict(json.loads(original_path.read_text(encoding='utf-8')))
    new=copy.deepcopy(old)
    physical=physical_mapping(source,mapping,old)
    if sorted(r['logical_number'] for r in physical)!=sorted(r.number for r in old.rounds):
        raise ValueError('Cached physical/logical map is incomplete or ambiguous')
    counts=Counter();events=[]
    for item in physical:
        folder_name=item['folder'];n=item['physical_number'];logical=item['logical_number']
        if folder_name not in folders:
            found=[p for p in (ROOT/'data/research/extracted').rglob(folder_name) if p.is_dir()]
            if len(found)!=1:raise ValueError('Ambiguous cached physical replay')
            folders[folder_name]=found[0]
            parsed[folder_name]=candidate_raw(found[0],executable)
        if item.get('sha256'):
            rec=folders[folder_name]/item['filename']
            if hashlib.sha256(rec.read_bytes()).hexdigest()!=item['sha256']:raise ValueError('Rehost replay digest changed')
        raw=parsed[folder_name]['rounds'][n-1];header=raw.get('header',raw)
        port=normalize([raw],round_numbers=[logical]).rounds[0]
        target=next(r for r in new.rounds if r.number==logical)
        # Keep proven original logical-map team/key remapping; only graft
        # verified actor credits. Every canonical username/side must agree.
        old_names={p.username:p.side for p in target.players}
        if old_names!={p.username:p.side for p in port.players}:raise ValueError('Original/port roster or side changed')
        target.objectives=[];target.objective_occurrences=[]
        for occurrence in header.get('objectiveOccurrences',[]):
            kind,actor=occurrence['kind'],occurrence.get('actor')
            credits=[o for o in port.objectives if o.kind==kind]
            if bool(actor)!=bool(credits) or len(credits)>1:raise ValueError('Trusted actor normalization disagrees')
            player=next((p for p in target.players if p.username==actor),None)
            if actor and player is None:raise ValueError('Stable actor not in canonical logical roster')
            if player:target.objectives.append(Objective(kind,player.key,player.team,0.0))
            target.objective_occurrences.append(ObjectiveOccurrence(kind,occurrence['source'],occurrence['plantStateOffset'],
                player.key if player else None,occurrence.get('actorID'),occurrence.get('actorSource'),occurrence.get('actorReason')))
            counts[kind]+=1;counts[kind+'_resolved' if actor else kind+'_unresolved']+=1
            events.append(dict(round=logical,physical_round=n,kind=kind,actor=actor,reason=occurrence.get('actorReason')))
    aggregate=calculate_match(new,rating_version='collegiate_v1')
    complete=not counts['plant_unresolved'] and not counts['disable_unresolved']
    output=[];kost_changes=[]
    for original in rows:
        if original['replay_folder']!=mapping['folder']:raise ValueError('Mismatched original player-map input')
        player=next(p for p in new.rounds[0].players if p.username==original['player'])
        stats=aggregate[player.key]
        round_stats=player_rounds(new,player.key)
        # Identity, operators and every gameplay count except objectives/KOST
        # must match the existing v2 research observations exactly.
        allowed={'plants','disables','kost_rounds'}
        for a,b in zip(original['rounds'],round_stats):
            if a['number']!=b['number']:raise ValueError('Round sequence changed')
            for key in a:
                if key not in allowed and a[key]!=b[key]:raise ValueError(f'Unrelated {key} changed during objective derivation')
        paired_rounds=[a|{k:b[k] for k in ('plants','disables')} for a,b in zip(original['rounds'],round_stats)]
        issues=list(original['quality_issues'])
        if not complete:issues.append('map has unresolved objective actor')
        row=copy.deepcopy(original)|dict(derived=stats,rounds=round_stats,paired_v2_rounds=paired_rounds,
            original_v2_derived=original['derived'],original_fit_eligible=original['fit_eligible'],
            objective_map_complete=complete,objective_counts=dict(counts),quality_issues=issues,fit_eligible=not issues)
        output.append(row)
        if stats['kost_rounds']!=original['derived']['kost_rounds']:
            kost_changes.append(dict(player=original['player'],old=original['derived']['kost_rounds'],new=stats['kost_rounds']))
    outdir=ROOT/'data/research/experiments/v3-normalized';outdir.mkdir(parents=True,exist_ok=True)
    (outdir/f"{source['siegegg_match_id']}-{mapping['siegegg_game_id']}.json").write_text(json.dumps(new.to_dict()),encoding='utf-8')
    return output,dict(match_id=source['siegegg_match_id'],game_id=mapping['siegegg_game_id'],map=old.map_name,
        event=source['event'],rounds=len(old.rounds),counts=dict(counts),objective_complete=complete,
        original_normalized_sha256=hashlib.sha256(original_path.read_bytes()).hexdigest(),events=events,kost_changes=kost_changes)


def main():
    protected=snapshot()
    original_path=ROOT/'data/research/experiments/player_maps.jsonl'
    original_sha=hashlib.sha256(original_path.read_bytes()).hexdigest()
    original=[json.loads(l) for l in original_path.read_text(encoding='utf-8').splitlines()]
    frozen_path=ROOT/'research/frozen-rating-candidate.json'
    frozen_sha=hashlib.sha256(frozen_path.read_bytes()).hexdigest();frozen=json.loads(frozen_path.read_text())
    allowed=set(frozen['train_events'])|{frozen['development_event']}
    sources=json.loads((ROOT/'research/sources.json').read_text(encoding='utf-8'))['matches']
    sources=[s for s in sources if s.get('siegegg_match_id') and s['event'] in allowed]
    by_map=defaultdict(list)
    for r in original:
        if r['event'] in allowed:by_map[r['match_id'],r['game_id']].append(r)
    executable=ROOT/'.local-tools/bin/siege-dissect-actors.exe'
    rows,maps,failures=[],[],[];folders={};parsed={}
    for source in sources:
        for mapping in source['maps']:
            key=source['siegegg_match_id'],mapping['siegegg_game_id']
            if key not in by_map:raise ValueError('New Rating data not authorized in this controlled experiment')
            try:
                new,report=derive_map(source,mapping,by_map[key],executable,folders,parsed)
                rows+=new;maps.append(report)
                print('derived',key,len(new),report['counts'],'complete',report['objective_complete'],flush=True)
            except Exception as error:
                failures.append(dict(match_id=key[0],game_id=key[1],error=str(error)))
                print('DERIVATION FAILED',key,str(error),flush=True)
    if snapshot()!=protected or hashlib.sha256(original_path.read_bytes()).hexdigest()!=original_sha or hashlib.sha256(frozen_path.read_bytes()).hexdigest()!=frozen_sha:
        raise ValueError('Live data, original observations or frozen v2 changed')
    destination=ROOT/'data/research/experiments/v3-player-maps.jsonl'
    destination.write_text(''.join(json.dumps(r)+'\n' for r in rows),encoding='utf-8')
    totals=Counter()
    for m in maps:totals.update(m['counts'])
    summary=dict(status='separate_v3_development_rederivation',rows=len(rows),clean_rows=sum(r['fit_eligible'] for r in rows),
        original_clean_development_rows=sum(r['fit_eligible'] for r in original if r['event'] in allowed),
        maps=len(maps),objective_totals=dict(totals),parser_or_alignment_failures=failures,records=maps,
        excluded_events=sorted({r['event'] for r in original}-allowed),dataset_sha256=hashlib.sha256(destination.read_bytes()).hexdigest(),
        original_dataset_sha256=original_sha,frozen_v2_sha256=frozen_sha,protected_files=len(protected),
        binary_sha256=hashlib.sha256(executable.read_bytes()).hexdigest(),paired_inputs='Eight frozen v2 round inputs retained identically; objective count added. Corrected KOST differences reported separately.')
    (ROOT/'data/research/diagnostics/v3-objective-derivation.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    lines=['# Separate v3 trusted-objective development data','',
        f'Player-map rows{len(rows)}, clean{summary["clean_rows"]}, original clean development{summary["original_clean_development_rows"]}; maps{len(maps)}. '
        f'Objective totals`{dict(totals)}`. Parser/alignment failures`{failures}`.','',
        'Original v2 train events and EWC development only; both September events excluded. No new Rating '
        'targets, no final errors, no source downloads. Existing physical/logical manifests and parser caches '
        'reused; normalized maps and observations written to separate ignored v3 paths. Full maps with '
        'unresolved objective actors are excluded from fit, never treated as zero. Actor labels/totals '
        'from third-party sites do not enter features or eligibility.','',
        'New normalized counts/KOST are rederived from verified actors. For the requested one-feature '
        'comparison both arms retain the original eight v2 round inputs (including KOST) identically, '
        'and only the verified plants+disables feature is added. Corrected KOST changes are listed below '
        'and are not silently introduced as a second feature change.','',
        '| Match/game | Map | Objectives | Complete | KOST changes |','| --- | --- | --- | --- | --- |']
    for m in maps:lines.append(f"| {m['match_id']}/{m['game_id']} | {m['map']} | {m['counts']} | {m['objective_complete']} | {m['kost_changes']} |")
    lines+=['',f'Original dataset SHA256`{original_sha}` unchanged; frozen v2 SHA256`{frozen_sha}` unchanged. '
        f'{len(protected)} live file hashes unchanged. No SQLite/public/archive/liveRating updates. '
        'Reproduce `.venv/Scripts/python.exe research/v3_objective_derive.py`; never run the original pipeline '
        'derive command to overwrite frozen observations for this experiment.','']
    (ROOT/'research/output/v3-objective-derivation.md').write_text('\n'.join(lines),encoding='utf-8')
    print('V3 DERIVED',summary['rows'],summary['clean_rows'],dict(totals),'failures',failures,flush=True)
    if failures:raise SystemExit(1)


if __name__=='__main__':main()
