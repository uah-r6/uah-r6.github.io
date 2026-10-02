"""One-shot frozen disable-only actor validation; all predictions before labels."""
from collections import Counter
import hashlib
import json
import re
import subprocess

from objective_cached_map_validation import digest
from objective_disable_owner_consumed import inspect_round
from objective_production_check import candidate_raw
from objective_score_delta_validation import grade
from objective_transition_probe import ROOT
from uah_guarded_actor_readonly import snapshot


def atomic_json(path,value):
    temporary=path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    temporary.replace(path)


def acceptance(records,errors):
    named=[r for r in records if r['proposal'] is not None]
    if errors: return False,'occurrence_mismatch'
    if any(r['verdict']!='correct' for r in named): return False,'primary_actor_disagreement_or_identity_unknown'
    if len(named)<5 or len({r['game_id'] for r in named})<3: return False,'insufficient_named_disables_or_maps'
    return True,'predeclared_research_gate_met_not_production_approval'


def main():
    cache=ROOT/'data/research/diagnostics/objective-disable-stage2-validation'
    cache.mkdir(parents=True,exist_ok=True)
    result_path=cache/'result.json'
    if result_path.exists():
        result=json.loads(result_path.read_text(encoding='utf-8'))
        print('Existing immutable result; no reevaluation:',result['counts'],result['acceptance'])
        return
    freeze_path=ROOT/'research/objective-disable-stage2-freeze.json'
    freeze=json.loads(freeze_path.read_text(encoding='utf-8'))
    for name,expected in freeze['sha256'].items():
        if digest(ROOT/name)!=expected: raise ValueError('Frozen dependency changed: '+name)
    if subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip():
        raise ValueError('Clean committed freeze required before new actor labels')
    protected=snapshot()
    old_results={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in freeze['original_immutable_results']}
    reserve=json.loads((ROOT/'research/objective-disable-stage2-reserve.json').read_text(encoding='utf-8'))
    run_path=cache/'run.json'
    if run_path.exists():
        run=json.loads(run_path.read_text(encoding='utf-8'))
        if run['freeze_sha256']!=digest(freeze_path): raise ValueError('Interrupted freeze cannot change')
    else:
        run=dict(freeze_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                 freeze_sha256=digest(freeze_path),phase='replay_predictions',disable_actor_labels_opened=False)
        atomic_json(run_path,run)
    records=[]
    for map_ in reserve['maps']:
        folders=[p for p in (ROOT/'data/research/extracted').rglob(map_['folder']) if p.is_dir()]
        if len(folders)!=1: raise ValueError('Ambiguous frozen physical map')
        folder=folders[0]
        parsed=candidate_raw(folder)
        for file in map_['exact_replay_sha256']:
            rec=folder/file['filename']
            if digest(rec)!=file['sha256']: raise ValueError('Frozen replay changed')
            path=cache/f"prediction-{map_['game_id']}-R{file['logical_round']:02d}.json"
            if path.exists():
                record=json.loads(path.read_text(encoding='utf-8'))
                if record['freeze_sha256']!=run['freeze_sha256'] or record['rec_sha256']!=file['sha256']:
                    raise ValueError('Interrupted prediction belongs to different inputs')
            else:
                raw=parsed['rounds'][file['physical_round']-1]
                header=raw.get('header',raw)
                item=dict(rec=rec,header=header,match_id=map_['match_id'],game_id=map_['game_id'],
                          round=file['logical_round'],physical_round=file['physical_round'],folder=map_['folder'],
                          cohort='stage2_new_disable_labels')
                record=inspect_round(item)|dict(freeze_sha256=run['freeze_sha256'],rec_sha256=file['sha256'])
                atomic_json(path,record)
            records.append(record)
            print('predicted',map_['game_id'],file['logical_round'],record['proposal'],record['reason'],flush=True)
    if len(records)!=sum(m['rounds'] for m in reserve['maps']): raise ValueError('Missing frozen predictions')
    atomic_json(cache/'predictions.json',records)
    run.update(phase='grade_frozen_predictions',disable_actor_labels_opened=True)
    atomic_json(run_path,run)
    # ALL predictions are durable. This is the first access to public disable
    # event text. Plant actor text is not graded by this disable-only candidate.
    events,errors=[],[]
    for map_ in reserve['maps']:
        target=json.loads((ROOT/f"data/research/targets/siegegg-match-{map_['match_id']}-api.json").read_text(encoding='utf-8'))
        games=[g for g in target['games'] if g['id']==map_['game_id']]
        if len(games)!=1 or len(games[0]['rounds'])!=map_['rounds']:
            raise ValueError('Target round alignment differs')
        source=dict(players=reserve['player_aliases_by_match'][str(map_['match_id'])])
        for number,round_ in enumerate(games[0]['rounds'],1):
            public=[e for e in round_['events'] if e['type']=='disable']
            if len(public)>1: raise ValueError('Multiple public disables in one round')
            predicted=next(r for r in records if r['game_id']==map_['game_id'] and r['round']==number)
            occurrence=any(o['kind']=='disable' for o in predicted['occurrences'])
            if bool(public)!=occurrence:
                errors.append(dict(match_id=map_['match_id'],game_id=map_['game_id'],round=number,
                                   error='missed' if public else 'extra'))
            if public:
                label=public[0].get('description',public[0].get('html',''))
                events.append(predicted|dict(verdict=grade(predicted['proposal'],label,source,target),public_label=label))
            elif predicted['proposal'] is not None:
                errors.append(dict(match_id=map_['match_id'],game_id=map_['game_id'],round=number,error='actor_without_public_disable'))
    accepted,reason=acceptance(events,errors)
    counts=dict(Counter(e['verdict'] for e in events))
    if snapshot()!=protected or any(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=sha for p,sha in old_results.items()):
        raise ValueError('Protected live data or previous immutable result changed')
    result=dict(freeze_commit=run['freeze_commit'],freeze_sha256=run['freeze_sha256'],
                predictions_sha256=hashlib.sha256((cache/'predictions.json').read_bytes()).hexdigest(),
                maps=len(reserve['maps']),rounds=len(records),counts=counts,events=events,occurrence_errors=errors,
                acceptance=dict(passed=accepted,reason=reason),all_predictions_before_actor_labels=True,
                protected_files_checked=len(protected),original_immutable_results=old_results,
                independence_scope=reserve['independence_scope'],status='permanent_result_cohort_now_consumed')
    atomic_json(result_path,result)
    run.update(phase='completed_immutable_result')
    atomic_json(run_path,run)
    lines=['# Frozen disable-owner September actor validation', '',
           f"Freeze `{run['freeze_commit']}`. Seven cached maps,67rounds. Every replay prediction saved before "
           'public disable actor labels opened. This cohort is now consumed for this validation. '
           'Rating data was already consumed; this is new actor-label evidence, not an untouched Rating event. '
           'Plant actors were not graded. Original A and previous results remain unchanged.', '',
           f'Primary counts: `{counts}`. Occurrence errors: `{errors}`.', '',
           f'Predeclared research acceptance: `{result["acceptance"]}`. No production approval or historical update.', '',
           '| Match / game / round | Proposal | Primary outcome | Reason | Public actor text |',
           '| --- | --- | --- | --- | --- |']
    for e in events:
        label=re.sub('<[^>]+>',' ',e['public_label'])
        label=' '.join(label.split())
        lines.append(f"| {e['match_id']}/{e['game_id']}/R{e['round']:02d} | {e['proposal'] or 'unresolved'} | "
                     f"{e['verdict']} | {e['reason']} | {label} |")
    lines+=['', f'{len(protected)} protected SQLite/archive/public file hashes and three earlier immutable results unchanged. '
            'Do not retune this candidate and call these outcomes fresh again. Every missing/unknown actor remains unresolved. '
            'No live v2, SQLite, archives, public data, push or publish.', '']
    (ROOT/'research/output/objective-disable-stage2-validation.md').write_text('\n'.join(lines),encoding='utf-8')
    print('PERMANENT RESULT',counts,result['acceptance'],'occurrence_errors',errors,'protected',len(protected),flush=True)


if __name__=='__main__':
    main()
