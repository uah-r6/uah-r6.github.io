"""Compare preserved consumed manual HUD labels with typed raw component values.

Only existing parser action markers and clock fields align displayed seconds.
Missing/ambiguous clock epochs or a raw transition within the sampled second
stay unresolved. This helper assigns no liveness enum or actor credit.
"""
import json
from pathlib import Path

from objective_bonus_body_oce_cohort import DATA
from objective_bonus_body_oce_review import verify_prelabel
from objective_oce_body_class_lifecycle import interval_observation, UNKNOWN_CLASS
from objective_oce_consumed_identity_review import verify as verify_consumed
from objective_player_component_fields import observe
from objective_score_structure import observe as observe_clock
from objective_actor_liveness import feedback
from uah_guarded_actor_readonly import snapshot
from v3_final_reserve import ROOT, sha, source_sha

LABELS = ROOT / 'research/objective-oce-body-class-hud-labels.json'
CHECKPOINT = ROOT / 'research/objective-oce-consumed-lifecycle-checkpoint.json'
OUTPUT = DATA / 'consumed-body-class-hud-review.json'


def action_clock_window(ticks, action_start, action_end, value):
    if not action_start or not action_end or action_end <= action_start:
        return None, 'missing_explicit_action_bounds'
    rows = [t for t in ticks if action_start <= t['offset'] < action_end and 0 <= t['value'] <= 180]
    if any(b['value'] > a['value'] for a, b in zip(rows, rows[1:])):
        return None, 'clock_reset_inside_action_bounds'
    same = [t for t in rows if t['value'] == value]
    if not same:
        return None, 'displayed_clock_tick_missing'
    following = next((t for t in rows if t['offset'] > same[-1]['offset'] and t['value'] < value), None)
    if following is None or following['value'] != value - 1:
        return None, 'adjacent_next_clock_tick_missing'
    return (same[0]['offset'], following['offset'] - 1), 'explicit_displayed_action_second_interval'


def classify_observation(interval):
    """Return a raw observation status, never an active/dead classification."""
    if interval['route_status'] != 'unique_unchanged_typed_route':
        return None, 'component_route_uncertain'
    if interval.get('class_hash') != UNKNOWN_CLASS:
        return None, 'different_component_class'
    if not interval.get('prior_state_present'):
        return None, 'missing_prior_raw_state'
    values = {s['value'] for s in interval['states']}
    if len(values) != 1:
        return None, 'raw_transition_within_displayed_second'
    return next(iter(values)), 'stable_raw_value_over_displayed_second'


