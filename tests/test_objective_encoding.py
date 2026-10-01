"""Synthetic property fragments based on inspected Y11 encoding shapes."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'research'))
from objective_encoding_probe import inherited_state_events
from objective_score_ledger import ledger
from objective_occurrence_validation import occurrences


REF = b'\x23' + (123).to_bytes(8, 'little')
STATE = bytes.fromhex('ff39f4080101')
SITE = bytes.fromhex('2f5e64410402000000')


def test_explicit_and_continued_state_have_same_entity():
    explicit = inherited_state_events(REF + STATE)
    continued = inherited_state_events(REF + SITE + b'\x22' + STATE)
    assert [(e['entity'], e['value']) for e in explicit] == [(123, 1)]
    assert [(e['entity'], e['value']) for e in continued] == [(123, 1)]
    assert continued[0]['inherited'] and not explicit[0]['inherited']


def test_no_identity_carry_across_unknown_metadata():
    assert inherited_state_events(REF + SITE + b'\x26\x22' + STATE) == []
    assert inherited_state_events(b'\x22' + STATE) == []


def test_truncated_or_unsupported_properties_are_rejected():
    assert inherited_state_events(REF + STATE[:-1]) == []
    assert inherited_state_events(REF + b'abcd\x03xyz\x22' + STATE) == []


def test_new_reference_changes_entity_and_cleanup_is_not_hidden():
    second = b'\x23' + (456).to_bytes(8, 'little')
    events = inherited_state_events(REF + STATE + second + STATE[:-1] + b'\0')
    assert [(e['entity'], e['value']) for e in events] == [(123, 1), (456, 0)]
    # This decoder reports evidence only; it does not label zero as a disable.
    assert all('actor' not in e and 'completion' not in e for e in events)


def test_repeated_continuations_are_supported_without_duplicate_events():
    events = inherited_state_events(REF + SITE + b'\x22' + SITE + b'\x22' + STATE)
    assert len(events) == 1 and events[0]['entity'] == 123


def test_score_ledger_preserves_mutable_names_as_ambiguous():
    name = bytes.fromhex('5be84728')
    score = bytes.fromhex('ecda4f8004')
    data = REF + name + b'\x04Raid' + b'\x22' + score + (200).to_bytes(4, 'little')
    data += REF + name + b'\x05Aiden' + b'\x22' + score + (300).to_bytes(4, 'little')
    result = ledger(data)
    assert result['entity_names']['123'] == ['Aiden', 'Raid']
    assert result['events'][0]['delta'] == 100
    assert result['events'][0]['names'] == ['Aiden', 'Raid']
    assert 'actor' not in result['events'][0]


def test_score_ledger_does_not_join_nearby_entities():
    name = bytes.fromhex('5be8472804') + b'Raid'
    other = b'\x23' + (127).to_bytes(8, 'little')
    score = bytes.fromhex('ecda4f8004')
    data = REF + name + other + score + (200).to_bytes(4, 'little')
    data += other + score + (300).to_bytes(4, 'little')
    assert ledger(data)['events'][0]['names'] == []


def test_candidate_disable_needs_plant_and_defender_win_not_zero_flag():
    plant = {'offset': 100, 'entity': 123, 'value': 1}
    result = occurrences([plant], 'Defense', 'Bomb')
    assert result['plant'] and result['disable'] and result['actor'] is None
    assert not occurrences([], 'Defense', 'Bomb')['disable']


def test_attack_win_with_later_cleanup_does_not_imply_disable():
    events = [{'offset': 100, 'entity': 123, 'value': 1},
              {'offset': 200, 'entity': 123, 'value': 0}]
    result = occurrences(events, 'Attack', 'Bomb')
    assert result['plant'] and not result['disable']


def test_ambiguous_or_unsupported_occurrences_remain_unresolved():
    plant = {'offset': 100, 'entity': 123, 'value': 1}
    assert occurrences([plant,plant], 'Defense', 'Bomb')['status'] == 'ambiguous_state_sequence'
    assert occurrences([plant], None, 'Bomb')['status'] == 'unsupported_round'
    assert occurrences([plant], 'Defense', 'Hostage')['status'] == 'unsupported_round'
    other = {'offset': 200, 'entity': 456, 'value': 0}
    assert occurrences([plant,other], 'Defense', 'Bomb')['status'] == 'ambiguous_state_sequence'
