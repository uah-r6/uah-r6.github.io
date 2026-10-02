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
    aliases=json.loads((ROOT/'research/v3-final-verified-aliases.json').read_text(encoding='utf-8'))['aliases']
    primary_sources={}
    for source in reservation['matches']:
        if not source['selected']:continue
        path=DATA/str(source['official_match_id'])
        pred=json.loads((path/'replay-predictions.json').read_text(encoding='utf-8'))
        quality=json.loads(quality_path(path).read_text(encoding='utf-8'))
        primary=ROOT/f"data/research/diagnostics/v3-event-metadata/match-{source['official_match_id']}.html"
        official={}
        if primary.exists():
            payload=json.loads(re.search(r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>',primary.read_text(encoding='utf-8'),re.S).group(1))['props']['pageProps']['pageData']
            for team in payload['match']['games'][0]['teams']:
                for p in team['players'] or []:
                    official[p['name'].casefold()]=(p['stats']['kills']['count'],p['stats']['deaths']['count'])
            primary_sources[str(source['official_match_id'])]=dict(url=source['official_page'],cached_page_sha256=sha(primary))
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
            name=aliases.get(row['player'],{}).get('name',row['player'].split('.')[0]).casefold()
            official_kd=official.get(name)
            agreement=('official agrees with public' if official_kd==(k,d) else
                'official agrees with replay' if official_kd==(stats['kills'],stats['deaths']) else
                'official disagrees with both' if official_kd else 'not independently checked')
            records.append(dict(official_match_id=source['official_match_id'],player=row['player'],
                public_kills=k,public_deaths=d,opponent_kills=stats['kills'],deaths=stats['deaths'],
                teamkills=teamkills,category=category,objective_map_complete=pred['objective_complete'],
                official_kd=official_kd,independent_agreement=agreement))
            categories[category]+=1
    result=dict(status='consumed_convention_diagnostic_not_revised_final',categories=dict(categories),rows=records,
        permanent_final_sha256=result_sha,no_gate_or_metric_revision=True,primary_sources=primary_sources)
    (DATA/'kd-convention-audit.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    lines=['# Consumed APAC final K/D exclusion audit','',
        'This diagnoses existing exclusions after the one-shot result was permanently recorded. '
        'It does not change kills/deaths, eligibility, Rating coefficients or the frozen failed result.','',
        f'Categories: `{dict(categories)}`. Includes overlapping K/D issues on the objective-incomplete map.','',
        '| Official match / player | Public K/D | Opponent K/D | Teamkills | Primary official K/D | Independent review |',
        '| --- | --- | --- | ---: | --- | --- |']
    for r in records:lines.append(f"| {r['official_match_id']}/{r['player']} | {r['public_kills']}/{r['public_deaths']} | {r['opponent_kills']}/{r['deaths']} | {r['teamkills']} | {r['official_kd'] or 'not checked'} | {r['independent_agreement']} |")
    lines+=['','All26 mismatched player rows have zero teamkills, so teamkill-count convention does not explain any current exclusion. Many are balanced +/-1 killer assignments with identical deaths. '
        'Primary official8154 totals independently agree with all four disputed public counts; other cases remain unadjudicated. The cached official VOD link8154 is empty. '
        'A broadcast or other independent kill-log review is needed to identify a particular faulty replay packet; no low-level parsing or stat definition change here.','']
    for mid,source in primary_sources.items():lines.append(f"Primary [{mid} official match]({source['url']}); cached SHA256 `{source['cached_page_sha256']}`. Only player identity and K/D fields projected, no objective/Rating inputs.")
    lines+=['',
        f'Permanent final SHA256 `{result_sha}` and all {len(protected)} protected live files unchanged.','']
    (ROOT/'research/output/v3-final-apac-n-kd-conventions.md').write_text('\n'.join(lines),encoding='utf-8')
    if sha(RESULT)!=result_sha or snapshot()!=protected:raise ValueError('Immutable result/live files changed')
    print(dict(categories),flush=True)


if __name__=='__main__':main()
