"""Logical-round fixtures use score sequences from real 2026 rehosts."""
from dataclasses import replace
import json
from pathlib import Path

import pytest

from r6stats.parser.logical_map import PhysicalRound, PhysicalSegment, stitch_segments
from r6stats.parser.models import Kill, Match, Objective, Player, Round
from r6stats.stats.calculate import calculate_match

CASES = json.loads((Path(__file__).parent / "fixtures/rehost_cases.json").read_text())["cases"]


def segments_for(case):
    result = []
    for segment_index, states in enumerate(case["segments"]):
        replay_id = f"replay-{case['id']}-{segment_index}"
        rounds, sources = [], []
        folder = f"physical-segment-{segment_index}"
        for physical_number, score in enumerate(states, start=1):
            starts = tuple(team[0] for team in score)
            ends = tuple(team[1] for team in score)
            winner = next(team for team in (0, 1) if ends[team] - starts[team] == 1)
            players = [Player("a", "A", 0, "Ace", "Attack"),
                       Player("b", "B", 0, "Sledge", "Attack"),
                       Player("c", "C", 1, "Mute", "Defense"),
                       Player("d", "D", 1, "Jager", "Defense")]
            excluded = [segment_index, physical_number] == case["excluded"]
            if excluded and case["id"] == 8007:
                players.pop()  # The real M80-Shopify abandoned R08 has nine players.
            killer, victim = ("a", "c") if winner == 0 else ("c", "a")
            kills = [Kill(0, 100, killer, victim, winner, 1 - winner)]
            objectives = []
            if excluded:
                # Excluded physical activity must never contribute to aggregates.
                kills.append(Kill(1, 90, killer, "d" if winner == 0 else "b",
                                  winner, 1 - winner))
                objectives.append(Objective("plant", killer, winner, 80))
            elif segment_index == 1 and physical_number == 1:
                objectives.append(Objective("plant", "b", 0, 80))
            round_ = Round(physical_number, "Site", winner, "KilledOpponents",
                           players, kills, objectives)
            rounds.append(round_)
            rosters = tuple(tuple(sorted(p.key for p in players if p.team == team))
                            for team in (0, 1))
            sources.append(PhysicalRound(folder, f"{folder}-R{physical_number:02d}.rec",
                                         f"digest-{case['id']}-{segment_index}-{physical_number}",
                                         replay_id, f"2026-06-25T{12 + segment_index * 4:02d}:00:00Z",
                                         physical_number, round_, starts, ends, rosters))
        match = Match(replay_id, sources[0].timestamp, case["map"],
                      "Custom Game", "Bomb", rounds)
        result.append(PhysicalSegment(match, tuple(sources)))
    return result


@pytest.mark.parametrize("case", CASES, ids=lambda case: str(case["id"]))
def test_real_rehost_score_sequences_exclude_only_abandoned_round(case):
    physical = segments_for(case)
    logical = stitch_segments(physical, expected_final_scores=tuple(case["final_scores"]))
    assert sum(len(segment.rounds) for segment in physical) == 13
    assert len(logical.match.rounds) == sum(case["final_scores"]) == 12
    assert [round_.number for round_ in logical.match.rounds] == list(range(1, 13))
    excluded = [item for item in logical.mapping if item.logical_number is None]
    assert len(excluded) == 1
    assert excluded[0].folder == f"physical-segment-{case['excluded'][0]}"
    assert excluded[0].physical_number == case["excluded"][1]
    assert excluded[0].exclusion_reason == "score_reset_before_next_segment"
    stats = calculate_match(logical.match)
    assert sum(item["kills"] for item in stats.values()) == 12
    assert sum(item["deaths"] for item in stats.values()) == 12
    assert sum(item["opening_kills"] for item in stats.values()) == 12
    assert sum(item["kost_rounds"] for item in stats.values()) == 36
    assert sum(item["plants"] for item in stats.values()) == 1
    assert sum(item["operators"]["Attack"].get("Ace", 0) for item in stats.values()) == 12
    assert all(max(sum(k.killer == player for k in round_.kills) for player in ("a", "c")) == 1
               for round_ in logical.match.rounds)
    repeated = stitch_segments(physical, expected_final_scores=tuple(case["final_scores"]))
    assert repeated.match.to_dict() == logical.match.to_dict()
    assert repeated.mapping == logical.mapping


def test_single_normal_segment_keeps_every_round():
    segment = segments_for(CASES[0])[0]
    scores = segment.rounds[-1].ending_scores
    logical = stitch_segments([segment], expected_final_scores=scores)
    assert len(logical.match.rounds) == len(segment.rounds)
    assert all(item.exclusion_reason is None for item in logical.mapping)


def test_rehost_join_rejects_unrelated_maps_and_unreachable_score():
    first, second = segments_for(CASES[0])
    unrelated = replace(second, match=replace(second.match, map_name="Bank"))
    with pytest.raises(ValueError, match="map or match type"):
        stitch_segments([first, unrelated])
    shifted = tuple(replace(source,
                            starting_scores=tuple(value + 10 for value in source.starting_scores),
                            ending_scores=tuple(value + 10 for value in source.ending_scores))
                    for source in second.rounds)
    bad_second = replace(second, rounds=shifted)
    with pytest.raises(ValueError, match="score-continuous"):
        stitch_segments([first, bad_second])


def test_real_missing_round_rehost_is_not_fabricated():
    # Official 7999 has two physical rounds ending 2-0; the next segment
    # starts 2-1. The Wildcard win between them is absent from both replays.
    case = {"id": 7999, "map": "Kafe", "excluded": None,
            "segments": [
                [[[0, 1], [0, 0]], [[1, 2], [0, 0]]],
                [[[2, 3], [1, 1]], [[3, 3], [1, 2]], [[3, 3], [2, 3]],
                 [[3, 4], [3, 3]], [[4, 5], [3, 3]], [[5, 5], [3, 4]],
                 [[5, 5], [4, 5]], [[5, 5], [5, 6]], [[5, 5], [6, 7]]]]}
    with pytest.raises(ValueError, match="score-continuous"):
        stitch_segments(segments_for(case), expected_final_scores=(5, 7))


def test_rehost_join_rejects_duplicate_segment_or_wrong_confirmed_final_score():
    first, second = segments_for(CASES[1])
    with pytest.raises(ValueError, match="same physical segment"):
        stitch_segments([first, first])
    with pytest.raises(ValueError, match="confirmed score"):
        stitch_segments([first, second], expected_final_scores=(5, 7))
