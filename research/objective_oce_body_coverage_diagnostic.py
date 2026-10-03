"""Consumed OCE body-route inventory; no resolver or result changes."""
from bisect import bisect_right
from collections import Counter
import json

from objective_bonus_body_oce_cohort import DATA,verify
from objective_player_component_fields import observe,bindings_at
from objective_disable_owner_candidate import BODY_SLOT,BODY_CLASS
from v3_final_reserve import ROOT,sha


def main():
    verify();checkpoint=json.loads((ROOT/'research/objective-bonus-body-oce-permanent-result-checkpoint.json').read_text(encoding='utf-8'))
    result=DATA/'one-shot-primary-result.json'
    if sha(result)!=checkpoint['result_sha256']:raise ValueError('Permanent pooled result changed')
    rows=[];routes=Counter();raw_values=Counter()
    for p in sorted(DATA.glob('*/replay-predictions.json')):
        prediction=json.loads(p.read_text(encoding='utf-8'))
        for r in prediction['rounds']:
            if not r['verified_plant'] or r['proposed']['actor']:continue
            context=r['proposed']['context'];owner=context.get('owner_entity');start=context.get('start');end=context.get('end')
            if owner is None or start is None:raise ValueError('Expected structurally completed unresolved owner')
            rec=ROOT/r['replay_path']
            if sha(rec)!=r['replay_sha256']:raise ValueError('Sealed physical replay changed')
            state,owners,slots,fields=observe(rec);bindings=bindings_at(owners,slots,start)
            declared=[]
            for (entity,slot),ds in slots.items():
                if entity!=owner:continue
                prior=[d for d in ds if d['offset']<=start]
                if not prior:continue
                d=prior[-1];props=[f for f in fields if f['entity']==d['component'] and f['offset']<=end]
                values=[f for f in props if f['hash']=='e788f6a5' and f['size']==4]
                preceding=[f for f in values if f['offset']<=start]
                seen=([preceding[-1]] if preceding else [])+[f for f in values if start<f['offset']<=end]
                binding=bindings.get(d['component'])
                candidate=dict(slot=slot,class_hash=d['class_hash'],component=d['component'],declaration_offset=d['offset'],
                    unique_route_at_start=binding,known_body_slot=slot==BODY_SLOT,known_body_class=d['class_hash']==BODY_CLASS,
                    observed_state_field_values=[dict(offset=f['offset'],value=f['value']) for f in seen],
                    observed_field_hashes=sorted({f['hash'] for f in props}),interpretation='Typed declared slot only; unknown slot/class is not automatically a body.')
                declared.append(candidate)
                if seen:
                    routes[slot,d['class_hash']]+=1
                    if slot==BODY_SLOT:raw_values.update(f['value'] for f in seen)
            rows.append(dict(official_match_id=prediction['official_match_id'],round=r['round'],physical_round=r['physical_round'],
                build=r['build'],owner=context['owner_observation'],numeric_uid=context['numeric_uid'],timer_owner=owner,
                start=start,end=end,unresolved_reason=r['proposed']['reason'],body_reason=context['body_reason'],
                known_body_declarations=slots.get((owner,BODY_SLOT),[]),owned_slot_inventory=declared,replay_sha256=r['replay_sha256']))
    record=dict(status='consumed_body_route_coverage_inventory_not_recovery',records=rows,
                counts=dict(unresolved_plants=len(rows),builds=dict(Counter(str(r['build']) for r in rows)),
                            reasons=dict(Counter(r['body_reason'] for r in rows))),
                raw_state_field_values_on_expected_slot={str(k):v for k,v in sorted(raw_values.items())},
                state_field_routes=[dict(slot=slot,class_hash=cls,rounds=n) for (slot,cls),n in sorted(routes.items())],
                permanent_result_sha256=sha(result),candidate_modified=False,actors_reassigned=False)
    # Preserve the initial route-only diagnostic separately. This additive
    # report summarizes the already recorded raw field values; no new actor.
    path=DATA/'consumed-body-coverage-diagnostic-with-values.json'
    if path.exists():
        if json.loads(path.read_text(encoding='utf-8'))!=record:raise ValueError('Preserved consumed diagnostic differs')
    else:path.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    lines=['# Consumed OCE body-route coverage diagnostic','',f'Counts: `{record["counts"]}`.','',
           'All31 plant abstentions are build9734089 with missing known body declarations. '
           'This diagnostic inventories already-decoded, typed direct timer-owner slots and state-field properties. '
           'No alternative class is declared an active body, no actor is recovered, and the pooled result remains permanently insufficient.','',
           '| State-field slot | Class | Unresolved rounds with route |','| --- | --- | ---: |']
    for route in record['state_field_routes']:lines.append(f'| {route["slot"]} | {route["class_hash"]} | {route["rounds"]} |')
    lines+=['',f'At the unresolved completion intervals, expected slot4154dcc4 carries classb529300b in all31 cases; '
            f'the frozen body class is0c98c63f. Raw e788f6a5 field values are `{dict(raw_values)}`:26zero,5two, noone. '
            'Thus these examined routes contain no hidden state1 plant observation to count as a prospective bonus recovery. '
            'No class compatibility change or actor recovery is made.', '',
            'A numerical state field on an unknown typed component is not proof of body semantics or liveness. '
            'This is a future compatibility lead only. Before a change, require independently validated body structure, '
            'UID ownership, lifecycle/death/DBNO controls and a separately frozen unused validation cohort. '
            'No HP>0 replacement, state allowlist expansion, source freeze/result regrading, Rating fit or private/public mutation.','']
    (ROOT/'research/output/objective-bonus-body-oce-body-coverage.md').write_text('\n'.join(lines),encoding='utf-8')
    verify()
    if sha(result)!=checkpoint['result_sha256']:raise ValueError('Permanent pooled result changed')
    print(record['counts'],record['state_field_routes'])


if __name__=='__main__':main()
