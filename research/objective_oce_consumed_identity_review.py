"""Additional exact account histories; separate consumed review only.

Current handles found in sealed UUID header inventories allow legitimate
profile-page retries. Original prospective identities/result are immutable.
No objective outcome, digit stripping, I/l/Unicode substitution or remaining
player inference chooses an identity.
"""
import argparse
from collections import Counter
from copy import deepcopy
import json
from pathlib import Path

from objective_bonus_body_oce_review import verify_prelabel,target,primary_constraints
from objective_bonus_body_oce_cohort import DATA
from v3_final_reserve import ROOT,sha,source_sha

IDENTITIES=DATA/'consumed-additional-identities.json'
SEAL=ROOT/'research/objective-bonus-body-oce-consumed-identity-seal.json'


def verify():
    frozen,reservation,inventory=verify_prelabel()
    checkpoint=json.loads((ROOT/'research/objective-bonus-body-oce-permanent-result-checkpoint.json').read_text(encoding='utf-8'))
    if sha(ROOT/checkpoint['result_path'])!=checkpoint['result_sha256']:raise ValueError('Original pooled result changed')
    original=json.loads((ROOT/'research/objective-bonus-body-oce-identity-seal.json').read_text(encoding='utf-8'))
    if sha(ROOT/original['artifact'])!=original['artifact_sha256']:raise ValueError('Original prospective identities changed')
    return frozen,reservation,inventory


def exact_history_identity(player,people,history):
    names=[player['username']]
    if history:
        uid=player['profile_id']
        if history.get('profile_id')!=uid or history.get('source_url','').rsplit('/',1)[-1]!=uid:
            raise ValueError('History must refer to exact account UUID')
        if history['status'] in ('retrieved','history_retrieved'):names+=history['history_names']
    matches=[(person,name) for person in people for name in names if person['name'].casefold()==name.split('.')[0].casefold()]
    identities={p['id']:p for p,_ in matches}
    if len(identities)!=1:return dict(status='unresolved',official_identity=None)
    person=next(iter(identities.values()));name=next(n for p,n in matches if p['id']==person['id'])
    return dict(status='verified',official_identity=person,evidence_name=name,
                confidence='exact_replay_basename' if name==player['username'] else 'exact_uuid_history_basename',
                history_url=history['source_url'] if history else None)


def seal_identities():
    _,reservation,inventory=verify()
    if SEAL.exists() or IDENTITIES.exists():raise ValueError('Additional identity evidence already sealed')
    sources={s['official_match_id']:s for s in reservation['matches']};histories={};hashes={}
    for directory in ('independent-identity-history','consumed-additional-identity-history'):
        for path in (DATA/directory).glob('*.json'):
            row=json.loads(path.read_text(encoding='utf-8'))
            if path.stem not in histories or row['status'] in ('retrieved','history_retrieved'):
                histories[path.stem]=row
            hashes[path.relative_to(ROOT).as_posix()]=sha(path)
    maps=[]
    for entry in inventory['entries']:
        pred=json.loads((ROOT/entry['path']).read_text(encoding='utf-8'))
        if 'rounds' not in pred:continue
        mid=entry['official_match_id'];obj,page=target(sources[mid])
        people=[dict(id=p['id'],name=p['name'],team_id=t['id']) for t in obj['games'][0]['teams'] for p in t['players'] or []]
        rows=[dict(username=p['username'],profile_id=p['profile_id'],team=p['team'],
                   **exact_history_identity(p,people,histories.get(p['profile_id']))) for p in pred['rounds'][0]['players']]
        selected=[p for p in rows if p['status']=='verified']
        if len({p['official_identity']['id'] for p in selected})!=len(selected):raise ValueError('Independent official identity collision')
        teams={i:{p['official_identity']['team_id'] for p in selected if p['team']==i} for i in (0,1)}
        if any(len(t)>1 for t in teams.values()) or (all(teams.values()) and teams[0]==teams[1]):raise ValueError('Independent team conflict')
        maps.append(dict(official_match_id=mid,status='full_unique_identity' if len(selected)==10 else 'unresolved_whole_map',players=rows))
        hashes[page.relative_to(ROOT).as_posix()]=sha(page)
    report=dict(tier='additional_consumed_identity_evidence_not_fresh',maps=maps,source_hashes=hashes,
                original_result_sha256=sha(DATA/'one-shot-primary-result.json'),objective_counts_used_for_mapping=False)
    IDENTITIES.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    checkpoint=dict(status='additional_identity_evidence_sealed_before_separate_consumed_constraint_report',
        artifact=IDENTITIES.relative_to(ROOT).as_posix(),artifact_sha256=sha(IDENTITIES),source_hashes=hashes,
        implementation_sha256=source_sha(Path(__file__)),original_result_sha256=report['original_result_sha256'],
        original_prospective_status='INSUFFICIENT',counts=dict(Counter(m['status'] for m in maps)))
    SEAL.write_text(json.dumps(checkpoint,indent=2)+'\n',encoding='utf-8')
    print(checkpoint['counts']);verify()


