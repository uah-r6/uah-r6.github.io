"""Metadata-only event reservation and an immutable v3 candidate freeze."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
RESERVE = ROOT/'research/v3-final-event-reservation.json'
FREEZE = ROOT/'research/v3-frozen-objective-candidate.json'
EVENT = 'Asia Pacific League Stage 2 - APAC N 2026'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_sha(path):
    return hashlib.sha256(path.read_bytes().replace(b'\r\n',b'\n')).hexdigest()


def reserve():
    if RESERVE.exists():
        raise ValueError('Reservation exists; never replace the prospective selection')
    cache=ROOT/'data/research/diagnostics/v3-event-metadata'
    page=cache/'competition-510-15001.html'
    data=json.loads(re.search(r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>',
        page.read_text(encoding='utf-8'),re.S).group(1))['props']['pageProps']['pageData']
    if data['competition']['id']!=510:raise ValueError('Unexpected official event')
    links=set()
    for path in cache.glob('siegegg-189-results-*.html'):
        links.update(re.findall(r'href="(?:https://siege.gg)?(/matches/[^"?#]+)',path.read_text(encoding='utf-8')))
    # Metadata-only pairing from independent schedule opponent names/dates;
    # quality stage must additionally prove competition/date/score/map identity.
    ids={8154:6200,8155:6201,8156:6202,8157:6203,8158:6347,8159:6348,
         8160:6349,8161:6350,8162:6351,8163:6352,8164:6353,8165:6354}
    matches=sorted([m for s in data['phaseDetails']['steps'] for m in s['matches']],key=lambda m:(m['date'],m['id']))
    inventory=[]
    for m in matches:
        entry=dict(official_match_id=m['id'],date=m['date'],archive_url=m.get('replayLink'),
            official_page=f"https://www.ubisoft.com/en-us/esports/rainbow-six/siege/match/{m['id']}",
            team_ids=sorted(t['id'] for t in m['teams']),
            official_scores=[sorted(t['score'] for t in g['teams']) for g in m['games']],
            selected=bool(m.get('replayLink')),reserved_for_final_test=True)
        if entry['selected']:
            sid=ids[m['id']];pages=[u for u in links if u.startswith(f'/matches/{sid}-')]
            if len(pages)!=1:raise ValueError('Missing unique SiegeGG schedule pairing')
            entry.update(siegegg_match_id=sid,siegegg_page='https://siege.gg'+pages[0])
        inventory.append(entry)
    if len(inventory)!=28 or {m['official_match_id'] for m in inventory if m['selected']}!=set(ids):
        raise ValueError('Metadata selection differs; do not silently change scope')
    old=json.loads((ROOT/'research/sources.json').read_text(encoding='utf-8'))['matches']
    if set(ids.values()) & {m.get('siegegg_match_id') for m in old}:raise ValueError('Previously consumed match')
    record=dict(event=EVENT,official_competition_id=510,siegegg_competition_id=189,
        created_at=datetime.now(timezone.utc).isoformat(),status='reserved_rating_targets_unopened',
        scope='Entire named regional Stage 2 event, including later matches; no training or tuning on any match.',
        evaluation_snapshot='All 12 official group-stage archives linked at metadata checkpoint; unavailable 16 and future playoffs remain reserved, outside this fixed one-shot sample.',
        selection='All currently linked official archives, chronological first archive for initial pipeline proof. No objective/outcome selection.',
        evidence=['https://www.ubisoft.com/en-us/esports/rainbow-six/siege/competition/510/15001',
                  'https://siege.gg/matches?competitions=189&tab=results&page=2'],
        metadata_page_sha256=sha(page),matches=inventory,ratings_inspected=False,actors_inspected=False)
    RESERVE.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    print('Reserved event',EVENT,'28 scheduled / 12 linked archives; Rating targets sealed')


def freeze():
    if FREEZE.exists():raise ValueError('Candidate already frozen; never overwrite')
    reservation=json.loads(RESERVE.read_text(encoding='utf-8'))
    first=ROOT/'data/research/experiments/v3-objective-first-model.json'
    development=json.loads(first.read_text(encoding='utf-8'))
    if development['experiment_id']!='v3-objectives-20261002T213548Z' or development['final_test_evaluated']:
        raise ValueError('Unexpected deliberate development model')
    files=set()
    for directory in ('r6stats/parser','r6stats/stats','third_party/siege-dissect/dissect'):
        files.update(p for p in (ROOT/directory).rglob('*') if p.suffix in ('.py','.go'))
    for filename in ('research/v3_final_reserve.py','research/v3_final_pipeline.py',
                     'research/fit_models.py','research/fit_baseline.py','research/uah_comparison.py',
                     'research/objective_production_check.py','research/objective_transition_probe.py',
                     'research/v3_objective_fit.py','tests/test_v3_objective_research_gates.py'):
        files.add(ROOT/filename)
    record=dict(name='siege_style_v3_verified_objectives_research',status='frozen_before_new_final_targets',
        created_at=datetime.now(timezone.utc).isoformat(),source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        development_experiment_id=development['experiment_id'],development_model_sha256=sha(first),
        reservation_sha256=source_sha(RESERVE),event=reservation['event'],model=development['candidate_model'],
        baseline_model=development['baseline_model_unchanged'],
        input_rule='Existing eight raw v2 inputs; KOST excludes all player objective credit as in original clean training. Ninth input is verified plants+disables/round. Trade window 8 seconds inclusive. No operator normalization.',
        quality_gates=['Unique complete physical/logical replay chronology, exact map/score/round count',
            'Full stable 5v5 roster; unique case-insensitive basename identity matches public IGN, otherwise explicitly unresolved alias',
            'Exact player K/D and rounds; no Rating-dependent eligibility',
            'All objectives on a map must have verified completing_timer_owner_v1 actor; otherwise exclude entire map',
            'No speculative rehost round exclusion: unambiguous complete score-contiguous winning rounds only'],
        acceptance=dict(min_clean_rows=80,min_clean_maps=8,min_distinct_rosters=4,min_objective_positive_rows=10,
            max_mae=.035,min_relative_mae_improvement_vs_frozen_v2=.05,min_within_005=.80,
            max_abs_error=.20,rmse_not_worse_than_frozen_v2=True),
        evaluation_policy='Save all selected replay-derived predictions and label-free quality decisions before reading Rating values; evaluate exactly once; preserve failure/insufficiency permanently. No automatic deployment regardless outcome.',
        parser_binary='.local-tools/bin/siege-dissect-actors.exe',parser_sha256=sha(ROOT/'.local-tools/bin/siege-dissect-actors.exe'),
        source_hashes={str(p.relative_to(ROOT)).replace('\\','/'):source_sha(p) for p in sorted(files)},
        final_test_evaluated=False,production_deployed=False)
    FREEZE.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    print('Frozen existing model + rules/gates/dependencies; no new final target errors')


if __name__=='__main__':
    import sys
    {'reserve':reserve,'freeze':freeze}[sys.argv[1]]()
