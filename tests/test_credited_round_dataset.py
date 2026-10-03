from copy import deepcopy
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research"))
from credited_round_dataset import counter_changes, event_inventory, player_rows
from credited_production_preview import basic_round, summarize
from credited_clock_epoch_audit import analyze
from r6stats.kill_credit import SOURCE
from r6stats.stats.calculate import empty


def credit():
    return {"source": SOURCE, "players": [
        {"uid": i+1, "username": f"p{i}", "team": i//5, "profileID": "",
         "initial": 0, "terminal": 0, "kills": 0, "reason": SOURCE,
         "samples": [{"offset": 10+i, "value": 0, "owner": i+1, "component": i+101}]}
        for i in range(10)], "finishes": []}


def finish(killer="p1", victim="p5", offset=100, kind="Kill", seconds=90):
    return {"offset": offset, "feedback": {"type": {"name": kind}, "username": killer,
            "target": victim, "timeInSeconds": seconds}}


@pytest.mark.parametrize("credited_player", [0, 1])
def test_credit_equal_or_different_keeps_finisher_and_counter_events_separate(credited_player):
    c = credit(); c["finishes"] = [finish()]
    p = c["players"][credited_player]
    p.update(kills=1, terminal=1)
    p["samples"].append({"offset": 98, "value": 1, "owner": p["uid"], "component": p["uid"]+100})
    before = deepcopy(c)
    rows, events = player_rows({}, {"credit": c}, True, True)
    assert rows[credited_player]["credited_kills"] == 1
    assert rows[1]["finisher_opponent_kills"] == 1
    assert events[0]["finisher"] == "uid:2"
    assert events[0]["credited_killer"] is None and events[0]["downer"] is None
    assert rows[credited_player]["counter_changes"][0]["victim"] is None
    assert c == before


@pytest.mark.parametrize("event,classification", [
    (finish("p0", "p1"), "teamkill"),
    (finish("p0", "p0"), "suicide"),
    (finish("p0", "", kind="Death"), "no_named_finisher_cause_unresolved")])
def test_teamkill_suicide_and_possible_environmental_death_manufacture_no_opponent_kills(event, classification):
    c = credit(); c["finishes"] = [event]
    rows, events = player_rows({}, {"credit": c}, True, True)
    assert events[0]["classification"] == classification
    assert sum(r["finisher_opponent_kills"] for r in rows) == 0
    assert sum(r["credited_kills"] for r in rows) == 0
    assert sum(len(r["victim_eliminations"]) for r in rows) == 1


def test_unsupported_round_retains_unknown_instead_of_zero():
    rows, _ = player_rows({}, {"credit": credit()}, False, False)
    assert all(r["credited_kills"] is None and r["difference"] is None for r in rows)


def test_duplicate_offset_rejected_and_unknown_legacy_death_not_assigned_offset():
    c = credit(); c["finishes"] = [finish(), finish(victim="p6")]
    with pytest.raises(ValueError, match="Duplicate"): event_inventory(c)
    c["finishes"] = [finish("p0", "", kind="Death", offset=0)]
    assert event_inventory(c)[0]["packet_offset"] is None


@pytest.mark.parametrize("mutation", ["reset", "replacement", "duplicate_offset", "bad_total"])
def test_counter_route_or_reset_gap_refused(mutation):
    p = credit()["players"][0]
    p.update(initial=0, terminal=1, kills=1)
    p["samples"].append({"offset": 98, "value": 1, "owner": 1, "component": 101})
    if mutation == "reset": p["samples"][0]["value"] = 2
    if mutation == "replacement": p["samples"][1]["component"] = 201
    if mutation == "duplicate_offset": p["samples"][1]["offset"] = 10
    if mutation == "bad_total": p["kills"] = 2
    with pytest.raises(ValueError): counter_changes(p)


def test_batched_increment_is_not_split_into_guessed_victim_events():
    p = credit()["players"][0]; p.update(kills=2, terminal=2)
    p["samples"].append({"offset": 98, "value": 2, "owner": 1, "component": 101})
    assert len(counter_changes(p)) == 1
    assert counter_changes(p)[0]["delta"] == 2 and counter_changes(p)[0]["victim"] is None


def test_credited_kost_and_multikill_keep_objectives_and_event_features():
    previous = empty(); previous.update(rounds=1, kills=0, deaths=1, plants=0, disables=0,
                                        opening_kills=0, kills_traded=0, pivot_kills=0)
    before = deepcopy(previous)
    projected = basic_round(previous, 3)
    assert projected["kills"] == 3 and projected["multikill_extra"] == 2 and projected["kost_rounds"] == 1
    assert previous == before
    assert projected["deaths"] == 1 and projected["opening_kills"] == 0
    assert projected["kills_traded"] == 0 and projected["pivot_kills"] == 0
    previous.update(kills=1, kost_rounds=1, disables=1)
    assert basic_round(previous, 0)["kost_rounds"] == 1
    assert basic_round(previous, 0)["disables"] == 1
    assert "rating" not in projected


def test_multikill_sizes_and_totals_aggregate_round_map_season():
    base = empty(); base["rounds"] = 1
    rows = [basic_round(base, k) for k in (1, 2, 3, 4, 5)]
    total = summarize(rows)
    assert total["kills"] == 15 and total["multikill_extra"] == 10
    assert total["multikill_sizes"] == {"2": 1, "3": 1, "4": 1, "5": 1}
    assert total["kost_rounds"] == 5


@pytest.mark.parametrize("first,last", [(32, 43), (6, 42)])
def test_both_reviewed_plant_countdown_resets_preserve_packet_order(first, last):
    events = [finish("p0", "p5", 100, seconds=first), finish("p1", "p6", 300, seconds=last)]
    result = analyze(events, {f"p{i}": i//5 for i in range(10)}, [200])
    assert result["full_order_changed"]
    assert result["reversals"][0]["earlier"]["offset"] == 100
    assert result["reversals"][0]["cross_plant_state"]


def test_trade_identity_and_timing_remain_unresolved_in_split_case():
    c = credit(); c["finishes"] = [finish("p1", "p5", 100), finish("p6", "p1", 200, seconds=85)]
    events = event_inventory(c)
    assert events[0]["finisher"] == events[1]["victim"]
    assert events[0]["credited_killer"] is None
    assert events[0]["elimination_elapsed_time"] is None
    assert "trade" not in events[1]
