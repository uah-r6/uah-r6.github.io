"""New SAL event metadata reserve and corrected-KOST model freeze."""
from datetime import datetime,timezone
import json
import re
import subprocess

from v3_final_reserve import ROOT,sha,source_sha

RESERVE=ROOT/'research/v3-corrected-final-event-reservation.json'
FREEZE=ROOT/'research/v3-corrected-frozen-candidate.json'


def reserve():
    if RESERVE.exists():raise ValueError('Never overwrite prospective event reservation')
    cache=ROOT/'data/research/diagnostics/v3-event-metadata'
    page=cache/'competition-515-15020.html'
    data=json.loads(re.search(r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>',page.read_text(encoding='utf-8'),re.S).group(1))['props']['pageProps']['pageData']
    if data['competition']['id']!=515:raise ValueError('Wrong independent regional event')
    # Independent public schedule-only opponent-name pairing. Target quality
    # must additionally verify exact competition/date/map/score after freeze.
    ids={8580:6178,8581:6179,8582:6180,8583:6253,8584:6262,8585:6182,8586:6183,
         8587:6263,8588:6264,8589:6185,8590:6318,8591:6319,8592:6320,
         8593:6321,8594:6322,8595:6323,8596:6324,8597:6325,8598:6326,8599:6327}
    links=set()
    for p in cache.glob('siegegg-187-results-*.html'):
        links.update(re.findall(r'href="(?:https://siege.gg)?(/matches/[^"?#]+)',p.read_text(encoding='utf-8')))
    inventory=[]
    matches=sorted([m for s in data['phaseDetails']['steps'] for m in s['matches']],key=lambda m:(m['date'],m['id']))
    for m in matches:
        item=dict(official_match_id=m['id'],date=m['date'],archive_url=m.get('replayLink'),
            official_page=f"https://www.ubisoft.com/en-us/esports/rainbow-six/siege/match/{m['id']}",
            team_ids=sorted(t['id'] for t in m['teams']),official_scores=[sorted(t['score'] for t in g['teams']) for g in m['games']],
            selected=bool(m.get('replayLink')),reserved_for_final_test=True)
        if item['selected']:
            sid=ids[m['id']];found=[u for u in links if u.startswith(f'/matches/{sid}-')]
            if len(found)!=1:raise ValueError('Unconfirmed unique schedule pairing')
            item.update(siegegg_match_id=sid,siegegg_page='https://siege.gg'+found[0])
        inventory.append(item)
    if len(matches)!=45 or {m['official_match_id'] for m in inventory if m['selected']}!=set(ids):
        raise ValueError('Metadata scope changed; never silently replace selection')
    sources=json.loads((ROOT/'research/sources.json').read_text(encoding='utf-8'))['matches']
    if set(ids.values())&{m.get('siegegg_match_id') for m in sources}:raise ValueError('Previously consumed match')
    reservation=dict(event='South America League Stage 2 2026',official_competition_id=515,siegegg_competition_id=187,
        created_at=datetime.now(timezone.utc).isoformat(),status='reserved_rating_targets_unopened',
        scope='Entire separate South America Stage2 event, including later matches; no training/tuning on any match.',
        evaluation_snapshot='All20 currently linked official group-stage archives. Later25 unavailable matches and playoffs remain reserved, outside this fixed one-shot snapshot.',
        selection='All currently linked archives selected using metadata only; first chronological archive for initial pipeline proof, then incremental batches.',
        event_exposures='Official dates/opponents/scores/archive links and public schedule URLs only. No SAL Rating/actor labels inspected. A separate CN discovery search exposed Rating snippets; CN is not this reserve and must not be called labels-unseen.',
        metadata_page_sha256=sha(page),matches=inventory,ratings_inspected=False,actors_inspected=False,
        evidence=['https://www.ubisoft.com/en-us/esports/rainbow-six/siege/competition/515/15020',
            'https://siege.gg/matches?competitions=187&tab=results&page=2'])
    RESERVE.write_text(json.dumps(reservation,indent=2)+'\n',encoding='utf-8')
    print('Reserved independent SAL Stage2:45scheduled/20linked archives, Rating labels unopened')


def freeze():
    if FREEZE.exists():raise ValueError('Never overwrite corrected candidate freeze')
    reservation=json.loads(RESERVE.read_text(encoding='utf-8'))
    path=ROOT/'data/research/experiments/v3-corrected-kost-model.json';development=json.loads(path.read_text(encoding='utf-8'))
    if development['experiment_id']!='v3-corrected-kost-20261002T221833Z' or development['final_events_used']:
        raise ValueError('Unexpected development candidate')
    files=set()
    for folder in ('r6stats/parser','r6stats/stats','third_party/siege-dissect/dissect'):
        files.update(p for p in (ROOT/folder).rglob('*') if p.suffix in ('.py','.go'))
    for filename in ('research/v3_corrected_final_reserve.py','research/v3_corrected_final_pipeline.py',
        'research/v3_corrected_kost_development.py','research/v3-corrected-kost-development-plan.json',
        'research/fit_models.py','research/fit_baseline.py','research/uah_comparison.py',
        'research/v3_objective_fit.py','research/objective_production_check.py','research/objective_transition_probe.py',
        'research/v3_final_reserve.py','tests/test_v3_corrected_final_gates.py'):
        files.add(ROOT/filename)
    record=dict(name='siege_style_v3_corrected_kost_verified_objectives_research',status='frozen_before_new_final_targets',
        created_at=datetime.now(timezone.utc).isoformat(),source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        development_experiment_id=development['experiment_id'],development_model_sha256=sha(path),
        reservation_sha256=source_sha(RESERVE),event=reservation['event'],model=development['model'],baseline_model=development['baseline'],
        input_rule='Both arms use fully verified objective-corrected KOST. Other eight/nine-family design definitions unchanged, raw metrics, trade window8 seconds inclusive, no operator normalization. A exact frozen v2 coefficients; B fixed ridge9features plus verified objectives.',
        quality_gates=['Complete unique score-contiguous physical/logical map and full stable5v5 roster, exact map/date/score/rounds',
            'Unique exact public IGN or independently verified UUID-bound alias; no fuzzy/KD/Rating identity inference',
            'Exact public per-player K/D and rounds; no outcome-dependent selection',
            'Every objective on map has verified completing_timer_owner_v1 credit, otherwise exclude entire map'],
        acceptance=dict(min_clean_rows=100,min_clean_maps=10,min_distinct_rosters=6,min_objective_positive_rows=15,
            max_mae=.035,min_relative_mae_improvement_vs_frozen_v2=.05,min_within_005=.80,max_abs_error=.20,rmse_not_worse_than_frozen_v2=True),
        evaluation_policy='Seal all20 predictions/quality before Rating read, evaluate once, preserve failure/insufficiency. No automatic deployment or reuse as untouched.',
        parser_binary='.local-tools/bin/siege-dissect-actors.exe',parser_sha256=sha(ROOT/'.local-tools/bin/siege-dissect-actors.exe'),
        source_hashes={str(p.relative_to(ROOT)).replace('\\','/'):source_sha(p) for p in sorted(files)},final_test_evaluated=False,production_deployed=False,
        first_v3_failed_final_sha256=sha(ROOT/'data/research/v3-final-apac-n-stage2/one-shot-result.json'))
    FREEZE.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    print('Corrected-KOST candidate frozen prospectively; original APAC failure unchanged')


if __name__=='__main__':
    import sys
    {'reserve':reserve,'freeze':freeze}[sys.argv[1]]()