def review():
    _,reservation,inventory=verify();seal=json.loads(SEAL.read_text(encoding='utf-8'))
    if sha(IDENTITIES)!=seal['artifact_sha256'] or source_sha(Path(__file__))!=seal['implementation_sha256']:
        raise ValueError('Additional identity implementation/evidence changed')
    for name,digest in seal['source_hashes'].items():
        if sha(ROOT/name)!=digest:raise ValueError('Additional identity source changed')
    bymap={m['official_match_id']:m for m in json.loads(IDENTITIES.read_text(encoding='utf-8'))['maps']}
    sources={s['official_match_id']:s for s in reservation['matches']};counts=Counter();records=[]
    for entry in inventory['entries']:
        pred=json.loads((ROOT/entry['path']).read_text(encoding='utf-8'))
        if 'rounds' not in pred:continue
        mid=entry['official_match_id'];bound=bymap[mid]
        if bound['status']!='full_unique_identity':counts['identity_blocked_maps']+=1;continue
        names={p['username']:p['official_identity']['name'] for p in bound['players']};projected=deepcopy(pred)
        for r in projected['rounds']:
            for p in r['players']:p['username']=names[p['username']]
            for key in ('original','proposed'):
                if r[key]['actor']:r[key]['actor']=names[r[key]['actor']]
        obj,_=target(sources[mid]);constraints=primary_constraints(projected,obj,sources[mid])
        if constraints['status']!='primary_complete_unique_identity':raise ValueError('Additional complete identity projection did not bind')
        counts.update(reviewed_maps=1,reviewed_rounds=len(pred['rounds']),
            constrained_agreements=sum(c['verdict']=='agreement' for c in constraints['constraints']),
            constrained_disagreements=sum(c['verdict']=='disagreement' for c in constraints['constraints']),
            constrained_abstentions=sum(c['verdict']=='unresolved' for c in constraints['constraints']),
            aggregate_conflicts=len(constraints['aggregate_conflicts']),occurrence_conflicts=len(constraints['occurrence_conflicts']))
        records.append(dict(official_match_id=mid,map=pred['map'],review=constraints))
    result=dict(tier='additional_consumed_primary_constraints_not_prospective_regrading',counts=dict(counts),records=records,
                identity_seal_sha256=sha(SEAL),original_result_sha256=seal['original_result_sha256'],original_prospective_status='INSUFFICIENT')
    path=DATA/'consumed-additional-primary-review.json'
    if path.exists():raise ValueError('Additional consumed review already recorded')
    path.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    lines=['# OCE additional consumed primary review','',f'Counts: `{dict(counts)}`.','',
           'The original one-shot prospective result remains **INSUFFICIENT** (four reviewed maps /28 blocked), byte-for-byte unchanged. '
           'These additional histories were retrieved after that result using current usernames from the sealed UUID header inventories. '
           'No objective totals selected an identity. This tier is consumed review; it cannot retroactively improve prospective coverage or acceptance.','',
           '| Match / map | Independent agreement | Independent disagreement | Known actor, parser abstains |','| --- | ---: | ---: | ---: |']
    for r in records:
        c=r['review']['constraints'];lines.append(f'| {r["official_match_id"]}/{r["map"]} | {sum(x["verdict"]=="agreement" for x in c)} | {sum(x["verdict"]=="disagreement" for x in c)} | {sum(x["verdict"]=="unresolved" for x in c)} |')
    lines+=['','Exact UID history basenames use the same documented case-insensitive team-suffix convention as the original primary review. '
            'Digits, confusable I/l letters, accent differences and remaining players are never inferred. Unknown profiles still block full-map review. '
            'Only sole-player totals constrain individual rounds; multi-player totals are aggregate evidence. All original targets/actors/gates '
            'are preserved; no runtime change, Rating fit, SQLite/archive/public modification, push or publish.','']
    (ROOT/'research/output/objective-bonus-body-oce-consumed-primary-review.md').write_text('\n'.join(lines),encoding='utf-8')
    verify();print(dict(counts))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--review',action='store_true');args=parser.parse_args()
    review() if args.review else seal_identities()
