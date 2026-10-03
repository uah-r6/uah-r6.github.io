"""Separate consumed identity review; never reruns the prospective evaluation.

Identity sealing projects only official roster names/IDs and exact-profile
username histories. Full ten-player bindings remain mandatory for primary
review. A supported individual with an otherwise blocked map is described
separately and never counted toward the original frozen acceptance gates.
"""
import argparse
from collections import Counter
from copy import deepcopy
import json
import re
from pathlib import Path

from objective_bonus_body_fresh_collection import INVENTORY_SEAL, verify_extension
from objective_bonus_body_fresh_pipeline import DATA
from objective_bonus_body_fresh_review import RESULT, primary_constraints
from v3_final_reserve import ROOT, sha

PERMANENT = '95f866760fa754407e83cf3d4e2be88a5f7a4d12cdc376fb512ed3c9875fff61'
PRELABEL = '8b4a40e5c642cced229e3351e2d91126e2110b0909a10e2d5a5f33f0193e4d72'
IDENTITIES = DATA/'consumed-verified-identities.json'
IDENTITY_SEAL = ROOT/'research/objective-bonus-body-asia-identity-seal.json'
SUFFIXES = {'f5','orc','elevate','wbg','dw','1z','gl','hlt','varianx','_','-','vitality','7th',
            'daystar','sharper','sh','fyr','fury','sf','scarz','wgb'}


def verify_preserved():
    frozen, reservation = verify_extension()
    if sha(RESULT) != PERMANENT or sha(INVENTORY_SEAL) != PRELABEL:
        raise ValueError('Permanent ASIA result or prelabel seal changed')
    seal = json.loads(INVENTORY_SEAL.read_text(encoding='utf-8'))
    for entry in seal['entries']:
        if sha(ROOT/entry['path']) != entry['sha256']:
            raise ValueError('Sealed replay prediction/quality record changed')
    return frozen, reservation, seal


