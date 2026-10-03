"""Consumed build9734089 component lifecycle observations, never actor eligibility.

The unknown class is inventoried through exact temporal UID ownership. Raw
integer states and numeric fields retain their values without assigning active,
DBNO, dead, bonus-health or revive semantics. No frozen resolver is changed.
"""
from collections import Counter, defaultdict
import json
from pathlib import Path

from objective_actor_liveness import feedback
from objective_bonus_body_oce_review import verify_prelabel
from objective_disable_owner_candidate import BODY_SLOT, BODY_CLASS
from objective_oce_consumed_identity_review import verify as verify_consumed
from objective_player_component_fields import observe, bindings_at
from objective_bonus_body_oce_cohort import DATA
from uah_guarded_actor_readonly import snapshot
from v3_body_state1_health_audit import numerical_snapshot
from v3_final_reserve import ROOT, sha, source_sha

BUILD = 9734089
UNKNOWN_CLASS = 'b529300b'
OUTPUT = DATA / 'consumed-body-class-lifecycle.json'


def deaths_for(events, name):
    return [e for e in events if
            (e['feedback']['type']['name'] == 'Kill' and e['feedback'].get('target') == name)
            or (e['feedback']['type']['name'] == 'Death' and e['feedback'].get('username') == name)]


def interval_observation(owner, name, start, end, owners, slots, fields, events):
    """Observe a declared component, explicitly refusing a liveness conclusion."""
    result = dict(active_body_verified=False, actor_credit_proposed=False,
                  interpretation='Unknown class; raw values do not establish liveness.')
    declarations = slots.get((owner, BODY_SLOT), [])
    prior = [d for d in declarations if d['offset'] <= start]
    if not prior or not prior[-1]['component']:
        return result | dict(route_status='missing_prior_component', states=[])
    d = prior[-1]
    component = d['component']
    values = [f for f in fields if f['entity'] == component and f['hash'] == 'e788f6a5' and f['size'] == 4]
    preceding = [f for f in values if f['offset'] <= start]
    selected = ([preceding[-1]] if preceding else []) + [f for f in values if start < f['offset'] <= end]
    # All declaration changes can alter sharing; own replacements may use a
    # different component. Check both, plus each retained property offset.
    points = {start, end, *(f['offset'] for f in selected)}
    points.update(x['offset'] for ds in slots.values() for x in ds if start < x['offset'] <= end)
    route_matches = all(bindings_at(owners, slots, point).get(component) is not None and
                        tuple(bindings_at(owners, slots, point)[component][k] for k in
                              ('owner', 'player', 'slot', 'class_hash')) ==
                        (owner, name, BODY_SLOT, d['class_hash']) for point in points)
    own = [e for e in fields if e['entity'] == component]
    deaths = deaths_for(events, name)
    return result | dict(component=component, class_hash=d['class_hash'], declaration_offset=d['offset'],
                         route_status='unique_unchanged_typed_route' if route_matches else 'missing_shared_or_replaced_route',
                         prior_state_present=bool(preceding),
                         states=[dict(offset=f['offset'], value=f['value'], record_start=f['record_start']) for f in selected],
                         numerical_at_start=numerical_snapshot(own, {'offset': start}),
                         numerical_at_end=numerical_snapshot(own, {'offset': end}),
                         death_offset_unknown=any(e['offset'] <= 0 for e in deaths),
                         known_death_by_terminal=any(0 < e['offset'] <= end for e in deaths),
                         death_events=deaths)


