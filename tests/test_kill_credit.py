import copy
from uuid import UUID

import pytest

from r6stats.kill_credit import SOURCE, validate_map_credit, project_credited_counts
from r6stats.parser.models import Match, Round, Player, Kill


def records():
    rows = []
    for number in (1, 2):
        players = [dict(uid=i+1, profileID=str(UUID(int=i+1)), username=f"p{i}",
                        team=i//5, initial=number-1, terminal=number, kills=1, reason=SOURCE)
                   for i in range(10)]
        rows.append(dict(logical_round=number, physical_round=number, segment="original",
                         credit=dict(source=SOURCE, complete=True, players=players)))
    return rows


def test_round_deltas_and_profile_identity_survive_alias_and_uid_changes():
    rows = records()
    rows[1]["credit"]["players"][0].update(username="new.name", uid=101)
    result = validate_map_credit(rows)
    assert result["complete"] and set(result["totals"].values()) == {2}


def test_explicit_rehost_reset_preserves_participation_and_segment_deltas():
    rows = records()
    rows[1].update(segment="rehost", physical_round=1)
    for p in rows[1]["credit"]["players"]:
        p.update(initial=0, terminal=2, kills=2, uid=p["uid"]+100)
    result = validate_map_credit(rows)
    assert result["complete"] and len(result["resets"]) == 1
    assert set(result["totals"].values()) == {3}


@pytest.mark.parametrize("mutation", ["same_folder", "R02", "profile_changed", "nil_profiles", "missing_player"])
def test_unproven_reset_or_participation_refuses_total(mutation):
    rows = records()
    rows[1].update(segment="rehost", physical_round=1)
    for p in rows[1]["credit"]["players"]:
        p.update(initial=0, terminal=1, kills=1)
    if mutation == "same_folder": rows[1].update(segment="original", physical_round=2)
    if mutation == "R02": rows[1]["physical_round"] = 2
    if mutation == "profile_changed": rows[1]["credit"]["players"][0]["profileID"] = str(UUID(int=100))
    if mutation == "nil_profiles":
        for r in rows:
            for p in r["credit"]["players"]: p["profileID"] = str(UUID(int=0))
    if mutation == "missing_player": rows[1]["credit"]["players"].pop()
    result = validate_map_credit(rows)
    assert not result["complete"] and result["totals"] is None and result["issues"]


@pytest.mark.parametrize("value", [None, True, -1, 6])
def test_invalid_or_unknown_delta_never_zero_filled(value):
    rows = records(); rows[0]["credit"]["players"][0]["kills"] = value
    assert not validate_map_credit(rows)["complete"]


def test_duplicate_physical_or_missing_logical_sources_refused():
    for field, value in (("physical_round", 1), ("logical_round", 3)):
        rows = records(); rows[1][field] = value
        with pytest.raises(ValueError): validate_map_credit(rows)


def test_display_projection_leaves_finish_event_death_and_frozen_rating_intact():
    rows = records()[:1]
    for p in rows[0]["credit"]["players"]: p.update(initial=0, terminal=0, kills=0)
    rows[0]["credit"]["players"][0].update(terminal=1, kills=1)
    players = [Player(str(UUID(int=i+1)), f"p{i}", i//5, "Unknown", "Attack" if i<5 else "Defense") for i in range(10)]
    # Finisher p1 receives no counter kill. Already-dead p0 receives credit.
    match = Match("id", "date", "map", "Custom Game", "Bomb", [Round(1,"site",0,"win",players,
        [Kill(0,100,"",players[0].key,-1,0), Kill(1,90,players[1].key,players[5].key,0,1)])])
    before = copy.deepcopy(match.to_dict())
    view = project_credited_counts(match, validate_map_credit(rows))
    assert view[players[0].key]["kills"] == 1 and view[players[0].key]["deaths"] == 1
    assert view[players[1].key]["kills"] == 0
    assert view[players[1].key]["original_finisher_statistics"]["kills"] == 1
    assert match.to_dict() == before


def test_incomplete_projection_fails_without_mutating_match():
    with pytest.raises(ValueError): project_credited_counts(None, {"complete": False})


def test_credited_multikill_projection_keeps_original_rating_features():
    rows = records()[:1]
    for p in rows[0]["credit"]["players"]: p.update(initial=0, terminal=0, kills=0)
    rows[0]["credit"]["players"][0].update(terminal=3, kills=3)
    players = [Player(str(UUID(int=i+1)), f"p{i}", i//5) for i in range(10)]
    match = Match("id", "date", "map", "Custom Game", "Bomb", [Round(1,"site",0,"win",players)])
    view = project_credited_counts(match,validate_map_credit(rows))[players[0].key]
    assert view["credited_multikill_sizes"] == {2:0, 3:1, 4:0, 5:0}
    assert view["credited_multikill_extra"] == 2 and view["credited_kill_rounds"] == 1
    assert view["original_finisher_statistics"]["multikill_extra"] == 0


def test_confirmed_rehost_team_index_flip_joins_profiles_bijectively():
    rows = records()[:1]
    for p in rows[0]["credit"]["players"]: p["team"] = 1-p["team"]
    players = [Player(str(UUID(int=i+1)).upper(), f"p{i}", i//5) for i in range(10)]
    match = Match("id", "date", "map", "Custom Game", "Bomb", [Round(1,"site",0,"win",players)])
    assert project_credited_counts(match,validate_map_credit(rows))[players[0].key]["kills"] == 1
    players[0].team = 1
    with pytest.raises(ValueError, match="team mismatch"):
        project_credited_counts(match,validate_map_credit(rows))
