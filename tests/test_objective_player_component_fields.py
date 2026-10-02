"""Temporal declared identity guards for the research observer only."""
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research'))
from objective_player_component_fields import primitive_fields, owners_and_slots, bindings_at


def declaration(owner,component,offset=0,slot='slot'):
    return dict(owner=owner,component=component,offset=offset,slot_hash=slot,class_hash='class' if component else '00000000')


def test_slot_replacement_and_clear_do_not_union_historical_components():
    raw = dict(header=dict(players=[dict(id=99,username='player')]),
               properties=[dict(kind='numeric_uid',value=99,entity=10)],
               declarations=[declaration(10,20),declaration(10,21,10),declaration(10,0,20)])
    owners,slots = owners_and_slots(raw)
    assert bindings_at(owners,slots,5)[20]['player'] == 'player'
    assert 20 not in bindings_at(owners,slots,15)
    assert bindings_at(owners,slots,15)[21]['player'] == 'player'
    assert 21 not in bindings_at(owners,slots,25)


def test_component_shared_with_unknown_owner_is_not_bound_to_known_player():
    owners = {10:'player'}
    slots = {(10,'slot'):[declaration(10,20)], (999,'other'):[declaration(999,20,slot='other')]}
    assert 20 not in bindings_at(owners,slots,5)


def test_duplicate_uid_owner_is_unresolved():
    raw = dict(header=dict(players=[dict(id=99,username='player')]),
               properties=[dict(kind='numeric_uid',value=99,entity=10),dict(kind='numeric_uid',value=99,entity=11)],
               declarations=[])
    assert owners_and_slots(raw)[0] == {}


def test_four_byte_name_is_text_and_continuation_preserves_entity():
    prefix = b'\x23'+(20).to_bytes(4,'little')+bytes(4)
    data = prefix+bytes.fromhex('5be84728')+b'\x04Ambi'+b'\x22'+bytes.fromhex('e9a37feb')+b'\x04'+bytes.fromhex('0000803f')
    fields = primitive_fields(data,{20})
    assert [f['value'] for f in fields] == ['Ambi',1065353216]
    assert fields[0]['interpretation'] == 'utf8_name'
    assert fields[1]['interpretation'] == 'unsigned_bits_only'
    assert fields[1]['inherited'] and fields[1]['entity'] == 20
