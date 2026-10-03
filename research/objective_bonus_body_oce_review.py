"""Identity-first, one-shot primary review for the fixed pooled OCE cohort.

Run --identities only after the full prediction seal. It projects names/IDs,
never objective counts, and seals exact bindings before --evaluate. An
unmapped player blocks the complete map; no remaining-player inference.
"""
import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime,timezone
import json
import re

from objective_bonus_body_oce_cohort import DATA, FREEZE, RESERVATION, verify
from objective_bonus_body_asia_identity_review import identity
from objective_bonus_body_fresh_review import primary_constraints,evaluate_gates
from v3_final_pipeline import cache_url
from v3_final_reserve import ROOT,sha,source_sha

ADDENDUM=ROOT/'research/objective-bonus-body-oce-review-freeze.json'
SEAL=DATA/'prelabel-inventory-seal.json'
IDENTITIES=DATA/'independent-identities.json'
RESULT=DATA/'one-shot-primary-result.json'


def verify_prelabel():
    frozen,reservation=verify(); amendment=json.loads(ADDENDUM.read_text(encoding='utf-8'))
    if amendment['candidate_freeze_sha256']!=source_sha(FREEZE):raise ValueError('Actor freeze changed')
    for name,digest in amendment['source_hashes'].items():
        if source_sha(ROOT/name)!=digest:raise ValueError('Review implementation changed')
    seal=json.loads(SEAL.read_text(encoding='utf-8'))
    if seal['freeze_sha256']!=source_sha(FREEZE) or len(seal['entries'])!=reservation['selected_maps']:
        raise ValueError('Full fixed sample must be sealed before identities/labels')
    for entry in seal['entries']:
        if sha(ROOT/entry['path'])!=entry['sha256']:raise ValueError('Sealed cohort outcome changed')
    return frozen,reservation,seal


