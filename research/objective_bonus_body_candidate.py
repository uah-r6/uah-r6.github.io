"""Isolated consumed-data plant hypothesis, never imported by the tracker.

All current plant guards run first. Only an otherwise eligible completer whose
known body route has state1 may be reconsidered using direct numerical bonus
health evidence. Defense and the frozen production resolver are unchanged.
"""
from collections import defaultdict

from objective_plant_owner_candidate import candidate as original_candidate
from objective_disable_owner_candidate import BODY_SLOT, BODY_CLASS
from objective_player_component_fields import bindings_at
from v3_body_state1_health_audit import last_field, numerical_snapshot


def candidate(header, observed, owners, slots, properties, deaths, full_feedback, body_fields=None):
    actor, reason, context = original_candidate(header, observed, owners, slots, properties, deaths, full_feedback)
    if actor is not None or reason != 'timer_owner_body_unresolved':
        return actor, reason, context
    values = context.get('body_values', [])
    if (context.get('body_reason') != 'body_state_unresolved_or_ineligible'
            or not values or 1 not in values or not set(values) <= {0, 1, 2}):
        return actor, reason, context
    owner, name = context['owner_entity'], context['owner_observation']
    start, end = context['start'], context['end']
    declarations = [d for d in slots.get((owner, BODY_SLOT), []) if d['offset'] <= start]
    component = declarations[-1]['component']
    fields = sorted((p for p in body_fields or [] if p['entity'] == component), key=lambda p:p['offset'])
    states = [p for p in fields if p['hash'] == 'e788f6a5' and p['size'] == 4]
    raw_states = sorted((p for p in properties if p['entity'] == component and p['hash'] == 'e788f6a5'
                         and p['size'] == 4), key=lambda p:p['offset'])
    if not fields or any('record_start' not in p for p in fields):
        return None, 'bonus_body_missing_explicit_property_records', context
    records = defaultdict(list)
    for p in fields:
        records[p['record_start']].append(p)
    # Snapshot at explicit body-property record ends, preserving atomic writes
    # when health/fraction/state are serialized in the same record. Also check
    # exact interaction endpoints; do not sample later whole-round values.
    points = {start, end}
    points.update(max(p['offset'] + 5 + p['size'] for p in record)
                  for record in records.values()
                  if start < max(p['offset'] + 5 + p['size'] for p in record) <= end)
    evidence = []
    for point in sorted(points):
        state, raw_state = last_field(states, point), last_field(raw_states, point)
        if state is None or raw_state is None or (state['offset'], state['value']) != (raw_state['offset'], raw_state['value']):
            return None, 'bonus_body_state_observers_disagree', context
        if state['value'] in (0, 2):
            continue
        if state['value'] != 1:
            return None, 'bonus_body_ineligible_state', context
        values = numerical_snapshot(fields, {'offset': point})
        if not values['consistent_positive_bonus'] or any(p['size'] != 4 for p in values['exact_fields'].values()):
            return None, 'bonus_body_missing_or_inconsistent_positive_health', context
        # The current snapshot and every retained numeric field must belong to
        # the same unique typed body owner at their own observation offsets.
        for offset in [point, state['offset'], *(p['offset'] for p in values['exact_fields'].values())]:
            route = bindings_at(owners, slots, offset).get(component)
            if not route or (route['owner'], route['player'], route['slot'], route['class_hash']) != (
                    owner, name, BODY_SLOT, BODY_CLASS):
                return None, 'bonus_body_numeric_identity_unresolved', context
        evidence.append(dict(offset=point, state=1, numerical=values))
    if not evidence:
        return None, 'bonus_body_no_verified_state1_snapshot', context
    context = context | dict(bonus_body_evidence=evidence,
                             research_only=True, production_body_allowlist_unchanged=True)
    return name, 'verified_bonus_health_plant_completer_research_v1', context
