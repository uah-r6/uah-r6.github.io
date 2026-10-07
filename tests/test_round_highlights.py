from copy import deepcopy
import json

import pytest

from r6stats.kill_credit import validate_map_credit
from r6stats.parser.models import Kill, Objective, ObjectiveOccurrence
from r6stats.round_highlights import curate, select_groups, objective_match
from r6stats.rating_inputs_v3 import store_objective_evidence
from test_credited_production import fixture, make_db
from test_rating_v3 import evidence


def setup():
    match, records = evidence(*fixture())
    r = match.rounds[0]
    bindings = {p.key: i for i, p in enumerate(r.players)}
    identities = {i: {'slug': f'our-{i}', 'name': f'Our {i}'} for i in range(5)}
    return match, records, bindings, identities


def highlights(match, records, bindings, identities, credit=True):
    return curate(match, validate_map_credit(records) if credit else None, records, bindings, identities, 0)


def set_credits(records, kills):
    for n, row in enumerate(records, 1):
        for i, p in enumerate(row['credit']['players']):
            k = kills.get(i, 0)
            p.update(initial=(n-1)*k, terminal=n*k, kills=k)


def test_normal_opening_trade_refrag_and_routine_2k_rounds_remain_empty():
    m, records, bound, ids = setup()
    for r in m.rounds:
        r.objectives=[];r.objective_occurrences=[]
    before = deepcopy(m.to_dict())
    assert highlights(m, records, bound, ids) == {1: [], 2: []}
    assert m.to_dict() == before


@pytest.mark.parametrize('size,label', [(3, '3K'), (4, '4K'), (5, 'ACE')])
def test_credited_multikill_not_finisher_guess_and_losing_round_still_notable(size, label):
    m, records, bound, ids = setup(); set_credits(records, {0: size})
    for r in m.rounds:r.objectives=[];r.objective_occurrences=[];r.winner=1
    result = highlights(m, records, bound, ids)
    assert result[1] == [{'player_slug': 'our-0', 'player_name': 'Our 0', 'labels': [label], 'emphasis': 'strong' if size>=4 else 'notable'}]
    # The native finisher log credits p1 twice, not p0. Counter evidence wins.
    assert not highlights(m, records, bound, ids, False)[1]


