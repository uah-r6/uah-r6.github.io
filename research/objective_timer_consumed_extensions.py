"""Declared timer grammar on three ALREADY CONSUMED actor validations.

Emits packet owner observations, not actors or revised validation outcomes.
Earlier immutable result hashes must match after the complete diagnostic.
No new labels, downloads, fitting, production or private data modification.
"""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from threading import Lock

from objective_cached_map_validation import inputs
from objective_player_component_fields import observe
from objective_timer_component_episodes import component_episodes
from objective_timer_negative_controls import completion_like
from objective_score_delta_validation import grade
from objective_production_check import candidate_raw
from objective_transition_probe import ROOT
from uah_guarded_actor_readonly import snapshot

SETS = (
    ('first-reserve','objective-combined-reserve','objective-actor-reserve.json'),
    ('si-final','objective-si-final-validation','objective-si-final-reserve.json'),
    ('cached-six-maps','objective-cached-map-validation','objective-cached-map-reserve.json'),
)


def associated_owner(observed, row, previous, roles, kind):
    state = 0 if kind=='plant' else 1
    runs = [e for e in observed['episodes'] if e['state']==state and completion_like(e)]
    associated = [e for e in runs if row and previous < e['start_record'] <= e['end_record'] < row['center']]
    owner = associated[0]['binding']['player'] if len(associated)==1 else None
    if owner and roles.get(owner) != ('Attack' if state==0 else 'Defense'):
        return None,'owner_role_conflict',runs
    reason = 'unique_component_run_before_anchor' if owner else 'missing_anchor' if row is None else 'absent_or_ambiguous_component_run'
    return owner,reason,runs


def event_observation(event, rec, raw, lock):
    # Two objective kinds may share one physical replay. Serialize their cache
    # reads/writes so a reader never opens another worker's unfinished JSON.
    with lock:
        return _event_observation(event, rec, raw)


def _event_observation(event, rec, raw):
    if 'header' not in raw:
        raw = dict(header=raw,matchFeedback=raw['matchFeedback'])
    row,_,_,previous = inputs(rec,raw,event['kind'])
    state,owners,slots,fields = observe(rec)
    observed = component_episodes(owners,slots,fields)
    roles = {p['username']:raw['header']['teams'][p['teamIndex']]['role'] for p in raw['header']['players']}
    owner,reason,runs = associated_owner(observed,row,previous,roles,event['kind'])
    return {k:event[k] for k in ('match_id','game_id','round','physical_round','folder','kind','build')} | dict(
        packet_owner_observation=owner,observation_reason=reason,
        all_phase_owner_observations=sorted({e['binding']['player'] for e in runs}),
        center=row['center'] if row else None,previous_anchor=previous,
        component_runs=observed,actor=None,actor_reason='research_only_semantics_not_promoted')


