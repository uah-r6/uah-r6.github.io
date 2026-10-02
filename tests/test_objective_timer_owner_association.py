"""No anchor, wrong role and competing runs cannot supply an owner proposal."""
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research'))
from objective_timer_consumed_extensions import associated_owner


def run(player='player',state=0,start=10,end=20,last=.01):
    return dict(state=state,start_record=start,end_record=end,end_reason='explicit_state_2',
                first_timer=7,last_timer=last,monotonic_timer=True,samples=[{},{}],
                binding=dict(player=player),actor=None)


def test_missing_anchor_does_not_use_last_timer_owner():
    owner,reason,_ = associated_owner(dict(episodes=[run()]),None,None,{'player':'Attack'},'plant')
    assert owner is None and reason=='missing_anchor'


def test_competing_completed_runs_abstain_without_picking_nearest():
    owner,reason,_ = associated_owner(dict(episodes=[run(),run('other',start=30,end=40)]),
                                     dict(center=50),0,{'player':'Attack','other':'Attack'},'plant')
    assert owner is None and reason=='absent_or_ambiguous_component_run'


def test_wrong_objective_role_is_not_credited():
    owner,reason,_ = associated_owner(dict(episodes=[run()]),dict(center=50),0,{'player':'Defense'},'plant')
    assert owner is None and reason=='owner_role_conflict'


def test_previous_global_anchor_excludes_earlier_attempts():
    owner,reason,_ = associated_owner(dict(episodes=[run(),run('other',start=30,end=40)]),
                                     dict(center=50),25,{'player':'Attack','other':'Attack'},'plant')
    assert owner=='other' and reason=='unique_component_run_before_anchor'


def test_incomplete_attempt_does_not_resolve_even_if_it_is_last():
    owner,reason,_ = associated_owner(dict(episodes=[run(last=2.881)]),dict(center=50),0,{'player':'Attack'},'plant')
    assert owner is None and reason=='absent_or_ambiguous_component_run'
