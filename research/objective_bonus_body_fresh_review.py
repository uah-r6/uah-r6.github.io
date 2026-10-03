"""One-shot independent Ubisoft actor constraints after the full replay seal.

No Rating field or public round actor is projected here. Independent round
constraints and map-total consistency are separate; unbound identities abstain.
"""
from collections import Counter
from datetime import datetime, timezone
import json
import re

from objective_bonus_body_fresh_pipeline import DATA, SEAL, verify
from objective_bonus_body_reserve import FREEZE
from v3_final_pipeline import cache_url
from v3_final_reserve import ROOT, sha, source_sha

RESULT = DATA/'one-shot-primary-result.json'


def evaluate_gates(counts, acceptance):
    failures=[]; insufficient=[]
    names={'min_complete_rounds':'rounds','min_complete_maps':'maps',
        'min_verified_plants':'plants','min_no_plant_controls':'no_plant_controls',
        'min_bonus_recoveries':'bonus_recoveries','min_distinct_bonus_maps':'bonus_maps',
        'min_independently_constrained_bonus_actors':'independent_bonus_agreements',
        'max_known_independent_wrong_actors':'independent_wrong_actors',
        'max_no_plant_false_positives':'no_plant_false_positives',
        'max_original_actor_changes':'original_actor_changes',
        'max_independent_objective_occurrence_conflicts':'occurrence_conflicts',
        'max_independent_aggregate_conflicts':'aggregate_conflicts'}
    for gate,field in names.items():
        if gate.startswith('min_') and counts.get(field,0)<acceptance[gate]: insufficient.append(gate)
        if gate.startswith('max_') and counts.get(field,0)>acceptance[gate]: failures.append(gate)
    return dict(status='FAILED' if failures else 'INSUFFICIENT' if insufficient else 'PASSED',
                failures=failures,insufficient=insufficient,production_deployed=False)


def canonical_map(value):
    return re.sub('[^a-z0-9]','',value.casefold()).replace('kafedostoyevsky','kafe')


