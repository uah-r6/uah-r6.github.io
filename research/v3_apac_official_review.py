"""Independent consumed APAC objective/KD constraints; no frozen corrections."""
import argparse
from collections import Counter
from html import unescape
import json
import re
import subprocess
from pathlib import Path

from v3_consumed_apac_credit_probe import sealed_apac_cache
from v3_consumed_cohort_integrity import sealed_sal_cache, PERMANENT_RESULTS
from v3_final_pipeline import DATA
from v3_final_reserve import ROOT, source_sha, sha
from r6stats.parser.models import Match
from objective_official_disable_review import objective_projection, constrained_disable_labels
from uah_guarded_actor_readonly import snapshot


def read_primary(mid, source):
    page = ROOT/f'data/research/diagnostics/v3-event-metadata/match-{mid}.html'
    if not page.exists():
        partial = page.with_suffix('.html.partial')
        subprocess.run(['curl.exe','--fail','--location','--retry','2','--output',str(partial),
                        source['official_page']],check=True,capture_output=True)
        partial.replace(page)
    payload = json.loads(re.search(r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>',
                         page.read_text(encoding='utf-8'),re.S).group(1))['props']['pageProps']['pageData']['match']
    if payload['id'] != mid or len(payload['games']) != 1:
        raise ValueError('Independent official match identity differs')
    return payload, page


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--limit',type=int,default=1);args=parser.parse_args()
    protected=snapshot();sealed_sal_cache();_,cached=sealed_apac_cache()
    aliases=json.loads((ROOT/'research/v3-final-verified-aliases.json').read_text())['aliases']
    # Keep the first strict three-map review/source in consumed-primary-review.
    # This revision records identity-blocked maps explicitly, without relaxing
    # the full ten-player/team guard or changing any frozen identity registry.
    destination=DATA/'consumed-primary-review-v2';destination.mkdir(parents=True,exist_ok=True)
    records=[]
    for mid,inputs in list(cached.items())[:args.limit]:
        prediction,quality,source=inputs['prediction'],inputs['quality'],inputs['source']
        payload,page=read_primary(mid,source);game=payload['games'][0]
        match=Match.from_dict(prediction['normalized'])
        if game['map']['name'].casefold().replace(' ','') != match.map_name.casefold().replace(' ',''):
            raise ValueError('Independent official map differs')
        people=[p|{'team_id':t['id']} for t in game['teams'] for p in t['players'] or []]
        if len(people)!=10 or len({p['id'] for p in people})!=10 or sorted(t['id'] for t in game['teams'])!=source['team_ids']:
            raise ValueError('Independent official roster differs')
        api=json.loads((DATA/str(mid)/'siegegg-api-sealed.json').read_text())
        identities={};team_ids={};kd_rows=[];identity_issues=[]
        for player in prediction['players']:
            name=player['player'];alias=aliases.get(name,{})
            if alias and alias['replay_profile_id']!=player['profile_id']:
                raise ValueError('Explicit alias profile differs')
            decision=next(q for q in quality['decisions'] if q['player']==name)
            public=next(p for p in api['players'] if p['id']==decision['player_id'])
            names={name.split('.')[0].casefold(),alias.get('name','').casefold(),
                   public['ign'].casefold(),public['stylized_name'].casefold()}
            names.update(n.split('.')[0].casefold() for n in alias.get('observed_names',[]))
            candidates=[p for p in people if p['name'].casefold() in names]
            if len(candidates)!=1:
                identity_issues.append(dict(player=name,profile_id=player['profile_id'],
                                            identity_spellings=sorted(names),
                                            candidates=[dict(name=p['name'],id=p['id']) for p in candidates],
                                            reason='No unique explicit primary identity; no spelling guess'))
                continue
            official=candidates[0];identities[name]=official
            team_ids.setdefault(player['team'],set()).add(official['team_id'])
            kd=re.fullmatch(r'(\d+)-(\d+)(?:\s+\([+-]?\d+\))?',decision['public_kd'])
            if not kd:raise ValueError('Unrecognized frozen public K/D')
            public_kd=list(map(int,kd.groups()))
            official_kd=[official['stats'][k]['count'] for k in ('kills','deaths')]
            replay_kd=[player['derived'][k] for k in ('kills','deaths')]
            kd_rows.append(dict(player=name,official_player_id=official['id'],official_name=official['name'],
                                official_team_id=official['team_id'],identity_spellings=sorted(names),
                                official_kd=official_kd,public_kd=public_kd,replay_kd=replay_kd,
                                frozen_eligible=decision['eligible']))
        if identity_issues:
            record=dict(official_match_id=mid,map=match.map_name,rounds=len(match.rounds),
                        status='primary_identity_unresolved_whole_map_review_unavailable',
                        identity_issues=identity_issues,totals={'primary_identity_unresolved_maps':1},
                        original_public_comparison=[],independent_constrained_rounds=[],
                        aggregate_conflicts=[],primary_kd_rows=[],
                        source=source['official_page'],source_sha256=sha(page),
                        prediction_sha256=sha(DATA/str(mid)/'replay-predictions.json'),
                        helper_sha256=source_sha(Path(__file__)),permanent_results=PERMANENT_RESULTS,
                        official_names=[dict(name=p['name'],id=p['id'],team_id=p['team_id']) for p in people],
                        limitation='Missing independent primary identity prevents full actor/KD review; '
                                   'no remaining-player, numeric-suffix, K/D or objective-total mapping.')
            path=destination/f'{mid}.json'
            if path.exists():
                if json.loads(path.read_text())!=record:raise ValueError('Preserved primary identity issue differs')
            else:path.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
            records.append(record)
            print('Consumed APAC primary identity unresolved',mid,identity_issues,flush=True)
            continue
        if len({p['id'] for p in identities.values()})!=10 or any(len(v)!=1 for v in team_ids.values()):
            raise ValueError('Complete unique official player/team binding required')
        team_ids={k:next(iter(v)) for k,v in team_ids.items()}
        official_rounds={r['index']:r for r in game['rounds']}
        if sorted(official_rounds)!=list(range(1,len(match.rounds)+1)) or len(game['rounds'])!=len(match.rounds):
            raise ValueError('Official round coverage differs')
        proposals=[];public_comparison=[];occurrence_differences=[];totals=Counter();credits=Counter()
        ids={d['player']:d['player_id'] for d in quality['decisions']}
        for round_ in match.rounds:
            official=official_rounds[round_.number]
            if team_ids[round_.winner]!=official['winnerId']:
                raise ValueError('Official round winner differs')
            if any(team_ids[p.team]!=(official['attackerId'] if p.side=='Attack' else official['defenderId']) for p in round_.players):
                raise ValueError('Official round role differs')
            public_round=api['games'][0]['rounds'][round_.number-1]
            for kind in ('plant','disable'):
                occurrences=[o for o in round_.objective_occurrences if o.kind==kind]
                events=[e for e in public_round['events'] if e['type']==kind]
                if len(events)!=len(occurrences):
                    occurrence_differences.append(dict(round=round_.number,kind=kind,public=len(events),replay=len(occurrences)))
                for occurrence in occurrences:
                    totals[kind]+=1
                    actor=next((p for p in round_.players if p.key==occurrence.actor),None)
                    trusted=actor and occurrence.actor_source==occurrence.actor_reason=='completing_timer_owner_v1'
                    person=identities[actor.username] if trusted else None
                    if person:
                        totals['resolved_'+kind]+=1;credits[person['id'],kind]+=1
                    proposals.append(dict(round=round_.number,kind=kind,replay_owner=actor.username if trusted else None,
                                          official_player_id=person['id'] if person else None,
                                          official_team_id=person['team_id'] if person else None,
                                          actor_uid=occurrence.actor_uid,reason=occurrence.actor_reason))
                    if len(events)!=1:continue
                    text=unescape(re.sub('<[^>]+>',' ',events[0]['html']))
                    parsed=re.search(r'([A-Za-z0-9_.-]+) (?:plants|disables) defuser',text)
                    if not parsed:raise ValueError('Cannot project original actor text')
                    name=parsed.group(1)
                    candidates=[p['id'] for p in api['players'] if name.casefold() in {p['ign'].casefold(),p['stylized_name'].casefold()}]
                    actual=ids[actor.username] if trusted else None
                    verdict='unresolved' if actual is None else 'identity review' if len(candidates)!=1 else 'agreement' if actual==candidates[0] else 'disagreement'
                    public_comparison.append(dict(round=round_.number,kind=kind,replay_owner=actor.username if trusted else None,
                                                  original_public_actor=name,original_public_player_ids=candidates,
                                                  replay_public_player_id=actual,verdict=verdict))
        constrained=[]
        for team in constrained_disable_labels(objective_projection(game)):
            for label in team['constrained_round_labels']:
                p=next(p for p in proposals if p['round']==label['round'] and p['kind']=='disable')
                verdict='unresolved' if p['official_player_id'] is None else 'agreement' if p['official_player_id']==label['id'] else 'disagreement'
                constrained.append(dict(round=label['round'],kind='disable',official_actor=label['player'],proposal=p,verdict=verdict))
        for team in game['teams']:
            planters=[p for p in team['players'] if p['stats']['diffuserPlanted']['count']]
            rounds=[p['round'] for p in proposals if p['kind']=='plant' and official_rounds[p['round']]['attackerId']==team['id']]
            if len(rounds)!=sum(p['stats']['diffuserPlanted']['count'] for p in team['players']):
                raise ValueError('Official team plant total differs from replay occurrence')
            if len(planters)==1:
                for number in rounds:
                    p=next(p for p in proposals if p['round']==number and p['kind']=='plant')
                    verdict='unresolved' if p['official_player_id'] is None else 'agreement' if p['official_player_id']==planters[0]['id'] else 'disagreement'
                    constrained.append(dict(round=number,kind='plant',official_actor=planters[0]['name'],proposal=p,verdict=verdict))
        aggregate=[];conflicts=[]
        for person in people:
            for kind,field in [('plant','diffuserPlanted'),('disable','diffuserDisabled')]:
                expected=person['stats'][field]['count'];count=credits[person['id'],kind]
                if type(expected)is not int or expected<0:raise ValueError('Invalid official objective count')
                row=dict(player=person['name'],kind=kind,official=expected,replay=count);aggregate.append(row)
                if count>expected or prediction['objective_complete'] and count!=expected:conflicts.append(row)
        for kind in ('plant','disable'):
            if sum(p['official'] for p in aggregate if p['kind']==kind)!=totals[kind]:
                raise ValueError('Official objective total differs from replay occurrences')
        record=dict(official_match_id=mid,map=match.map_name,rounds=len(match.rounds),totals=dict(totals),
                    status='primary_complete_unique_identity',
                    original_public_comparison=public_comparison,occurrence_differences=occurrence_differences,
                    independent_constrained_rounds=constrained,aggregate_objectives=aggregate,aggregate_conflicts=conflicts,
                    primary_kd_rows=kd_rows,source=source['official_page'],source_sha256=sha(page),
                    prediction_sha256=sha(DATA/str(mid)/'replay-predictions.json'),
                    public_api_sha256=sha(DATA/str(mid)/'siegegg-api-sealed.json'),helper_sha256=source_sha(Path(__file__)),
                    permanent_results=PERMANENT_RESULTS,
                    limitation='Primary single-player totals constrain rounds as an explicit inference. Multiple-player totals are aggregate consistency, not visual actor proof. Original public labels remain a separate tier.')
        path=destination/f'{mid}.json'
        if path.exists():
            if json.loads(path.read_text())!=record:raise ValueError('Preserved consumed primary audit differs')
        else:path.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
        records.append(record)
        print('Consumed APAC primary actor/KD',mid,record['totals'],'conflicts',len(conflicts),
              'public comparison',dict(Counter((p['kind'],p['verdict']) for p in public_comparison)),flush=True)
    totals=Counter();original=Counter();independent=Counter();kd=Counter()
    for record in records:
        totals.update(record['totals']);totals.update(maps=1,rounds=record['rounds'])
        if record['status']=='primary_complete_unique_identity':
            totals.update(primary_reviewed_maps=1,primary_reviewed_rounds=record['rounds'])
        original.update((p['kind'],p['verdict']) for p in record['original_public_comparison'])
        independent.update((p['kind'],p['verdict']) for p in record['independent_constrained_rounds'])
        for row in record['primary_kd_rows']:
            kd['official_public_agreement']+=row['official_kd']==row['public_kd']
            kd['all_three_agree']+=row['official_kd']==row['public_kd']==row['replay_kd']
    lines=['# Independent consumed APAC actor and K/D review','',
           'No frozen model, actor rule, eligibility, predictions, target or final result is changed. '
           'Replay proposals were fixed before these primary and public actor fields were projected.', '',
           f'Totals: `{dict(totals)}`. Original lower-confidence actor comparison: `{dict(original)}`. '
           f'Separate independently constrained actor comparison: `{dict(independent)}`. K/D consistency: `{dict(kd)}`.', '',
           '| Official / map | Replay occurrence / actor resolution | Aggregate conflicts | Independent round constraints |',
           '| --- | --- | --- | --- |']
    for r in records:
        conflicts=r['aggregate_conflicts'] if r['status']=='primary_complete_unique_identity' else 'Unavailable: primary identity unresolved'
        lines.append(f"| [{r['official_match_id']}]({r['source']})/{r['map']} | {r['totals']} | {conflicts} | "+
                     '; '.join(f"R{p['round']:02d} {p['kind']}: {p['official_actor']} / {p['verdict']}" for p in r['independent_constrained_rounds'])+' |')
    lines+=['','## Explicit primary identity exclusions','']
    for r in records:
        if 'identity_issues' in r:
            lines.append(f"- {r['official_match_id']}: {r['identity_issues']}.")
    lines+=['','The earlier strict three-map review and exact source are preserved in the ignored '
            '`consumed-primary-review/initial-strict-audit` cache. This revision proceeds past identity-blocked '
            'maps by reporting them as unavailable; it retains the original complete unique ten-player guard. '
            'No primary actor/KD verdict is assigned on those maps and no frozen alias is changed.','']
    lines+=['','Original public disagreements/unresolved actors:', '']
    for r in records:
        for p in r['original_public_comparison']:
            if p['verdict']!='agreement':lines.append(f"- {r['official_match_id']}/R{p['round']:02d}: {p}.")
    lines+=['','Unique official team objective totals plus independently verified occurrence/side constrain an actor; '
            'these are explicit inferences, not direct round actor fields or visual verification. Multiple-player totals '
            'cannot assign individual rounds. Missing replay body/UID evidence remains unresolved even when an official '
            'total constrains a name. No actor is filled from a remaining external count.', '',
            'Independent official/public K/D agreement does not establish each round-level credited-kill pattern. '
            'The separate stable-UID counter audit investigates that limitation without changing original quality decisions. '
            'Official/public telemetry may share upstream data; broadcast evidence is separately identified.', '',
            'Both permanent failed v3 finals, live v2, all 86 protected hashes and both source freezes remain unchanged. '
            'No import, historical correction, public regeneration, push, publish or deployment.', '']
    (ROOT/'research/output/v3-consumed-apac-primary-review.md').write_text('\n'.join(lines),encoding='utf-8')
    sealed_sal_cache();sealed_apac_cache()
    if snapshot()!=protected:raise ValueError('Protected live files changed')
    print('Consumed APAC primary totals',dict(totals),dict(original),dict(independent),dict(kd),flush=True)


if __name__=='__main__':main()