def target(source):
    page=DATA/str(source['official_match_id'])/'official-target.html'
    cache_url(source['official_page'],page)
    match=re.search(r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>',page.read_text(encoding='utf-8'),re.S)
    return json.loads(match.group(1))['props']['pageProps']['pageData']['match'],page


def bindings(players,people,histories):
    rows=[]
    if len(players)!=10 or len({p['profile_id'] for p in players})!=10:
        raise ValueError('Full distinct stable replay roster required')
    for p in players:
        exact=[person for person in people if person['name'].casefold()==p['username'].split('.')[0].casefold()]
        found=dict(status='verified',official_identity=exact[0],confidence='frozen_exact_replay_basename') if len(exact)==1 else identity(p,people,histories.get(p['profile_id']))
        rows.append(dict(username=p['username'],profile_id=p['profile_id'],team=p['team'],**found))
    bound=[p for p in rows if p['status']=='verified']
    if len({p['official_identity']['id'] for p in bound})!=len(bound):raise ValueError('Independent player IDs collide')
    groups={i:{p['official_identity']['team_id'] for p in bound if p['team']==i} for i in (0,1)}
    if any(len(x)>1 for x in groups.values()) or (all(groups.values()) and groups[0]==groups[1]):raise ValueError('Independent team binding conflicts')
    return dict(status='full_unique_primary_identity' if len(bound)==10 else 'identity_unresolved_whole_map',players=rows)


def identities():
    _,reservation,seal=verify_prelabel()
    if IDENTITIES.exists() or RESULT.exists():raise ValueError('Independent identities already sealed; never revise after results')
    sources={s['official_match_id']:s for s in reservation['matches']}
    histories={p.stem:json.loads(p.read_text(encoding='utf-8')) for p in (DATA/'independent-identity-history').glob('*.json')}
    hashes={p.relative_to(ROOT).as_posix():sha(p) for p in (DATA/'independent-identity-history').glob('*.json')}
    maps=[]
    for entry in seal['entries']:
        pred=json.loads((ROOT/entry['path']).read_text(encoding='utf-8'))
        if 'rounds' not in pred:continue
        mid=entry['official_match_id'];obj,page=target(sources[mid]);game=obj['games'][0]
        # Restrict the identity phase to official roster projection. No stats.
        people=[dict(id=p['id'],name=p['name'],team_id=t['id']) for t in game['teams'] for p in t['players'] or []]
        if len(people)!=10 or len({p['id'] for p in people})!=10:raise ValueError('Independent complete official roster missing')
        maps.append(dict(official_match_id=mid,**bindings(pred['rounds'][0]['players'],people,histories)))
        hashes[page.relative_to(ROOT).as_posix()]=sha(page)
    record=dict(status='independent_exact_identity_snapshot_before_objective_review',maps=maps,
                source_hashes=hashes,prelabel_seal_sha256=sha(SEAL),review_implementation_freeze_sha256=source_sha(ADDENDUM),
                objective_counts_used=False,ratings_read=False)
    DATA.mkdir(parents=True,exist_ok=True)
    with IDENTITIES.open('x',encoding='utf-8') as out:out.write(json.dumps(record,indent=2)+'\n')
    verify_prelabel();print('Identities sealed',Counter(m['status'] for m in maps),flush=True)


def evaluate():
    frozen,reservation,seal=verify_prelabel()
    if RESULT.exists():raise ValueError('Fixed cohort permanently consumed; never repeat evaluation')
    identities=json.loads(IDENTITIES.read_text(encoding='utf-8'))
    if identities['prelabel_seal_sha256']!=sha(SEAL) or identities['review_implementation_freeze_sha256']!=source_sha(ADDENDUM):
        raise ValueError('Independent identity provenance differs')
    for name,digest in identities['source_hashes'].items():
        if sha(ROOT/name)!=digest:raise ValueError('Independent identity source changed')
    marker=DATA/'actor-targets-opened.json'
    if marker.exists():raise ValueError('Interrupted evaluation already consumed labels; investigate, never silently retry')
    with marker.open('x',encoding='utf-8') as out:out.write(json.dumps(dict(status='primary_objective_targets_consumed',identity_sha256=sha(IDENTITIES),
                prelabel_seal_sha256=sha(SEAL),created_at=datetime.now(timezone.utc).isoformat()),indent=2)+'\n')
    sources={s['official_match_id']:s for s in reservation['matches']}; bindings_byid={m['official_match_id']:m for m in identities['maps']}
    counts=Counter(selected_maps=len(seal['entries']));records=[]
    for entry in seal['entries']:
        pred=json.loads((ROOT/entry['path']).read_text(encoding='utf-8'));mid=entry['official_match_id']
        if 'rounds' not in pred:
            counts['quality_failed_maps']+=1;records.append(dict(official_match_id=mid,status=pred['status'],reason=pred['reason']));continue
        rows=pred['rounds']; counts.update(maps=1,rounds=len(rows),plants=sum(r['verified_plant'] for r in rows),
            original_resolved=sum(bool(r['original']['actor']) for r in rows),proposed_resolved=sum(bool(r['proposed']['actor']) for r in rows),
            bonus_recoveries=sum(bool(r['proposed']['actor']) and not r['original']['actor'] for r in rows),
            bonus_maps=int(any(bool(r['proposed']['actor']) and not r['original']['actor'] for r in rows)),
            no_plant_controls=sum(not r['verified_plant'] for r in rows),
            no_plant_false_positives=sum(not r['verified_plant'] and bool(r['proposed']['actor']) for r in rows),
            original_actor_changes=sum(bool(r['original']['actor']) and r['proposed']!=r['original'] for r in rows))
        bound=bindings_byid[mid]
        if bound['status']!='full_unique_primary_identity':
            review=dict(status='primary_identity_unresolved_whole_map',constraints=[],aggregate_conflicts=[],occurrence_conflicts=[],identity_issues=[p for p in bound['players'] if p['status']!='verified'])
        else:
            projected=deepcopy(pred);names={p['username']:p['official_identity']['name'] for p in bound['players']}
            for r in projected['rounds']:
                for p in r['players']:p['username']=names[p['username']]
                for k in ('original','proposed'):
                    if r[k]['actor']:r[k]['actor']=names[r[k]['actor']]
            obj,_=target(sources[mid]);review=primary_constraints(projected,obj,sources[mid])
        counts.update(primary_reviewed_maps=int(review['status']=='primary_complete_unique_identity'),
            primary_identity_blocked_maps=int(review['status']!='primary_complete_unique_identity'),
            independent_bonus_agreements=sum(c['bonus_recovery'] and c['verdict']=='agreement' for c in review['constraints']),
            independent_wrong_actors=sum(c['verdict']=='disagreement' for c in review['constraints']),
            aggregate_conflicts=len(review['aggregate_conflicts']),occurrence_conflicts=len(review['occurrence_conflicts']))
        records.append(dict(official_match_id=mid,map=pred['map'],review=review))
        print('Pooled primary review',mid,review['status'],len(review['constraints']),flush=True)
    gates=evaluate_gates(counts,frozen['acceptance']);verify_prelabel()
    result=dict(status='permanent_one_shot_pooled_actor_result_events_now_consumed',counts=dict(counts),gates=gates,records=records,
                freeze_sha256=source_sha(FREEZE),prelabel_seal_sha256=sha(SEAL),identity_sha256=sha(IDENTITIES),
                ratings_read=False,production_deployed=False)
    with RESULT.open('x',encoding='utf-8') as out:out.write(json.dumps(result,indent=2)+'\n')
    lines=['# OCE fixed two-event one-shot actor result','',f'Frozen pooled result: **{gates["status"]}**.','',
           f'Counts: `{dict(counts)}`. Failures: `{gates["failures"]}`. Insufficient gates: `{gates["insufficient"]}`.','',
           'All38 selected metadata sources remained fixed through collection, including quality failures. '
           'Predictions sealed before independently selected exact identity bindings, then primary objective review performed once. '
           'Missing full identities abstain; only sole-player team totals constrain individual round actors. Multi-player aggregate agreement '
           'is not individual ground truth. No Rating targets or models were used. Neither event is fresh for this hypothesis anymore.','',
           '| Match | Map | Primary review / quality failure |','| --- | --- | --- |']
    for r in records:lines.append(f'| {r["official_match_id"]} | {r.get("map","unavailable")} | {r.get("review",{}).get("status",r.get("reason"))} |')
    lines+=['','No automatic bonus-health port or acceptance relaxation. ASIA and both failed v3 historical results stay unchanged. '
            'Live siege_style_v2, SQLite, archives and public JSON unchanged. No push or publish.','']
    (ROOT/'research/output/objective-bonus-body-oce-one-shot.md').write_text('\n'.join(lines),encoding='utf-8')
    print('Permanent pooled result',dict(counts),gates,flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--identities',action='store_true');parser.add_argument('--evaluate',action='store_true');args=parser.parse_args()
    if args.identities:identities()
    elif args.evaluate:evaluate()
    else:verify_prelabel();print('Sealed cohort/implementation intact')