def primary_constraints(prediction, payload, source):
    if payload['id']!=source['official_match_id'] or len(payload['games'])!=1:
        raise ValueError('Independent official match identity differs')
    game=payload['games'][0]
    if canonical_map(game['map']['name'])!=canonical_map(prediction['map']):
        raise ValueError('Independent map metadata differs')
    if sorted(t['score'] for t in game['teams'])!=sorted(prediction['score']):
        raise ValueError('Independent score differs')
    people=[p|dict(team_id=t['id']) for t in game['teams'] for p in t['players'] or []]
    if len(people)!=10 or len({p['id'] for p in people})!=10 or sorted(t['id'] for t in game['teams'])!=source['team_ids']:
        raise ValueError('Independent full official roster differs')
    identities={}; issues=[]; team_ids={}
    for p in prediction['rounds'][0]['players']:
        name=p['username']; spelling=name.split('.')[0].casefold()
        candidates=[person for person in people if person['name'].casefold()==spelling]
        if len(candidates)!=1:
            issues.append(dict(player=name,profile_id=p['profile_id'],reason='No unique exact primary spelling; no remaining-player/score/objective matching'))
        else:
            identities[name]=candidates[0]; team_ids.setdefault(p['team'],set()).add(candidates[0]['team_id'])
    if issues:
        return dict(status='primary_identity_unresolved_whole_map',identity_issues=issues,
            official_names=[dict(name=p['name'],id=p['id'],team_id=p['team_id']) for p in people],
            constraints=[],aggregate_conflicts=[],occurrence_conflicts=[])
    if len({p['id'] for p in identities.values()})!=10 or any(len(x)!=1 for x in team_ids.values()) or set(team_ids)!={0,1}:
        raise ValueError('Complete unique primary team binding failed')
    team_ids={k:next(iter(v)) for k,v in team_ids.items()}
    official_rounds={r['index']:r for r in game['rounds']}
    if sorted(official_rounds)!=list(range(1,len(prediction['rounds'])+1)) or len(official_rounds)!=len(game['rounds']):
        raise ValueError('Independent full round coverage differs')
    proposals=[]; counts=Counter(); occurrence_conflicts=[]
    for r in prediction['rounds']:
        official=official_rounds[r['round']]
        if team_ids[r['winner']]!=official['winnerId']:
            raise ValueError('Official round winner differs')
        for i,t in enumerate(r['teams']):
            if team_ids[i]!=(official['attackerId'] if t['role']=='Attack' else official['defenderId']):
                raise ValueError('Official round role differs')
        if not r['verified_plant']: continue
        actor=r['proposed']['actor']; person=identities[actor] if actor else None
        if person: counts[person['id']]+=1
        proposals.append(dict(round=r['round'],owner=actor,official_player_id=person['id'] if person else None,
            official_team_id=person['team_id'] if person else None,bonus_recovery=actor!=r['original']['actor'],
            reason=r['proposed']['reason']))
    constraints=[]
    for team in game['teams']:
        totals=[p for p in team['players'] if p['stats']['diffuserPlanted']['count']]
        rounds=[p for p in proposals if official_rounds[p['round']]['attackerId']==team['id']]
        expected=sum(p['stats']['diffuserPlanted']['count'] for p in team['players'])
        if len(rounds)!=expected:
            occurrence_conflicts.append(dict(team_id=team['id'],kind='plant',official=expected,replay=len(rounds)))
        if len(totals)==1 and len(rounds)==expected:
            for proposal in rounds:
                verdict='unresolved' if proposal['official_player_id'] is None else 'agreement' if proposal['official_player_id']==totals[0]['id'] else 'disagreement'
                constraints.append(proposal|dict(independent_actor=totals[0]['name'],independent_id=totals[0]['id'],
                    verdict=verdict,inference='one_official_player_accounts_for_all_team_plants_on_complete_map'))
    aggregate=[]; conflicts=[]; all_resolved=all(p['owner'] for p in proposals)
    for person in people:
        expected=person['stats']['diffuserPlanted']['count']
        if type(expected)is not int or expected<0: raise ValueError('Invalid independent plant count')
        row=dict(player=person['name'],id=person['id'],official=expected,replay=counts[person['id']])
        aggregate.append(row)
        if row['replay']>expected or all_resolved and row['replay']!=expected: conflicts.append(row)
    return dict(status='primary_complete_unique_identity',constraints=constraints,proposals=proposals,
        aggregate_totals=aggregate,aggregate_conflicts=conflicts,occurrence_conflicts=occurrence_conflicts,
        limitation='Single-player map totals logically constrain rounds; multi-player aggregate consistency is not round actor ground truth or visible completion.')


