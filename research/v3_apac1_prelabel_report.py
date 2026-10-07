"""Summarize terminal cached prelabel decisions without accessing Rating targets."""
from collections import Counter
import json

from v3_apac1_pipeline import DATA
from v3_apac1_reserve import RESERVE
from v3_final_reserve import ROOT


def main():
    reserve=json.loads(RESERVE.read_text(encoding='utf-8'));maps=[];builds=Counter()
    for source in reserve['matches']:
        p=DATA/str(source['official_match_id'])/'prelabel-replays-v3.json'
        record=json.loads(p.read_text(encoding='utf-8'))
        for m in record['maps']:
            maps.append((source,m))
            for path in m['inputs']:
                raw=json.loads((ROOT/path).read_text(encoding='utf-8'))
                if 'header' in raw:builds[raw['header']['codeVersion']]+=1
    clean=[r for _,m in maps for r in m['rows'] if r['fit_eligible']]
    lines=['# Untouched APAC North Stage1 prelabel cohort','',
        f"All {len(maps)} group-stage BO1 archives received terminal decisions. {len(clean)} clean player-map rows / {sum(bool(m['clean_rows']) for _,m in maps)} clean maps / {len({r['roster_id'] for r in clean})} rosters / {sum(r['objective_positive'] for r in clean)} objective-positive rows.",
        '',reserve['exposure'],'',
        'No Rating targets fetched or opened. Core actor completeness, credited counters, exact independent primary K/D/objectives/round winners/roles, full public/primary roster bijection and positive native elimination offsets are required. Older builds and unresolved evidence remain refusals. All earlier prelabel decisions stay preserved; no old objective compatibility expansion.',
        '', 'Raw observation builds: '+json.dumps(dict(builds)), '',
        '| Official / public match | Map | Clean rows | Refusals |','| --- | --- | ---: | --- |']
    for s,m in maps:
        issues=sorted({i for r in m['rows'] for i in r['quality_issues']}|({m['whole_map_refusal']} if m.get('whole_map_refusal') else set()))
        lines.append(f"| {s['official_match_id']}/{s['siegegg_match_id']} | {m['map']} | {m['clean_rows']} | {'; '.join(issues)} |")
    lines+=['',
        'Identity resolution used exact replay/public/primary basenames, previous independently bound nonnil UUID/public-ID records, or exact UUID browser username history. Demic164 and Nina666 reuse sealed profile bindings; OKOMESSH history explicitly includes OKOMESH. No digit stripping, K/D alias selection or remaining-player association.',
        '',
        'Candidate and final gates remain fixed in v3-native-order-candidate.json and v3-native-order-plan.json. NEXT: clean-source full model/row/input freeze, commit it before Rating requests; evaluate once and preserve failure permanently.',
        '',
        'Primary schedule: [Ubisoft APAC North Stage1 group stage](https://www.ubisoft.com/en-us/esports/rainbow-six/siege/competition/505/15000). Independent schedule: [SiegeGG results](https://siege.gg/matches?competitions=110&tab=results). All replay/identity/input caches stay ignored/private.','']
    (ROOT/'research/output/v3-native-final-apac1-prelabel.md').write_text('\n'.join(lines),encoding='utf-8')
    print(lines[2],flush=True)


if __name__=='__main__':main()
