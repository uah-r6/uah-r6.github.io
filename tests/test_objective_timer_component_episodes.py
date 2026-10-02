"""Structural research observer guards; no actor credits or score heuristics."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'research'))
from objective_timer_component_episodes import component_episodes, STATE, TIMER, SLOT, CLASS


def decl(owner, component, offset=0):
    return dict(owner=owner,component=component,offset=offset,slot_hash=SLOT,
                class_hash=CLASS if component else '00000000')


def field(record, entity, tag, value, offset=None):
    return dict(record_start=record,entity=entity,hash=tag,value=value,offset=offset or record+9,
                size=4 if tag==STATE else 5,raw_hex='00000000')


def test_cancel_then_different_player_complete_is_split_by_explicit_state():
    fields = [field(10,20,STATE,0),field(10,20,TIMER,'7.000',25),
              field(30,20,TIMER,'6.694'),field(40,20,STATE,2),
              field(50,21,STATE,0),field(50,21,TIMER,'7.000',65),
              field(70,21,TIMER,'0.015'),field(80,21,STATE,2)]
    result = component_episodes({1:'Kason',2:'Hotancold'}, {(1,SLOT):[decl(1,20)],(2,SLOT):[decl(2,21)]},fields)
    assert [e['binding']['player'] for e in result['episodes']] == ['Kason','Hotancold']
    assert [e['last_timer'] for e in result['episodes']] == [6.694,0.015]
    assert all(e['actor'] is None for e in result['episodes'])


def test_terminal_record_timer_belongs_to_ending_run():
    fields = [field(10,20,STATE,1),field(10,20,TIMER,'6.972',25),
              field(30,20,STATE,2),field(30,20,TIMER,'0.004',45)]
    result = component_episodes({1:'player'}, {(1,SLOT):[decl(1,20)]},fields)
    episode = result['episodes'][0]
    assert episode['last_timer'] == .004
    assert episode['end_record'] == 30
    assert episode['state'] == 1
    assert episode['actor'] is None


def test_near_zero_without_terminal_is_not_completed():
    fields = [field(10,20,STATE,0),field(10,20,TIMER,'7.000',25),field(30,20,TIMER,'0.018')]
    result = component_episodes({1:'player'}, {(1,SLOT):[decl(1,20)]},fields)
    assert result['episodes'][0]['end_reason'] == 'round_ended_without_explicit_terminal'
    assert result['episodes'][0]['actor'] is None


def test_cleared_slot_ends_run_even_when_no_more_component_properties_exist():
    fields = [field(10,20,STATE,0),field(10,20,TIMER,'7.000',25)]
    result = component_episodes({1:'player'}, {(1,SLOT):[decl(1,20),decl(1,0,30)]},fields)
    assert result['episodes'][0]['end_reason'] == 'ownership_declaration_boundary'
    assert result['episodes'][0]['end_offset'] == 30
    assert result['episodes'][0]['end_source'] == 'slot_declaration'


def test_shared_unknown_owner_cannot_supply_a_start_or_timer_owner():
    fields = [field(10,20,STATE,0),field(10,20,TIMER,'7.000',25)]
    result = component_episodes({1:'player'}, {(1,SLOT):[decl(1,20)],(999,SLOT):[decl(999,20)]},fields)
    assert not result['episodes']
    assert result['orphan_records'][0]['reason'] == 'unknown_or_non_timer_component_route'


def test_interleaved_players_are_never_merged():
    fields = [field(10,20,STATE,0),field(10,20,TIMER,'7.000',25),
              field(30,21,STATE,0),field(30,21,TIMER,'7.000',45),
              field(50,20,TIMER,'6.000'),field(60,21,TIMER,'5.000'),
              field(70,20,STATE,2),field(80,21,STATE,2)]
    result = component_episodes({1:'a',2:'b'}, {(1,SLOT):[decl(1,20)],(2,SLOT):[decl(2,21)]},fields)
    assert [e['last_timer'] for e in result['episodes']] == [6,5]
    assert [len(e['samples']) for e in result['episodes']] == [2,2]


def test_unexpected_state_width_is_unresolved():
    state = field(10,20,STATE,0) | dict(size=8)
    result = component_episodes({1:'player'}, {(1,SLOT):[decl(1,20)]},[state,field(10,20,TIMER,'7.000',25)])
    assert not result['episodes']
    assert result['orphan_records'][0]['reason'] == 'unsupported_state_width'
