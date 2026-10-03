from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"research"))
from credited_late_credit_hypothesis import reconstruct


def event(kind,scalar,first,victim):
    return {"kind_byte":kind,"opaque_scalar":scalar,"first":{"uid":first},"second":{"uid":victim},
            "raw_hex":f"{kind}:{scalar}:{first}:{victim}"}


def test_opponent_down_candidate_and_different_finisher_are_kept_separate():
    r = reconstruct([event(5,100,1,3),event(1,200,2,3)],{1:0,2:0,3:1})
    assert r["counts"] == {1:1}
    assert r["ledger"][0]["finisher_uid"] == 2 and r["ledger"][0]["elapsed_seconds"] is None
    assert not r["production_authoritative"]


def test_recovery_clears_prior_down_and_subsequent_down_replaces_it():
    teams={1:0,2:0,3:1}
    r = reconstruct([event(5,100,1,3),event(7,150,3,3),event(1,200,2,3)],teams)
    assert r["counts"] == {2:1}
    r = reconstruct([event(5,100,1,3),event(7,150,3,3),event(5,170,2,3),event(1,200,1,3)],teams)
    assert r["counts"] == {2:1}


def test_self_down_does_not_manufacture_opponent_credit_and_duplicates_are_copies():
    e = event(1,200,1,3)
    r = reconstruct([event(5,100,3,3),e,e],{1:0,3:1})
    assert r["counts"] == {1:1} and len(r["ledger"]) == 1


def test_tied_scalar_duplicate_death_and_unproven_teamkill_refused():
    teams={1:0,2:0,3:1}
    for events in ([event(5,100,1,3),event(1,100,2,3)],
                   [event(1,100,1,3),event(1,200,2,3)], [event(1,100,1,2)]):
        with pytest.raises(ValueError): reconstruct(events,teams)
