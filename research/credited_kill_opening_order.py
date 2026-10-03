"""Separate consumed opening order controls; never modify frozen event features."""
from collections import Counter
import json

from uah_guarded_actor_readonly import snapshot
from v3_final_reserve import ROOT


def first_opponent_finish(events, teams, *, packet_order):
    ordered=sorted(events,key=(lambda e:e['offset']) if packet_order else
        (lambda e:(-e['feedback']['timeInSeconds'],e['offset'])))
    alive=set(teams)
    for e in ordered:
        f=e['feedback'];kind=f['type']['name']
        victim=f.get('target') if kind=='Kill' else f.get('username') if kind=='Death' else None
        if victim not in alive:continue
        alive.remove(victim)
        killer=f.get('username') if kind=='Kill' else None
        if killer in teams and teams[killer]!=teams[victim]:return e
    return None


def main():
    protected=snapshot(); feature=json.loads((ROOT/'data/research/credited-kills-v1/feature-audit.json').read_text(encoding='utf-8'))
    rounds=[];rows=[]
    for path in sorted((ROOT/'data/research/diagnostics/v3-sal-kill-credit').glob('*.json')):
        if not path.stem.isdigit():continue
        old=json.loads(path.read_text(encoding='utf-8'));mid=old['official_match_id']
        pred=json.loads((ROOT/f'data/research/v3-corrected-final-sal-stage2/{mid}/replay-predictions.json').read_text(encoding='utf-8'))
        teams={p['player']:p['team'] for p in pred['players']};kills=Counter();deaths=Counter()
        for r in old['rounds']:
            if any(e['offset']<=0 for e in r['feed']):raise ValueError('Packet-first control needs exact feed offsets')
            packet=first_opponent_finish(r['feed'],teams,packet_order=True)
            timed=first_opponent_finish(r['feed'],teams,packet_order=False)
            if packet:
                kills[packet['feedback']['username']]+=1;deaths[packet['feedback']['target']]+=1
            if packet!=timed:
                rounds.append(dict(official_match_id=mid,round=r['logical_round'],packet_first=packet,
                    timer_first=timed,all_raw_finish_events=r['feed'],
                    credit_deltas={name:p['delta'] for name,p in r['players'].items()},
                    caveat='Packet-first finisher/victim is observed. A credited killer of that victim is not assigned from a round total.'))
        for name in teams:
            external=next(p for p in feature['player_maps'] if p['official_match_id']==mid and p['player']==name)
            rows.append(dict(official_match_id=mid,player=name,packet_first=[kills[name],deaths[name]],
                             timer_first=external['finisher_opening'],official=external['official_opening'],public=external['public_opening']))
    counts=dict(player_maps=len(rows),packet_first_official_matches=sum(r['packet_first']==r['official'] for r in rows),
        timer_first_official_matches=sum(r['timer_first']==r['official'] for r in rows),
        packet_first_public_matches=sum(r['packet_first']==r['public'] for r in rows),
        different_rounds=len(rounds))
    result=dict(counts=counts,rounds=rounds,rows=rows,protected_hashes=protected,
                status='consumed_event_order_hypothesis_not_runtime_change')
    (ROOT/'data/research/credited-kills-v1/opening-order.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    lines=['# Consumed SAL opening packet-order control','',str(counts),'',
        'A separate diagnostic compares first opponent final elimination in exact raw packet order with '
        'the original decreasing coarse-timer order. Original features/results/production logic are preserved. '
        'DBNO transitions are not deaths; no credited victim is inferred from counters.','',
        '| Official map / round | Packet-first finisher -> victim / clock | Timer-first finisher -> victim / clock |',
        '| --- | --- | --- |']
    for r in rounds:
        p,t=r['packet_first']['feedback'],r['timer_first']['feedback']
        lines.append(f"| {r['official_match_id']}/R{r['round']:02d} | {p['username']} -> {p['target']} / {p['time']} | {t['username']} -> {t['target']} / {t['time']} |")
    lines+=['','## Limits','',
        'Map-level agreement with independent official/public opening totals constrains the order hypothesis. '
        'It does not establish the official policy for a DBNO/downer versus finisher split or individual '
        'subsecond trade windows. Timing mismatches need independent modern HUD/death-sequence corroboration '
        'before replacing the live opening/trade logic. No nearest-counter or expected-total assignment is permitted.', '']
    (ROOT/'research/output/credited-kill-opening-order.md').write_text('\n'.join(lines),encoding='utf-8')
    if snapshot()!=protected:raise ValueError('Protected state changed')
    print(counts)


if __name__=='__main__':main()
