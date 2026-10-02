"""Development-only disable hypothesis on already-consumed physical rounds.

Does not mutate original targets/results, implement production actors, or open
new validation labels. No download or new round/kill decoder is involved.
"""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json

from objective_actor_liveness import feedback
from objective_disable_owner_candidate import candidate
from objective_player_component_fields import observe
from objective_production_check import candidate_raw
from objective_score_delta_validation import grade
from objective_timer_component_episodes import component_episodes
from objective_timer_consumed_extensions import SETS
from objective_transition_probe import ROOT, replay_file
from uah_guarded_actor_readonly import snapshot


def inspect_round(item):
    rec,header=item['rec'],item['header']
    if any(o['kind']=='disable' for o in header.get('objectiveOccurrences',[])):
        state,owners,slots,fields=observe(rec)
        feed=feedback(rec)
        if state['feedback']!=header['matchFeedback']:
            raise ValueError('Component observer changed replay feedback')
        expected=[e for e in header['matchFeedback'] if e['type']['name'] in ('Kill','Death')]
        if [e['feedback'] for e in feed['events']]!=expected:
            raise ValueError('Death observer changed replay feedback')
        observed=component_episodes(owners,slots,fields)
        proposal,reason,context=candidate(header,observed,owners,slots,state['properties'],feed['events'],header['matchFeedback'])
    else:
        proposal,reason,context=candidate(header,dict(episodes=[],orphan_records=[]),{}, {},[],[],header['matchFeedback'])
    return {k:item[k] for k in ('match_id','game_id','round','physical_round','folder','cohort')} | dict(
        proposal=proposal,reason=reason,context=context,build=header['codeVersion'],actor=None,
        occurrences=header.get('objectiveOccurrences',[]))


