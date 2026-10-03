"""Broad consumed controls for an isolated bonus-health plant hypothesis."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from objective_completer_consumed_audit import inputs, observation
from objective_player_component_fields import observe
from objective_actor_liveness import feedback
from objective_plant_owner_candidate import candidate as original
from objective_bonus_body_candidate import candidate as proposed
from objective_production_check import candidate_raw
from v3_consumed_cohort_integrity import sealed_sal_cache, PERMANENT_RESULTS
from v3_consumed_apac_credit_probe import sealed_apac_cache
from v3_final_reserve import ROOT, sha, source_sha
from uah_guarded_actor_readonly import snapshot


def inventory(include_prior):
    _,sal,_=sealed_sal_cache();_,apac=sealed_apac_cache()
    work=[]
    for event,cohort,prefix in [('SAL',sal,'v3-corrected-final-sal'),('APAC',apac,'v3-final-apac-n')]:
        for mid,inputs_ in cohort.items():
            for mapping in inputs_['prediction']['physical_mapping']:
                extraction=ROOT/f'data/research/extracted/{prefix}-{mid}'
                found=[p for p in extraction.rglob(mapping['filename']) if p.parent.name==mapping['folder']]
                if len(found)!=1 or sha(found[0])!=mapping['sha256']:raise ValueError('Consumed physical replay differs')
                work.append((found[0],dict(event=event,official_match_id=mid,round=mapping['logical_round'],
                                           physical_round=mapping['physical_round'],folder=mapping['folder'])))
    if include_prior:
        for item in inputs().values():
            folders=[p for p in (ROOT/'data/research/extracted').rglob(item['folder']) if p.is_dir()]
            if len(folders)!=1:raise ValueError('Ambiguous prior consumed physical folder')
            found=list(folders[0].glob(f"*-R{item['physical_round']:02d}.rec"))
            if len(found)!=1:raise ValueError('Ambiguous prior consumed round')
            work.append((found[0],item|dict(event='PRIOR_CONSUMED')))
    if len({r.resolve() for r,_ in work})!=len(work):raise ValueError('Duplicate physical source in consumed audit')
    return work


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--include-prior',action='store_true');args=parser.parse_args()
    protected=snapshot();records=[];parsed={};executable=ROOT/'.local-tools/bin/siege-dissect-actors.exe'
    dependencies=['research/objective_bonus_body_candidate.py','research/objective_plant_owner_candidate.py',
                  'research/objective_disable_owner_candidate.py','research/v3_body_state1_health_audit.py',
                  'research/objective_player_component_fields.py','research/objective_completer_consumed_audit.py']
    hashes={name:source_sha(ROOT/name) for name in dependencies}
    signature=hashlib.sha256(json.dumps(hashes,sort_keys=True).encode()+executable.read_bytes()).hexdigest()
    cache=ROOT/'data/research/diagnostics/bonus-body-consumed-audit';cache.mkdir(parents=True,exist_ok=True)
    for rec,meta in inventory(args.include_prior):
        replay_sha=sha(rec);path=cache/(hashlib.sha256((signature+replay_sha).encode()).hexdigest()+'.json')
        if path.exists():
            saved=json.loads(path.read_text())
            if saved['meta']!=meta:raise ValueError('Cached consumed physical/logical identity differs')
        else:
            if rec.parent not in parsed:parsed[rec.parent]=candidate_raw(rec.parent,executable)
            raw=parsed[rec.parent]['rounds'][meta['physical_round']-1];header=raw.get('header',raw)
            state,owners,slots,fields=observe(rec);feed=feedback(rec)['events']
            expected=[e for e in raw['matchFeedback'] if e['type']['name'] in ('Kill','Death')]
            if [e['feedback'] for e in feed]!=expected:raise ValueError('Existing feedback observer differs')
            observed=observation(header,owners,slots,fields)
            data=dict(header=header,observed=observed,owners=owners,slots=slots,
                      properties=state['properties'],deaths=feed,full_feedback=raw['matchFeedback'])
            before=original(**data);after=proposed(**data,body_fields=fields)
            occurrence=any(o['kind']=='plant' for o in header.get('objectiveOccurrences',[]))
            if before[0] and after!=before:raise ValueError('Already-resolved original actor changed')
            if after[0] and not occurrence:raise ValueError('Actor false positive without verified occurrence')
            saved=dict(meta=meta,replay_sha256=replay_sha,source_hashes=hashes,signature=signature,
                       verified_plant=occurrence,original=dict(actor=before[0],reason=before[1],context=before[2]),
                       proposed=dict(actor=after[0],reason=after[1],context=after[2]),
                       frozen_port_occurrences=header.get('objectiveOccurrences',[]),
                       interpretation='Consumed isolated plant hypothesis only; no port, target, statistic or model change.')
            path.write_text(json.dumps(saved,indent=2)+'\n',encoding='utf-8')
        records.append(saved)
        if len(records)%25==0 or saved['original']['actor']!=saved['proposed']['actor']:
            print('Consumed bonus-body audit',len(records),meta,'before',saved['original']['actor'],
                  'after',saved['proposed']['actor'],saved['proposed']['reason'],flush=True)
    counts=dict(rounds=len(records),verified_plants=sum(r['verified_plant'] for r in records),
                original_resolved=sum(r['original']['actor'] is not None for r in records),
                proposed_resolved=sum(r['proposed']['actor'] is not None for r in records),
                known_actor_regressions=sum(bool(r['original']['actor']) and r['original']['actor']!=r['proposed']['actor'] for r in records),
                no_plant_actor_false_positives=sum(not r['verified_plant'] and bool(r['proposed']['actor']) for r in records),
                no_plant_controls=sum(not r['verified_plant'] for r in records))
    changed=[r for r in records if r['original']['actor']!=r['proposed']['actor']]
    unresolved=[r for r in records if r['verified_plant'] and not r['proposed']['actor']]
    summary=dict(status='consumed_isolated_bonus_body_not_fresh_validation_or_production',counts=counts,
                 source_hashes=hashes,changes=changed,unresolved=unresolved,permanent_results=PERMANENT_RESULTS,
                 protected_hashes=protected,records=records)
    destination=cache/('summary-all-consumed.json' if args.include_prior else 'summary-sal-apac.json')
    if destination.exists():
        if json.loads(destination.read_text())!=summary:raise ValueError('Never overwrite changed consumed body hypothesis results')
    else:destination.write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    lines=['# Isolated bonus-health plant hypothesis: consumed structural audit','',
           'The frozen production resolver is unchanged. Its existing global occurrence, full unique roster, '
           'stable owner, complete interaction, cancellation/restart/competition, body route, death and last-opponent '
           'guards run first. A fallback is considered only for known state1 on an otherwise eligible plant owner. '
           'Disable behavior is unchanged.', '',
           f'Coverage/results: `{counts}`.', '',
           'At explicit body-property record endpoints and exact interaction endpoints, raw state observations must '
           'agree between existing observers. State1 requires direct same-owner typed numerical fields: '
           'health>baseline>0, ceiling=baseline+20, health<=ceiling, positive bonus fraction matching '
           '(health-baseline)/baseline within1e-6. Every retained numeric field must be uniquely bound at its own '
           'offset. State3/4/unknown, missing fields, sharing/replacement, unknown deaths and cancellation abstain. '
           'No operator name, score value or public actor label selects an owner.', '',
           '| Consumed event / map identity | Round | Original | Isolated proposal | Evidence |',
           '| --- | ---: | --- | --- | --- |']
    for r in changed:
        m=r['meta'];lines.append(f"| {m['event']}/{m.get('official_match_id',m.get('match_id'))}/{m['folder']} | "
                               f"{m['round']} | {r['original']['actor'] or 'unresolved'} | {r['proposed']['actor']} | {r['proposed']['reason']} |")
    lines+=['','Remaining unresolved verified plants:', '']
    for r in unresolved:
        m=r['meta'];lines.append(f"- {m['event']}/{m.get('official_match_id',m.get('match_id'))}/R{m['round']:02d}: {r['proposed']['reason']}.")
    lines+=['','The independent [KDS HUD review](v3-bonus-body-vod-review.md) corroborates one recovered case. '
            'The other recoveries are replay-derived proposals, not independently visually reviewed ground truth. '
            'Original public comparisons, reviewed labels and failed Rating final exclusions/metrics remain unchanged. '
            'No new fit or replay import. Broad consumed controls are development evidence; fresh unused actor '
            'validation must be prospectively reserved/frozen before production promotion.', '',
            'Both source freezes, both failed result hashes and all86live hashes unchanged. No runtime body/operator/'
            'action/kill/Rating change, SQLite writes, archive mutation, public regeneration, push or publish.', '']
    (ROOT/'research/output/objective-bonus-body-consumed-audit.md').write_text('\n'.join(lines),encoding='utf-8')
    sealed_sal_cache();sealed_apac_cache()
    if snapshot()!=protected:raise ValueError('Protected live files changed')
    print('Consumed isolated bonus-body results',counts,flush=True)


if __name__=='__main__':main()