@pytest.mark.parametrize('size', [1, 2, 3, 4, 5])
def test_native_clutch_source_first_sole_survivor_and_actual_winner(size):
    m, records, bound, ids = setup();r=m.rounds[0];players=r.players
    pairs=[(1, i) for i in range(5, 10-size)]+[(9, i) for i in range(1,5)]
    r.kills=[Kill(i, 100-i, players[a].key, players[b].key, a//5, b//5) for i,(a,b) in enumerate(pairs)]
    r.objectives=[];r.objective_occurrences=[];evidence(m,records)
    result=highlights(m,records,bound,ids)[1]
    assert next(h for h in result if h['player_slug']=='our-0')['labels']==[f'1v{size}']
    r.winner=1
    assert not any(f'1v{size}' in h['labels'] for h in highlights(m,records,bound,ids)[1])
    r.winner=0;records[0]['credit']['finishes'][0]['offset']=0
    assert not any(label.startswith('1v') for h in highlights(m,records,bound,ids)[1] for label in h['labels'])


@pytest.mark.parametrize('kind,label', [('plant','Plant'),('disable','Disable')])
def test_verified_core_objective_and_per_event_abstention_without_credit(kind,label):
    m, records, bound, ids=setup();r=m.rounds[0];key=r.players[2].key
    if kind=='disable':
        for p in r.players:p.side='Defense' if p.team==0 else 'Attack'
    r.objectives=[Objective(kind,key,0,40)]
    r.objective_occurrences=[ObjectiveOccurrence(kind,'defuser_state_v1' if kind=='plant' else 'defuser_state_and_defense_win_v1',2000,key,3,'completing_timer_owner_v1','completing_timer_owner_v1')]
    assert highlights(m,records,bound,ids,False)[1][0]['labels']==[label]
    r.objective_occurrences[0].actor_reason='guessed'
    assert not highlights(m,records,bound,ids,False)[1]


def test_same_player_combination_priority_and_max_two_groups_with_many_events():
    m, records, bound, ids=setup();set_credits(records,{0:5,1:4,2:3})
    result=highlights(m,records,bound,ids)[1]
    assert len(result)==2 and [h['labels'] for h in result]==[['ACE'],['4K']]
    # Explicit compact candidate projection also caps labels for the same player.
    result=select_groups({'a':{'name':'A','labels':['Plant','3K','1v2']},
                          'b':{'name':'B','labels':['Disable']},'c':{'name':'C','labels':['Plant']}})
    assert result[0]['labels']==['1v2','3K'] and len(result)==2
    # Same-player trusted objective + credited multikill becomes one group.
    set_credits(records,{2:3})
    result=highlights(m,records,bound,ids)[1]
    assert len(result)==1 and result[0]['labels']==['3K','Plant']


def test_opponents_missing_binding_teamkill_and_uncertain_native_identity_abstain():
    m, records, bound, ids=setup()
    for r in m.rounds:r.objectives=[];r.objective_occurrences=[]
    set_credits(records,{5:5})
    assert not highlights(m,records,bound,ids)[1]  # No opponent highlights.
    set_credits(records,{0:2})
    r=m.rounds[0];r.kills.append(Kill(3,60,r.players[0].key,r.players[1].key,0,0))
    evidence(m,records)
    assert not highlights(m,records,bound,ids)[1]  # Teamkill cannot turn 2K into 3K.
    set_credits(records,{0:3});bound.pop(r.players[0].key)
    assert not highlights(m,records,bound,ids)[1]


def test_logical_rehost_round_number_and_public_allowlist():
    m, records, bound, ids=setup();set_credits(records,{0:4})
    report=records[1]
    report['physical_round']=1;report['segment']='segment-02'
    for p in report['credit']['players']:
        p.update(initial=0,terminal=p['kills'])
    result=highlights(m,records,bound,ids)
    assert set(result)=={1,2} and result[2]  # Segment R01 remains logical R2.
    for groups in result.values():
        for h in groups:
            assert set(h)=={'player_slug','player_name','labels','emphasis'}
    payload=json.dumps(result)
    assert all(field not in payload for field in ['profileID','offset','segment','physical_round','source_path','fingerprint'])


def test_unsupported_objective_kind_does_not_hide_verified_kind_or_other_round():
    m, records, bound, ids = setup()
    # Verified plant plus unsupported disable: only the corroborated plant survives.
    r = m.rounds[0]
    r.objectives.append(Objective('disable', r.players[3].key, 0, 10))
    r.objective_occurrences.append(ObjectiveOccurrence('disable', 'legacy_guess', 2500, r.players[3].key))
    result = highlights(m, records, bound, ids, False)
    assert result[1][0]['labels'] == ['Plant']
    assert result[2][0]['labels'] == ['Plant']
    r.objective_occurrences[0].actor = 'unknown'
    assert not highlights(m, records, bound, ids, False)[1]
    assert highlights(m, records, bound, ids, False)[2][0]['labels'] == ['Plant']


def test_objective_seal_integrity_and_stale_fingerprint_do_not_assert_new_actors(tmp_path):
    db, mid, m, records = make_db(tmp_path)
    evidence(m, records)
    store_objective_evidence(db, mid, m)
    row = db.execute('SELECT * FROM maps WHERE id=?', (mid,)).fetchone()
    assert objective_match(db, row, m).to_dict() == m.to_dict()
    db.execute("UPDATE map_v3_objective_evidence SET fingerprint='stale' WHERE map_id=?", (mid,))
    assert objective_match(db, row, m) is m
    db.execute("UPDATE map_v3_objective_evidence SET evidence_sha256='bad' WHERE map_id=?", (mid,))
    with pytest.raises(ValueError, match='integrity'):
        objective_match(db, row, m)
    db.close()
