"""Bounded discovery audit of score batches in the original objective cohort.

Raw entities are not assumed to be teammates or identified players. A common
delta plus 100 is a residual candidate only, never actor credit. The twelve-map
extension is not used for actor-hypothesis development by this script.
"""
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

from objective_score_ledger import ledger
from objective_transition_probe import ROOT, PARSER, replay_file


def batch(events, center):
    window=[e for e in events if -5000<=e['offset']-center<=20000]
    by_entity=defaultdict(list)
    for event in window:by_entity[event['entity']].append(event)
    rows=[]
    for entity,changes in by_entity.items():
        score=[e for e in changes if e['counter']=='score' and e['offset']>=center]
        if not score:continue
        rows.append({'entity':entity,'prior_score':score[0]['previous'],'new_score':score[-1]['value'],
                     'score_delta':sum(e['delta'] for e in score),
                     'kill_delta':sum(e['delta'] for e in changes if e['counter']=='kills'),
                     'assist_delta':sum(e['delta'] for e in changes if e['counter']=='assists'),
                     'changes':changes})
    frequency=Counter(r['score_delta'] for r in rows if r['score_delta']>0)
    common=[delta for delta,count in frequency.items() if count>=3]
    residual=[{'entity':r['entity'],'base_candidate':base,'residual':100,
               'kill_delta':r['kill_delta'],'assist_delta':r['assist_delta']}
              for r in rows for base in common if r['score_delta']-base==100]
    return {'entities':rows,'common_delta_groups':dict(frequency),
            'residual_candidates':residual,'actor':None,
            'limitation':'Entity/player/team binding and other score contributions are unresolved'}


def main():
    diag=ROOT/'data/research/diagnostics'
    decoded=json.loads((diag/'objective-encoding-validation/summary.json').read_text())['rounds']
    classified={(r['match_id'],r['round']):r['result'] for r in json.loads(
        (diag/'objective-encoding-validation/occurrence-validation.json').read_text())['results']}
    cache=diag/'objective-score-batch-cohort';cache.mkdir(parents=True,exist_ok=True)
    signature=hashlib.sha256(Path(__file__).with_name('objective_score_ledger.py').read_bytes()).hexdigest()
    reports=[]
    with tempfile.TemporaryDirectory() as temp:
        dump=Path(temp)/'round.dump'
        for row in decoded:
            classification=classified[(row['match_id'],row['round'])]
            if not classification['plant']:continue
            rec,diagnostic=replay_file(row['match_id'],row['round'])
            target=cache/f"{row['match_id']}-R{row['round']:02d}.json"
            result=json.loads(target.read_text()) if target.exists() else {}
            if result.get('signature')!=signature:
                cached_dump=diag/f"objective-encoding/{row['match_id']}-R{row['round']:02d}.dump"
                if cached_dump.exists():data=cached_dump.read_bytes()
                else:
                    subprocess.run([str(PARSER),'--dump','-o',str(dump),str(rec)],check=True,capture_output=True)
                    data=dump.read_bytes()
                result={'signature':signature,**ledger(data)}
                target.write_text(json.dumps(result))
            plant=next(e for e in row['events'] if e['value']==1)
            centers=[('plant',plant['offset'],'plant_state')]
            if classification['disable']:
                zero=[e for e in row['events'] if e['value']==0 and e['offset']>plant['offset']]
                terminal=[r for r in diagnostic['timer_runs'] if r['min']<=.1 and r['last_offset']>plant['offset']]
                if zero:centers.append(('disable',zero[-1]['offset'],'disable_state'))
                elif terminal:centers.append(('disable',terminal[-1]['last_offset'],'diagnostic_timer_only_alignment'))
                else:raise ValueError('No diagnostic disable center')
            for kind,center,source in centers:
                reports.append({'match_id':row['match_id'],'round':row['round'],'kind':kind,
                                'center':center,'center_source':source,**batch(result['events'],center)})
            print('checked',row['match_id'],row['round'],flush=True)
    counts={kind:{'events':sum(r['kind']==kind for r in reports),
                  'one_residual_entity':sum(r['kind']==kind and len({e['entity'] for e in r['residual_candidates']})==1 for r in reports),
                  'no_residual_entity':sum(r['kind']==kind and not r['residual_candidates'] for r in reports),
                  'multiple_residual_entities':sum(r['kind']==kind and len({e['entity'] for e in r['residual_candidates']})>1 for r in reports),
                  'resolved_actors':0} for kind in ['plant','disable']}
    output={'counts':counts,'events':reports}
    (cache/'summary.json').write_text(json.dumps(output,indent=2))
    print(json.dumps(counts,indent=2))


if __name__=='__main__':main()
