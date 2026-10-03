"""Metadata-only ASIA Stage2 actor reserve; isolated plant candidate freeze.

This is not a Rating experiment. Neither Rating targets nor actor outcomes are
used to choose the sample, model, numerical body predicate or acceptance gates.
"""
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import sys

from objective_bonus_body_candidate import candidate
from objective_completer_consumed_audit import observation
from objective_actor_liveness import feedback
from objective_production_check import candidate_raw
from r6stats.parser.siege_dissect import normalize, physical_round_numbers
from uah_guarded_actor_readonly import snapshot
from v3_final_reserve import ROOT, sha, source_sha

RESERVE = ROOT/'research/objective-bonus-body-asia-reservation.json'
FREEZE = ROOT/'research/objective-bonus-body-asia-freeze.json'
METADATA = ROOT/'data/research/diagnostics/v3-event-metadata/competition-511-15002-bonus-discovery.html'
EXPECTED = set(range(8182, 8194))


def reserve():
    if RESERVE.exists(): raise ValueError('Never replace prospective actor selection')
    data = json.loads(re.search(r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>',
        METADATA.read_text(encoding='utf-8'), re.S).group(1))['props']['pageProps']['pageData']
    if data['competition']['id'] != 511 or data['params']['phaseId'] != 15002:
        raise ValueError('Wrong official metadata event/phase')
    matches = sorted((m for step in data['phaseDetails']['steps'] for m in step['matches']),
                     key=lambda m:(m['date'], m['id']))
    if len(matches) != 28 or {m['id'] for m in matches if m.get('replayLink')} != EXPECTED:
        raise ValueError('Fixed metadata snapshot differs')
    old = json.loads((ROOT/'research/sources.json').read_text(encoding='utf-8'))['matches']
    if EXPECTED & {m.get('official_match_id') for m in old}:
        raise ValueError('Previously consumed research source')
    record = dict(event='Asia Pacific League Stage 2 - ASIA 2026', official_competition_id=511,
        phase_id=15002, created_at=datetime.now(timezone.utc).isoformat(),
        status='prospective_actor_reserve_no_replay_or_target_outcomes_opened',
        purpose='Fresh actor validation only, not Rating fit/final evaluation.',
        source='https://www.ubisoft.com/en-us/esports/rainbow-six/siege/competition/511/15002',
        metadata_sha256=sha(METADATA),
        selection='All12 currently linked official group-stage archives; first chronological8182 for small pipeline proof, then incremental batches. No objective-presence/bonus-health/actor selection.',
        scope='Entire named event reserved for actor validation. Later16 unavailable group matches and playoffs outside this fixed snapshot remain reserved; never silently extend the one-shot sample.',
        exposures='Official schedule/opponents/scores/replay URLs only; discovery web search returned no ASIA actor labels. No selected replay, objective total, round actor or Rating target inspected.',
        actors_inspected=False, ratings_inspected=False,
        matches=[dict(official_match_id=m['id'], date=m['date'], team_ids=sorted(t['id'] for t in m['teams']),
            official_scores=[sorted(t['score'] for t in g['teams']) for g in m['games']],
            archive_url=m.get('replayLink'), selected=bool(m.get('replayLink')),
            official_page=f"https://www.ubisoft.com/en-us/esports/rainbow-six/siege/match/{m['id']}") for m in matches])
    with RESERVE.open('x', encoding='utf-8') as out: out.write(json.dumps(record, indent=2)+'\n')
    print('Reserved ASIA Stage2:28scheduled/12linked, all actor outcomes unopened', flush=True)


def freeze():
    if FREEZE.exists(): raise ValueError('Never overwrite isolated hypothesis freeze')
    if not RESERVE.exists(): raise ValueError('Reserve before freezing')
    # Capture the actually imported observation/candidate dependency closure.
    files = {ROOT/'research/objective_bonus_body_reserve.py', ROOT/'research/objective_bonus_body_fresh_pipeline.py',
             ROOT/'research/objective_bonus_body_fresh_review.py', ROOT/'tests/test_objective_bonus_body_fresh.py',
             ROOT/'tests/test_objective_bonus_body_candidate.py', ROOT/'tests/fixtures/objective-bonus-health-plant.json'}
    for module in list(sys.modules.values()):
        filename = getattr(module, '__file__', None)
        if filename:
            path = Path(filename).resolve()
            if path.suffix == '.py' and path.is_relative_to(ROOT) and '.venv' not in path.parts:
                files.add(path)
    files.update((ROOT/'third_party/siege-dissect/dissect').glob('*.go'))
    files.update((ROOT/'research').glob('*.py'))
    for directory in ('r6stats/parser','r6stats/stats'):
        files.update((ROOT/directory).rglob('*.py'))
    binary_names = ['.local-tools/bin/siege-dissect-actors.exe', '.local-tools/bin/state-component-probe.exe',
                    '.local-tools/bin/actor-feedback-probe.exe', '.local-tools/bin/siege-dissect-objectives.exe',
                    '.local-tools/bin/siege-dissect.exe']
    record = dict(name='isolated_bonus_health_plant_completer_research_v1',
        created_at=datetime.now(timezone.utc).isoformat(),
        source_commit=subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip(),
        status='frozen_before_fresh_actor_outcomes', reservation_sha256=source_sha(RESERVE),
        candidate_rule='Every original plant guard first; fallback only known state1 on otherwise eligible uniquely bound completer. Direct temporal same-owner 4-byte health/base/ceiling/bonus fields at explicit record/interaction endpoints:0<base<health<=ceiling,ceiling-base20,positive finite bonus=(health-base)/base within1e-6. Original0/2 unchanged; state3/4/unknown/missing/sharing/cancel/death abstain. Defense unchanged.',
        acceptance=dict(min_complete_rounds=80, min_complete_maps=8, min_verified_plants=20,
            min_no_plant_controls=50, min_bonus_recoveries=3, min_distinct_bonus_maps=2,
            min_independently_constrained_bonus_actors=2, max_known_independent_wrong_actors=0,
            max_no_plant_false_positives=0, max_original_actor_changes=0,
            max_independent_objective_occurrence_conflicts=0, max_independent_aggregate_conflicts=0),
        evaluation_policy='Seal all12 replay predictions/physical hashes and label-free complete-map chronology before actor labels or official player objective totals. Preserve one-shot pass/fail/insufficiency, original public comparisons and separate primary/reviewed constraints. Insufficient bonus cases or unreviewed identities is not a pass. No automatic promotion; frozen Rating dependencies immutable.',
        identity_policy='Unique full10 nonzero stable profiles/round UIDs; explicit physical R## order; complete score-contiguous same-roster BO1/rehosts only. Primary labels need exact case-insensitive replay basename or separately independently verified profile history, never objective/KD/remaining-player matching.',
        source_hashes={str(p.relative_to(ROOT)).replace('\\','/'):source_sha(p) for p in sorted(files)},
        binary_hashes={name:sha(ROOT/name) for name in binary_names}, protected_hashes=snapshot(),
        rating_model_changed=False, production_deployed=False)
    with FREEZE.open('x', encoding='utf-8') as out: out.write(json.dumps(record, indent=2)+'\n')
    print('Frozen candidate, dependencies, observer binaries and prospective gates', flush=True)


if __name__ == '__main__':
    {'reserve':reserve, 'freeze':freeze}[sys.argv[1]]()
