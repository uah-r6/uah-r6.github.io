"""Reduce consumed selector inputs; no raw replay, dump, UUID or private path."""
import copy
import json

from objective_actor_liveness import feedback
from objective_disable_owner_candidate import candidate, run_end
from objective_player_component_fields import observe
from objective_production_check import candidate_raw
from objective_timer_component_episodes import component_episodes
from objective_transition_probe import ROOT, replay_file
from uah_guarded_actor_readonly import snapshot


def main():
    protected=snapshot()
    source=ROOT/'data/research/diagnostics/player-component-fields/disable-owner-consumed-result.json'
    rows=json.loads(source.read_text(encoding='utf-8'))['records']
    selected=[next(r for r in rows if (r['match_id'],r['game_id'],r['round'])==key)
              for key in ((3173,5931,3),(3173,5932,17),(3563,6675,2),(3563,6675,10),
                          (6157,10427,1),(3073,None,8))]
    selected += [dict(match_id=m,round=n,physical_round=n,rec=replay_file(m,n)[0])
                 for m,n in ((4138,9),(4141,14),(4139,7))]
    cases=[]
    for row in selected:
        if 'rec' in row:
            rec=row['rec']
        else:
            folder=next(p for p in (ROOT/'data/research/extracted').rglob(row['folder']) if p.is_dir())
            rec=next(folder.glob(f"*-R{row['physical_round']:02d}.rec"))
        raw=candidate_raw(rec.parent)['rounds'][row['physical_round']-1]
        raw=raw.get('header',raw)
        state,owners,slots,fields=observe(rec)
        observed=component_episodes(owners,slots,fields)
        feed=feedback(rec)
        kind='plant' if row['match_id']==4139 else 'disable'
        expected=candidate(raw,observed,owners,slots,state['properties'],feed['events'],raw['matchFeedback'],kind)[:2]
        header={k:raw.get(k) for k in ('gamemode','teams','objectiveOccurrences')}
        header['players']=[dict(username=p['username'],teamIndex=p['teamIndex'],id=i+1)
                           for i,p in enumerate(raw['players'])]
        episodes=copy.deepcopy(observed['episodes'])
        for e in episodes:
            # Decoder coverage has a separate full-field fixture. This tests
            # selector semantics with endpoints, retaining all competing runs.
            e['records']=e['records'][-1:]
            e['samples']=e['samples'][:1]+e['samples'][-1:] if len(e['samples'])>1 else e['samples']
            e.pop('progress_float_observation',None)
        retained={d['component'] for (owner,slot),ds in slots.items() for d in ds
                  if slot in ('4154dcc4','27c08dca') and d['component']}
        reduced_slots={key:ds for key,ds in slots.items() if any(d['component'] in retained for d in ds)}
        reduced_properties=[{k:p[k] for k in ('entity','hash','size','offset','value')}
                            for p in state['properties'] if p['entity'] in retained
                            and p['hash']=='e788f6a5' and p['size']==4]
        phase1=[e for e in episodes if e['state']==1]
        if phase1:
            start=min(e['start_record'] for e in phase1)
            end=max(run_end(e) or e['samples'][-1]['offset'] for e in phase1)
            prior={}
            for p in reduced_properties:
                if p['offset']<=start and (p['entity'] not in prior or p['offset']>prior[p['entity']]['offset']):
                    prior[p['entity']]=p
            reduced_properties=list(prior.values())+[p for p in reduced_properties if start<p['offset']<=end]
        else:
            reduced_properties=[]
        reduced=dict(header=header,observed=dict(episodes=episodes,orphan_records=observed['orphan_records']),
                     owners=owners,slots=reduced_slots,properties=reduced_properties,deaths=feed['events'],
                     full_feedback=[dict(type=e['type']) for e in raw['matchFeedback']],kind=kind)
        if candidate(**reduced)[:2]!=expected:
            raise ValueError('Reduced fixture changed selector outcome')
        reduced['owners']={str(k):v for k,v in owners.items()}
        reduced['slots']=[dict(owner=owner,slot=slot,declarations=ds) for (owner,slot),ds in reduced_slots.items()]
        cases.append(dict(match_id=row['match_id'],game_id=row.get('game_id'),round=row['round'],
                          expected_proposal=expected[0],expected_reason=expected[1],input=reduced))
        print(row['match_id'],row['round'],expected,flush=True)
    if snapshot()!=protected:
        raise ValueError('Protected local files changed')
    dest=ROOT/'tests/fixtures/objective-disable-owner.json'
    dest.write_text(json.dumps(dict(status='consumed_research_only_not_production_credit',
        reduction='Header UIDs replaced by stable ordinal test IDs. Timer/body ownership histories and health '
                  'states retained as the last pre-interaction value and all during interactions; episode samples reduced to endpoints after full monotonic verification, '
                  'last record retained for exact terminal property end. No raw replay/dump/UUID/private path.',
        cases=cases),indent=2,allow_nan=False),encoding='utf-8')
    print('fixture',len(cases),'bytes',dest.stat().st_size,'protected',len(protected))


if __name__=='__main__':
    main()
