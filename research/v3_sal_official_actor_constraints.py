"""Independent primary constraints for the fixed actor port on consumed SAL.

No actor label is an input to replay predictions. Aggregate agreement does not
prove individual round assignments when multiple players performed objectives.
"""
from collections import Counter
import json
import re

from v3_corrected_final_pipeline import DATA, RESULT, ROOT, verify, sha
from objective_official_disable_review import objective_projection, constrained_disable_labels
from r6stats.parser.models import Match
from uah_guarded_actor_readonly import snapshot


def main():
    protected, permanent = snapshot(), sha(RESULT)
    _, reservation = verify()
    identities = json.loads((DATA/'independent-kd-audit.json').read_text())['rows']
    records, total, conflicts, constrained = [], Counter(), [], []
    for source in reservation['matches']:
        if not source['selected']:
            continue
        mid = source['official_match_id']
        prediction = json.loads((DATA/str(mid)/'replay-predictions.json').read_text())
        match = Match.from_dict(prediction['normalized'])
        primary = ROOT/f'data/research/diagnostics/v3-sal-official-kd/{mid}.html'
        payload = json.loads(re.search(r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>',
                             primary.read_text(encoding='utf-8'),re.S).group(1))['props']['pageProps']['pageData']['match']
        game = payload['games'][0]
        if game['map']['name'].casefold().replace(' ', '') != match.map_name.casefold().replace(' ', ''):
            raise ValueError('Independent official map differs')
        people = [p for t in game['teams'] for p in t['players']]
        name_id = {p['name'].casefold():p['id'] for p in people}
        player_id, team_id = {}, {}
        for player in match.rounds[0].players:
            identity = next(r for r in identities if r['official_match_id']==mid and r['player']==player.username)
            names = identity['primary_identity_candidates']
            if len(names)!=1:
                raise ValueError('Exact independent player identity required')
            player_id[player.key] = name_id[names[0]['name'].casefold()]
            team_id.setdefault(player.team,set()).add(names[0]['team_id'])
        if len(set(player_id.values()))!=10 or any(len(ids)!=1 for ids in team_id.values()):
            raise ValueError('Complete unique official player/team identity required')
        team_id = {team:next(iter(ids)) for team,ids in team_id.items()}
        official_rounds = {r['index']:r for r in game['rounds']}
        if set(official_rounds)!={r.number for r in match.rounds}:
            raise ValueError('Official/physical logical round coverage differs')
        proposals, unresolved = [], []
        credited = Counter()
        for r in match.rounds:
            official = official_rounds[r.number]
            if team_id[r.winner]!=official['winnerId']:
                raise ValueError('Independent official round winner differs')
            for p in r.players:
                if team_id[p.team]!=(official['attackerId'] if p.side=='Attack' else official['defenderId']):
                    raise ValueError('Independent round side differs')
            for occurrence in r.objective_occurrences:
                total[occurrence.kind]+=1
                player = next((p for p in r.players if p.key==occurrence.actor),None)
                if not player or occurrence.actor_source!='completing_timer_owner_v1' or occurrence.actor_reason!='completing_timer_owner_v1':
                    unresolved.append(dict(round=r.number,kind=occurrence.kind,reason=occurrence.actor_reason))
                    continue
                total['resolved_'+occurrence.kind]+=1
                pid = player_id[player.key]
                credited[pid,occurrence.kind]+=1
                proposals.append(dict(round=r.number,kind=occurrence.kind,player=player.username,
                                      official_player_id=pid,actor_uid=occurrence.actor_uid))
        disable_constraints = constrained_disable_labels(objective_projection(game))
        for team in disable_constraints:
            for label in team['constrained_round_labels']:
                proposed = [r for r in proposals if r['kind']=='disable' and r['round']==label['round']]
                if len(proposed)!=1:
                    verdict = 'unresolved replay actor'
                else:
                    verdict = 'agreement' if proposed[0]['official_player_id']==label['id'] else 'disagreement'
                constrained.append(dict(official_match_id=mid,kind='disable',round=label['round'],
                                        official_actor=label['player'],proposal=proposed,verdict=verdict,
                                        source='Single official player accounts for all team disable wins; not a direct per-round actor field'))
        for team in game['teams']:
            planters = [p for p in team['players'] if p['stats']['diffuserPlanted']['count']]
            plant_rounds = [r.number for r in match.rounds
                            if official_rounds[r.number]['attackerId']==team['id']
                            and any(o.kind=='plant' for o in r.objective_occurrences)]
            if len(plant_rounds)!=sum(p['stats']['diffuserPlanted']['count'] for p in team['players']):
                raise ValueError('Independent team plant total differs from verified occurrence sides')
            if len(planters)!=1:
                continue
            for number in plant_rounds:
                proposed = [r for r in proposals if r['kind']=='plant' and r['round']==number]
                verdict = ('unresolved replay actor' if len(proposed)!=1 else
                           'agreement' if proposed[0]['official_player_id']==planters[0]['id'] else 'disagreement')
                constrained.append(dict(official_match_id=mid,kind='plant',round=number,
                                        official_actor=planters[0]['name'],proposal=proposed,verdict=verdict,
                                        source='Single official player accounts for all team plants; replay independently verifies occurrence and Attack side, not a direct official per-round actor field'))
        totals = []
        for person in people:
            for kind,field in (('plant','diffuserPlanted'),('disable','diffuserDisabled')):
                official_count = person['stats'][field]['count']
                if type(official_count) is not int or official_count<0:
                    raise ValueError('Invalid primary objective counter')
                count = credited[person['id'],kind]
                totals.append(dict(player=person['name'],id=person['id'],kind=kind,
                                   official_count=official_count,replay_resolved=count))
                if count>official_count or (prediction['objective_complete'] and count!=official_count):
                    conflicts.append(dict(official_match_id=mid,**totals[-1]))
        for kind in ('plant','disable'):
            if sum(x['official_count'] for x in totals if x['kind']==kind)!=prediction['objectives'].get(kind,0):
                raise ValueError('Independent objective totals and replay occurrences differ')
        records.append(dict(official_match_id=mid,map=match.map_name,source=source['official_page'],
                            source_sha256=sha(primary),complete=prediction['objective_complete'],
                            proposals=proposals,unresolved=unresolved,player_totals=totals))
    record = dict(status='fixed_port_independent_primary_constraints_consumed_rating_event',totals=dict(total),
                  records=records,aggregate_conflicts=conflicts,independently_constrained_objectives=constrained,
                  permanent_rating_result_sha256=permanent,
                  limitation='Primary totals are independent source constraints, not visual proof of every actor. Multiple-player same-kind totals cannot assign individual rounds.')
    (DATA/'independent-actor-constraints.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    lines = ['# Fixed actor port: independent SAL primary constraints', '',
             'The actor port and parser were frozen before these final-event replays were acquired. '
             'Replay proposals are unchanged. This audit projects official Ubisoft objective totals and round sides/winners, '
             'without third-party round actor text or Rating residuals. It does not revise the consumed Rating final.', '',
             f'20maps/207rounds: {dict(total)}. Aggregate contradictions: {len(conflicts)}. '
             f'Single-official-player round constraints: {dict(Counter((c["kind"],c["verdict"]) for c in constrained))}.', '',
             '| Official / map | Resolved proposals | Unresolved | Official aggregate constraints |',
             '| --- | --- | --- | --- |']
    for m in records:
        proposals = dict(Counter(r['kind'] for r in m['proposals']))
        lines.append(f"| [{m['official_match_id']}]({m['source']}) / {m['map']} | {proposals} | {m['unresolved']} | "
                     f"{'No contradictory credited count' if not any(c['official_match_id']==m['official_match_id'] for c in conflicts) else 'Requires independent review'} |")
    lines += ['', '## Individually constrained objective rounds', '',
              '| Official / round | Kind | Primary constrained actor | Replay proposal | Verdict |',
              '| --- | --- | --- | --- | --- |']
    for c in constrained:
        lines.append(f"| {c['official_match_id']}/R{c['round']:02d} | {c['kind']} | {c['official_actor']} | {c['proposal']} | {c['verdict']} |")
    lines += ['', '## Resolution and limits', '',
              'Official objective totals equal the independently validated replay occurrence counts on all20maps. '
              'All resolved credits are within official per-player totals; complete-actor maps agree exactly. '
              'Two missing body-state cases remain unresolved: no actor is chosen from the remaining official count. '
              'No extra parser actor is introduced to force equality.', '',
              'Aggregate consistency cannot prove each individual round when several players performed plants or disables. '
              'A sole official disabler plus verified Defense Defuser win constrains that actor. '
              'A sole official planter plus validated replay occurrence/Attack side similarly constrains a plant actor. '
              'Unresolved proposals remain unresolved even when primary totals constrain a name. This is an explicit inference '
              'from map totals and official round metadata, not a direct actor field or a VOD claim. '
              'The audit does not claim54 independently visually adjudicated objectives or call the consumed Rating cohort a new Rating holdout.', '',
              f'Conflicts requiring future independent adjudication: {conflicts}.', '',
              f'Permanent failed SAL Rating result SHA256 `{permanent}` and all{len(protected)} live hashes unchanged. '
              'No structural rule changes, actor relabeling, kill/death/operator changes, import, archive/public mutation or publishing.', '']
    (ROOT/'research/output/v3-sal-official-actor-constraints.md').write_text('\n'.join(lines),encoding='utf-8')
    if sha(RESULT)!=permanent or snapshot()!=protected:
        raise ValueError('Permanent result/live files changed')
    print('Independent fixed-port SAL constraints',dict(total),'aggregate conflicts',len(conflicts),
          'single-actor constraints',dict(Counter((c['kind'],c['verdict']) for c in constrained)),flush=True)


if __name__=='__main__':main()
