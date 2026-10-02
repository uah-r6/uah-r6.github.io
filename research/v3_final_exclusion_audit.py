"""Consumed final K/D convention diagnostics; never revise gates or results."""
from collections import Counter
import json
import re

from v3_final_pipeline import DATA, RESULT, quality_path, verify
from v3_final_reserve import ROOT, sha
from uah_guarded_actor_readonly import snapshot


def main():
    protected=snapshot();result_sha=sha(RESULT)
    _,reservation=verify();records=[];categories=Counter()
    for source in reservation['matches']:
        if not source['selected']:continue
        path=DATA/str(source['official_match_id'])
        pred=json.loads((path/'replay-predictions.json').read_text(encoding='utf-8'))
        quality=json.loads(quality_path(path).read_text(encoding='utf-8'))
        for decision in quality['decisions']:
            if 'Exact K/D mismatch' not in decision['issues']:continue
            row=next(r for r in pred['players'] if r['player']==decision['player'])
            k,d=map(int,re.match(r'(\d+)-(\d+)',decision['public_kd']).groups())
            stats=row['derived'];teamkills=stats['teamkills']
            category='other discrepancy'
            if d==stats['deaths'] and k==stats['kills']+teamkills and teamkills:
                category='public kills include teamkill events'
            elif d==stats['deaths'] and k==stats['kills']-teamkills and teamkills:
                category='public kills subtract teamkill events'
            records.append(dict(official_match_id=source['official_match_id'],player=row['player'],
                public_kills=k,public_deaths=d,opponent_kills=stats['kills'],deaths=stats['deaths'],
                teamkills=teamkills,category=category,objective_map_complete=pred['objective_complete']))
            categories[category]+=1
    result=dict(status='consumed_convention_diagnostic_not_revised_final',categories=dict(categories),rows=records,
        permanent_final_sha256=result_sha,no_gate_or_metric_revision=True)
    (DATA/'kd-convention-audit.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    lines=['# Consumed APAC final K/D exclusion audit','',
        'This diagnoses existing exclusions after the one-shot result was permanently recorded. '
        'It does not change kills/deaths, eligibility, Rating coefficients or the frozen failed result.','',
        f'Categories: `{dict(categories)}`. Includes overlapping K/D issues on the objective-incomplete map.','',
        '| Official match / player | Public K/D | Opponent K/D | Teamkills | Diagnostic |',
        '| --- | --- | --- | ---: | --- |']
    for r in records:lines.append(f"| {r['official_match_id']}/{r['player']} | {r['public_kills']}/{r['public_deaths']} | {r['opponent_kills']}/{r['deaths']} | {r['teamkills']} | {r['category']} |")
    lines+=['','A future quality protocol may distinguish public total kill events from the engine\'s opponent-only kills, after independent raw-log checks. No such protocol is applied retroactively here. Nonconforming cases remain parser/source discrepancies, not automatically admitted.','',
        f'Permanent final SHA256 `{result_sha}` and all {len(protected)} protected live files unchanged.','']
    (ROOT/'research/output/v3-final-apac-n-kd-conventions.md').write_text('\n'.join(lines),encoding='utf-8')
    if sha(RESULT)!=result_sha or snapshot()!=protected:raise ValueError('Immutable result/live files changed')
    print(dict(categories),flush=True)


if __name__=='__main__':main()
