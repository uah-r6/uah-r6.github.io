"""Discovery evaluation of team-relative score residuals; never production credit.

Fixed rule: explicit component/UID join, unique team modal delta shared by at
least three players, unique +100 residual, and no simultaneous kill/assist
counter increase for that candidate. The 12-map actor extension stays unused.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

from objective_score_identity import score_identity_candidates
from objective_production_check import candidate_raw
from objective_transition_probe import ROOT, PARSER, replay_file


def predict_actor(event, identities, header):
    side='Attack' if event['kind']=='plant' else 'Defense'
    names={p['username'] for p in header['players'] if header['teams'][p['teamIndex']]['role']==side}
    mapping={int(k):v[0] for k,v in identities['entity_names'].items() if len(v)==1}
    bound=[name for name in mapping.values() if name in names]
    if len(bound)!=len(names) or len(set(bound))!=len(names):return None,{'reason':'incomplete_identity_binding'}
    deltas={name:0 for name in names};conflicts=set()
    for row in event['entities']:
        name=mapping.get(row['entity'])
        if name not in names:continue
        deltas[name]=row['score_delta']
        if row['kill_delta']>0 or row['assist_delta']>0:conflicts.add(name)
    modes=Counter(deltas.values());bases=[v for v,n in modes.items() if n>=3]
    candidates=[name for name,delta in deltas.items() if any(delta-base==100 for base in bases) and name not in conflicts]
    evidence={'team_score_deltas':deltas,'base_candidates':bases,'counter_conflicts':sorted(conflicts),
              'candidate_names':candidates,'reason':'unique_residual' if len(candidates)==1 else 'absent_or_ambiguous_residual'}
    return (candidates[0] if len(candidates)==1 else None),evidence


def main():
    diag=ROOT/'data/research/diagnostics';cache=diag/'objective-score-identity';cache.mkdir(parents=True,exist_ok=True)
    events=json.loads((diag/'objective-score-batch-cohort/summary.json').read_text())['events']
    signature=hashlib.sha256(Path(__file__).with_name('objective_score_identity.py').read_bytes()).hexdigest()
    raw_cache={};identity_cache={};reports=[]
    sources=json.loads((ROOT/'research/sources.json').read_text())['matches']
    targets={}
    with tempfile.TemporaryDirectory() as temp:
        dump=Path(temp)/'round.dump'
        for event in events:
            mid,n=event['match_id'],event['round'];rec,diagnostic=replay_file(mid,n)
            if rec.parent.name not in raw_cache:raw_cache[rec.parent.name]=candidate_raw(rec.parent)
            row=raw_cache[rec.parent.name]['rounds'][n-1];header=row.get('header',row)
            if (mid,n) not in identity_cache:
                dest=cache/f'{mid}-R{n:02d}.json';identities=json.loads(dest.read_text()) if dest.exists() else {}
                if identities.get('signature')!=signature:
                    cached_dump=diag/f'objective-encoding/{mid}-R{n:02d}.dump'
                    if cached_dump.exists():data=cached_dump.read_bytes()
                    else:
                        subprocess.run([str(PARSER),'--dump','-o',str(dump),str(rec)],check=True,capture_output=True)
                        data=dump.read_bytes()
                    identities={'signature':signature,**score_identity_candidates(data,header['players'])}
                    dest.write_text(json.dumps(identities))
                identity_cache[(mid,n)]=identities
            actual,evidence=predict_actor(event,identity_cache[(mid,n)],header)
            label=next(o['description'] for o in diagnostic['public_objectives'] if o['type']==event['kind'])
            expected=label.split(' plants ')[0].split(' disables ')[0].strip().casefold()
            # Existing source identity mapping and public roster IDs grade the
            # prediction; they cannot influence predict_actor above.
            if mid not in targets:targets[mid]=json.loads((ROOT/f'data/research/targets/siegegg-match-{mid}-api.json').read_text())
            source=next(s for s in sources if s.get('siegegg_match_id')==mid)
            expected_ids={p['id'] for p in targets[mid]['players'] if expected in
                          {str(p.get('ign','')).casefold(),str(p.get('stylized_name','')).casefold()}}
            actual_id=source.get('players',{}).get(actual)
            if actual is None:verdict='unresolved'
            elif len(expected_ids)==1 and actual_id is not None:
                verdict='correct' if actual_id in expected_ids else 'incorrect'
            else:verdict='identity_review'
            reports.append({'match_id':mid,'round':n,'kind':event['kind'],'candidate':actual,
                            'public_actor':expected,'verdict':verdict,'evidence':evidence})
            print(mid,n,event['kind'],verdict,flush=True)
    summary={kind:dict(Counter(r['verdict'] for r in reports if r['kind']==kind)) for kind in ['plant','disable']}
    (cache/'validation.json').write_text(json.dumps({'summary':summary,'events':reports},indent=2))
    print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