def main():
    frozen,reservation=verify()
    if RESULT.exists(): raise ValueError('Fresh actor reserve permanently consumed; never rerun one-shot evaluation')
    seal=json.loads(SEAL.read_text(encoding='utf-8'))
    if seal['freeze_sha256']!=source_sha(FREEZE) or len(seal['predictions'])!=12:
        raise ValueError('Complete12-map prelabel seal required')
    for name,digest in seal['predictions'].items():
        if sha(ROOT/name)!=digest: raise ValueError('Sealed actor prediction changed')
    # Consume marker precedes any independent actor/outcome request. A failed
    # implementation is recorded; never call the event untouched afterwards.
    marker=DATA/'actor-targets-opened.json'
    if not marker.exists():
        with marker.open('x',encoding='utf-8') as out:
            out.write(json.dumps(dict(created_at=datetime.now(timezone.utc).isoformat(),
                freeze_sha256=source_sha(FREEZE),seal_sha256=sha(SEAL),status='actor_targets_consumed_no_ratings_opened'),indent=2)+'\n')
    records=[]; counts=Counter()
    for source in (m for m in reservation['matches'] if m['selected']):
        mid=source['official_match_id'];path=DATA/str(mid)/'replay-predictions.json'
        prediction=json.loads(path.read_text(encoding='utf-8')); rounds=prediction['rounds']
        counts.update(maps=1,rounds=len(rounds),plants=sum(r['verified_plant'] for r in rounds),
            original_resolved=sum(bool(r['original']['actor']) for r in rounds),
            proposed_resolved=sum(bool(r['proposed']['actor']) for r in rounds),
            bonus_recoveries=sum(bool(r['proposed']['actor']) and not r['original']['actor'] for r in rounds),
            bonus_maps=int(any(bool(r['proposed']['actor']) and not r['original']['actor'] for r in rounds)),
            no_plant_controls=sum(not r['verified_plant'] for r in rounds),
            no_plant_false_positives=sum(not r['verified_plant'] and bool(r['proposed']['actor']) for r in rounds),
            original_actor_changes=sum(bool(r['original']['actor']) and r['proposed']!=r['original'] for r in rounds))
        page=DATA/str(mid)/'official-target.html';cache_url(source['official_page'],page)
        payload=json.loads(re.search(r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>',
            page.read_text(encoding='utf-8'),re.S).group(1))['props']['pageProps']['pageData']['match']
        review=primary_constraints(prediction,payload,source)
        record=dict(official_match_id=mid,map=prediction['map'],rounds=len(rounds),review=review,
            source=source['official_page'],source_sha256=sha(page),prediction_sha256=sha(path))
        records.append(record)
        counts.update(primary_reviewed_maps=int(review['status']=='primary_complete_unique_identity'),
            primary_identity_blocked_maps=int(review['status']!='primary_complete_unique_identity'),
            independent_bonus_agreements=sum(c['bonus_recovery'] and c['verdict']=='agreement' for c in review['constraints']),
            independent_wrong_actors=sum(c['verdict']=='disagreement' for c in review['constraints']),
            aggregate_conflicts=len(review['aggregate_conflicts']),
            occurrence_conflicts=len(review['occurrence_conflicts']))
        print('Fresh primary review',mid,review['status'],'constraints',len(review['constraints']),flush=True)
    gates=evaluate_gates(counts,frozen['acceptance'])
    result=dict(status='permanent_fresh_actor_result_event_now_consumed',created_at=datetime.now(timezone.utc).isoformat(),
        counts=dict(counts),gates=gates,records=records,freeze_sha256=source_sha(FREEZE),seal_sha256=sha(SEAL),
        original_public_comparison='Not opened in this primary-only evaluation; any later comparison must be separate.',
        ratings_read=False,production_deployed=False,protected_hashes=frozen['protected_hashes'])
    verify()
    with RESULT.open('x',encoding='utf-8') as out: out.write(json.dumps(result,indent=2)+'\n')
    lines=['# Fresh ASIA bonus-health actor validation','',f'Prospective gates: **{gates["status"]}**.',
        f'Counts: `{dict(counts)}`.',f'Failures: `{gates["failures"]}`. Insufficient: `{gates["insufficient"]}`.',
        '', 'All12 replay proposals were sealed before player objective totals. Official single-player constraints and aggregate consistency are separate. '
        'Identity-blocked maps do not receive guessed labels. The entire event is now consumed for this actor hypothesis; no Rating target was used. '
        'No runtime/SQLite/archive/public change, model fit, push, publish or automatic promotion.', '',
        '| Official match | Map | Rounds | Primary review |', '| --- | --- | ---: | --- |']
    for r in records:lines.append(f"| {r['official_match_id']} | {r['map']} | {r['rounds']} | {r['review']['status']} |")
    lines+=['','Frozen minimum3bonus recoveries on2maps and2independently constrained bonus actors cannot be waived after seeing this result. '
        'A pass still requires later review before any production port; frozen v3 results/dependencies remain immutable.', '']
    (ROOT/'research/output/objective-bonus-body-fresh-asia.md').write_text('\n'.join(lines),encoding='utf-8')
    print('Permanent fresh actor result',dict(counts),gates,flush=True)


if __name__=='__main__': main()