def main():
    frozen, _, prelabel = verify_prelabel()
    verify_consumed()
    protected = snapshot()
    identities_path = DATA / 'consumed-additional-identities.json'
    review_path = DATA / 'consumed-additional-primary-review.json'
    identity_maps = {m['official_match_id']: m for m in json.loads(identities_path.read_text())['maps']}
    review = json.loads(review_path.read_text())
    independent = {(m['official_match_id'], c['round']): c for m in review['records']
                   for c in m['review']['constraints'] if c['verdict'] == 'unresolved'}
    counts, state_counts, after_death, transitions = Counter(), Counter(), Counter(), Counter()
    actor_rows, round_rows, property_rows, death_rows = [], [], [], []
    source_hashes = {identities_path.relative_to(ROOT).as_posix(): sha(identities_path),
                     review_path.relative_to(ROOT).as_posix(): sha(review_path)}
    for entry in prelabel['entries']:
        prediction_path = ROOT / entry['path']
        prediction = json.loads(prediction_path.read_text())
        if 'rounds' not in prediction:
            continue
        source_hashes[entry['path']] = entry['sha256']
        mid = prediction['official_match_id']
        for row in prediction['rounds']:
            if row['build'] != BUILD:
                continue
            rec = ROOT / row['replay_path']
            if sha(rec) != row['replay_sha256']:
                raise ValueError('Sealed physical replay changed')
            state, owners, slots, fields = observe(rec)
            events = feedback(rec)['events']
            counts.update(rounds=1, header_players=len(state['header']['players']),
                          unknown_death_offsets=sum(e['offset'] <= 0 for e in events))
            by_entity = defaultdict(list)
            for f in fields:
                by_entity[f['entity']].append(f)
            observed_by_player = defaultdict(list)
            for f in fields:
                if f['hash'] != 'e788f6a5' or f['size'] != 4:
                    continue
                route = bindings_at(owners, slots, f['offset']).get(f['entity'])
                if not route or (route['slot'], route['class_hash']) != (BODY_SLOT, UNKNOWN_CLASS):
                    continue
                name = route['player']
                deaths = deaths_for(events, name)
                dead = any(0 < e['offset'] <= f['offset'] for e in deaths)
                numeric = numerical_snapshot(by_entity[f['entity']], f)
                observed = dict(official_match_id=mid, round=row['round'], physical_round=row['physical_round'],
                                replay_sha256=row['replay_sha256'], player=name, route=route, component=f['entity'],
                                offset=f['offset'], record_start=f['record_start'], raw_value=f['value'],
                                numerical=numeric, known_death_before_property=dead,
                                unknown_death_offset=any(e['offset'] <= 0 for e in deaths),
                                active_body_verified=False)
                property_rows.append(observed)
                observed_by_player[name].append(observed)
                state_counts[str(f['value'])] += 1
                if dead:
                    after_death[str(f['value'])] += 1
                counts['state_properties'] += 1
                counts['raw_state1_properties'] += int(f['value'] == 1)
                counts['state1_consistent_numerical_bonus'] += int(f['value'] == 1 and numeric['consistent_positive_bonus'])
                counts['raw_state3_or4_positive_health'] += int(f['value'] in (3, 4) and type(numeric['health']) is int and numeric['health'] > 0)
            for name, observations in observed_by_player.items():
                # Transitions remain per component; replacements are not joined.
                prior = {}
                for observation in observations:
                    component, value = observation['component'], observation['raw_value']
                    if component in prior and prior[component] != value:
                        transitions[f'{prior[component]}->{value}'] += 1
                    prior[component] = value
                for death in deaths_for(events, name):
                    if death['offset'] <= 0:
                        continue
                    before = [o for o in observations if o['offset'] < death['offset']]
                    after = [o for o in observations if o['offset'] >= death['offset']]
                    death_rows.append(dict(official_match_id=mid, round=row['round'], player=name,
                                           death=death, last_property_before=before[-1] if before else None,
                                           first_property_after=after[0] if after else None,
                                           interpretation='Offset association only; a feed death does not identify a downing shot or revive.'))
            if row['verified_plant'] and not row['proposed']['actor']:
                context = row['proposed']['context']
                interval = interval_observation(context['owner_entity'], context['owner_observation'], context['start'],
                                                context['end'], owners, slots, fields, events)
                constraint = independent.get((mid, row['round']))
                identity_map = identity_maps[mid]
                bound = next((p for p in identity_map['players'] if p['username'] == context['owner_observation']), None)
                # Existing independent identities only; no actor/totals select a mapping.
                official_owner = bound['official_identity'] if bound and bound['status'] == 'verified' else None
                actor_rows.append(dict(official_match_id=mid, round=row['round'], physical_round=row['physical_round'],
                                       timer_owner=context['owner_observation'], numeric_uid=context['numeric_uid'],
                                       start=context['start'], end=context['end'], completion=context['plant_offset'],
                                       terminal=context['terminal'], original_abstention=row['proposed']['reason'],
                                       interval=interval, independent_constraint=constraint, official_owner=official_owner,
                                       independent_owner_agrees=(official_owner['id'] == constraint['independent_id'])
                                       if official_owner and constraint else None,
                                       actor_credit_proposed=False))
            round_rows.append(dict(official_match_id=mid, round=row['round'], replay_sha256=row['replay_sha256'],
                                   observed_players=len(observed_by_player), state_properties=sum(map(len, observed_by_player.values()))))
        print('Cached class lifecycle', mid, counts['rounds'], flush=True)
    constrained = [r for r in actor_rows if r['independent_constraint']]
    counts.update(unresolved_plants=len(actor_rows), independent_owner_constraints=len(constrained),
                  independent_owner_agreements=sum(r['independent_owner_agrees'] is True for r in constrained),
                  independent_owner_disagreements=sum(r['independent_owner_agrees'] is False for r in constrained),
                  known_death_controls=len(death_rows))
    record = dict(status='consumed_unknown_class_lifecycle_diagnostic_no_actor_or_semantic_promotion',
                  build=BUILD, component_class=UNKNOWN_CLASS, frozen_body_class=BODY_CLASS,
                  counts=dict(counts), state_counts=dict(state_counts), explicit_property_values_after_known_death=dict(after_death),
                  observed_transitions=dict(transitions), actor_intervals=actor_rows, rounds=round_rows,
                  state_properties=property_rows, death_controls=death_rows, source_hashes=source_hashes,
                  source_sha256=source_sha(Path(__file__)), permanent_oce_result_sha256=sha(DATA/'one-shot-primary-result.json'),
                  protected_hashes=protected, semantics_validated=False, candidate_changed=False, actor_credit_proposed=False)
    if OUTPUT.exists():
        if json.loads(OUTPUT.read_text()) != record:
            raise ValueError('Preserved consumed lifecycle diagnostic differs')
    else:
        OUTPUT.write_text(json.dumps(record, indent=2)+'\n', encoding='utf-8')
    lines = ['# Consumed OCE build9734089 unknown body-class lifecycle', '',
             f'Cached complete-build inventory: `{dict(counts)}`.', '',
             f'Raw state fields: `{dict(state_counts)}`. Explicit properties after known feed deaths: `{dict(after_death)}`.', '',
             f'Per-component observed transitions: `{dict(transitions)}`.', '',
             'The typed expected slot4154dcc4 declares classb529300b rather than frozen class0c98c63f. '
             'Every property below belongs to a unique temporal declared UID route. No raw value is assigned alive, '
             'DBNO, dead, revive or bonus-health semantics on this unknown class. Feed deaths provide negative '
             'timing controls; they do not identify downing shots. Positive health and correlation are insufficient for liveness.', '',
             '## Independently constrained plant owner observations', '',
             '| Match / logical round | Direct owner | Independent official actor | Exact identity agrees | Raw interval | Typed route | Known death by completion |',
             '| --- | --- | --- | --- | --- | --- | --- |']
    for r in constrained:
        interval = r['interval']
        lines.append(f'| {r["official_match_id"]}/R{r["round"]:02d} | {r["timer_owner"]} | '
                     f'{r["independent_constraint"]["independent_actor"]} | {r["independent_owner_agrees"]} | '
                     f'{[s["value"] for s in interval["states"]]} | {interval["route_status"]} | {interval["known_death_by_terminal"]} |')
    lines += ['', 'These are seven consumed owner-agreement observations, not seven newly resolved actors. '
              'The frozen body guard still abstains and the original OCE result stays permanently **INSUFFICIENT**. '
              'Numeric owner association is supported independently; component liveness semantics need separate '
              'DBNO/revive/cancellation/sharing controls and an unused reserved validation cohort before any compatibility promotion.', '',
              'Raw properties, declaration and death offsets, numerical snapshots, exact replay hashes and independent identity '
              'constraints are preserved privately in the ignored lifecycle JSON. No replay bytes or private UUIDs are committed. '
              'No candidate/runtime/class allowlist, kill credit, operator/action-start logic, Rating, SQLite, archives, public JSON, '
              'website or failed historical result changed. No publish/push.', '']
    (ROOT/'research/output/objective-bonus-body-oce-body-class-lifecycle.md').write_text('\n'.join(lines), encoding='utf-8')
    verify_prelabel()
    verify_consumed()
    if snapshot() != protected or protected != frozen['protected_hashes']:
        raise ValueError('Protected live files changed')
    print('Lifecycle diagnostic complete', dict(counts), flush=True)


if __name__ == '__main__':
    main()
