"""Resumable structural completion-owner audit on exclusively consumed rounds.

Includes every original negative control and consumed actor reserve. Separate
plant hypothesis and unchanged frozen disable rule. No live data mutation.
"""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import importlib.util
import json
from pathlib import Path

from objective_actor_liveness import feedback
from objective_disable_owner_candidate import candidate as disable_candidate, run_end
from objective_plant_owner_candidate import candidate as plant_candidate
from objective_player_component_fields import observe
from objective_production_check import candidate_raw
from objective_score_delta_validation import grade
from objective_timer_component_episodes import component_episodes
from objective_timer_consumed_extensions import SETS
from objective_transition_probe import ROOT
from uah_guarded_actor_readonly import snapshot


def observation(header, owners, slots, fields):
    if header.get('codeVersion') != 9734089:
        return component_episodes(owners,slots,fields)
    # Exact already-observed build/class variant, isolated from frozen modules.
    spec=importlib.util.spec_from_file_location('consumed_timer_variant',
        Path(__file__).with_name('objective_timer_component_episodes.py'))
    isolated=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(isolated)
    isolated.CLASS='a859ffff'
    return isolated.component_episodes(owners,slots,fields)


def inspect(rec,header,meta,code_hash):
    rec_sha=hashlib.sha256(rec.read_bytes()).hexdigest()
    signature=hashlib.sha256((rec_sha+code_hash).encode()).hexdigest()
    cache=ROOT/'data/research/diagnostics/completer-consumed-audit'
    cache.mkdir(parents=True,exist_ok=True)
    path=cache/(signature+'.json')
    if path.exists():
        saved=json.loads(path.read_text(encoding='utf-8'))
        if any(saved.get(k)!=meta.get(k) for k in ('folder','physical_round','match_id')):
            raise ValueError('Cached physical identity differs')
        return saved
    state,owners,slots,fields=observe(rec)
    feed=feedback(rec)
    expected=[e for e in header['matchFeedback'] if e['type']['name'] in ('Kill','Death')]
    if state['feedback']!=header['matchFeedback'] or [e['feedback'] for e in feed['events']]!=expected:
        raise ValueError('Observers changed normalized kill/death feedback')
    observed=observation(header,owners,slots,fields)
    predictions={}
    for kind,selector in (('plant',plant_candidate),('disable',disable_candidate)):
        name,reason,context=selector(header,observed,owners,slots,state['properties'],feed['events'],header['matchFeedback'])
        predictions[kind]=dict(proposal=name,reason=reason,context=context,actor=None)
    runs=[dict(player=r['binding']['player'],owner=r['binding']['owner'],component=r['entity'],
        slot=r['binding']['slot'],class_hash=r['binding']['class_hash'],phase=r['state'],
        start=r['start_record'],end=run_end(r),first_timer=r['first_timer'],last_timer=r['last_timer'],
        n=len(r['samples']),monotonic=r['monotonic_timer'],terminal=r['end_reason']) for r in observed['episodes']]
    result=meta|dict(rec_sha256=rec_sha,signature=signature,build=header['codeVersion'],
        occurrences=header.get('objectiveOccurrences',[]),predictions=predictions,runs=runs,
        orphan_timer_records=len(observed['orphan_records']))
    temporary=path.with_suffix('.tmp')
    temporary.write_text(json.dumps(result,indent=2),encoding='utf-8')
    temporary.replace(path)
    return result


def inputs():
    base=ROOT/'data/research/diagnostics'
    previous=json.loads((base/'player-component-fields/disable-owner-consumed-result.json').read_text(encoding='utf-8'))
    september_path=base/'objective-disable-stage2-validation/result.json'
    september=json.loads(september_path.read_text(encoding='utf-8'))
    if previous['rounds']!=502 or september['status']!='permanent_result_cohort_now_consumed':
        raise ValueError('Only completed consumed cohorts allowed')
    records=previous['records']+json.loads((september_path.parent/'predictions.json').read_text(encoding='utf-8'))
    work={}
    for r in records:
        key=(r['folder'],r['physical_round'])
        if key in work:
            raise ValueError('Duplicate physical sources in consumed inventory')
        work[key]={k:r[k] for k in ('match_id','game_id','round','physical_round','folder','cohort')}
    return work


