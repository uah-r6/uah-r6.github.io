"""Additive prelabel wrapper for permanent whole-map quality failures.

The original frozen acquisition, actor predicate and gates are unchanged. A
score-discontinuous map gets no reconstructed actor proposals. All twelve
selected sources remain visible in the sealed inventory and permanent result.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import re
import traceback

from objective_bonus_body_fresh_pipeline import DATA, acquire, verify
from objective_bonus_body_fresh_review import RESULT, evaluate_gates, primary_constraints
from objective_bonus_body_reserve import FREEZE
from v3_final_pipeline import cache_url
from v3_final_reserve import ROOT, sha, source_sha

EXTENSION=ROOT/'research/objective-bonus-body-asia-collection-addendum.json'
INVENTORY_SEAL=DATA/'prelabel-complete-inventory-seal.json'
QUALITY_FAILURES={
    'Duplicate physical round source', 'Full distinct stable10-player profiles and round UIDs required',
    'Rehost profile roster changed', 'BO1 map changed across physical fragments',
    'Incomplete/discontinuous completed score path', 'Official complete BO1 score/count differs',
    'Physical R## sources must be contiguous', 'Parser/physical count differs'}


def verify_extension():
    frozen,reservation=verify(); extension=json.loads(EXTENSION.read_text(encoding='utf-8'))
    if extension['original_freeze_sha256']!=source_sha(FREEZE) or extension['target_actors_opened']:
        raise ValueError('Invalid prelabel collection addendum')
    for name,digest in extension['source_hashes'].items():
        if source_sha(ROOT/name)!=digest: raise ValueError('Collection extension source changed:'+name)
    return frozen,reservation


def acquire_with_quality_record(source, frozen):
    out=DATA/str(source['official_match_id']); failure=out/'whole-map-quality-failure.json'
    if failure.exists(): return dict(status='whole_map_quality_failure',path=failure)
    try:
        acquire(source,frozen)
        return dict(status='complete_replay_prediction',path=out/'replay-predictions.json')
    except ValueError as exc:
        # Only explicit chronology/identity quality refusals can be recorded as
        # unavailable maps. Actor regression/control failures must abort.
        if str(exc) not in QUALITY_FAILURES: raise
        record=dict(official_match_id=source['official_match_id'],status='whole_map_quality_failure',
            freeze_sha256=source_sha(FREEZE),extension_sha256=source_sha(EXTENSION),
            reason=str(exc),traceback=traceback.format_exc(),actor_proposals_created=False,labels_read=False,
            physical_sources=[dict(path=str(p.relative_to(ROOT)).replace('\\','/'),sha256=sha(p))
                for p in sorted((ROOT/f"data/research/extracted/bonus-body-asia-{source['official_match_id']}").rglob('*.rec'))],
            interpretation='Whole fixed-selected map unavailable; no speculative deletion of completed/rolled-back physical rounds. Not an actor correctness failure or omitted sample.')
        out.mkdir(parents=True,exist_ok=True)
        with failure.open('x',encoding='utf-8') as dst: dst.write(json.dumps(record,indent=2)+'\n')
        print('Fresh quality refusal',source['official_match_id'],str(exc),flush=True)
        return dict(status='whole_map_quality_failure',path=failure)


def selected_inventory(reservation):
    entries=[]
    for source in (s for s in reservation['matches'] if s['selected']):
        mid=source['official_match_id'];out=DATA/str(mid)
        paths=[p for p in (out/'replay-predictions.json',out/'whole-map-quality-failure.json') if p.exists()]
        if len(paths)!=1: raise ValueError('Every selected map needs exactly one prediction OR whole-map quality refusal')
        p=paths[0];record=json.loads(p.read_text(encoding='utf-8'))
        if record['official_match_id']!=mid or record['freeze_sha256']!=source_sha(FREEZE) or record['labels_read']:
            raise ValueError('Label-free complete selected inventory differs')
        entries.append(dict(official_match_id=mid,status='whole_map_quality_failure' if 'status' in record else 'complete_replay_prediction',
                            path=str(p.relative_to(ROOT)).replace('\\','/'),sha256=sha(p)))
    if len(entries)!=12: raise ValueError('Fixed entire12-map snapshot required')
    return entries


def seal_inventory(frozen, reservation):
    entries=selected_inventory(reservation)
    if INVENTORY_SEAL.exists():
        seal=json.loads(INVENTORY_SEAL.read_text(encoding='utf-8'))
        if seal['entries']!=entries or seal['extension_sha256']!=source_sha(EXTENSION):
            raise ValueError('Never change sealed complete actor inventory')
        return seal
    if (DATA/'actor-targets-opened.json').exists(): raise ValueError('Cannot create prospective seal after labels')
    record=dict(status='all12_replay_or_quality_outcomes_sealed_before_any_actor_target',
        created_at=datetime.now(timezone.utc).isoformat(),freeze_sha256=source_sha(FREEZE),
        extension_sha256=source_sha(EXTENSION),entries=entries,protected_hashes=frozen['protected_hashes'])
    with INVENTORY_SEAL.open('x',encoding='utf-8') as dst: dst.write(json.dumps(record,indent=2)+'\n')
    print('Sealed fixed12-map inventory',dict(Counter(e['status'] for e in entries)),flush=True)
    return record


def evaluate():
    frozen,reservation=verify_extension()
    if RESULT.exists(): raise ValueError('Permanent fresh actor result exists; never reevaluate')
    seal=json.loads(INVENTORY_SEAL.read_text(encoding='utf-8'))
    if (seal['entries']!=selected_inventory(reservation) or seal['freeze_sha256']!=source_sha(FREEZE)
            or seal['extension_sha256']!=source_sha(EXTENSION)):
        raise ValueError('All12 sealed outcomes required before any independent actor target')
    marker=DATA/'actor-targets-opened.json'
    if not marker.exists():
        with marker.open('x',encoding='utf-8') as dst:dst.write(json.dumps(dict(
            status='actor_targets_consumed_no_ratings_opened',created_at=datetime.now(timezone.utc).isoformat(),
            freeze_sha256=source_sha(FREEZE),inventory_seal_sha256=sha(INVENTORY_SEAL)),indent=2)+'\n')
    sources={s['official_match_id']:s for s in reservation['matches'] if s['selected']}
    records=[];counts=Counter(selected_maps=len(seal['entries']))
    for entry in seal['entries']:
        mid=entry['official_match_id'];path=ROOT/entry['path'];prediction=json.loads(path.read_text(encoding='utf-8'))
        if entry['status']=='whole_map_quality_failure':
            records.append(dict(official_match_id=mid,status=entry['status'],reason=prediction['reason'],source_sha256=sha(path)))
            counts.update(quality_failed_maps=1);continue
        rounds=prediction['rounds']
        counts.update(maps=1,rounds=len(rounds),plants=sum(r['verified_plant'] for r in rounds),
            original_resolved=sum(bool(r['original']['actor']) for r in rounds),
            proposed_resolved=sum(bool(r['proposed']['actor']) for r in rounds),
            bonus_recoveries=sum(bool(r['proposed']['actor']) and not r['original']['actor'] for r in rounds),
            bonus_maps=int(any(bool(r['proposed']['actor']) and not r['original']['actor'] for r in rounds)),
            no_plant_controls=sum(not r['verified_plant'] for r in rounds),
            no_plant_false_positives=sum(not r['verified_plant'] and bool(r['proposed']['actor']) for r in rounds),
            original_actor_changes=sum(bool(r['original']['actor']) and r['proposed']!=r['original'] for r in rounds))
        page=DATA/str(mid)/'official-target.html';cache_url(sources[mid]['official_page'],page)
        payload=json.loads(re.search(r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>',page.read_text(encoding='utf-8'),re.S).group(1))['props']['pageProps']['pageData']['match']
        review=primary_constraints(prediction,payload,sources[mid])
        record=dict(official_match_id=mid,map=prediction['map'],rounds=len(rounds),status='complete_replay_prediction',review=review,
            source=sources[mid]['official_page'],source_sha256=sha(page),prediction_sha256=sha(path))
        records.append(record)
        counts.update(primary_reviewed_maps=int(review['status']=='primary_complete_unique_identity'),
            primary_identity_blocked_maps=int(review['status']!='primary_complete_unique_identity'),
            independent_bonus_agreements=sum(c['bonus_recovery'] and c['verdict']=='agreement' for c in review['constraints']),
            independent_wrong_actors=sum(c['verdict']=='disagreement' for c in review['constraints']),
            aggregate_conflicts=len(review['aggregate_conflicts']),occurrence_conflicts=len(review['occurrence_conflicts']))
        print('Fresh independent review',mid,review['status'],'constraints',len(review['constraints']),flush=True)
    gates=evaluate_gates(counts,frozen['acceptance']);verify_extension()
    result=dict(status='permanent_fresh_actor_result_event_now_consumed',created_at=datetime.now(timezone.utc).isoformat(),
        counts=dict(counts),gates=gates,records=records,freeze_sha256=source_sha(FREEZE),
        inventory_seal_sha256=sha(INVENTORY_SEAL),extension_sha256=source_sha(EXTENSION),
        original_public_comparison='Unopened primary-only evaluation; any later public/reviewed comparison separate.',
        ratings_read=False,production_deployed=False,protected_hashes=frozen['protected_hashes'])
    with RESULT.open('x',encoding='utf-8') as dst:dst.write(json.dumps(result,indent=2)+'\n')
    lines=['# Fresh ASIA bonus-health actor validation','',f'Frozen gate result: **{gates["status"]}**.',
        f'Counts: `{dict(counts)}`.',f'Failures: `{gates["failures"]}`; insufficient: `{gates["insufficient"]}`.',
        '', 'Every selected map remains in the sealed prelabel inventory, including whole-map quality failures. '
        'No score-discontinuous replay is repaired by dropping a completed physical round. Original actor predicate/gates unchanged. '
        'Independent single-player constraints and aggregate consistency are separate. Unbound primary identities abstain. '
        'The event is now consumed for actor validation; no Rating target/model/SQLite/archive/public change or promotion.', '',
        '| Official match | Map | Rounds | Status |','| --- | --- | ---: | --- |']
    for r in records:lines.append(f"| {r['official_match_id']} | {r.get('map','unavailable')} | {r.get('rounds','unavailable')} | {r.get('review',{}).get('status',r['status'])} |")
    lines+=['','Frozen minimum3bonus cases on2maps and2independent bonus agreements cannot be waived after results. '
        'Original public labels remain unopened; independent primary disagreement is not forced into agreement. '
        'No push/publish/deployment; both failed v3 finals and livev2 remain unchanged.','']
    (ROOT/'research/output/objective-bonus-body-fresh-asia.md').write_text('\n'.join(lines),encoding='utf-8')
    print('Permanent fresh actor result',dict(counts),gates,flush=True)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--limit',type=int,default=1);parser.add_argument('--seal',action='store_true');parser.add_argument('--evaluate',action='store_true');args=parser.parse_args()
    if args.evaluate: evaluate();return
    frozen,reservation=verify_extension()
    if (DATA/'actor-targets-opened.json').exists(): raise ValueError('Collection cannot change after targets opened')
    for source in [s for s in reservation['matches'] if s['selected']][:args.limit]:acquire_with_quality_record(source,frozen)
    if args.seal:seal_inventory(frozen,reservation)
    verify_extension()


if __name__=='__main__':main()
