"""Consumed older-class timer terminal inventory; no actor or state promotion."""
from collections import Counter
import json
from pathlib import Path

from objective_bonus_body_oce_cohort import DATA
from objective_bonus_body_oce_review import verify_prelabel
from objective_completer_consumed_audit import observation
from objective_player_component_fields import observe
from objective_actor_liveness import feedback
from objective_disable_owner_candidate import run_end
from objective_oce_body_class_lifecycle import BUILD, interval_observation
from uah_guarded_actor_readonly import snapshot
from v3_final_reserve import ROOT, sha, source_sha

OUTPUT = DATA / 'consumed-older-class-timer-controls.json'


def main():
    _, _, seal = verify_prelabel()
    protected = snapshot()
    rows, totals, terminals = [], Counter(), Counter()
    for entry in seal['entries']:
        prediction = json.loads((ROOT / entry['path']).read_text(encoding='utf-8'))
        if 'rounds' not in prediction:
            continue
        for r in prediction['rounds']:
            if r['build'] != BUILD:
                continue
            rec = ROOT / r['replay_path']
            if sha(rec) != r['replay_sha256']:
                raise ValueError('Sealed replay differs')
            state, owners, slots, fields = observe(rec)
            events = feedback(rec)['events']
            observed = observation(state['header'], owners, slots, fields)
            totals.update(rounds=1, rounds_without_plant=int(not r['verified_plant']),
                          orphan_timer_records=len(observed['orphan_records']))
            for run in observed['episodes']:
                end = run_end(run)
                interval = interval_observation(run['binding']['owner'], run['binding']['player'],
                                                run['start_record'], end, owners, slots, fields, events) if end else None
                terminal_above_range = (run['end_reason'] == 'explicit_state_2' and
                                        run['last_timer'] is not None and run['last_timer'] > .1)
                values = {s['value'] for s in interval['states']} if interval else set()
                # This is a literal timer observation, not a cancel event label.
                # An apparent body value0/2 cannot repair an incomplete timer.
                plausible_states = bool(values) and values <= {0, 2}
                totals.update(episodes=1,
                              explicit_state2_terminal_above_completion_range=int(terminal_above_range),
                              above_range_with_only_raw_body0_or2=int(terminal_above_range and plausible_states),
                              above_range_in_no_plant_round=int(terminal_above_range and not r['verified_plant']))
                terminals[run['end_reason']] += 1
                rows.append(dict(official_match_id=prediction['official_match_id'], round=r['round'],
                                 physical_round=r['physical_round'], replay_sha256=r['replay_sha256'],
                                 plant_occurrence=r['verified_plant'], occurrences=r['occurrences'],
                                 frozen_original_reason=r['original']['reason'], frozen_original_actor=r['original']['actor'],
                                 timer_owner=run['binding']['player'], timer_route=run['binding'], phase=run['state'],
                                 first_timer=run['first_timer'], last_timer=run['last_timer'], samples=len(run['samples']),
                                 monotonic=run['monotonic_timer'], start=run['start_record'], end=end,
                                 terminal=run['end_reason'], terminal_above_completion_range=terminal_above_range,
                                 interval=interval, active_body_verified=False, actor_credit_proposed=False))
    record = dict(tier='consumed_timer_terminal_controls_not_cancellation_semantics_or_actor_credit',
                  counts=dict(totals), terminals=dict(terminals), episodes=rows,
                  source_sha256=source_sha(Path(__file__)), seal_sha256=sha(DATA/'prelabel-inventory-seal.json'),
                  permanent_oce_result_sha256=sha(DATA/'one-shot-primary-result.json'), protected_hashes=protected,
                  candidate_changed=False, actor_credit_proposed=False)
    if OUTPUT.exists():
        if json.loads(OUTPUT.read_text(encoding='utf-8')) != record:
            raise ValueError('Preserved consumed terminal inventory differs')
    else:
        OUTPUT.write_text(json.dumps(record, indent=2)+'\n', encoding='utf-8')
    lines = ['# Consumed OCE older-class timer controls', '',
             f'Counts: `{dict(totals)}`; terminals `{dict(terminals)}`.', '',
             'All114 complete build9734089 rounds are included. The existing frozen observer handles the declared '
             'timer class varianta859ffff without changing the resolver. Raw body intervals are independently '
             'inventoried on their temporal UID routes; no unknown class is declared eligible. '
             'Every original actor outcome and every no-plant round remains sealed.', '',
             '## Explicit terminal records above the completion range', '',
             '| Match / round | Timer owner | Phase | Timer first / last | Verified plant in round | Raw body values |',
             '| --- | --- | ---: | --- | --- | --- |']
    for r in rows:
        if r['terminal_above_completion_range']:
            values = [s['value'] for s in r['interval']['states']] if r['interval'] else []
            lines.append(f'| {r["official_match_id"]}/R{r["round"]:02d} | {r["timer_owner"]} | {r["phase"]} | '
                         f'{r["first_timer"]}/{r["last_timer"]} | {r["plant_occurrence"]} | {values} |')
    lines += ['', 'An explicit state2 terminal also occurs while the timer is well above zero. '
              'A raw0/2 body field or positive health cannot turn such a run into a completing objective interaction. '
              'These are structural incomplete/interrupted controls; without independent HUD they are not '
              'universally labeled canceled attempts. Completion still needs the full frozen timer, occurrence, '
              'side, unique owner, no competing/orphan/later attempt and death/body guards. '
              'No near-zero value, score or last killer supplies actor identity.', '',
              'No actor recovery, class allowlist change, bonus rule, runtime/operator/kill/Rating change, '
              'SQL/archive/public modification, old result regrading, push or publish.', '']
    (ROOT/'research/output/objective-bonus-body-oce-timer-controls.md').write_text('\n'.join(lines), encoding='utf-8')
    verify_prelabel()
    if snapshot() != protected:
        raise ValueError('Protected live files changed')
    print('Consumed older timer controls', dict(totals), flush=True)


if __name__ == '__main__':
    main()
