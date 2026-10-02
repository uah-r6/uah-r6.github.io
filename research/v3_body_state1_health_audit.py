"""Consumed numerical body-state evidence, not a new actor eligibility rule."""
from bisect import bisect_right
from collections import Counter, defaultdict
import json
import math
from pathlib import Path
import struct

from objective_player_component_fields import observe, bindings_at
from objective_actor_liveness import feedback
from objective_disable_owner_candidate import BODY_SLOT, BODY_CLASS
from v3_consumed_cohort_integrity import sealed_sal_cache, PERMANENT_RESULTS
from v3_consumed_apac_credit_probe import sealed_apac_cache
from v3_final_reserve import ROOT, source_sha, sha
from uah_guarded_actor_readonly import snapshot


def last_field(fields, offset):
    index = bisect_right([p['offset'] for p in fields], offset) - 1
    return fields[index] if index >= 0 else None


def numerical_snapshot(fields, state):
    values = {tag:last_field([p for p in fields if p['hash']==tag],state['offset'])
              for tag in ('252676c9','1149a672','013fd2da','80adcf7b')}
    hp, base, ceiling, bits = [values[tag]['value'] if values[tag] else None
                              for tag in ('252676c9','1149a672','013fd2da','80adcf7b')]
    fraction = struct.unpack('<f',struct.pack('<I',bits))[0] if type(bits)is int and 0<=bits<=0xffffffff else None
    evidence = (all(type(v)is int for v in (hp,base,ceiling)) and 0<base<hp<=ceiling
                and ceiling-base==20 and fraction is not None and math.isfinite(fraction)
                and fraction>0 and abs(fraction-(hp-base)/base)<1e-6)
    return dict(health=hp,baseline_field=base,ceiling_field=ceiling,bonus_fraction=fraction,
                above_baseline=hp>base if type(hp)is int and type(base)is int else None,
                consistent_positive_bonus=evidence,
                exact_fields={tag:p for tag,p in values.items() if p})


