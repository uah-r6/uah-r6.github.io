"""Research counter resets must have explicit physical replay evidence."""
import copy
import importlib
import sys
from pathlib import Path
from uuid import UUID

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'research'))
probe = importlib.import_module('v3_consumed_kill_credit_probe')


def rounds():
    before = dict(folder='Match-original', physical_round=5, logical_round=5,
                  players={f'p{i}': dict(profile_id=str(UUID(int=i+1)), initial=2, terminal=3)
                           for i in range(10)})
    after = copy.deepcopy(before)
    after.update(physical_round=6, logical_round=6)
    for p in after['players'].values():
        p.update(initial=3, terminal=4)
    return before, after


def test_contiguous_counter_values_need_no_reset():
    assert probe.counter_continuity(rounds()) == ([], [])


def test_new_folder_round_one_with_same_full_profiles_has_explicit_reset():
    before, after = rounds()
    after.update(folder='Match-rehost', physical_round=1)
    for p in after['players'].values():
        p.update(initial=0, terminal=1)
    issues, resets = probe.counter_continuity([before, after])
    assert not issues and len(resets) == 1


def test_counter_drop_with_no_physical_folder_boundary_is_rejected():
    before, after = rounds()
    for p in after['players'].values():
        p['initial'] = 0
    issues, resets = probe.counter_continuity([before, after])
    assert len(issues) == 10 and not resets


def test_changed_profile_cannot_authorize_a_rehost_reset():
    before, after = rounds()
    after.update(folder='Match-rehost', physical_round=1)
    for p in after['players'].values():
        p['initial'] = 0
    after['players']['p0']['profile_id'] = 'someone-else'
    issues, resets = probe.counter_continuity([before, after])
    assert len(issues) == 10 and not resets


def test_new_folder_with_round_two_does_not_authorize_counter_reset():
    before, after = rounds()
    after.update(folder='Match-rehost', physical_round=2)
    for p in after['players'].values():
        p['initial'] = 0
    issues, resets = probe.counter_continuity([before, after])
    assert len(issues) == 10 and not resets


def test_nil_or_shared_profiles_cannot_authorize_rehost_reset():
    for shared in (str(UUID(int=0)), str(UUID(int=1))):
        before, after = rounds()
        after.update(folder='Match-rehost', physical_round=1)
        for p in before['players'].values():
            p['profile_id'] = shared
        for p in after['players'].values():
            p.update(initial=0, profile_id=shared)
        issues, resets = probe.counter_continuity([before, after])
        assert len(issues) == 10 and not resets