def labels_for_consumed():
    """Read historical target text only for completed consumed cases."""
    base=ROOT/'data/research/diagnostics'
    sources={s['siegegg_match_id']:s for s in json.loads((ROOT/'research/sources.json').read_text(encoding='utf-8'))['matches']
             if s.get('siegegg_match_id')}
    labels={}
    from objective_transition_probe import replay_file
    old=json.loads((base/'objective-encoding-validation/summary.json').read_text(encoding='utf-8'))['rounds']
    for row in old:
        rec,_=replay_file(row['match_id'],row['round'])
        for e in row['public_objectives']:
            labels[rec.parent.name,row['round'],e['type']]=(e.get('description',e.get('html','')),sources[row['match_id']])
    extension=json.loads((base/'objective-score-delta-validation/summary.json').read_text(encoding='utf-8'))['events']
    for e in extension:
        key=(e['folder'],e['round'],e['kind'])
        if key not in labels:
            labels[key]=(e['public_actor']+(' plants defuser' if e['kind']=='plant' else ' disables defuser'),sources[e['match_id']])
    for _,directory,manifest_name in SETS:
        result=json.loads((base/directory/'result.json').read_text(encoding='utf-8'))
        manifest=json.loads((ROOT/'research'/manifest_name).read_text(encoding='utf-8'))
        for e in result['events']:
            aliases=manifest.get('player_aliases',manifest.get('player_aliases_by_match',{}).get(str(e['match_id'])))
            source=dict(players=aliases) if aliases else sources[e['match_id']]
            labels[e['folder'],e['physical_round'],e['kind']]=(e['public_label'],source)
    reserve=json.loads((ROOT/'research/objective-disable-stage2-reserve.json').read_text(encoding='utf-8'))
    for m in reserve['maps']:
        target=json.loads((ROOT/f"data/research/targets/siegegg-match-{m['match_id']}-api.json").read_text(encoding='utf-8'))
        game=next(g for g in target['games'] if g['id']==m['game_id'])
        source=dict(players=reserve['player_aliases_by_match'][str(m['match_id'])])
        for file in m['exact_replay_sha256']:
            for e in game['rounds'][file['logical_round']-1]['events']:
                if e['type'] in ('plant','disable'):
                    labels[m['folder'],file['physical_round'],e['type']]=(e.get('description',e.get('html','')),source)
    return labels


def reviewed_label(record,kind):
    # Public targets are never replaced; these are separate documented reviews.
    key=(record['match_id'],record['game_id'],record['round'],kind)
    by_key={(3554,6679,4,'plant'):'kyno', (3563,6675,2,'disable'):'njr',
            (3173,5932,17,'disable'):'handyy', (6157,10427,1,'disable'):'LoiraDEMON',
            (6170,10592,7,'disable'):'Gunnar.M80'}
    if record['match_id']==4139 and record['physical_round']==7 and kind=='plant':
        return 'Aiden.SSG','official_vod'
    name=by_key.get(key)
    return (name,'documented_official_review') if name else (None,None)


