"""Reduced consumed SI/SLC/EWC identity/teardown and negative selector controls."""
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research'))
from objective_disable_owner_candidate import candidate


def cases():
    path=Path(__file__).parent/'fixtures/objective-disable-owner.json'
    return json.loads(path.read_text(encoding='utf-8'))['cases']


def unpack(row):
    data=row['input']
    return data | dict(owners={int(k):v for k,v in data['owners'].items()},
                       slots={(d['owner'],d['slot']):d['declarations'] for d in data['slots']})


def test_consumed_declared_owner_and_teardown_controls():
    rows=cases()
    assert len(rows)==9
    for row in rows:
        proposal,reason,_=candidate(**unpack(row))
        assert (proposal,reason)==(row['expected_proposal'],row['expected_reason']), (row['match_id'],row['round'])
    assert next(r['expected_proposal'] for r in rows if (r['match_id'],r['round'])==(3173,17))=='handyy'
    assert next(r['expected_proposal'] for r in rows if (r['match_id'],r['round'])==(4139,7)) is None


def test_missing_plant_or_defense_win_never_turns_cancellation_into_disable():
    for row in cases():
        if row['expected_proposal'] is None: continue
        data=unpack(row)
        no_plant=data|dict(header=data['header']|dict(objectiveOccurrences=[]))
        assert candidate(**no_plant)[0] is None
        scores=[t|dict(score=t['startingScore']+(t['role']=='Attack')) for t in data['header']['teams']]
        attack_won=data|dict(header=data['header']|dict(teams=scores))
        assert candidate(**attack_won)[0] is None