def main():
    base=ROOT/'data/research/diagnostics'
    protected=snapshot()
    sources={s['siegegg_match_id']:s for s in json.loads((ROOT/'research/sources.json').read_text(encoding='utf-8'))['matches']
             if s.get('siegegg_match_id')}
    work,labels,source_for_case={}, {}, {}
    folders,parsed={}, {}

    def add(rec,match,game,logical,cohort,expected=None):
        if expected and hashlib.sha256(rec.read_bytes()).hexdigest()!=expected:
            raise ValueError('Consumed replay digest changed')
        if rec.parent not in parsed:
            parsed[rec.parent]=candidate_raw(rec.parent)
        physical=int(rec.stem.rsplit('-R',1)[1])
        raw=parsed[rec.parent]['rounds'][physical-1]
        header=raw.get('header',raw)
        key=rec.parent.name,physical
        if key not in work:
            work[key]=dict(rec=rec,header=header,match_id=match,game_id=game,round=logical,
                           physical_round=physical,folder=rec.parent.name,cohort=cohort)
            source_for_case[key]=sources.get(match)
        return key

    def physical(folder,number):
        if folder not in folders:
            found=[p for p in (ROOT/'data/research/extracted').rglob(folder) if p.is_dir()]
            if len(found)!=1: raise ValueError('Ambiguous consumed replay folder')
            folders[folder]=found[0]
        found=list(folders[folder].glob(f'*-R{number:02d}.rec'))
        if len(found)!=1: raise ValueError('Ambiguous consumed physical round')
        return found[0]

    # Entire original 291-round cohort, including 230 objective-free controls.
    old=json.loads((base/'objective-encoding-validation/summary.json').read_text(encoding='utf-8'))['rounds']
    structures=[]
    for name in ('development','extension'):
        structures+=json.loads((base/f'objective-score-structure-{name}.json').read_text(encoding='utf-8'))
    old_labels=json.loads((base/'objective-score-delta-validation/summary.json').read_text(encoding='utf-8'))['events']
    for row in old:
        rec,_=replay_file(row['match_id'],row['round'])
        meta=next((s for s in structures if (s['folder'],s['round'])==(rec.parent.name,row['round'])),{})
        key=add(rec,row['match_id'],meta.get('game_id'),row['round'],'original-291')
        labels[key]=next((e.get('description',e.get('html','')) for e in row['public_objectives'] if e['type']=='disable'),None)
    # Extra positive rounds from the consumed extension. Negative coverage for
    # unlisted rounds of those maps is NOT claimed by this narrow diagnostic.
    for row in structures:
        rec=physical(row['folder'],row['round'])
        key=add(rec,row['match_id'],row['game_id'],row['round'],'consumed-extension-positive')
        if key not in labels:
            event=next((e for e in old_labels if all(e.get(k)==row[k] for k in ('match_id','game_id','round'))
                        and e['kind']=='disable'),None)
            labels[key]=(event['public_actor']+' disables defuser') if event else None
    hashes={}
    for cohort,directory,manifest_name in SETS:
        path=base/directory/'result.json'
        result=json.loads(path.read_text(encoding='utf-8'))
        if not result.get('freeze_commit'): raise ValueError('Unconsumed cohort refused')
        hashes[str(path.relative_to(ROOT))]=hashlib.sha256(path.read_bytes()).hexdigest()
        manifest=json.loads((ROOT/'research'/manifest_name).read_text(encoding='utf-8'))
        previous=json.loads((base/directory/'predictions.json').read_text(encoding='utf-8'))
        for map_ in previous:
            # Original predictions include the exact COMPLETED physical files;
            # aborted rehost rounds are never added just because they exist.
            for file in map_['files']:
                n=int(file['filename'].removesuffix('.rec').rsplit('-R',1)[1])
                rec=physical(file['folder'],n)
                event=next((e for e in result['events'] if e['folder']==file['folder'] and e['physical_round']==n),None)
                logical=event['round'] if event else None
                key=add(rec,map_['match_id'],map_['game_id'],logical,cohort,file['sha256'])
                disable=next((e for e in result['events'] if e['folder']==file['folder'] and e['physical_round']==n
                              and e['kind']=='disable'),None)
                labels[key]=disable['public_label'] if disable else None
                if 'player_aliases' in manifest:
                    source_for_case[key]=dict(players=manifest['player_aliases'])
                elif 'player_aliases_by_match' in manifest:
                    source_for_case[key]=dict(players=manifest['player_aliases_by_match'][str(map_['match_id'])])
    records=[]
    print('Consumed physical rounds',len(work),'disable-occurrence rounds',
          sum(any(o['kind']=='disable' for o in r['header'].get('objectiveOccurrences',[])) for r in work.values()),flush=True)
    with ThreadPoolExecutor(max_workers=2) as pool:
        pending={pool.submit(inspect_round,item):key for key,item in work.items()}
        for future in as_completed(pending):
            record=future.result()
            records.append(record)
            if record['occurrences'] and any(o['kind']=='disable' for o in record['occurrences']):
                print(record['match_id'],record['game_id'],record['round'],record['physical_round'],
                      record['proposal'],record['reason'],flush=True)
    records.sort(key=lambda r:(r['match_id'],r['game_id'] or 0,r['folder'],r['physical_round']))
    dest=base/'player-component-fields'
    (dest/'disable-owner-consumed-predictions.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
    positive,negative=[],[]
    for record in records:
        key=record['folder'],record['physical_round']
        if labels.get(key):
            target=json.loads((ROOT/f"data/research/targets/siegegg-match-{record['match_id']}-api.json").read_text(encoding='utf-8'))
            record.update(public_label=labels[key],primary_alignment=grade(record['proposal'],labels[key],source_for_case[key],target))
            positive.append(record)
        else:
            negative.append(record)
    if snapshot()!=protected or any(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=sha for p,sha in hashes.items()):
        raise ValueError('Protected data or immutable original result changed')
    counts=dict(Counter(r['primary_alignment'] for r in positive))
    summary=dict(status='unfrozen_consumed_disable_hypothesis',rounds=len(records),positive_disable_rounds=len(positive),
        primary_alignment=counts,negative_disable_rounds=len(negative),
        negative_proposals=sum(r['proposal'] is not None for r in negative),records=records,
        protected_files_checked=len(protected),immutable_results=hashes)
    (dest/'disable-owner-consumed-result.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    lines=['# Unfrozen direct disable-owner hypothesis: consumed rounds', '',
           'Development only. This candidate supports disables only; plants (including mandatory4139/R07) '
           'are unsupported. Original A, targets and primary results are unchanged. Each proposal requires '
           'existing verified Bomb/plant/Defense-score occurrence, unique temporal UID timer route, correct '
           'state1 phase and side, complete monotonic timer, explicit terminal2 or literal owner slot clear, '
           'no competing/later/unbound timer evidence, no death/disconnect ambiguity and known active '
           'body route/state throughout. Score bonus and inferred winCondition are not used. '
           'Actors stay null until new validation; proposals are not confident historical credit.', '',
           f"Consumed physical rounds{len(records)}; public disable rounds{len(positive)}; primary alignment{counts}; "
           f"rounds without public disable{len(negative)}; proposals there{summary['negative_proposals']}.", '',
           'Original291 rounds plus all completed physical files in three consumed reserves, and additional '
           'consumed extension positive rounds. Unlisted negative rounds in extension maps are not covered. '
           'Do not describe this as new or independent actor accuracy.', '',
           '| Match / game / logical / physical | Proposal | Primary public alignment | Reason |',
           '| --- | --- | --- | --- |']
    for r in positive:
        lines.append(f"| {r['match_id']}/{r['game_id']}/R{r['round']}/R{r['physical_round']:02d} | "
                     f"{r['proposal'] or 'unresolved'} | {r['primary_alignment']} | {r['reason']} |")
    lines+=['', 'Separate primary Ubisoft review supports njr overJ9O, handyy overVITAKING and Loira overDias for the known '
            'disputed labels. Preserve raw primary alignment above; never silently grade those wrong '
            'labels as corrected. Mandatory unchanged diagnostic controls remain unresolved, and the '
            'new disable hypothesis has not passed a fresh freeze/evaluation gate. No production or v3 work.', '',
            f'{len(protected)} protected local hashes and three immutable original results unchanged.', '']
    (ROOT/'research/output/objective-disable-owner-consumed.md').write_text('\n'.join(lines),encoding='utf-8')
    print('FINAL',counts,'negative proposals',summary['negative_proposals'],'protected',len(protected),flush=True)


if __name__=='__main__':
    main()
