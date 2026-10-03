"""Narrow direct-identity reference check on one independently reviewed DBNO.

No event reassignment: absence of literal UID/entity references in already
decoded owned component fields does not prove the downer is absent elsewhere.
"""
import json
from pathlib import Path

from objective_player_component_fields import observe, bindings_at
from objective_actor_liveness import feedback
from v3_body_state1_health_audit import numerical_snapshot
from v3_consumed_cohort_integrity import sealed_sal_cache
from v3_final_reserve import ROOT, sha, source_sha
from uah_guarded_actor_readonly import snapshot


def main():
    protected=snapshot();_,cached,_=sealed_sal_cache()
    prediction=cached[8580]['prediction'];mapping=prediction['physical_mapping'][5]
    sources=[p for p in (ROOT/'data/research/extracted/v3-corrected-final-sal-8580').rglob(mapping['filename'])
             if p.parent.name==mapping['folder']]
    if len(sources)!=1 or sha(sources[0])!=mapping['sha256']:raise ValueError('Consumed physical identity differs')
    rec=sources[0];state,owners,slots,fields=observe(rec);feed=feedback(rec)['events']
    names={p['id']:p['username'] for p in state['header']['players']}
    victim='Stk.INTZ';body=[];references=[];n_fields=0;declared_routes=set()
    for field in fields:
        route=bindings_at(owners,slots,field['offset']).get(field['entity'])
        if not route or route['player']!=victim:continue
        declared_routes.add((route['slot'],route['class_hash']))
        if route['slot']=='4154dcc4' and field['hash']=='e788f6a5' and field['size']==4:
            values=numerical_snapshot([f for f in fields if f['entity']==field['entity']],field)
            body.append(dict(offset=field['offset'],raw_state=field['value'],route=route,
                             health=values['health'],baseline=values['baseline_field'],record_start=field['record_start']))
        if field['size'] not in (4,8):continue
        n_fields+=1;other=names.get(field['value']) or owners.get(field['value'])
        if other and other!=victim:
            references.append(dict(field=field,route=route,referenced_player=other,
                                   interpretation='Literal value matches another header UID or declared UID-owner entity; semantics unverified.'))
    target_events=[e for e in feed if e['feedback'].get('target')==victim]
    if len(target_events)!=1 or target_events[0]['feedback']['username']!='Maia.TLAW':
        raise ValueError('Previously reviewed finish differs')
    record=dict(status='consumed_narrow_body_reference_negative_no_kill_reassignment',official_match_id=8580,
        physical_round=6,victim=victim,replay_sha256=sha(rec),helper_sha256=source_sha(Path(__file__)),
        body_states=body,fields_examined=n_fields,distinct_owned_routes=len(declared_routes),
        direct_other_player_numeric_references=references,observed_finish=target_events[0],
        independent_review='research/output/v3-consumed-dbno-vod-review.md',
        independent_review_sha256=sha(ROOT/'research/output/v3-consumed-dbno-vod-review.md'),protected_hashes=protected,
        limitations='Checks only already decoded4/8-byte fields with unique temporal Stk UID/component routes and literal UID/owner-entity values. Unknown packet classes, indirect/encoded references and unowned components are not covered. No nearest-event/counter/value inference or universal body enum assertion.')
    out=ROOT/'data/research/diagnostics/consumed-stk-dbno-body-reference.json'
    if out.exists():
        if json.loads(out.read_text(encoding='utf-8'))!=record:raise ValueError('Never overwrite changed consumed diagnostic')
    else:out.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    lines=['# Consumed Stk DBNO direct-reference check','',
        'SAL8580/Lair/R06 was independently reviewed in official broadcast; Kheyze receives credited kill while Maia is the displayed finisher. '
        'This diagnostic searches existing explicit typed component routes for a direct victim/downer reference, without assigning any credit.', '',
        '| Body property offset | Raw state | Health | Baseline |', '| ---: | ---: | ---: | ---: |']
    for row in body:lines.append(f"| {row['offset']} | {row['raw_state']} | {row['health']} | {row['baseline']} |")
    lines+=['',f'Observed finish: Maia ->Stk, offset{target_events[0]["offset"]}. '
        f'{n_fields} owned4/8-byte numeric fields across{len(declared_routes)} uniquely declared component routes examined; '
        f'{len(references)} literal references to other header playerUIDs or UID-owner entities.', '',
        'The raw3 transition precedes Stk finish in this particular independently visible DBNO case. It is not a universal enum definition. '
        'No direct downer identity was found in this narrow component-field view. This does not prove no reliable victim/downer packet exists elsewhere. '
        'The cumulative credited-kill counter does not by itself provide victim/event association. Do not assign from last counter, packet proximity or public totals.', '',
        'Next: inspect parser-owned damage/DBNO records for an explicit stable identity relation while retaining the separate finisher/death event. '
        'No runtime/operator/action boundary/statistic/model/database/public changes, new fit, push or publish. All86protected hashes and failed final seals unchanged.','']
    (ROOT/'research/output/v3-consumed-dbno-body-reference.md').write_text('\n'.join(lines),encoding='utf-8')
    sealed_sal_cache()
    if snapshot()!=protected:raise ValueError('Protected live files changed')
    print('Consumed direct reference check:',n_fields,'numeric fields;',len(references),'other-player references; no reassignment',flush=True)


if __name__=='__main__':main()
