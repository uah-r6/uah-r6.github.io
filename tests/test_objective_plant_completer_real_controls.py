"""Consumed structural completers and independently reviewed disputed labels."""
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research'))
from objective_plant_owner_candidate import candidate


def cases():
    return json.loads((Path(__file__).parent/'fixtures/objective-plant-completer.json').read_text(encoding='utf-8'))['cases']


def unpack(row):
    data=row['input']
    return data|dict(owners={int(k):v for k,v in data['owners'].items()},
                     slots={(d['owner'],d['slot']):d['declarations'] for d in data['slots']})


def test_real_completers_preserve_every_interrupted_and_negative_case():
    rows=cases()
    assert len(rows)==8
    for row in rows:
        assert candidate(**unpack(row))[:2]==(row['expected_proposal'],row['expected_reason'])
    mixed=next(r for r in rows if r['match_id']==4150)
    assert [r['binding']['player'] for r in mixed['input']['observed']['episodes']]==['Kason.100T','Kason.100T','Hotancold.100T']
    assert mixed['expected_proposal']=='Hotancold.100T'
    assert next(r['expected_proposal'] for r in rows if r['match_id']==4139)=='Aiden.SSG'
    assert next(r['expected_proposal'] for r in rows if r['match_id']==3554)=='kyno'
    assert all(r['expected_proposal'] is None for r in rows if r['match_id'] in (4138,4141))


def test_real_completed_episodes_without_validated_plant_cannot_receive_actor_credit():
    for row in cases():
        data=unpack(row)
        data['header']=data['header']|dict(objectiveOccurrences=[])
        assert candidate(**data)[0] is None
