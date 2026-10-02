"""Characterize consumed body abstentions; do not expand the actor allowlist."""
from bisect import bisect_right
import json
from pathlib import Path

from objective_player_component_fields import observe, bindings_at
from objective_actor_liveness import feedback
from objective_completer_consumed_audit import observation
from objective_plant_owner_candidate import candidate
from objective_production_check import candidate_raw
from objective_disable_owner_candidate import BODY_SLOT, BODY_CLASS
from v3_consumed_cohort_integrity import sealed_sal_cache, PERMANENT_RESULTS
from v3_consumed_apac_credit_probe import sealed_apac_cache
from v3_corrected_final_pipeline import DATA as SAL
from v3_final_pipeline import DATA as APAC
from v3_final_reserve import ROOT, source_sha, sha
from uah_guarded_actor_readonly import snapshot


def main():
    protected=snapshot();sal_frozen,sal,_=sealed_sal_cache();apac_frozen,apac=sealed_apac_cache()
    results=[];parsed={}
    for event,directory,cohort,frozen,prefix in [('SAL',SAL,sal,sal_frozen,'v3-corrected-final-sal'),
                                               ('APAC',APAC,apac,apac_frozen,'v3-final-apac-n')]:
        for mid,inputs in cohort.items():
            prediction=inputs['prediction']
            for unresolved in prediction['unresolved_objectives']:
                if unresolved['reason']!='timer_owner_body_unresolved':continue
                mapping=next(m for m in prediction['physical_mapping'] if m['logical_round']==unresolved['round'])
                extraction=ROOT/f'data/research/extracted/{prefix}-{mid}'
                files=[p for p in extraction.rglob(mapping['filename']) if p.parent.name==mapping['folder']]
                if len(files)!=1 or sha(files[0])!=mapping['sha256']:raise ValueError('Physical replay identity differs')
                rec=files[0]
                if rec.parent not in parsed:parsed[rec.parent]=candidate_raw(rec.parent,ROOT/frozen['parser_binary'])
                raw=parsed[rec.parent]['rounds'][mapping['physical_round']-1];header=raw.get('header',raw)
                state,owners,slots,fields=observe(rec);feed=feedback(rec)
                observed=observation(header,owners,slots,fields)
                actor,reason,context=candidate(header,observed,owners,slots,state['properties'],feed['events'],raw['matchFeedback'])
                if actor is not None or reason!='timer_owner_body_unresolved':
                    raise ValueError('Research inventory differs from frozen conservative abstention')
                name,owner=context['owner_observation'],context['owner_entity']
                start,end=context['start'],context['end']
                declarations=slots.get((owner,BODY_SLOT),[])
                prior=[d for d in declarations if d['offset']<=start]
                declaration=prior[-1] if prior else None
                component=declaration['component'] if declaration else None
                body=[p for p in fields if p['entity']==component and p['hash']=='e788f6a5' and p['size']==4]
                previous=[p for p in body if p['offset']<=start]
                during=[p for p in body if start<p['offset']<=end]
                adjacent=([previous[-1]] if previous else [])+during+[p for p in body if p['offset']>end][:3]
                tagged=[]
                for p in adjacent:
                    route=bindings_at(owners,slots,p['offset']).get(p['entity'])
                    tagged.append(p|dict(route=route,position='prior' if p['offset']<=start else 'during' if p['offset']<=end else 'after'))
                player=next(p for p in header['players'] if p['username']==name)
                changes=[d for d in declarations if start<d['offset']<=end]
                row=dict(event=event,official_match_id=mid,map=prediction['map'],logical_round=unresolved['round'],
                         folder=mapping['folder'],filename=mapping['filename'],physical_round=mapping['physical_round'],
                         replay_sha256=mapping['sha256'],build=header['codeVersion'],port_actor=None,port_reason=reason,
                         timer_owner_observation=name,timer_uid=player['id'],header_operator=player.get('operator'),
                         context=context,body_declaration=declaration,body_declaration_changes=changes,
                         body_fields_around_episode=tagged,
                         property_hash_counts={h:sum(p['hash']==h for p in fields if p['entity']==component)
                                               for h in sorted({p['hash'] for p in fields if p['entity']==component})},
                         whole_body_timeline=[dict(offset=p['offset'],value=p['value'],record_start=p['record_start']) for p in body],
                         timer_episode=[r for r in observed['episodes'] if r['start_record']==start],
                         feedback=feed['events'],prediction_sha256=sha(directory/str(mid)/'replay-predictions.json'),
                         interpretation='Timer owner observation is not promoted to actor. Unknown body state/route remains unresolved. '
                                        'No operator name or external label chooses an owner or expands a body-state enum.')
                results.append(row)
                print('Consumed unknown body',event,mid,'R',row['logical_round'],name,
                      'operator',player.get('operator'),'body reason',context['body_reason'],
                      'values',context['body_values'],'declaration',declaration,flush=True)
    report=dict(status='consumed_unknown_body_inventory_no_actor_rule_change',helper_sha256=source_sha(Path(__file__)),
                records=results,permanent_results=PERMANENT_RESULTS,protected_hashes=protected)
    path=ROOT/'data/research/diagnostics/consumed-unknown-body-inventory.json'
    if path.exists():
        if json.loads(path.read_text())!=report:raise ValueError('Preserved unknown-body inventory differs')
    else:path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    lines=['# Consumed professional unknown-body actor abstentions','',
           'The frozen production actor resolver is unchanged. This inventory identifies which guard prevents '
           'credit in the three current SAL/APAC abstentions. A unique timer owner is an observation, not an '
           'approved actor when the known-active body guard fails. No external actor label is used.', '',
           '| Event / official / round | Timer owner observation | Recorded operator | Body guard | Values over episode | Declaration class / route changes |',
           '| --- | --- | --- | --- | --- | --- |']
    for row in results:
        d=row['body_declaration'];c=row['context'];operator=row['header_operator']
        lines.append(f"| {row['event']}/{row['official_match_id']}/R{row['logical_round']:02d} | {row['timer_owner_observation']} | "
                     f"{operator} | {c['body_reason']} | {c['body_values']} | {d['class_hash'] if d else 'missing'} / {row['body_declaration_changes']} |")
    lines+=['','Raw state integers are not relabeled as DBNO, shield, active or dead from operator correlations. '
            'Existing active values {0,2} remain the only accepted states. A future rule needs direct state semantics '
            'and cancellation/death/revive controls, an isolated consumed-data candidate, and a separately frozen '
            'actor validation. This inventory does not retroactively admit excluded maps or revise either failed final.', '',
            'Exact prior/during/after property offsets, temporal ownership routes, body declaration histories, '
            'timer episode and original kill/death feedback are retained in the ignored diagnostic JSON. '
            'No new low-level decoder, objective credit, operator/action-start, Rating or historical data change.', '',
            'Both source freezes, both failed result hashes and all 86 protected live hashes are unchanged. '
            'No SQLite writes, archive mutation, public regeneration, push or publish.', '']
    (ROOT/'research/output/v3-consumed-unknown-body-inventory.md').write_text('\n'.join(lines),encoding='utf-8')
    sealed_sal_cache();sealed_apac_cache()
    if snapshot()!=protected:raise ValueError('Protected live files changed')


if __name__=='__main__':main()
