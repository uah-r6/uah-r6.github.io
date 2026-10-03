"""Additive consumed HUD clock projection; preserve the initial strict result.

An existing action marker starts the scope. The first subsequent clock increase
ends this diagnostic's first countdown epoch, even if the serialized plant
anchor follows later. This never changes parser action detection or round data.
"""
import json
from collections import Counter
from pathlib import Path

from objective_oce_body_class_hud_review import LABELS, action_clock_window, classify_observation
from objective_oce_body_class_lifecycle import interval_observation
from objective_bonus_body_oce_cohort import DATA
from objective_bonus_body_oce_review import verify_prelabel
from objective_oce_consumed_identity_review import verify as verify_consumed
from objective_player_component_fields import observe
from objective_actor_liveness import feedback
from objective_score_structure import observe as observe_clock
from uah_guarded_actor_readonly import snapshot
from v3_final_reserve import ROOT, sha, source_sha

OUTPUT = DATA / 'consumed-body-class-hud-first-epoch-review.json'


def first_epoch_window(ticks, action_start, anchor_end, value):
    if not action_start or not anchor_end or anchor_end <= action_start:
        return None, dict(reason='missing_explicit_action_bounds')
    rows = [t for t in ticks if action_start <= t['offset'] < anchor_end and 0 <= t['value'] <= 180]
    reset = next((b for a, b in zip(rows, rows[1:]) if b['value'] > a['value']), None)
    end = reset['offset'] if reset else anchor_end
    window, reason = action_clock_window(ticks, action_start, end, value)
    return window, dict(reason=reason, original_anchor_end=anchor_end,
                        first_countdown_end=end, observed_reset=reset,
                        action_marker_changed=False, round_omitted=False)


