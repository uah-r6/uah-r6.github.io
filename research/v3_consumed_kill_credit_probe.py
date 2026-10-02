"""Consumed SAL scoreboard-credit versus finisher evidence; no stat corrections.

Reuses existing Go observers and typed temporal UID/component joins. Counter
owners are observed independently of official/public kill totals. The report
does not assign counter increases to a victim or replace any kill event.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
from uuid import UUID

from objective_production_check import candidate_raw
from objective_player_component_fields import observe, bindings_at
from objective_actor_liveness import feedback
from v3_corrected_final_pipeline import DATA, RESULT, ROOT, verify, sha
from uah_guarded_actor_readonly import snapshot


def counter_continuity(rounds):
    issues, resets = [], []
    for before, after in zip(rounds, rounds[1:]):
        same_roster = (len(before['players']) == len(after['players']) == 10
                       and before['players'].keys() == after['players'].keys())
        profiles = [p['profile_id'] for p in before['players'].values()]
        try:
            valid_profiles = len(set(profiles)) == 10 and all(UUID(p).int != 0 for p in profiles)
        except (ValueError, TypeError, AttributeError):
            valid_profiles = False
        same_profiles = same_roster and valid_profiles and all(
            before['players'][name]['profile_id']
            and before['players'][name]['profile_id'] == after['players'][name]['profile_id']
            for name in before['players'])
        explicit_reset = (same_profiles and before['folder'] != after['folder']
                          and after['physical_round'] == 1
                          and all(p['initial'] == 0 for p in after['players'].values()))
        if explicit_reset:
            resets.append(dict(round=after['logical_round'],folder=after['folder'],
                               reason='New physical replay folder R01; all ten counters start at zero; exact same ten distinct nonzero profiles'))
            continue
        if not same_roster:
            issues.append(dict(round=after['logical_round'],reason='Counter roster differs'))
        for name in before['players'].keys() & after['players'].keys():
            if before['players'][name]['terminal'] != after['players'][name]['initial']:
                issues.append(dict(round=after['logical_round'],player=name,
                                   previous=before['players'][name]['terminal'],initial=after['players'][name]['initial']))
    return issues, resets


def round_evidence(rec, raw, logical, accepted_finishes):
    state, owners, slots, fields = observe(rec)
    feed = feedback(rec)
    expected = [e for e in raw['matchFeedback'] if e['type']['name'] in ('Kill','Death')]
    if [e['feedback'] for e in feed['events']] != expected:
        raise ValueError('Existing observer differs from frozen kill/death feedback')
    players = state['header']['players']
    if len(players)!=10 or len({p['id'] for p in players})!=10 or any(not p['id'] for p in players):
        raise ValueError('Full distinct stable UID roster required')
    header = raw.get('header',raw)
    if {p['username']:p['id'] for p in players} != {p['username']:p['id'] for p in header['players']}:
        raise ValueError('Observer stable UID/header roster differs from frozen parser')
    counter_rows, unresolved = [], []
    for f in fields:
        if f['hash'] not in ('1cd2b19d','4d737f9e'):
            continue
        route = bindings_at(owners,slots,f['offset']).get(f['entity'])
        if route and route['class_hash']=='18a591a1' and route['slot']=='eb219b38':
            counter_rows.append(dict(player=route['player'],counter='kills' if f['hash']=='1cd2b19d' else 'assists',
                                     value=f['value'],offset=f['offset'],entity=f['entity'],route=route))
    feed_counts = Counter(e['feedback']['username'] for e in feed['events'] if e['feedback']['type']['name']=='Kill')
    by_player, differences = {}, []
    for player in players:
        name = player['username']
        rows = [r for r in counter_rows if r['player']==name and r['counter']=='kills']
        if not rows:
            unresolved.append(dict(player=name,reason='Missing direct stable-UID scoreboard kill counter'))
            continue
        values = [r['value'] for r in rows]
        first_kill = min((e['offset'] for e in feed['events'] if e['offset'] > 0),default=None)
        if first_kill is not None and rows[0]['offset'] >= first_kill:
            unresolved.append(dict(player=name,reason='Initial counter not established before first death/finish'))
            continue
        if len({r['entity'] for r in rows})!=1 or any(v>250 for v in values) or any(b<a for a,b in zip(values,values[1:])):
            unresolved.append(dict(player=name,reason='Changing component, implausible or decreasing cumulative counter'))
            continue
        delta = values[-1]-values[0]
        by_player[name] = dict(uid=player['id'],profile_id=player.get('profileID'),
                               initial=values[0],terminal=values[-1],delta=delta,
                               raw_feedback_kill_packets=feed_counts[name],feed_finishes=accepted_finishes[name])
        if delta != accepted_finishes[name]:
            differences.append(dict(player=name,counter_credit_delta=delta,feed_finishes=accepted_finishes[name]))
    return dict(logical_round=logical,filename=rec.name,replay_sha256=sha(rec),
                full_counter_binding=not unresolved,unresolved=unresolved,players=by_player,
                differences=differences,counter_rows=counter_rows,feed=feed['events'])


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--limit',type=int,default=1);args=parser.parse_args()
    protected,permanent_sha=snapshot(),sha(RESULT)
    frozen,reservation=verify()
    destination=ROOT/'data/research/diagnostics/v3-sal-kill-credit';destination.mkdir(parents=True,exist_ok=True)
    records=[]
    for source in [m for m in reservation['matches'] if m['selected']][:args.limit]:
        mid=source['official_match_id']
        prediction=json.loads((DATA/str(mid)/'replay-predictions.json').read_text())
        extraction=ROOT/f'data/research/extracted/v3-corrected-final-sal-{mid}'
        cache={};rounds=[]
        for mapping in prediction['physical_mapping']:
            found=[r for r in extraction.rglob(mapping['filename']) if r.parent.name==mapping['folder']]
            if len(found)!=1 or sha(found[0])!=mapping['sha256']:
                raise ValueError('Physical replay identity mismatch')
            rec=found[0]
            if rec.parent not in cache:
                cache[rec.parent]=candidate_raw(rec.parent,ROOT/frozen['parser_binary'])
            raw=cache[rec.parent]['rounds'][mapping['physical_round']-1]
            accepted_finishes={p['player']:p['rounds'][mapping['logical_round']-1]['kills'] for p in prediction['players']}
            result=round_evidence(rec,raw,mapping['logical_round'],accepted_finishes)
            result.update(folder=mapping['folder'],physical_round=mapping['physical_round'])
            rounds.append(result)
            print('Consumed credit evidence',mid,'R',result['logical_round'],'bound',result['full_counter_binding'],
                  'credit/finisher differences',result['differences'],flush=True)
        complete=all(r['full_counter_binding'] for r in rounds)
        continuity,resets=counter_continuity(rounds)
        if continuity:complete=False
        # Only fully bound, cumulative-contiguous evidence can be totaled.
        summary=[]
        if complete:
            primary=json.loads((DATA/'independent-kd-audit.json').read_text())['rows']
            for p in prediction['players']:
                name=p['player'];credit=sum(r['players'][name]['delta'] for r in rounds)
                external=next(r for r in primary if r['official_match_id']==mid and r['player']==name)
                summary.append(dict(player=name,credit_counter_kills=credit,feed_finishes=p['derived']['kills'],
                                    official_kills=external['official_kd'][0],public_kills=external['public_kd'][0],
                                    credit_matches_independent=credit==external['official_kd'][0]==external['public_kd'][0]))
        result=dict(official_match_id=mid,map=prediction['map'],rounds=rounds,complete_counter_binding=complete,
                    continuity_issues=continuity,explicit_rehost_resets=resets,summary=summary,source_sha256=sha(Path(__file__)),
                    explanation='Kill credit and displayed finisher can differ. Counter binding is independent of public totals; victim association and DBNO causality remain unproven. No kills/deaths or model features changed.')
        (destination/f'{mid}.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
        records.append(result)
        print('Consumed map credit summary',mid,'complete',complete,summary,flush=True)
    lines=['# Consumed SAL credited-kill versus finisher evidence','',
           'Research only. No changes to parser kills/deaths, model inputs, frozen eligibility/results, SQLite or public data. '
           'Temporal declared scoreboard component -> stable numeric UID -> header player identity; no nearest-ID '
           'or public-counter matching chooses a player. Existing Go feedback observer is compared to frozen raw feedback. '
           'Full unique5v5 counter binding, monotonic values and between-round cumulative continuity are required. '
           'A reset is accepted only at a new physical replay folder R01 with exactly the same ten distinct nonzero profile UUIDs '
           'and all ten counters initialized to zero. Existing frozen score-contiguous chronology identifies the logical round; '
           'scores never infer a physical round or a credited player. '
           'Opponent finish counts come from the already-frozen per-round tracker inputs, which exclude teamkills, suicides '
           'and invalid repeated-victim deaths. Raw feedback Kill packet counts remain separate in the evidence ledger.', '',
           '| Official / player | Scoreboard credited kills | Tracker opponent finishes | Official kills | Public kills | Counter agrees |',
           '| --- | ---: | ---: | ---: | ---: | --- |']
    for m in records:
        for p in m['summary']:
            lines.append(f"| {m['official_match_id']}/{p['player']} | {p['credit_counter_kills']} | {p['feed_finishes']} | "
                         f"{p['official_kills']} | {p['public_kills']} | {p['credit_matches_independent']} |")
    lines+=['','## Every round with credit/finisher differences','',
            '| Official / physical round file | Differences |','| --- | --- |']
    for m in records:
        for r in m['rounds']:
            if r['differences']:lines.append(f"| {m['official_match_id']}/{r['filename']} | {r['differences']} |")
    failures=[dict(match=m['official_match_id'],continuity=m['continuity_issues'],
                   unresolved=[dict(round=r['logical_round'],issues=r['unresolved']) for r in m['rounds'] if r['unresolved']])
              for m in records if not m['complete_counter_binding']]
    reset_records=[(m['official_match_id'],m['explicit_rehost_resets']) for m in records if m['explicit_rehost_resets']]
    lines+=['',f'Binding/continuity failures: {failures}.', '',
            f'Explicit rehost resets: {reset_records}. '
            'The first stricter cumulative-only audit is preserved under ignored initial-continuity-audit; '
            'no frozen model, quality decision or final metric is changed by this expanded consumed diagnostic.', '',
            'The initial raw-feed comparison also included mitrix killing teammate Legacy in8596/R10. '
            'The tracker already correctly excludes that packet from opponent kills; the separate raw count is retained '
            'as a negative control, not a credited-opponent-kill discrepancy. No kill or teamkill convention is changed.', '',
            'Primary [Ubisoft August18,2021 DBNO notes](https://www.ubisoft.com/en-us/game/rainbow-six/siege/news-updates/1YPQ5yw9TaRhQwghjStqn2) '
            'describe a downing player receiving kill credit while another player finishes the opponent and appears in the kill feed. '
            'This historical mechanic is consistent with a balanced difference between credited kills and feed finishes. '
            'The current replay counter evidence does not by itself show who downed which victim. '
            'No individual feedback event is reassigned. Current Y11 VOD/body-state evidence would be needed for that causal association.', '',
            f'Permanent corrected final result SHA256 `{permanent_sha}` and all{len(protected)} live hashes unchanged.', '']
    (ROOT/'research/output/v3-consumed-sal-kill-credit.md').write_text('\n'.join(lines),encoding='utf-8')
    if sha(RESULT)!=permanent_sha or snapshot()!=protected:raise ValueError('Protected result/live files changed')


if __name__=='__main__':main()
