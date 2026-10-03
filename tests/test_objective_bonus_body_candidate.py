"""Research-only bonus plant guard; original production controls remain intact."""
import copy
import json
from pathlib import Path
import struct
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'research'))
from objective_bonus_body_candidate import candidate
from objective_plant_owner_candidate import candidate as original
from test_objective_plant_owner_candidate import evidence


def bonus_evidence():
    data = evidence()
    data['properties'][0]['value'] = 1
    data['body_fields'] = [dict(entity=3000, hash=tag, size=4, offset=offset, value=value, record_start=2)
        for tag, offset, value in [('252676c9', 3, 120), ('1149a672', 4, 100),
                                  ('e788f6a5', 5, 1), ('013fd2da', 6, 120),
                                  ('80adcf7b', 7, struct.unpack('<I', struct.pack('<f', .2))[0])]]
    return data


def test_verified_bonus_snapshot_is_isolated_from_original_body_allowlist():
    data = bonus_evidence()
    assert original(**{k:v for k,v in data.items() if k != 'body_fields'})[0] is None
    actor, reason, context = candidate(**data)
    assert (actor, reason) == ('p0', 'verified_bonus_health_plant_completer_research_v1')
    assert context['research_only'] and context['production_body_allowlist_unchanged']


@pytest.mark.parametrize('change', ['no_occurrence', 'canceled', 'dead', 'zero_death', 'shared',
                                   'dbno_positive_hp', 'unknown', 'missing_health', 'no_bonus',
                                   'wrong_ceiling', 'wrong_fraction', 'missing_records', 'all_opponents_dead'])
def test_bonus_health_never_overrides_completion_identity_or_liveness_guards(change):
    data = bonus_evidence()
    if change == 'no_occurrence': data['header']['objectiveOccurrences'] = []
    if change == 'canceled': data['observed']['episodes'][0]['last_timer'] = 2
    if change in ('dead', 'zero_death'):
        data['deaths'] = [dict(offset=30 if change == 'dead' else 0,
                              feedback=dict(type=dict(name='Death'), username='p0'))]
    if change == 'shared': data['slots'][9999, 'other'] = [dict(offset=30, component=3000, class_hash='anything')]
    if change in ('dbno_positive_hp', 'unknown'):
        value = 3 if change == 'dbno_positive_hp' else 99
        data['properties'][0]['value'] = value
        data['body_fields'][2]['value'] = value
    if change == 'missing_health': data['body_fields'] = [p for p in data['body_fields'] if p['hash'] != '252676c9']
    if change == 'no_bonus': data['body_fields'][0]['value'] = 100
    if change == 'wrong_ceiling': data['body_fields'][3]['value'] = 145
    if change == 'wrong_fraction': data['body_fields'][4]['value'] = 0
    if change == 'missing_records':
        for p in data['body_fields']: p.pop('record_start')
    if change == 'all_opponents_dead':
        data['deaths'] = [dict(offset=10+i, feedback=dict(type=dict(name='Kill'), username='p0', target=f'p{i}'))
                          for i in range(5,10)]
    assert candidate(**data)[0] is None


def test_ordinary_active_plant_remains_exactly_unchanged():
    data = evidence()
    assert candidate(**data) == original(**data)


def test_positive_hp_does_not_replace_state_or_numeric_body_identity():
    data = bonus_evidence()
    # Move just the baseline field to before the unique body declaration.
    data['body_fields'][1]['offset'] = 0
    assert candidate(**data)[0] is None


def test_bonus_decay_to_normal_state_is_read_as_one_explicit_property_record():
    data = bonus_evidence()
    data['properties'].append(dict(entity=3000, hash='e788f6a5', size=4, offset=38, value=0))
    data['body_fields'] += [dict(entity=3000, hash=tag, size=4, offset=offset, value=value, record_start=30)
                          for tag, offset, value in [('252676c9', 31, 100), ('80adcf7b', 32, 0),
                                                    ('e788f6a5', 38, 0)]]
    assert candidate(**data)[0] == 'p0'


def test_consumed_kds_bonus_health_completion_preserves_frozen_abstention():
    fixture = json.loads((Path(__file__).parent / 'fixtures/objective-bonus-health-plant.json').read_text())
    data = fixture['evidence']
    data['owners'] = {int(k):v for k,v in data['owners'].items()}
    data['slots'] = {tuple(k):v for k,v in data['slots']}
    assert original(**{k:v for k,v in data.items() if k != 'body_fields'})[:2] == (
        None, 'timer_owner_body_unresolved')
    actor, reason, context = candidate(**data)
    assert (actor, reason) == (fixture['expected_actor'], fixture['expected_reason'])
    assert context['start'] == 51432785 and context['end'] == 51469727
    assert context['plant_offset'] == 51470330
    assert context['bonus_body_evidence'][0]['numerical']['health'] == 120
    assert context['bonus_body_evidence'][0]['numerical']['baseline_field'] == 100