def main():
    verify_prelabel()
    verify_consumed()
    protected = snapshot()
    strict_path = DATA / 'consumed-body-class-hud-review.json'
    strict = json.loads(strict_path.read_text(encoding='utf-8'))
    labels = json.loads(LABELS.read_text(encoding='utf-8'))
    if strict['labels_sha256'] != source_sha(LABELS):
        raise ValueError('Independent labels changed')
    prediction_path = DATA / '8082/replay-predictions.json'
    if sha(prediction_path) != strict['prediction_sha256']:
        raise ValueError('Sealed predictions changed')
    for s in labels['samples']:
        if sha(ROOT / s['frame_path']) != s['frame_sha256']:
            raise ValueError('Independent frame changed')
    prediction = json.loads(prediction_path.read_text(encoding='utf-8'))
    cache, results = {}, []
    for original in strict['results']:
        sample = original['sample']
        number = sample['round']
        if number not in cache:
            row = next(r for r in prediction['rounds'] if r['round'] == number)
            rec = ROOT / row['replay_path']
            if sha(rec) != row['replay_sha256']:
                raise ValueError('Physical replay changed')
            state, owners, slots, fields = observe(rec)
            events = feedback(rec)['events']
            clocks = [t for t in observe_clock(rec)['fields'] if t['kind'] == 'clock']
            start = state['header'].get('actionPhaseStartOffset')
            end = min((o['plantStateOffset'] for o in row['occurrences'] if o['kind'] == 'plant'),
                      default=max(t['offset'] for t in clocks) + 1)
            cache[number] = owners, slots, fields, events, clocks, start, end
        owners, slots, fields, events, clocks, start, end = cache[number]
        window, scope = first_epoch_window(clocks, start, end, sample['clock_seconds'])
        owner = [o for o, name in owners.items() if name == sample['player']]
        interval, raw = None, None
        status = scope['reason']
        if window and len(owner) == 1:
            interval = interval_observation(owner[0], sample['player'], *window, owners, slots, fields, events)
            raw, status = classify_observation(interval)
        elif len(owner) != 1:
            status = 'exact_UID_owner_missing_or_ambiguous'
        if original['raw_value'] is not None and raw != original['raw_value']:
            raise ValueError('An already observed raw value changed')
        results.append(dict(sample=sample, initial_strict_raw=original['raw_value'],
                            initial_strict_reason=original['observation_status'], raw_value=raw,
                            observation_status=status, window=window, interval=interval,
                            clock_scope=scope, action_marker=start, active_body_verified=False,
                            actor_credit_proposed=False))
    groups = Counter((r['sample']['hud_label'], r['raw_value']) for r in results)
    record = dict(tier='consumed_additive_first_clock_epoch_diagnostic_not_parser_change',
                  initial_strict_result_sha256=sha(strict_path), labels_sha256=source_sha(LABELS),
                  prediction_sha256=sha(prediction_path), source_sha256=source_sha(Path(__file__)),
                  results=results, unresolved=sum(r['raw_value'] is None for r in results),
                  groups=[dict(hud=k[0], raw_value=k[1], frames=v) for k, v in groups.items()],
                  original_strict_unresolved=strict['unresolved'], action_marker_changed=False,
                  actor_credit_proposed=False, candidate_changed=False, protected_hashes=protected)
    record = json.loads(json.dumps(record))
    if OUTPUT.exists():
        if json.loads(OUTPUT.read_text(encoding='utf-8')) != record:
            raise ValueError('Preserved additive clock comparison differs')
    else:
        OUTPUT.write_text(json.dumps(record, indent=2)+'\n', encoding='utf-8')
    lines = ['# Consumed OCE HUD: scoped first clock epoch follow-up', '',
             '[Official OCE Day4 broadcast](https://www.youtube.com/watch?v=ZCQqoIH4O0U&t=1132s), '
             'same preserved ten frames/labels as the initial strict report, two consumed Nighthaven rounds.', '',
             'The initial comparison leaves five R01frames unresolved: a postplant clock reset is written before '
             'the existing serialized plant occurrence anchor, so its conservative whole-range monotonicity '
             'guard refuses every sample in the range. That initial JSON is preserved byte-for-byte. '
             'This additive diagnostic bounds only the first countdown following the unchanged existing action marker. '
             'Its end is the first observed clock increase, or the existing anchor if no increase occurs. '
             'It never selects a later phase, omits a physical round or changes action-start/operator parsing.', '',
             '| Video seconds | Round / player | HUD clock | Named HUD observation | Raw value | Original strict raw |',
             '| ---: | --- | --- | --- | --- | --- |']
    for r in results:
        s = r['sample']
        lines.append(f'| {s["seconds"]} | R{s["round"]:02d}/{s["player"]} | '
                     f'{s["clock_seconds"] // 60}:{s["clock_seconds"] % 60:02d} | '
                     f'{s["hud_label"]} | {r["raw_value"]} | {r["initial_strict_raw"]} |')
    lines += ['', f'Counts: `{record["groups"]}`; unresolved `{record["unresolved"]}`. '
              'Already projected R07values remain unchanged.', '',
              'The two named downed-cross/recovery sequences corroborate raw3 during visible DBNO and raw2 '
              'after recovery on classb529300b in these consumed cases. Raw0 accompanies active cards; raw4 '
              'accompanies an eliminated WATCHING card. Same-owner typed route checks and stable state across '
              'the full displayed second are retained. No exact within-second synchronization, numeric HUD health, '
              'downer identity, complete reviver identity, universal enum, disconnect behavior or bonus-health '
              'plant evidence is established. Selection follows exposed consumed transitions and is not fresh.', '',
              'The conservative production class remains0c98c63f. No old outcome/actor/gate is regraded, no '
              'bonus candidate is changed and no actor is credited. Original ASIA/OCE insufficient and both '
              'failed v3 finals remain permanent. SQLite, archives, public JSON, live Rating/operator/kill logic '
              'and website remain unchanged; no push/publish.', '']
    (ROOT/'research/output/objective-bonus-body-oce-body-clock-scope.md').write_text('\n'.join(lines), encoding='utf-8')
    verify_prelabel()
    verify_consumed()
    if snapshot() != protected:
        raise ValueError('Protected live files changed')
    print('Consumed first-epoch diagnostic', record['groups'], 'unresolved', record['unresolved'])


if __name__ == '__main__':
    main()