def main():
    verify_prelabel()
    verify_consumed()
    protected = snapshot()
    checkpoint = json.loads(CHECKPOINT.read_text(encoding='utf-8'))
    for name, digest in checkpoint['result_hashes'].items():
        if sha(ROOT / name) != digest:
            raise ValueError('Preserved consumed diagnostic changed')
    for name, digest in checkpoint['source_hashes'].items():
        if source_sha(ROOT / name) != digest:
            raise ValueError('Consumed diagnostic source changed')
    labels = json.loads(LABELS.read_text(encoding='utf-8'))
    metadata_path = ROOT / 'data/research/video/oce-20260616/day4.info.json'
    if sha(metadata_path) != labels['metadata_sha256']:
        raise ValueError('Official video metadata changed')
    metadata = json.loads(metadata_path.read_text(encoding='utf-8'))
    if (metadata['id'], metadata['channel_id'], metadata['upload_date']) != (
            'ZCQqoIH4O0U', 'UCWKHac5bjhsUtSnMDFCT-7A', '20260616'):
        raise ValueError('Official broadcast identity differs')
    prediction_path = DATA / '8082/replay-predictions.json'
    prediction = json.loads(prediction_path.read_text(encoding='utf-8'))
    round_cache, results = {}, []
    for sample in labels['samples']:
        if sha(ROOT / sample['frame_path']) != sample['frame_sha256']:
            raise ValueError('Manually inspected frame changed')
        number = sample['round']
        row = next(r for r in prediction['rounds'] if r['round'] == number)
        rec = ROOT / row['replay_path']
        if sha(rec) != row['replay_sha256']:
            raise ValueError('Sealed physical replay differs')
        if number not in round_cache:
            state, owners, slots, fields = observe(rec)
            events = feedback(rec)['events']
            clocks = [f for f in observe_clock(rec)['fields'] if f['kind'] == 'clock']
            round_cache[number] = state, owners, slots, fields, events, clocks
        state, owners, slots, fields, events, clocks = round_cache[number]
        action_start = state['header'].get('actionPhaseStartOffset')
        # The existing occurrence anchor bounds this diagnostic's action epoch.
        # No new action-start detector or objective occurrence is inferred.
        action_end = min((o['plantStateOffset'] for o in row['occurrences'] if o['kind'] == 'plant'),
                         default=max(t['offset'] for t in clocks) + 1)
        window, reason = action_clock_window(clocks, action_start, action_end, sample['clock_seconds'])
        owner = [o for o, name in owners.items() if name == sample['player']]
        result = dict(sample=sample, replay_sha256=row['replay_sha256'], physical_round=row['physical_round'],
                      action_marker=action_start, window=window, clock_status=reason,
                      active_body_verified=False, actor_credit_proposed=False)
        if window and len(owner) == 1:
            interval = interval_observation(owner[0], sample['player'], *window, owners, slots, fields, events)
            raw, status = classify_observation(interval)
            result.update(interval=interval, raw_value=raw, observation_status=status)
        else:
            result.update(raw_value=None, observation_status=reason if not window else 'exact_UID_owner_missing_or_ambiguous')
        results.append(result)
    from collections import Counter
    groups = Counter((r['sample']['hud_label'], r['raw_value']) for r in results)
    record = dict(tier='consumed_independent_HUD_corroboration_not_prospective_acceptance',
                  labels_sha256=source_sha(LABELS), prediction_sha256=sha(prediction_path),
                  lifecycle_checkpoint_sha256=source_sha(CHECKPOINT), source_sha256=source_sha(Path(__file__)),
                  results=results, hud_raw_counts=[dict(hud=k[0], raw_value=k[1], frames=v) for k, v in groups.items()],
                  unresolved=sum(r['raw_value'] is None for r in results), semantics_promoted=False,
                  candidate_changed=False, permanent_oce_result_sha256=sha(DATA/'one-shot-primary-result.json'),
                  protected_hashes=protected)
    # JSON round-trips tuples as lists; canonicalize before comparing a cache.
    record = json.loads(json.dumps(record))
    if OUTPUT.exists():
        if json.loads(OUTPUT.read_text(encoding='utf-8')) != record:
            raise ValueError('Preserved independent consumed HUD comparison differs')
    else:
        OUTPUT.write_text(json.dumps(record, indent=2)+'\n', encoding='utf-8')
    lines = ['# Consumed OCE unknown component: independent DBNO/recovery HUD controls', '',
             '[Official Rainbow Six Esports OCE Stage1 Day4 broadcast](https://www.youtube.com/watch?v=ZCQqoIH4O0U), '
             'uploaded2026-06-16, exact channelUCWKHac5bjhsUtSnMDFCT-7A. Match8082 ManLFO–Rival, Nighthaven Labs.', '',
             'Ten manually inspected frames from two already-consumed raw3-to2 observations. Named player cards '
             'supply independent labels; the camera subject is explicitly not used as the target identity. '
             'Labels and frame hashes were preserved before this interval projection. Selection was informed by '
             'consumed raw transitions and is not blind, representative or prospective.', '',
             '| Video seconds | Round / named player | HUD action clock | Visible status | Stable raw value | Interval outcome |',
             '| ---: | --- | --- | --- | --- | --- |']
    for r in results:
        s = r['sample']
        lines.append(f'| {s["seconds"]} | R{s["round"]:02d}/{s["player"]} | '
                     f'{s["clock_seconds"] // 60}:{s["clock_seconds"] % 60:02d} | '
                     f'{s["hud_label"]} | {r["raw_value"]} | {r["observation_status"]} |')
    lines += ['', f'Grouped observations: `{record["hud_raw_counts"]}`; unresolved frames `{record["unresolved"]}`.', '',
              '## Interpretation and limits', '',
              'Existing parser action markers and occurrence offsets bound the action clock epoch. Each displayed '
              'second is bracketed by adjacent clock ticks; missing ticks, a reset or raw transition within that '
              'second abstains. Typed component ownership is checked throughout the bracket, at retained property '
              'offsets and every declaration change. Byte/frame synchronization within a displayed second is not claimed.', '',
              'The downed crosses and later active weapon cards corroborate two recovery sequences on classb529300b. '
              'The visual evidence supports raw3 as downed and raw2 as active in these cases; it does not authorize '
              'a universal enum or class mapping. It does not establish numeric HUD health, the downing shooter, '
              'which player performed the complete revival, bonus-health plant semantics or disconnect behavior. '
              'No component is approved because its HP is positive.', '',
              'All frozen candidates and original ASIA/OCE classifications remain unchanged. These are DBNO/recovery '
              'compatibility controls, not new bonus-health actor observations or corrections. The seven primary '
              'plant-owner supports remain consumed and the31older plant actors remain unresolved in production. '
              'No SQLite/archive/public/Rating/operator/kill change, push or publish.', '']
    (ROOT/'research/output/objective-bonus-body-oce-body-class-hud.md').write_text('\n'.join(lines), encoding='utf-8')
    verify_prelabel()
    verify_consumed()
    if snapshot() != protected:
        raise ValueError('Protected live files changed')
    print('Independent consumed HUD projection', record['hud_raw_counts'], 'unresolved', record['unresolved'])


if __name__ == '__main__':
    main()
