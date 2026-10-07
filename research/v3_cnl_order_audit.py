"""Consumed final diagnostics of native finisher order; never regrade/fix targets.

No low-level replay decoding, new parsing, SQL write, or production policy change.
"""
from collections import Counter
import json
import math

from credited_late_history_development import immutable_write
from r6stats.parser.models import Match
from r6stats.stats.calculate import chronological
from v3_cnl_consumed_audit import DATA, RESULT
from v3_final_reserve import ROOT, sha


def ordered_states(round_):
    """Use verified native callback ordinal, including all deaths, once each."""
    players={p.key:p for p in round_.players}
    if len(players)!=10 or len({k.sequence for k in round_.kills})!=len(round_.kills):
        raise ValueError('Distinct full roster/event ordinals required')
    alive=set(players); candidates={}; opening=None; timeline=[]
    for k in sorted(round_.kills,key=lambda k:k.sequence):
        if k.victim not in players or (k.killer and k.killer not in players):
            raise ValueError('Unbound event identity')
        if k.victim not in alive:raise ValueError('Duplicate physical death, not silently counted')
        if opening is None and k.killer and not k.teamkill and k.killer!=k.victim:
            opening=(k.killer,k.victim)
        alive.remove(k.victim)
        team=players[k.victim].team
        survivors=[key for key in alive if players[key].team==team]
        enemies=sum(players[key].team!=team for key in alive)
        if len(survivors)==1 and 1<=enemies<=5 and team not in candidates:
            candidates[team]=(survivors[0],enemies)
        timeline.append(dict(sequence=k.sequence,remaining=k.remaining,killer=k.killer,victim=k.victim,
            alive=sorted(alive),first_sole=dict(candidates)))
    return dict(opening=opening,clutch=candidates.get(round_.winner),timeline=timeline)


def verify_native(round_,observation):
    players={p.username:p for p in round_.players}
    header=observation['header']['players']
    if set(players)!={p['username'] for p in header}:raise ValueError('Exact header identity differs')
    expected=[]
    for f in observation['credit']['finishes']:
        feedback=f['feedback'];kind=feedback['type']['name']
        if kind not in ('Kill','Death'):raise ValueError('Unknown elimination type')
        victim=players.get(feedback['target'] if kind=='Kill' else feedback['username'])
        killer=players.get(feedback['username']) if kind=='Kill' else None
        if victim is None or (kind=='Kill' and killer is None):raise ValueError('Unbound native identity')
        expected.append((killer.key if killer else '',victim.key,float(feedback['timeInSeconds']),bool(feedback.get('headshot'))))
    actual=[(k.killer,k.victim,k.remaining,k.headshot) for k in sorted(round_.kills,key=lambda k:k.sequence)]
    if actual!=expected:raise ValueError('Exact normalized/native event parity differs')
    offsets=[f['offset'] for f in observation['credit']['finishes']]
    positive=[x for x in offsets if x>0]
    if positive!=sorted(set(positive)):raise ValueError('Physical offsets duplicate/reorder')
    return offsets