def main():
    protected=snapshot();_,sal,_=sealed_sal_cache();_,apac=sealed_apac_cache()
    totals=Counter();states=Counter();state1=[];nonactive_positive=[];rounds=[]
    for event,cohort,prefix in [('SAL',sal,'v3-corrected-final-sal'),('APAC',apac,'v3-final-apac-n')]:
        for mid,inputs in cohort.items():
            prediction=inputs['prediction']
            for mapping in prediction['physical_mapping']:
                extraction=ROOT/f'data/research/extracted/{prefix}-{mid}'
                files=[p for p in extraction.rglob(mapping['filename']) if p.parent.name==mapping['folder']]
                if len(files)!=1 or sha(files[0])!=mapping['sha256']:raise ValueError('Consumed physical replay identity differs')
                rec=files[0];raw,owners,slots,fields=observe(rec);feed=feedback(rec)['events']
                by_entity=defaultdict(list)
                for p in fields:by_entity[p['entity']].append(p)
                bound=[]
                for p in fields:
                    if p['hash']!='e788f6a5' or p['size']!=4:continue
                    route=bindings_at(owners,slots,p['offset']).get(p['entity'])
                    if not route or (route['slot'],route['class_hash'])!=(BODY_SLOT,BODY_CLASS):continue
                    name=route['player'];player=next(h for h in raw['header']['players'] if h['username']==name)
                    values=numerical_snapshot(by_entity[p['entity']],p)
                    dead_before=any(e['offset']>0 and e['offset']<=p['offset'] and (
                        e['feedback'].get('target')==name if e['feedback']['type']['name']=='Kill'
                        else e['feedback'].get('username')==name) for e in feed)
                    row=dict(event=event,official_match_id=mid,logical_round=mapping['logical_round'],
                             filename=mapping['filename'],replay_sha256=mapping['sha256'],
                             player=name,uid=player['id'],body_component=p['entity'],state=p['value'],
                             state_offset=p['offset'],state_record=p['record_start'],route=route,
                             numerical=values,dead_before_state=dead_before,
                             action_marker=raw['header'].get('actionPhaseStartOffset'),
                             interpretation='Observed raw state and numeric fields; no active-state enum or objective credit inferred.')
                    states[p['value']]+=1;bound.append(row)
                    if p['value']==1:state1.append(row)
                    if p['value']in (3,4) and values['health'] and values['health']>0:nonactive_positive.append(row)
                totals.update(rounds=1,bound_body_state_properties=len(bound))
                rounds.append(dict(event=event,official_match_id=mid,logical_round=mapping['logical_round'],
                                   replay_sha256=mapping['sha256'],state1_count=sum(p['state']==1 for p in bound)))
            print('Consumed numeric body state',event,mid,'state1 cumulative',len(state1),flush=True)
    counts=dict(totals,state_counts=dict(states),state1_properties=len(state1),
                state1_above_baseline=sum(p['numerical']['above_baseline'] is True for p in state1),
                state1_consistent_bonus=sum(p['numerical']['consistent_positive_bonus'] for p in state1),
                state1_dead_before=sum(p['dead_before_state'] for p in state1),
                state3_or4_with_positive_hp=len(nonactive_positive))
    report=dict(status='consumed_body_state1_numerical_observation_not_enum_promotion',counts=counts,
                rounds=rounds,state1_properties=state1,positive_hp_negative_controls=nonactive_positive,
                helper_sha256=source_sha(Path(__file__)),permanent_results=PERMANENT_RESULTS,protected_hashes=protected,
                interpretation='State1 may represent bonus/overheal health. Numerical correlation is not independent '
                               'visual semantic validation. State3/4 can have positive HP, so HP>0 alone cannot prove active. '
                               'Current resolver stays {0,2}; no objective/Rating/historical corrections.')
    path=ROOT/'data/research/diagnostics/consumed-body-state1-health.json'
    if path.exists():
        if json.loads(path.read_text())!=report:raise ValueError('Preserved numerical body evidence differs')
    else:path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    lines=['# Consumed body state 1: numerical bonus-health hypothesis','',
           'Research observation only. The production objective actor resolver still rejects state 1. '
           'No body enum, operator/action-start rule, objective actor, model input or final quality decision changes.', '',
           f'Complete consumed SAL/APAC audit: `{counts}`.', '',
           'Typed temporal body routes join the property to a unique declared stable UID. '
           'Known health field `252676c9` is compared with observed baseline/ceiling candidate fields '
           '`1149a672`/`013fd2da` and float field `80adcf7b`. The numerical hypothesis requires health '
           'above baseline, ceiling exactly baseline+20, health at most ceiling, and a positive fraction '
           'matching `(health-baseline)/baseline` within 1e-6. Names or external totals never choose a binding.', '',
           '## Interpretation limits', '',
           'Ubisoft describes [Finka Adrenal Surge](https://www.ubisoft.com/en-us/game/rainbow-six/siege/game-info/operators/finka) '
           'as a temporary team health boost. That primary description supports investigating bonus health; it does '
           'not define this internal replay state integer or certify all fields above. An independent current '
           'broadcast/HUD review is needed to distinguish bonus health from DBNO, revival or another condition.', '',
           'Positive HP is insufficient for actor eligibility: known state 3/4 negative controls can retain positive '
           'health values. Do not replace the body guard with `HP>0`, infer state from an operator name, or allow '
           'unknown states by default. No extra kill, injury or revive event is reconstructed from these fields.', '',
           'The exact three unresolved timer-owner cases and property offsets are in '
           '[the abstention inventory](v3-consumed-unknown-body-inventory.md). Their hypothetical recovery would '
           'require an isolated rule, broad cancellation/death/body-sharing/revive controls and separately frozen '
           'actor validation; original excluded maps and failed Rating finals remain excluded and failed.', '',
           'Both source freezes, both failed final hashes and all 86 protected live-file hashes are unchanged. '
           'No import, archive mutation, public regeneration, push, publishing or live Rating change.', '']
    (ROOT/'research/output/v3-body-state1-health-hypothesis.md').write_text('\n'.join(lines),encoding='utf-8')
    sealed_sal_cache();sealed_apac_cache()
    if snapshot()!=protected:raise ValueError('Protected live files changed')
    print('Consumed numerical state1 audit complete',counts,flush=True)


if __name__=='__main__':main()
