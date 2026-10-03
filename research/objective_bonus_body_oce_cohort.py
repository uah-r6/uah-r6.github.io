"""Fixed two-event OCE actor cohort; cached collection before any actor labels.

Reuses the unchanged ASIA BO1 collector in an isolated CLI process with an
explicit data/freeze context. Original functions, candidate and guards are
unchanged. Its legacy ASIA event label/extraction prefix is not authoritative;
the frozen cohort reservation supplies source provenance.
"""
import argparse
from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import traceback

import objective_bonus_body_fresh_pipeline as collector
from objective_bonus_body_fresh_collection import QUALITY_FAILURES
from objective_bonus_body_asia_identity_review import verify_preserved
from uah_guarded_actor_readonly import snapshot
from v3_final_reserve import ROOT, sha, source_sha

DATA=ROOT/'data/research/objective-bonus-body-oce-cohort'
RESERVATION=ROOT/'research/objective-bonus-body-oce-reservation.json'
FREEZE=ROOT/'research/objective-bonus-body-oce-freeze.json'
EVENTS=[(507,14998),(512,15003)]
MAX_EVENTS=2
MAX_MAPS=56


def schedule(path):
    match=re.search(r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>',path.read_text(encoding='utf-8'),re.S)
    return json.loads(match.group(1))['props']['pageProps']['pageData']


def select_events(events, consumed_ids):
    if len(events)>MAX_EVENTS:raise ValueError('Predeclared event ceiling exceeded')
    selected=[]
    for event in events:
        cid=event['competition']['id']
        matches=[m for step in event['phaseDetails']['steps'] for m in step['matches']]
        for m in sorted(matches,key=lambda m:(m['date'],m['id'])):
            if m['id'] in consumed_ids:raise ValueError('Consumed event match cannot become fresh')
            if m.get('replayLink'):
                if len(m['games'])!=1:raise ValueError('Fixed OCE cohort supports complete BO1 metadata only')
                selected.append(dict(official_match_id=m['id'],competition_id=cid,date=m['date'],
                    team_ids=sorted(t['id'] for t in m['teams']),
                    official_scores=[sorted(t['score'] for t in m['games'][0]['teams'])],
                    archive_url=m['replayLink'],selected=True,
                    official_page=f'https://www.ubisoft.com/en-us/esports/rainbow-six/siege/match/{m["id"]}'))
    selected.sort(key=lambda m:(m['date'],m['official_match_id']))
    if len(selected)>MAX_MAPS or len({m['official_match_id'] for m in selected})!=len(selected):
        raise ValueError('Map ceiling or unique metadata selection violated')
    return selected


@contextmanager
def collection_context(data, freeze):
    if data.resolve()==collector.DATA.resolve():raise ValueError('Never reuse consumed ASIA output')
    old_data,old_freeze=collector.DATA,collector.FREEZE
    collector.DATA,collector.FREEZE=data,freeze
    try:yield
    finally:collector.DATA,collector.FREEZE=old_data,old_freeze


def reserve():
    original, _, _=verify_preserved()
    if RESERVATION.exists() or FREEZE.exists():raise ValueError('Never replace a prospective cohort')
    events=[];metadata={}
    consumed=set()
    for p in (ROOT/'research').glob('*reservation.json'):
        obj=json.loads(p.read_text(encoding='utf-8'))
        consumed.update(m['official_match_id'] for m in obj.get('matches',[]) if 'official_match_id' in m)
    consumed.update(m.get('official_match_id') for m in json.loads((ROOT/'research/sources.json').read_text(encoding='utf-8'))['matches'])
    for cid,phase in EVENTS:
        path=ROOT/f'data/research/diagnostics/v3-event-metadata/competition-{cid}-{phase}-sequential-discovery.html'
        event=schedule(path)
        if event['competition']['id']!=cid or event['params']['phaseId']!=phase:raise ValueError('Official event/phase differs')
        events.append(event);metadata[path.relative_to(ROOT).as_posix()]=sha(path)
    selected=select_events(events,consumed)
    record=dict(status='prospective_fixed_multi_event_actor_reservation',created_at=datetime.now(timezone.utc).isoformat(),
        events=[dict(competition_id=e['competition']['id'],event=e['competition']['name'],
                     phase_id=e['params']['phaseId'],scheduled=sum(len(s['matches']) for s in e['phaseDetails']['steps'])) for e in events],
        maximum_events=MAX_EVENTS,maximum_maps=MAX_MAPS,selected_maps=len(selected),metadata_hashes=metadata,matches=selected,
        selection='All currently linked archives from the fixed OCE Stage1 and Stage2 group-stage snapshots, chronological date/id order; no actor/bonus/Rating selection.',
        stopping='Collect every selected source before actor labels regardless of observed bonus frequency. No early success, optional outcome-driven event additions or retries. One pooled final evaluation.',
        unavailable='Unlinked scheduled matches remain visible through metadata; later links/playoffs outside this snapshot are not silently added.',
        acceptance=original['acceptance'],identity_policy=original['identity_policy'],
        quality_policy='Same full10 stable nonzero profile/UID, continuous BO1 score, physical R## and unchanged occurrence/body/ownership guards. Whole-map declared quality refusals preserved; no round/player invention.',
        review_policy='Seal complete predictions OR whole-map quality refusals; then independently bind all ten official identities without stats/actor matching and seal aliases; only then open objective ground truth once. Unbound maps unreviewed; individual evidence cannot satisfy acceptance.',
        freshness='No OCE selected replays/actor targets inspected. Metadata-only schedule/map counts/scores/URLs projected. CNL discovery inspected metadata only here; earlier CNLStage2 Rating snippets remain exposed and are not part of this actor cohort.',
        actor_labels_read=False,ratings_read=False,production_deployed=False)
    RESERVATION.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    sources=dict(original['source_hashes'])
    for name in ('research/objective_bonus_body_oce_cohort.py','tests/test_objective_bonus_body_oce_cohort.py',
                 'research/objective_bonus_body_fresh_collection.py','research/objective_bonus_body_asia_identity_review.py'):
        sources[name]=source_sha(ROOT/name)
    frozen=dict(status='frozen_before_any_selected_OCE_replay_or_actor_target',
        source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        created_at=datetime.now(timezone.utc).isoformat(),reservation_sha256=source_sha(RESERVATION),
        source_hashes=sources,binary_hashes=original['binary_hashes'],protected_hashes=original['protected_hashes'],
        acceptance=original['acceptance'],candidate_rule=original['candidate_rule'],
        legacy_collector_context='Only DATA/FREEZE module globals scoped and restored; legacy literal ASIA event label/extraction prefix ignored in favor of this reservation provenance.',
        production_deployed=False)
    FREEZE.write_text(json.dumps(frozen,indent=2)+'\n',encoding='utf-8')
    lines=['# Fixed prospective bonus-health actor cohort: OCE Stage 1 + Stage 2','',
           f'{len(selected)} linked BO1 archives selected across two fixed events, from 56 scheduled maps. Maximum2events/56maps. '
           'All linked metadata sources are selected; no objective presence, bonus frequency or correctness filtering.','',
           'Collect every selected source in chronological date/ID order. Seal predictions or explicit whole-map quality refusals. '
           'Independently resolve identities and seal the evidence before actor ground truth. Evaluate the pooled cohort exactly once. '
           'No early success stop or extra-event chasing; insufficient rare cases stays insufficient.','',
           f'Unchanged acceptance: `{original["acceptance"]}`. Zero known wrong credits, no-plant false positives, old actor changes, '
           'independent occurrence or aggregate conflicts allowed. At least3bonus cases on2maps and2independently constrained bonus actors. '
           'Full10 independent official identities mandatory for acceptance review.','',
           'Unknown/DBNO/dead/ambiguous/body-sharing/canceled timer data abstains. Original action/operator/kill/statistics/Rating code remains frozen. '
           'ASIA and earlier cohorts stay consumed. This is actor-only validation, not a fresh Rating experiment. No automatic promotion.','',
           'Sources: [OCE Stage1 official metadata](https://www.ubisoft.com/en-us/esports/rainbow-six/siege/competition/507/14998), '
           '[OCE Stage2 official metadata](https://www.ubisoft.com/en-us/esports/rainbow-six/siege/competition/512/15003).','']
    (ROOT/'research/output/objective-bonus-body-oce-prospective-plan.md').write_text('\n'.join(lines),encoding='utf-8')
    print('Reserved/frozen',len(selected),'maps',[(e['competition']['id'],sum(bool(m.get('replayLink')) for s in e['phaseDetails']['steps'] for m in s['matches'])) for e in events])


def verify():
    verify_preserved()
    frozen=json.loads(FREEZE.read_text(encoding='utf-8'));reservation=json.loads(RESERVATION.read_text(encoding='utf-8'))
    if source_sha(RESERVATION)!=frozen['reservation_sha256']:raise ValueError('Fixed cohort reservation changed')
    for name,digest in frozen['source_hashes'].items():
        if source_sha(ROOT/name)!=digest:raise ValueError('Cohort source changed:'+name)
    for name,digest in frozen['binary_hashes'].items():
        if sha(ROOT/name)!=digest:raise ValueError('Cohort binary changed:'+name)
    if snapshot()!=frozen['protected_hashes']:raise ValueError('Protected live data changed')
    for name,digest in reservation['metadata_hashes'].items():
        if sha(ROOT/name)!=digest:raise ValueError('Metadata snapshot changed')
    return frozen,reservation


def acquire(source,frozen):
    mid=source['official_match_id'];out=DATA/str(mid);failure=out/'whole-map-quality-failure.json'
    if failure.exists():
        record=json.loads(failure.read_text(encoding='utf-8'))
        if record['freeze_sha256']!=source_sha(FREEZE):raise ValueError('Cached failure freeze differs')
        return failure
    with collection_context(DATA,FREEZE):
        try:collector.acquire(source,frozen)
        except ValueError as exc:
            if str(exc) not in QUALITY_FAILURES:raise
            record=dict(status='whole_map_quality_failure',official_match_id=mid,reason=str(exc),traceback=traceback.format_exc(),
                        freeze_sha256=source_sha(FREEZE),labels_read=False,ratings_read=False)
            out.mkdir(parents=True,exist_ok=True);failure.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
            print('Whole-map quality refusal',mid,str(exc),flush=True);return failure
    return out/'replay-predictions.json'


def inventory(reservation):
    entries=[];counts=Counter()
    for source in reservation['matches']:
        out=DATA/str(source['official_match_id']);paths=[p for p in (out/'replay-predictions.json',out/'whole-map-quality-failure.json') if p.exists()]
        if len(paths)!=1:raise ValueError('Exactly one complete outcome required for every selected source')
        path=paths[0];obj=json.loads(path.read_text(encoding='utf-8'))
        if obj['freeze_sha256']!=source_sha(FREEZE) or obj['labels_read']:raise ValueError('Outcome freeze/label status differs')
        entries.append(dict(official_match_id=source['official_match_id'],path=path.relative_to(ROOT).as_posix(),sha256=sha(path)))
        if 'rounds' in obj:
            rows=obj['rounds'];counts.update(maps=1,rounds=len(rows),plants=sum(r['verified_plant'] for r in rows),
                bonus_recoveries=sum(bool(r['proposed']['actor']) and not r['original']['actor'] for r in rows),
                bonus_maps=int(any(bool(r['proposed']['actor']) and not r['original']['actor'] for r in rows)),
                no_plant_controls=sum(not r['verified_plant'] for r in rows))
        else:counts['quality_failed_maps']+=1
    return entries,dict(counts)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--reserve',action='store_true');parser.add_argument('--limit',type=int,default=1);parser.add_argument('--seal',action='store_true');args=parser.parse_args()
    if args.reserve:reserve();return
    frozen,reservation=verify()
    if (DATA/'actor-targets-opened.json').exists() or (DATA/'prelabel-inventory-seal.json').exists():
        raise ValueError('Collection already sealed/consumed; do not change outcomes')
    for source in reservation['matches'][:args.limit]:acquire(source,frozen)
    if args.seal:
        entries,counts=inventory(reservation);DATA.mkdir(parents=True,exist_ok=True)
        seal=dict(status='all_selected_OCE_outcomes_sealed_before_actor_targets',entries=entries,counts=counts,
                  freeze_sha256=source_sha(FREEZE),created_at=datetime.now(timezone.utc).isoformat())
        (DATA/'prelabel-inventory-seal.json').write_text(json.dumps(seal,indent=2)+'\n',encoding='utf-8')
        print('Full fixed cohort sealed',counts,flush=True)
    verify()


if __name__=='__main__':main()
