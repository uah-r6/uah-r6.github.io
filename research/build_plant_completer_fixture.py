"""Reduce consumed plant selector evidence, preserving exact selector outcomes."""
import copy
import json

from objective_actor_liveness import feedback
from objective_completer_consumed_audit import inputs, observation
from objective_plant_owner_candidate import candidate
from objective_disable_owner_candidate import run_end
from objective_player_component_fields import observe
from objective_production_check import candidate_raw
from objective_transition_probe import ROOT
from uah_guarded_actor_readonly import snapshot


def main():
    before=snapshot()
    inventory=list(inputs().values())
    desired=((4139,None,7),(4150,None,11),(3554,6679,4),(3173,5931,6),
             (3905,7016,3),(4138,None,9),(4141,None,14),(4141,None,6))
    cases=[]
    for match,game,number in desired:
        matches=[r for r in inventory if r['match_id']==match and (game is None or r['game_id']==game)
                 and (r['round']==number if game else r['physical_round']==number)]
        if len(matches)!=1: raise ValueError(f'Ambiguous fixture selection {match}/{game}/{number}: {len(matches)}')
        row=matches[0]
        folder=next(p for p in (ROOT/'data/research/extracted').rglob(row['folder']) if p.is_dir())
        rec=next(folder.glob(f"*-R{row['physical_round']:02d}.rec"))
        raw=candidate_raw(folder)['rounds'][row['physical_round']-1]
        header=raw.get('header',raw)
        state,owners,slots,fields=observe(rec)
        observed=observation(header,owners,slots,fields)
        deaths=feedback(rec)['events']
        expected=candidate(header,observed,owners,slots,state['properties'],deaths,header['matchFeedback'])[:2]
        reduced_header={k:header.get(k) for k in ('gamemode','codeVersion','teams','objectiveOccurrences')}
        reduced_header['objectiveOccurrences']=header.get('objectiveOccurrences',[])
        reduced_header['players']=[dict(username=p['username'],teamIndex=p['teamIndex'],id=i+1)
                                  for i,p in enumerate(header['players'])]
        episodes=copy.deepcopy(observed['episodes'])
        for e in episodes:
            e['records']=e['records'][-1:]
            e['samples']=e['samples'][:1]+e['samples'][-1:] if len(e['samples'])>1 else e['samples']
            e.pop('progress_float_observation',None)
        body_entities={d['component'] for (owner,slot),ds in slots.items() for d in ds
                       if slot=='4154dcc4' and d['component']}
        states=[{k:p[k] for k in ('entity','hash','size','offset','value')}
                for p in state['properties'] if p['entity'] in body_entities and p['hash']=='e788f6a5' and p['size']==4]
        if episodes:
            start=min(e['start_record'] for e in episodes)
            end=max(run_end(e) or e['samples'][-1]['offset'] for e in episodes)
            prior={}
            for p in states:
                if p['offset']<=start and (p['entity'] not in prior or p['offset']>prior[p['entity']]['offset']):
                    prior[p['entity']]=p
            states=list(prior.values())+[p for p in states if start<p['offset']<=end]
            lower=min([start]+[p['offset'] for p in states])
        else:
            states=[];lower=0;end=0
        relevant=body_entities|{e['entity'] for e in episodes}
        reduced_slots={}
        for key,ds in slots.items():
            if not any(d['component'] in relevant for d in ds): continue
            preceding=[d for d in ds if d['offset']<=lower]
            selected=preceding[-1:]+[d for d in ds if lower<d['offset']<=end]
            if selected: reduced_slots[key]=selected
        data=dict(header=reduced_header,observed=dict(episodes=episodes,orphan_records=observed['orphan_records']),
                  owners=owners,slots=reduced_slots,properties=states,deaths=deaths,
                  full_feedback=[dict(type=e['type']) for e in header['matchFeedback']])
        if candidate(**data)[:2]!=expected: raise ValueError('Reduction changed real selector outcome')
        data['owners']={str(k):v for k,v in owners.items()}
        data['slots']=[dict(owner=k[0],slot=k[1],declarations=ds) for k,ds in reduced_slots.items()]
        cases.append(dict(match_id=match,game_id=game,round=number,physical_round=row['physical_round'],
            expected_proposal=expected[0],expected_reason=expected[1],input=data))
        print(match,game,number,expected,flush=True)
    if snapshot()!=before: raise ValueError('Protected data changed')
    dest=ROOT/'tests/fixtures/objective-plant-completer.json'
    dest.write_text(json.dumps(dict(status='consumed_research_not_production_credit',
        reduction='No raw bytes/UUID/private path. Header numeric UIDs ordinalized. Episode endpoints retained after full monotonic validation, terminal fields retained, all relevant prior/during temporal routes and body state retained. Kason starters and Hotancold completer are separate.',
        cases=cases),indent=2),encoding='utf-8')
    print('public-safe fixture',len(cases),dest.stat().st_size)


if __name__=='__main__': main()