def payload(mid):
    page = DATA/str(mid)/'official-target.html'
    text = page.read_text(encoding='utf-8')
    match = re.search(r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>', text, re.S)
    return json.loads(match.group(1))['props']['pageProps']['pageData']['match']


def spellings(name):
    """Exact name or a documented team suffix; never strip digits/fuzzy-match."""
    result = {name.casefold()}
    if name.endswith('.'):
        result.add(name.rstrip('.').casefold())
    if '.' in name:
        base, suffix = name.rsplit('.', 1)
        if suffix.casefold() in SUFFIXES:
            result.add(base.casefold())
    return result


def identity(player, people, history=None):
    names = [player['username']]
    source = 'exact_replay_spelling'
    if history:
        uid = player['profile_id']
        if history.get('profile_id') != uid or history.get('source_url','').rsplit('/',1)[-1] != uid:
            raise ValueError('History evidence must identify the exact replay UUID')
        if history.get('status') in {'retrieved','history_retrieved'}:
            names += history['history_names']
    matches = [(p, n) for p in people for n in names if p['name'].casefold() in spellings(n)]
    candidates = {p['id']: p for p, _ in matches}
    if len(candidates) != 1:
        return dict(status='unresolved', official_identity=None,
                    reason='No unique exact independently recorded name; no fuzzy/digit/remaining-player inference')
    person = next(iter(candidates.values()))
    exact = next(n for p,n in matches if p['id']==person['id'])
    if exact != player['username']:
        source = 'exact_profile_uuid_username_history'
    return dict(status='verified', official_identity=person, evidence_name=exact,
                confidence=source, source_url=history['source_url'] if source.endswith('history') else None)


def bind(players, people, histories):
    if (len(players)!=10 or len({p['profile_id'] for p in players})!=10 or
            any(not p['profile_id'] or p['profile_id']=='00000000-0000-0000-0000-000000000000' for p in players)
            or sorted(Counter(p['team'] for p in players).values()) != [5,5]):
        raise ValueError('Full unique ten-player replay identities required')
    rows = [dict(username=p['username'], profile_id=p['profile_id'], team=p['team'],
                 **identity(p,people,histories.get(p['profile_id']))) for p in players]
    verified = [r for r in rows if r['status']=='verified']
    if len({r['official_identity']['id'] for r in verified}) != len(verified):
        raise ValueError('Independent identities collide')
    teams = {i:{r['official_identity']['team_id'] for r in verified if r['team']==i} for i in (0,1)}
    if any(len(t)>1 for t in teams.values()) or (all(teams.values()) and teams[0]==teams[1]):
        raise ValueError('Independent team identity conflicts')
    return dict(status='full_unique_independent_identity' if len(verified)==10 else 'identity_blocked_whole_map',
                players=rows)


def seal_identities():
    _, reservation, seal = verify_preserved()
    if IDENTITY_SEAL.exists():
        raise ValueError('Identity review already sealed; preserve original evidence')
    histories = {p.stem:json.loads(p.read_text(encoding='utf-8'))
                 for p in (DATA/'consumed-identity-history').glob('*.json')}
    maps=[]; gaps={}; source_hashes={}
    old=json.loads(RESULT.read_text(encoding='utf-8'))
    gap_uids={i['profile_id'] for r in old['records'] for i in r.get('review',{}).get('identity_issues',[])}
    for entry in seal['entries']:
        if entry['status']!='complete_replay_prediction': continue
        mid=entry['official_match_id']; prediction=json.loads((ROOT/entry['path']).read_text(encoding='utf-8'))
        # Explicit identity-only projection: no stats, Rating, objectives or actors.
        people=[dict(id=p['id'],name=p['name'],team_id=t['id']) for t in payload(mid)['games'][0]['teams'] for p in t['players']]
        review=bind(prediction['rounds'][0]['players'],people,histories)
        source_hashes[str((DATA/str(mid)/'official-target.html').relative_to(ROOT)).replace('\\','/')]=sha(DATA/str(mid)/'official-target.html')
        for row in review['players']:
            if row['profile_id'] in gap_uids:
                h=histories.get(row['profile_id'],{})
                previous=gaps.setdefault(row['profile_id'],dict(profile_id=row['profile_id'], replay_usernames=[],maps=[],
                    history_names=h.get('history_names',[]),history_status=h.get('status','unavailable'),
                    history_url=h.get('source_url'),status=row['status'],official_identity=row['official_identity'],
                    evidence_name=row.get('evidence_name'),confidence=row.get('confidence'),reason=row.get('reason')))
                if row['username'] not in previous['replay_usernames']: previous['replay_usernames'].append(row['username'])
                previous['maps'].append(mid)
        maps.append(dict(official_match_id=mid, **review))
    for p in (DATA/'consumed-identity-history').glob('*.json'):
        source_hashes[p.relative_to(ROOT).as_posix()]=sha(p)
    report=dict(tier='separate_consumed_identity_review',original_prospective_status='INSUFFICIENT',
                original_result_sha256=PERMANENT,inventory_sha256=PRELABEL,maps=maps,gaps=list(gaps.values()),
                source_hashes=source_hashes,objective_values_used_for_mapping=False,ratings_used=False)
    if IDENTITIES.exists():
        # An interrupted pre-seal attempt is not authoritative. Preserve its
        # evidence separately; never replace any artifact after its seal exists.
        old_report=json.loads(IDENTITIES.read_text(encoding='utf-8'))
        if old_report != report:
            backup=IDENTITIES.with_name('consumed-verified-identities-preseal-interrupted.json')
            if backup.exists(): raise ValueError('Unexpected second interrupted identity attempt')
            backup.write_bytes(IDENTITIES.read_bytes())
    IDENTITIES.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    manifest=dict(status='consumed_identity_evidence_sealed_before_separate_actor_review',
                  artifact=IDENTITIES.relative_to(ROOT).as_posix(),artifact_sha256=sha(IDENTITIES),
                  original_result_sha256=PERMANENT,original_result_status='INSUFFICIENT',
                  counts=dict(gaps=len(gaps),verified=sum(g['status']=='verified' for g in gaps.values()),
                              full_maps=sum(m['status']=='full_unique_independent_identity' for m in maps)),
                  source_hashes=source_hashes,implementation_sha256=sha(Path(__file__)),ratings_read=False)
    IDENTITY_SEAL.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    lines=['# ASIA consumed independent identity review','',
           'Identity selection used exact replay UUID histories and official roster names only. Hidden aliases are not evidence. '
           'Missing names, digits, I/l substitutions and remaining-player matching are never inferred. '
           'The permanent prospective result remains **INSUFFICIENT**.','',
           f'Counts: `{manifest["counts"]}`. Full ten-player primary bindings remain mandatory.','',
           '| Replay handle | UUID | Official identity | Exact evidence | Status |',
           '| --- | --- | --- | --- | --- |']
    for g in gaps.values():
        person=g['official_identity']; evidence=f'[{g["evidence_name"] or g["history_status"]}]({g["history_url"]})' if g['history_url'] else 'unavailable'
        lines.append(f'| {", ".join(g["replay_usernames"])} | {g["profile_id"]} | {person["name"] if person else "unresolved"} | {evidence} | {g["status"]} |')
    lines += ['', 'Unavailable exact profiles were retried with stats.cc/www and recorded historical handles; '
              'direct HTTP was Cloudflare-blocked. Secondary name references do not replace missing UUID histories here. '
              'No official objective count or candidate correctness selected an alias. All sealed replay predictions remain unchanged.','']
    (ROOT/'research/output/objective-bonus-body-asia-identities.md').write_text('\n'.join(lines),encoding='utf-8')
    verify_preserved(); print(manifest['counts'])


def review_actors():
    _,reservation,_=verify_preserved()
    manifest=json.loads(IDENTITY_SEAL.read_text(encoding='utf-8'))
    if sha(IDENTITIES)!=manifest['artifact_sha256'] or sha(Path(__file__))!=manifest['implementation_sha256']:
        raise ValueError('Sealed identity review changed')
    for name,digest in manifest['source_hashes'].items():
        if sha(ROOT/name)!=digest: raise ValueError('Independent identity source changed')
    identities=json.loads(IDENTITIES.read_text(encoding='utf-8'))
    sources={s['official_match_id']:s for s in reservation['matches'] if s['selected']}
    maps=[]; counts=Counter(plants=19)
    for binding in identities['maps']:
        mid=binding['official_match_id']; pred=json.loads((DATA/str(mid)/'replay-predictions.json').read_text(encoding='utf-8'))
        target=payload(mid); byname={p['username']:p for p in binding['players']}
        official=target['games'][0]; support=[]
        # Individual evidence is descriptive only. No mapping of ambiguous teammates,
        # no full-map pass, aggregate gate or prospective acceptance credit.
        for r in pred['rounds']:
            if not r['verified_plant']: continue
            owner=r['proposed']['actor']; bound=byname.get(owner,{})
            evidence=dict(round=r['round'],actor=owner,bonus_recovery=bool(owner and not r['original']['actor']),
                          status='unreviewed_identity_or_multi_player_ground_truth')
            if bound.get('status')=='verified':
                person=bound['official_identity']; team=next(t for t in official['teams'] if t['id']==person['team_id'])
                planted=[p for p in team['players'] if p['stats']['diffuserPlanted']['count']]
                roundtarget=next(o for o in official['rounds'] if o['index']==r['round'])
                replayteam=next(p['team'] for p in r['players'] if p['username']==owner)
                if r['teams'][replayteam]['role']!='Attack': raise ValueError('Proposed plant actor on wrong side')
                teamrows=[rr for rr in pred['rounds'] if rr['verified_plant'] and rr['teams'][replayteam]['role']=='Attack']
                expected=sum(p['stats']['diffuserPlanted']['count'] for p in team['players'])
                if len(planted)==1 and len(teamrows)==expected and roundtarget['attackerId']==person['team_id']:
                    evidence.update(status='individual_primary_support' if planted[0]['id']==person['id'] else 'individual_primary_disagreement',
                        official_actor=planted[0]['name'],official_actor_id=planted[0]['id'],identity_evidence=bound.get('confidence'),
                        limitation='Full-map review remains blocked if any identity missing; individual support does not satisfy historical/future acceptance gates.')
            support.append(evidence)
        full=None
        if binding['status']=='full_unique_independent_identity':
            projected=deepcopy(pred)
            for r in projected['rounds']:
                for p in r['players']: p['username']=byname[p['username']]['official_identity']['name']
                for k in ('original','proposed'):
                    if r[k]['actor']: r[k]['actor']=byname[r[k]['actor']]['official_identity']['name']
            full=primary_constraints(projected,target,sources[mid])
            counts.update(full_maps=1,independently_reviewable=len(full['constraints']),
                          agreements=sum(c['verdict']=='agreement' for c in full['constraints']),
                          disagreements=sum(c['verdict']=='disagreement' for c in full['constraints']))
        counts.update(individual_support=sum(s['status']=='individual_primary_support' for s in support),
                      individual_disagreement=sum(s['status']=='individual_primary_disagreement' for s in support))
        maps.append(dict(official_match_id=mid,map=pred['map'],identity_status=binding['status'],full_primary_review=full,individual_evidence=support))
    counts['unresolved_full_map_ground_truth']=19-counts['independently_reviewable']
    result=dict(tier='separate_consumed_review_not_regrading',original_prospective_status='INSUFFICIENT',counts=dict(counts),maps=maps,
                identity_seal_sha256=sha(IDENTITY_SEAL),original_result_sha256=PERMANENT,production_deployed=False)
    destination=DATA/'consumed-identity-actor-review.json'
    if destination.exists(): raise ValueError('Separate reviewed actor result already recorded')
    destination.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    lines=['# ASIA separate consumed actor review','',f'Counts: `{dict(counts)}`. Original prospective result: **INSUFFICIENT**, unchanged.','',
           'Complete replay roster/UID and chronology safeguards are unchanged. Full primary review still requires all ten independently bound official identities. '
           'Individual sole-planter support is recorded separately; it is not a complete-map agreement or acceptance-gate credit. No Rating values were used.','',
           '| Match / map | Round | Proposed actor | Bonus | Separate evidence | Official sole planter |',
           '| --- | ---: | --- | --- | --- | --- |']
    for m in maps:
        for e in m['individual_evidence']:
            lines.append(f'| {m["official_match_id"]}/{m["map"]} | {e["round"]} | {e["actor"]} | {e["bonus_recovery"]} | {e["status"]} | {e.get("official_actor","unreviewed")} |')
    lines+=['','## Lone bonus recovery','',
            '[KlzzSS.. exact UUID history](https://stats.cc/siege/KlzzSS../62e12cb2-8e51-4cb6-80d6-fe66b566ad26) includes Klz.F5 and Klz.ORC. '
            '[Ubisoft 8186](https://www.ubisoft.com/en-us/esports/rainbow-six/siege/match/8186) records Klz (2123) as the sole LEFTOVERS planter (one), others zero. '
            'The sealed R10 completion owner is KlzzSS..; original conservative resolver abstains. This supports one individual observation, '
            'but Jittery remains without exact UUID history, so no complete-map reviewed agreement is awarded. '
            'No VOD completion review was performed for this case. Three bonus cases on two maps and two independently constrained actors remain required.', '',
            'Timer start64161184/end64203709, completion64203718, stable UID14027449448452907923. Direct body states1/0/1; '
            'initial111/110HP, ceiling130, later130/110HP, positive fractions match excess/base at recorded endpoints. '
            'These are replay diagnostics, not independent visual HP evidence. Candidate, gates, old targets and historical results unchanged.','']
    (ROOT/'research/output/objective-bonus-body-asia-reviewed-actors.md').write_text('\n'.join(lines),encoding='utf-8')
    verify_preserved(); print(dict(counts))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--review',action='store_true');args=parser.parse_args()
    review_actors() if args.review else seal_identities()
