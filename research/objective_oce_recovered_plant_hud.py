"""Preserve one consumed plant-after-recovery HUD control; never credit actors."""
import json
from pathlib import Path

from objective_bonus_body_oce_cohort import DATA
from objective_bonus_body_oce_review import verify_prelabel
from objective_oce_body_class_lifecycle import interval_observation
from objective_player_component_fields import observe
from objective_actor_liveness import feedback
from uah_guarded_actor_readonly import snapshot
from v3_final_reserve import ROOT, sha, source_sha


def main():
    verify_prelabel()
    protected = snapshot()
    video = ROOT / 'data/research/video/oce-20260616'
    metadata = json.loads((video/'day4.info.json').read_text(encoding='utf-8'))
    if (metadata['id'], metadata['channel_id'], metadata['upload_date']) != (
            'ZCQqoIH4O0U', 'UCWKHac5bjhsUtSnMDFCT-7A', '20260616'):
        raise ValueError('Official video identity differs')
    recovery_path = DATA/'consumed-body-class-hud-first-epoch-review.json'
    recovery = json.loads(recovery_path.read_text(encoding='utf-8'))
    before = [r for r in recovery['results'] if r['sample']['round'] == 1]
    if {r['raw_value'] for r in before if r['sample']['hud_label'] == 'downed'} != {3} or {
            r['raw_value'] for r in before if r['sample']['hud_label'] == 'active_after_recovery'} != {2}:
        raise ValueError('Preserved recovery evidence differs')
    prediction_path = DATA/'8082/replay-predictions.json'
    row = json.loads(prediction_path.read_text(encoding='utf-8'))['rounds'][0]
    c = row['proposed']['context']
    if row['proposed']['actor'] is not None or c['owner_observation'] != 'Proxy.RVL':
        raise ValueError('Expected still-unresolved unique timer owner')
    rec = ROOT / row['replay_path']
    if sha(rec) != row['replay_sha256']:
        raise ValueError('Sealed replay differs')
    state, owners, slots, fields = observe(rec)
    events = feedback(rec)['events']
    interval = interval_observation(c['owner_entity'], c['owner_observation'], c['start'], c['end'],
                                    owners, slots, fields, events)
    if (interval['class_hash'], interval['route_status'], {s['value'] for s in interval['states']}) != (
            'b529300b', 'unique_unchanged_typed_route', {2}):
        raise ValueError('Recorded unknown typed component interval differs')
    observations = {
        1202: 'R01/action8.41: Proxy has an ordinary active card; camera follows Pluto.',
        1205: 'R01/action5.40: named Proxy card explicitly says Planting the Defuser; camera follows ChefJeff.',
        1208: 'R01/action2.41: Proxy card still says Planting the Defuser; named Proxy is crouched at the site; camera follows ChefJeff.',
        1210: 'R01/action0.40: Proxy card still says Planting the Defuser while ChefJeff shoots Pluto.',
        1212: 'R01/postplant44.93: global DEFUSER IS PLANTED banner; Proxy card has returned to an active weapon card; camera follows downed ChefJeff.',
        1218: 'R01/postplant38.93: Sharkie card explicitly says Counter-Defusing, camera follows Sharkie; Proxy has been eliminated.'}
    record = dict(tier='consumed_independent_plant_after_recovery_control_not_bonus_or_prospective_acceptance',
                  official_match_id=8082, map='Nighthaven Labs', round=1, player='Proxy.RVL',
                  video_url='https://www.youtube.com/watch?v=ZCQqoIH4O0U&t=1205s',
                  metadata_sha256=sha(video/'day4.info.json'), prediction_sha256=sha(prediction_path),
                  recovery_review_sha256=sha(recovery_path), replay_sha256=row['replay_sha256'],
                  frames=[dict(seconds=s, observation=o, frame_sha256=sha(video/f'day4-{s}-299.jpg'))
                          for s, o in observations.items()], completing_timer_context=c, component_interval=interval,
                  source_sha256=source_sha(Path(__file__)), active_body_verified=False, actor_credit_proposed=False,
                  permanent_oce_result_sha256=sha(DATA/'one-shot-primary-result.json'), protected_hashes=protected)
    path = DATA/'consumed-plant-after-recovery-hud.json'
    if path.exists():
        if json.loads(path.read_text(encoding='utf-8')) != record:
            raise ValueError('Preserved plant-after-recovery control differs')
    else:
        path.write_text(json.dumps(record, indent=2)+'\n', encoding='utf-8')
    lines = ['# Consumed OCE Proxy plant after recovery', '',
             '[Official OCE Stage1 Day4 broadcast,1205s](https://www.youtube.com/watch?v=ZCQqoIH4O0U&t=1205s). '
             'Match8082, Nighthaven Labs R01. This map is consumed and remains in the permanently insufficient pool.', '',
             '| Video seconds | Independently visible evidence |', '| ---: | --- |']
    lines += [f'| {s} | {o} |' for s, o in observations.items()]
    lines += ['', 'The earlier separate ten-frame review shows Proxy visibly downed at1132/1138/1146 '
              'and active again at1148. His exact temporal declared UID route has raw3 then2 in those '
              'clock brackets. The completing plant interval uses the same unknown classb529300b body '
              'component with raw2 throughout, unique unchanged ownership and no preceding decoded death. '
              'The replay numeric health is20 at the interval endpoints; no numeric HUD health is claimed.', '',
              f'Completing timer start `{c["start"]}`, terminal `{c["end"]}` (`{c["terminal"]}`), '
              f'global plant anchor `{c["plant_offset"]}`. Frozen raw actor remains unresolved '
              f'(`{row["proposed"]["reason"]}` / `{c["body_reason"]}`). The direct owner Proxy is '
              'independently identified by the named planting card, rather than the camera subject or '
              'last killer ChefJeff. Plant occurrence follows; Sharkie later counter-defuses.', '',
              'This adds one independent consumed plant-owner/after-recovery observation beyond the '
              'seven sole-player objective constraints. It supports investigating older body/timer class '
              'compatibility, not a blanket active mapping, body1 bonus plant, fresh validation observation '
              'or prospective pass. Recovery mechanism/reviver, downing shooter, precise byte/frame '
              'alignment and universal enum semantics remain outside the evidence.', '',
              'No resolver/class allowlist, actor, statistics, Rating, SQLite/archive/public data, '
              'operator/action-start/kill behavior, historical grade, deployment, push or publish changed.', '']
    (ROOT/'research/output/objective-bonus-body-oce-plant-after-recovery.md').write_text('\n'.join(lines), encoding='utf-8')
    verify_prelabel()
    if snapshot() != protected:
        raise ValueError('Protected live files changed')
    print('Preserved one consumed Proxy planting/recovery control; actor remains unresolved')


if __name__ == '__main__':
    main()
