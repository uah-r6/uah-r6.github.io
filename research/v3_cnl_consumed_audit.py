"""Post-final diagnostics only; the CNL FAIL is immutable and never regraded."""
from collections import Counter
import html
import json
import re

from credited_late_history_development import immutable_write
from v3_cnl_final import DATA,RESULT,read_frozen
from v3_cnl_metadata import DATA as METADATA
from v3_final_reserve import ROOT,sha


def main():
    frozen=read_frozen();before=sha(RESULT);result=json.loads(RESULT.read_text(encoding='utf-8'))
    if result['passed'] or not result['final_event_consumed']:raise ValueError('Expected permanently consumed FAIL')
    totals=Counter();rows=[]
    for row in frozen['rows']:
        targets=json.loads((DATA/'targets'/f"{row['match_id']}.json").read_text(encoding='utf-8'))
        target=targets[str(row['game_id'])][str(row['player_id'])]
        meta=json.loads((METADATA/f"cnl1-metadata-{row['match_id']}.json").read_text(encoding='utf-8'))
        person=next(p for p in meta['players'] if p['id']==row['player_id'])
        spellings={person['ign'].casefold(),person['stylized_name'].casefold()}
        game=next(g for g in meta['games'] if g['id']==row['game_id'])
        public_clutches=[]
        for number,r in enumerate(game['rounds'],1):
            for event in r['events']:
                if event['type']!='clutch':continue
                text=html.unescape(re.sub('<[^>]+>',' ',event['html']))
                match=re.search(r'([A-Za-z0-9_.-]+) clutches a 1v([1-5])',text)
                if not match:raise ValueError('Opaque public clutch log; do not infer')
                if match.group(1).casefold() in spellings:public_clutches.append(dict(round=number,size=int(match.group(2))))
        replay_clutches=[dict(round=r['number'],size=x) for r in row['rounds'] for x in range(1,6) if r[f'clutch_1v{x}']]
        derived={k:sum(r[k] for r in row['rounds']) for k in ('kills','deaths','kost_rounds','survived','plants','disables','opening_kills','opening_deaths','clutches')}
        metrics=dict(kost=(derived['kost_rounds']/len(row['rounds'])*100,float(target['kost'])),
            survival=(derived['survived']/len(row['rounds'])*100,float(target['srv'])),
            clutches=(derived['clutches'],int(target['clutches'])))
        opening=re.fullmatch(r'(\d+)-(\d+)(?:\s+\([+-]?\d+\))?',target['ok'])
        if not opening:raise ValueError('Opaque public opening total')
        metrics['opening_kills']=(derived['opening_kills'],int(opening[1]));metrics['opening_deaths']=(derived['opening_deaths'],int(opening[2]))
        for k,(a,b) in metrics.items():totals[k+'_agreements' if abs(a-b)<=.51 else k+'_disagreements']+=1
        totals['clutch_size_agreements' if replay_clutches==public_clutches else 'clutch_size_disagreements']+=1
        totals['positive_clutch_rows']+=bool(replay_clutches or public_clutches)
        rows.append(dict(match_id=row['match_id'],game_id=row['game_id'],player=row['player'],derived=derived,
            metrics=metrics,replay_clutches=replay_clutches,public_clutches=public_clutches,
            residual=row['v3_prediction']-float(target['rating']),rating=float(target['rating'])))
    immutable_write(DATA/'consumed-feature-audit.json',dict(final_result_sha256=before,rows=rows,totals=dict(totals),
        final_regraded=False,model_changed=False,scope='All300frozen CNL rows; public log sizes and public metric totals are diagnostics, never an eligibility revision'))
    if sha(RESULT)!=before:raise ValueError('Consumed final changed')
    lines=['# Consumed CNL feature diagnostics','',
        'The final FAIL remains at its original SHA; this is a post-final diagnostic and never a replacement final score. All300frozen rows are included.','',
        'The raw percentage comparison used a .51-point tolerance. The subsequent native-order audit establishes public truncation: survival agrees300/300 and KOST216/300. Thus raw percentage disagreement labels include display formatting; exact integer opening/clutch comparisons are unaffected. See v3-credited-cnl-order-diagnostics.md.','',
        json.dumps(dict(totals),indent=2),'',
        '| Player / map game | Residual | Replay first-sole clutch | Independent public clutch log |','| --- | ---: | --- | --- |']
    for r in sorted(rows,key=lambda r:abs(r['residual']),reverse=True)[:12]:
        lines.append(f"| {r['player']}/{r['game_id']} | {r['residual']:+.5f} | {r['replay_clutches']} | {r['public_clutches']} |")
    lines += ['','Direction 9-5,KOST60%,survival50%,openings0-0 and one clutch all independently match. His largest residual accompanies a publicly corroborated1v5; Cpk has a corroborated1v4. This motivates a structural size-feature audit, not removing outliers, changing targets, or fitting individual size coefficients. The old small-cohort linear size experiment remains rejected at its original result; a new larger-cohort study would need a separate prospective plan and entirely new final event.','']
    (ROOT/'research/output/v3-credited-cnl-consumed-diagnostics.md').write_text('\n'.join(lines),encoding='utf-8')
    print('CONSUMED DIAGNOSTICS',dict(totals),flush=True)


if __name__=='__main__':main()
