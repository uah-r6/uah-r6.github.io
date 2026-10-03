"""Unknown classes must remain observations even with plausible raw states."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'research'))
from objective_oce_body_class_lifecycle import interval_observation, deaths_for


def example():
    owners = {7: 'Player'}
    slots = {(7, '4154dcc4'): [dict(offset=1, component=8, class_hash='b529300b')]}
    fields = [dict(entity=8, hash='e788f6a5', size=4, offset=5, value=0, record_start=4)]
    return owners, slots, fields


def inspect(owners, slots, fields, events=()):
    return interval_observation(7, 'Player', 10, 30, owners, slots, fields, events)


def test_plausible_unknown_state_never_verifies_liveness_or_credits_actor():
    result = inspect(*example())
    assert result['route_status'] == 'unique_unchanged_typed_route'
    assert result['prior_state_present']
    assert result['states'][0]['value'] == 0
    assert result['active_body_verified'] is False
    assert result['actor_credit_proposed'] is False


def test_transient_sharing_during_interval_is_retained_as_uncertain():
    owners, slots, fields = example()
    slots[9, 'unknown_slot'] = [dict(offset=12, component=8, class_hash='b529300b'),
                                dict(offset=20, component=0, class_hash='00000000')]
    result = inspect(owners, slots, fields)
    assert result['route_status'] == 'missing_shared_or_replaced_route'
    assert result['active_body_verified'] is False


def test_own_component_replacement_is_not_joined_to_previous_body():
    owners, slots, fields = example()
    slots[7, '4154dcc4'].append(dict(offset=20, component=88, class_hash='b529300b'))
    fields.append(dict(entity=88, hash='e788f6a5', size=4, offset=25, value=2, record_start=24))
    result = inspect(owners, slots, fields)
    assert result['route_status'] == 'missing_shared_or_replaced_route'
    assert [s['value'] for s in result['states']] == [0]


def test_prior_property_shared_at_observation_offset_is_not_unique_evidence():
    owners, slots, fields = example()
    slots[9, 'unknown_slot'] = [dict(offset=2, component=8, class_hash='b529300b'),
                                dict(offset=8, component=0, class_hash='00000000')]
    result = inspect(owners, slots, fields)
    assert result['route_status'] == 'missing_shared_or_replaced_route'


def test_unknown_death_offsets_do_not_become_alive_claims():
    events = [dict(offset=0, feedback=dict(type=dict(name='Kill'), username='Enemy', target='Player'))]
    result = inspect(*example(), events)
    assert result['death_offset_unknown'] is True
    assert result['known_death_by_terminal'] is False
    assert result['active_body_verified'] is False


def test_death_association_distinguishes_victim_from_killer():
    events = [dict(offset=15, feedback=dict(type=dict(name='Kill'), username='Player', target='Enemy')),
              dict(offset=20, feedback=dict(type=dict(name='Death'), username='Player'))]
    assert deaths_for(events, 'Player') == [events[1]]
    result = inspect(*example(), events)
    assert result['known_death_by_terminal'] is True
    assert result['active_body_verified'] is False
