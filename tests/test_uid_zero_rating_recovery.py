from copy import deepcopy

import pytest

from r6stats.kill_credit import SOURCE, validate_map_credit
from r6stats.rating_credit_evidence import apply_uid_zero_recovery, uid_zero_recovery


def evidence_pair():
    def player(i, round_number):
        uid = 777 if i == 6 and round_number == 2 else i + 1
        sample = {'offset': 20, 'value': 0, 'component': 100 + i, 'owner': 200 + i, 'declarationOffset': 10}
        return {'uid': uid, 'profileID': f'00000000-0000-0000-0000-{i+1:012d}',
                'username': f'Player{i}', 'team': i // 5,
                'initial': 0, 'terminal': 0, 'kills': 0, 'samples': [sample], 'reason': SOURCE}
    records = []
    for number in (1, 2):
        records.append({'logical_round': number, 'physical_round': number, 'segment': 'original',
                        'credit': {'source': SOURCE, 'complete': True, 'reason': SOURCE,
                                   'actionStartOffset': 100, 'players': [player(i, number) for i in range(10)],
                                   'finishes': []}})
    missing = records[0]['credit']['players'][6]
    missing.update(initial=None, terminal=None, kills=None, samples=[], reason='missing_direct_uid_counter')
    records[0]['credit'].update(complete=False, reason='unresolved_player_counters')
    prior = deepcopy(records)
    missing['counterGap'] = {'source': 'in_round_uid_replacement_zero_counters_v1', 'owner': 206,
                             'oldUID': 7, 'newUID': 777, 'oldUIDOffset': 30, 'newUIDOffset': 140,
                             'oldScoreComponent': 106, 'newScoreComponent': 306,
                             'oldScoreOffset': 10, 'newScoreOffset': 120,
                             'oldSampleOffset': 20, 'newSampleOffset': 130}
    return prior, records


def test_exact_native_zero_samples_and_next_round_bridge_recover_rating_only():
    old, raw = evidence_pair()
    saved_old = deepcopy(old)
    recovered = apply_uid_zero_recovery(old, raw)
    assert recovered is not None
    assert validate_map_credit(recovered)['complete']
    assert uid_zero_recovery(old, recovered)
    assert old == saved_old
    assert recovered[0]['credit']['players'][6]['kills'] == 0
    assert recovered[0]['credit']['players'][6]['samples'] == []


@pytest.mark.parametrize('mutation', ['missing_proof','positive_second_round','different_profile',
                                     'different_uid','changed_other_player','changed_source','bad_offset'])
def test_zero_bridge_refuses_missing_or_conflicting_evidence(mutation):
    old, raw = evidence_pair()
    if mutation == 'missing_proof': raw[0]['credit']['players'][6].pop('counterGap')
    elif mutation == 'positive_second_round': raw[1]['credit']['players'][6]['initial'] = 1
    elif mutation == 'different_profile': raw[1]['credit']['players'][6]['profileID'] = '00000000-0000-0000-0000-000000000999'
    elif mutation == 'different_uid': raw[1]['credit']['players'][6]['uid'] = 778
    elif mutation == 'changed_other_player': raw[0]['credit']['players'][0]['kills'] = 1
    elif mutation == 'changed_source': raw[0]['segment'] = 'other'
    elif mutation == 'bad_offset': raw[0]['credit']['players'][6]['counterGap']['newSampleOffset'] = 150
    assert apply_uid_zero_recovery(old, raw) is None