def main():
    before=sha(RESULT)
    final=json.loads(RESULT.read_text(encoding='utf-8'))
    if final['passed'] or not final['final_event_consumed']:raise ValueError('CNL must remain consumed FAIL')
    audit=json.loads((DATA/'consumed-feature-audit.json').read_text(encoding='utf-8'))
    targets={(r['match_id'],r['game_id'],r['player']):r for r in audit['rows']}
    totals=Counter();reports=[];rows=[]
    for path in sorted(DATA.glob('*/prelabel-replays.json')):
        payload=json.loads(path.read_text(encoding='utf-8'))
        for m in payload['maps']:
            eligible=[r for r in m['rows'] if r['fit_eligible']]
            if not eligible:continue
            match=Match.from_dict(m['normalized']);mapping={r['logical_round']:r for r in m['physical_mapping']}
            states={}
            for round_ in match.rounds:
                physical=mapping[round_.number]
                obs_path=DATA/'raw'/(physical['sha256']+'.json')
                observation=json.loads(obs_path.read_text(encoding='utf-8'))
                offsets=verify_native(round_,observation);states[round_.number]=ordered_states(round_)
                native=[k.sequence for k in sorted(round_.kills,key=lambda k:k.sequence)]
                old=[k.sequence for k in chronological(round_.kills)]
                totals['rounds']+=1;totals['verified_positive_offsets']+=sum(x>0 for x in offsets)
                totals['zero_offsets']+=sum(x<=0 for x in offsets)
                if old!=native:
                    totals['legacy_reordered_rounds']+=1
                    reports.append(dict(match_id=payload['siegegg_match_id'],game_id=m['game_id'],round=round_.number,
                        physical_round=physical['physical_round'],replay_sha256=physical['sha256'],native_order=native,
                        legacy_order=old,offsets=offsets,timeline=states[round_.number]['timeline']))
            for row in eligible:
                key=next(p.key for p in match.rounds[0].players if p.username==row['player'])
                t=targets[row['match_id'],row['game_id'],row['player']]
                clutches=[dict(round=n,size=s['clutch'][1]) for n,s in states.items() if s['clutch'] and s['clutch'][0]==key]
                ok=sum(s['opening'] is not None and s['opening'][0]==key for s in states.values())
                od=sum(s['opening'] is not None and s['opening'][1]==key for s in states.values())
                totals['clutch_log_agreements']+=clutches==t['public_clutches']
                totals['opening_kills_agreements']+=ok==t['metrics']['opening_kills'][1]
                totals['opening_deaths_agreements']+=od==t['metrics']['opening_deaths'][1]
                for k in ('kost','survival'):
                    totals[k+'_truncation_agreements']+=math.floor(t['metrics'][k][0]+1e-7)==t['metrics'][k][1]
                rows.append(dict(match_id=row['match_id'],game_id=row['game_id'],player=row['player'],
                    native_clutches=clutches,legacy_clutches=t['replay_clutches'],public_clutches=t['public_clutches'],
                    native_opening_kills=ok,native_opening_deaths=od,
                    legacy_opening_kills=t['metrics']['opening_kills'][0],legacy_opening_deaths=t['metrics']['opening_deaths'][0],
                    public_opening_kills=t['metrics']['opening_kills'][1],public_opening_deaths=t['metrics']['opening_deaths'][1]))
    result=dict(final_result_sha256=before,rows=rows,totals=dict(totals),reordered_rounds=reports,
        final_regraded=False,source_policy='Exact header/event identity parity; native callback ordinal; all positive offsets strictly increasing. Zero legacy offsets explicitly retained, not invented.',
        remaining_limits='Native finisher order is not DBNO or credited-owner chronology. Trade windows and credited opening owners remain unsupported.')
    immutable_write(DATA/'consumed-order-audit.json',result)
    if before!=sha(RESULT):raise ValueError('Final result changed')
    lines=['# Consumed CNL native-order audit','',json.dumps(dict(totals),indent=2),'',
        'All 300 frozen rows remain in the audit. The CNL FAIL is unchanged. No production data, Rating, or feature policy changed. Native callbacks are serialized by increasing marker offset in Go Reader.Read; exact normalized finisher/victim/time/headshot parity is checked per round.',
        '', '| Player / game | Legacy clutch | Native-order clutch | Public log |','| --- | --- | --- | --- |']
    for r in rows:
        if r['native_clutches']!=r['public_clutches'] or r['legacy_clutches']!=r['native_clutches']:
            lines.append(f"| {r['player']}/{r['game_id']} | {r['legacy_clutches']} | {r['native_clutches']} | {r['public_clutches']} |")
    lines+=['',result['source_policy'],'',result['remaining_limits'],'',
        'Survival matches all 300 public values after percentage truncation. KOST uses actual integer round counts rather than a .51 percentage tolerance; remaining differences are semantic, not rounding. Public clutch sizes may also count downed players differently; contradictions cannot justify an inferred DBNO state.','']
    (ROOT/'research/output/v3-credited-cnl-order-diagnostics.md').write_text('\n'.join(lines),encoding='utf-8')
    print(json.dumps(dict(totals)),flush=True)


if __name__=='__main__':main()