def main():
    protected=snapshot()
    base=ROOT/'data/research/diagnostics'
    frozen_paths=[base/d/'result.json' for _,d,_ in SETS]+[base/'objective-disable-stage2-validation/result.json']
    immutable={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in frozen_paths}
    code_hash=hashlib.sha256(b''.join(Path(__file__).with_name(n).read_bytes() for n in
        ('objective_completer_consumed_audit.py','objective_plant_owner_candidate.py','objective_disable_owner_candidate.py',
         'objective_timer_component_episodes.py','objective_player_component_fields.py'))).hexdigest()
    work=inputs()
    folders,parsed={},{}
    tasks=[]
    for (folder,physical),meta in work.items():
        if folder not in folders:
            found=[p for p in (ROOT/'data/research/extracted').rglob(folder) if p.is_dir()]
            if len(found)!=1: raise ValueError('Ambiguous consumed folder')
            folders[folder]=found[0]
            parsed[folder]=candidate_raw(found[0])
        recs=list(folders[folder].glob(f'*-R{physical:02d}.rec'))
        if len(recs)!=1: raise ValueError('Ambiguous physical round')
        raw=parsed[folder]['rounds'][physical-1]
        tasks.append((recs[0],raw.get('header',raw),meta,code_hash))
    predictions=[]
    print('Full consumed physical inventory',len(tasks),flush=True)
    with ThreadPoolExecutor(max_workers=2) as pool:
        pending=[pool.submit(inspect,*args) for args in tasks]
        for future in as_completed(pending):
            r=future.result();predictions.append(r)
            print(len(predictions),'/',len(tasks),r['match_id'],r['physical_round'],
                  [(k,v['proposal'],v['reason']) for k,v in r['predictions'].items()] if r['occurrences'] else 'negative',flush=True)
    predictions.sort(key=lambda r:(r['match_id'],r['game_id'] or 0,r['folder'],r['physical_round']))
    destination=base/'completer-consumed-audit'
    (destination/'predictions.json').write_text(json.dumps(predictions,indent=2),encoding='utf-8')
    labels=labels_for_consumed()
    events,errors=[],[]
    for r in predictions:
        for kind,prediction in r['predictions'].items():
            label=labels.get((r['folder'],r['physical_round'],kind))
            occurred=any(o['kind']==kind for o in r['occurrences'])
            if bool(label)!=occurred:
                errors.append(dict(folder=r['folder'],round=r['physical_round'],kind=kind,error='occurrence_label_mismatch'))
            if prediction['proposal'] and not occurred:
                raise ValueError('Actor assigned without occurrence')
            if label:
                target=json.loads((ROOT/f"data/research/targets/siegegg-match-{r['match_id']}-api.json").read_text(encoding='utf-8'))
                name,tier=reviewed_label(r,kind)
                verdict=grade(prediction['proposal'],label[0],label[1],target)
                reviewed=verdict
                if name:
                    proposal=prediction['proposal']
                    reviewed='unresolved' if not proposal else 'correct' if proposal.split('.')[0].casefold()==name.split('.')[0].casefold() else 'incorrect'
                events.append({k:r[k] for k in ('match_id','game_id','round','physical_round','folder','build','cohort')}
                    |prediction|dict(kind=kind,original_label=label[0],original_verdict=verdict,
                                     reviewed_actor=name,review_tier=tier,reviewed_verdict=reviewed,runs=r['runs']))
    counts={kind:dict(total=sum(e['kind']==kind for e in events),
        original=dict(Counter(e['original_verdict'] for e in events if e['kind']==kind)),
        reviewed=dict(Counter(e['reviewed_verdict'] for e in events if e['kind']==kind)),
        independently_reviewed_events=sum(bool(e['reviewed_actor']) for e in events if e['kind']==kind))
        for kind in ('plant','disable')}
    negative=[r for r in predictions if not r['occurrences']]
    if snapshot()!=protected or any(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=sha for p,sha in immutable.items()):
        raise ValueError('Live data or immutable results changed')
    result=dict(status='consumed_development_structural_audit_not_fresh_validation',rounds=len(predictions),
        counts=counts,objective_free_rounds=len(negative),negative_proposals=sum(bool(v['proposal']) for r in negative for v in r['predictions'].values()),
        occurrence_errors=errors,events=events,protected_files=len(protected),immutable_results=immutable,
        variant_scope='exact9734089/a859ffff plant observer; frozenD remainsunchanged')
    (destination/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    lines=['# Consumed structural completing-owner audit','',
        'All original and completed consumed actor cohorts plus consumed September. Separate plant hypothesis; '
        'frozen disable rule unchanged. Uses occurrence + explicit lifecycle + unique temporal UID/body + side. '
        'No score bonuses, closest packets, last-killer labels or case-name exceptions. '
        'The already-observed build9734089/classa859ffff grammar is isolated and explicitly checked. '
        'These are development alignments, not fresh accuracy or production approval.','',
        f'Physical rounds{len(predictions)}; counts `{counts}`. Objective-free rounds{len(negative)}, '
        f'false actor proposals{result["negative_proposals"]}; occurrence/target errors`{errors}`.','',
        'Reviewed counts use documented official review labels for disputed cases, and original labels '
        'elsewhere. They are not all independently adjudicated ground truth. Original comparisons and '
        'every frozen result remain preserved. Known true wrong credits must be investigated separately.','',
        '| Match/game/logical or physical round | Kind | Completing owner | Original | Reviewed | Reason |',
        '| --- | --- | --- | --- | --- | --- |']
    for e in events:
        lines.append(f"| {e['match_id']}/{e['game_id']}/R{e['round'] or e['physical_round']:02d} | {e['kind']} | "
                     f"{e['proposal'] or 'unresolved'} | {e['original_verdict']} | {e['reviewed_verdict']} | {e['reason']} |")
    lines += ['', 'Every explicit attempt is retained in ignored per-round ledgers with owner, phase, start/end, '
        'timer progress, terminal and competing/unbound evidence. Kason/Hotancold, nearzero/state2 negatives '
        'and last-opponent deaths are mandatory controls. No historical DB changes. '
        f'{len(protected)} protected local file hashes and four immutable validation results unchanged.','',
        'Reproduce `.venv/Scripts/python.exe research/objective_completer_consumed_audit.py`. '
        'Per-round caches are keyed by replay and candidate dependency digests. No public JSON, livev2, '
        'archive, SQLite or target writes; no production promotion or v3 fit.','']
    (ROOT/'research/output/objective-completer-consumed-audit.md').write_text('\n'.join(lines),encoding='utf-8')
    print('COMPLETE',counts,'negatives',len(negative),result['negative_proposals'],'errors',errors,flush=True)


if __name__=='__main__':
    main()