def main():
    base = ROOT/'data/research/diagnostics'
    protected = snapshot()
    hashes, work, manifests, originals, sources = {}, [], {}, {}, {}
    source_by_id = {s['siegegg_match_id']:s for s in json.loads((ROOT/'research/sources.json').read_text(encoding='utf-8'))['matches'] if s.get('siegegg_match_id')}
    for label,directory,manifest_name in SETS:
        path = base/directory/'result.json'
        result = json.loads(path.read_text(encoding='utf-8'))
        # A completed immutable result is required: the manifest's historical
        # sealed status alone is not authority to examine any new actor labels.
        if not result.get('freeze_commit') or result.get('rounds') not in (60,58,61):
            raise ValueError('Cohort lacks a completed consumed validation result')
        hashes[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
        manifest = json.loads((ROOT/'research'/manifest_name).read_text(encoding='utf-8'))
        manifests[label],originals[label] = manifest,result
        folders = {}
        for event in result['events']:
            if event['folder'] not in folders:
                matches = [p for p in (ROOT/'data/research/extracted').rglob(event['folder']) if p.is_dir()]
                if len(matches)!=1:
                    raise ValueError('Ambiguous consumed physical folder')
                folder = matches[0]
                folders[event['folder']] = (folder,candidate_raw(folder))
            folder,raw = folders[event['folder']]
            recs = list(folder.glob(f"*-R{event['physical_round']:02d}.rec"))
            if len(recs)!=1:
                raise ValueError('Ambiguous consumed physical replay round')
            map_ = next(m for m in manifest['maps'] if m['game_id']==event['game_id'])
            expected = [r for r in map_.get('exact_replay_sha256',[]) if r['folder']==event['folder'] and r['filename']==recs[0].name]
            if expected and (len(expected)!=1 or hashlib.sha256(recs[0].read_bytes()).hexdigest()!=expected[0]['sha256']):
                raise ValueError('Consumed replay digest changed')
            sources[label,event['match_id']] = (dict(players=manifest['player_aliases']) if 'player_aliases' in manifest
                else dict(players=manifest['player_aliases_by_match'][str(event['match_id'])]) if 'player_aliases_by_match' in manifest
                else source_by_id[event['match_id']])
            work.append((label,event,recs[0],raw['rounds'][event['physical_round']-1]))
    observations = []
    locks = {rec:Lock() for _,_,rec,_ in work}
    with ThreadPoolExecutor(max_workers=2) as pool:
        pending = {pool.submit(event_observation,event,rec,raw,locks[rec]):(label,event) for label,event,rec,raw in work}
        for future in as_completed(pending):
            label,event = pending[future]
            observation = future.result() | dict(cohort=label)
            observations.append(observation)
            print(len(observations),'/',len(work),label,event['game_id'],event['round'],event['kind'],
                  observation['packet_owner_observation'],observation['observation_reason'],flush=True)
    observations.sort(key=lambda r:(r['cohort'],r['match_id'],r['game_id'],r['round'],r['kind']))
    dest = base/'player-component-fields'
    # Save all replay observations before consulting even consumed target text.
    (dest/'consumed-extensions-observations.json').write_text(json.dumps(observations,indent=2,allow_nan=False),encoding='utf-8')
    records = []
    for row in observations:
        result = originals[row['cohort']]
        event = next(e for e in result['events'] if all(e[k]==row[k] for k in ('match_id','game_id','round','kind')))
        target = json.loads((ROOT/f"data/research/targets/siegegg-match-{row['match_id']}-api.json").read_text(encoding='utf-8'))
        alignment = grade(row['packet_owner_observation'],event['public_label'],sources[row['cohort'],row['match_id']],target)
        records.append({k:row[k] for k in ('cohort','match_id','game_id','round','physical_round','kind','build',
                                         'packet_owner_observation','observation_reason','all_phase_owner_observations')}
                       | dict(public_label_alignment=alignment,original_candidate=event['candidate'],
                              original_verdict=event['verdict'],actor=None))
    if snapshot()!=protected:
        raise ValueError('Protected SQLite/archive/public file changed during observation')
    if any(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=want for p,want in hashes.items()):
        raise ValueError('Immutable earlier validation result changed')
    counts = {label:{kind:dict(Counter(r['public_label_alignment'] for r in records if r['cohort']==label and r['kind']==kind))
                     for kind in ('plant','disable')} for label,_,_ in SETS}
    (dest/'consumed-extensions-alignment.json').write_text(json.dumps(dict(counts=counts,immutable_result_sha256=hashes,
                                                    protected_files_checked=len(protected),records=records),indent=2),encoding='utf-8')
    lines = ['# Timer component grammar on consumed actor extensions', '',
             '**Development ownership alignment only.** All three validation sets were already consumed. '
             'No revised validation result, fresh accuracy claim or actor credit. Every actor remains null. '
             'Replay observations were saved before reading consumed public label text. '
             'An explicit state0/1 run, monotonic full timer and state2 ending may be associated with an existing '
             'unique global completion anchor; missing anchors remain missing. Same-kind competing runs abstain. '
             'Owner must match the objective side. Near-zero/state2 alone is insufficient (negative controls).', '',
             f'Consumed label alignment: `{counts}`.', '',
             '| Set / game / round / kind | Owner observation | Reason | Consumed label alignment | Original A / primary result unchanged |',
             '| --- | --- | --- | --- | --- |']
    for r in records:
        lines.append(f"| {r['cohort']}/{r['game_id']}/R{r['round']:02d}/{r['kind']} | {r['packet_owner_observation']} | "
                     f"{r['observation_reason']} | {r['public_label_alignment']} | {r['original_candidate']} / {r['original_verdict']} |")
    lines += ['', f'All three immutable result SHA256 values unchanged; {len(protected)} protected local file hashes unchanged.', '',
              'No frozen candidate or health-class allowlist was changed. Missing legacy scoreboard identity does not '
              'itself invalidate a separate explicit timer ownership observation, but broader semantic validation is '
              'required before it can supply actor credit. Both mandatory Raid/Aiden and J9O/njr controls remain unresolved. '
              'Public target contradictions remain recorded separately; never silently revise them.', '']
    (ROOT/'research/output/objective-timer-consumed-extensions.md').write_text('\n'.join(lines),encoding='utf-8')
    print(counts, 'protected',len(protected),'immutable results unchanged')


if __name__ == '__main__':
    main()
