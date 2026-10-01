"""Explicit local rehosts preserve physical evidence and count only selected rounds."""
from dataclasses import replace
from pathlib import Path
from contextlib import closing
from unittest.mock import patch

import pytest

from r6stats.db import repository as repo
from r6stats.parser.confirmed_rehost import (assemble_rehost, physical_segment,
                                             source_fingerprint, stitch_confirmed)
from r6stats.parser.models import Kill, Match, Objective, Player, Round
from r6stats import replay_archive
from r6stats.stats.calculate import calculate_match


def segment(root: Path, name: str, winners: list[int], *, swapped: bool = False,
            ours_count: int = 5, start_score: tuple[int, int] | None = None,
            ours_side: str = "Attack"):
    folder = root / name
    folder.mkdir()
    rounds = []
    score = list(start_score or (0, 0))
    for number, winner in enumerate(winners, start=1):
        (folder / f"{name}-R{number:02d}.rec").write_bytes(f"{name}:{number}".encode())
        players = [Player(f"ours-{i}", f"Our{i}", int(swapped), "Buck", ours_side)
                   for i in range(ours_count)] + [
            Player(f"foe-{i}", f"Foe{i}", int(not swapped), "Wamai",
                   "Defense" if ours_side == "Attack" else "Attack")
            for i in range(5)]
        kill = Kill(0, 100, "ours-0", "foe-0", int(swapped), int(not swapped))
        before = tuple(score)
        score[winner] += 1
        rounds.append(Round(number, "Site", winner, "KilledOpponents", players, [kill],
                            starting_scores=before if start_score is not None else None,
                            ending_scores=tuple(score) if start_score is not None else None))
    match = Match(name, "2026-09-30T20:00:00Z", "Border", "Custom Game", "Bomb", rounds)
    return physical_segment(match, folder, int(name[-1]))


def test_two_segment_reset_and_explicit_abandoned_round(tmp_path):
    first = segment(tmp_path, "segment1", [0, 1, 0])
    second = segment(tmp_path, "segment2", [0, 1])  # physical score restarts at 0-0
    logical = stitch_confirmed([first, second],
                               excluded={("segment-01", 3): "abandoned rehost"},
                               expected_final_scores=(2, 2))
    assert [item.logical_number for item in logical.mapping] == [1, 2, None, 3, 4]
    assert [item.physical_number for item in logical.mapping] == [1, 2, 3, 1, 2]
    assert logical.final_scores == (2, 2)
    assert [round_.number for round_ in logical.match.rounds] == [1, 2, 3, 4]
    assert calculate_match(logical.match)["ours-0"]["kills"] == 4
    with pytest.raises(ValueError, match="confirmed score"):
        stitch_confirmed([first, second], excluded={("segment-01", 3): "abandoned"},
                         expected_final_scores=(3, 2))
    all_count = stitch_confirmed([first, second], excluded={}, expected_final_scores=(3, 2))
    assert len(all_count.match.rounds) == 5


def test_three_segments_and_swapped_team_indices(tmp_path):
    first = segment(tmp_path, "segment1", [0])
    second = segment(tmp_path, "segment2", [1])
    third = segment(tmp_path, "segment3", [1], swapped=True)
    logical = stitch_confirmed([first, second, third], excluded={},
                               expected_final_scores=(2, 1))
    assert logical.final_scores == (2, 1)
    assert logical.match.rounds[-1].winner == 0
    assert next(p for p in logical.match.rounds[-1].players if p.key == "ours-0").team == 0
    assert logical.match.rounds[-1].kills[0].killer_team == 0
    assert calculate_match(logical.match)["ours-0"]["kills"] == 3


def test_score_preserving_rehost_needs_no_override_and_keeps_physical_sides(tmp_path):
    first = segment(tmp_path, "segment1", [0, 1], start_score=(0, 0))
    second = segment(tmp_path, "segment2", [0, 1], start_score=(1, 1),
                     ours_side="Defense")
    logical = stitch_confirmed([first, second], excluded={}, expected_final_scores=(2, 2))
    assert logical.segment_details[1]["physical_start"] == [1, 1]
    assert logical.segment_details[1]["score_mode"] == "continued"
    ours = calculate_match(logical.match)["ours-0"]
    assert ours["rounds"] == 4
    assert ours["sides"]["Attack"]["rounds"] == 2
    assert ours["sides"]["Defense"]["rounds"] == 2
    assert ours["operators"]["Attack"] == {"Buck": 2}
    assert ours["operators"]["Defense"] == {"Buck": 2}


def test_5v5_to_4v5_counts_only_actual_player_participation(tmp_path):
    first = segment(tmp_path, "segment1", [0, 1], start_score=(0, 0))
    second = segment(tmp_path, "segment2", [0, 1], ours_count=4,
                     start_score=(1, 1), ours_side="Defense")
    logical = stitch_confirmed([first, second], excluded={}, expected_final_scores=(2, 2))
    assert [len(r.players) for r in logical.match.rounds] == [10, 10, 9, 9]
    assert logical.segment_details[1]["score_mode"] == "continued"
    stats = calculate_match(logical.match)
    absent = stats["ours-4"]
    assert absent["rounds"] == 2 and absent["deaths"] == 0
    assert absent["kost_rounds"] == 2 and absent["survived"] == 2
    assert absent["operators"]["Defense"] == {}
    assert absent["sides"]["Defense"]["rounds"] == 0
    assert absent["kpr"] == 0 and absent["kost"] == 1
    assert stats["ours-0"]["rounds"] == 4
    assert stats["ours-0"]["sides"]["Defense"]["rounds"] == 2
    assert sum(r.winner == 0 for r in logical.match.rounds) == 2


def test_malformed_rehost_score_is_explicitly_marked_as_override(tmp_path):
    first = segment(tmp_path, "segment1", [0, 1], start_score=(0, 0))
    second = segment(tmp_path, "segment2", [0, 1], start_score=(0, 0))
    logical = stitch_confirmed([first, second], excluded={}, expected_final_scores=(2, 2))
    assert logical.segment_details[1]["physical_start"] == [0, 0]
    assert logical.segment_details[1]["logical_start"] == [1, 1]
    assert logical.segment_details[1]["score_mode"] == "override_0_0"
    second_bad = segment(tmp_path, "segment3", [0], start_score=(2, 0))
    with pytest.raises(ValueError, match="starting scores disagree"):
        stitch_confirmed([first, second_bad], excluded={})


def test_one_round_abandoned_segment_is_preserved_but_not_counted(tmp_path):
    first = segment(tmp_path, "segment1", [0, 1], start_score=(0, 0))
    abandoned = segment(tmp_path, "segment2", [0], start_score=(1, 1))
    abandoned.match.rounds[0].ending_scores = (1, 1)
    third = segment(tmp_path, "segment3", [0, 1], start_score=(1, 1))
    paths = [tmp_path / f"segment{i}" for i in (1, 2, 3)]
    with patch("r6stats.parser.confirmed_rehost.parse_match",
               side_effect=[first.match, abandoned.match, third.match]):
        logical, manifest, _ = assemble_rehost(
            paths, [{"segment": 2, "physical_number": 1, "reason": "abandoned lobby"}],
            (2, 2))
    assert [item.logical_number for item in logical.mapping] == [1, 2, None, 3, 4]
    assert logical.final_scores == (2, 2)
    assert logical.segment_details[1]["score_mode"] == "continued"
    assert manifest["mapping"][2]["exclusion_reason"] == "abandoned lobby"
    assert len(logical.match.rounds) == 4


def test_excluded_physical_round_never_contributes_to_any_stat_family(tmp_path):
    first = segment(tmp_path, "segment1", [0, 1])
    second = segment(tmp_path, "segment2", [0])
    counted = first.match.rounds[0]
    counted.kills = [Kill(0, 99, "foe-0", "ours-1", 1, 0),
                     Kill(1, 95, "ours-0", "foe-0", 0, 1),
                     Kill(2, 90, "foe-1", "ours-2", 1, 0),
                     Kill(3, 85, "foe-2", "ours-3", 1, 0),
                     Kill(4, 80, "foe-3", "ours-4", 1, 0)]
    counted.objectives = [Objective("plant", "ours-0", 0, 30)]
    excluded_round = first.match.rounds[1]
    excluded_round.players[0].operator = "Deimos"
    excluded_round.kills = [Kill(0, 100, "ours-0", "foe-0", 0, 1),
                            Kill(1, 90, "foe-1", "ours-0", 1, 0)]
    excluded_round.objectives = [Objective("plant", "ours-0", 0, 35),
                                 Objective("disable", "foe-0", 1, 15)]
    logical = stitch_confirmed([first, second],
                               excluded={("segment-01", 2): "abandoned round"},
                               expected_final_scores=(2, 0))
    observed = calculate_match(logical.match)
    direct_counted = Match("expected", first.match.timestamp, "Border", "Custom Game",
                           "Bomb", [counted, second.match.rounds[0]])
    assert observed == calculate_match(direct_counted)
    ours = observed["ours-0"]
    assert ours["rounds"] == 2 and ours["kills"] == 2 and ours["deaths"] == 0
    assert ours["opening_kills"] == 1 and ours["refrag_kills"] == 1
    assert ours["clutch_1v4"] == 1 and ours["kost_rounds"] == 2
    assert ours["plants"] == 1 and ours["operators"]["Attack"] == {"Buck": 2}
    assert observed["ours-1"]["deaths_traded"] == 1
    assert observed["foe-0"]["disables"] == 0


def test_rehost_rejects_unrelated_or_duplicate_sources(tmp_path):
    first = segment(tmp_path, "segment1", [0])
    second = segment(tmp_path, "segment2", [1])
    with pytest.raises(ValueError, match="once"):
        stitch_confirmed([first, first], excluded={})
    with pytest.raises(ValueError, match="not found"):
        stitch_confirmed([first, second], excluded={("segment-02", 9): "abandoned"})
    unrelated_round = replace(second.match.rounds[0], players=[
        replace(player, profile_id=f"unrelated-{index}")
        for index, player in enumerate(second.match.rounds[0].players)])
    unrelated_match = replace(second.match, rounds=[unrelated_round])
    second = physical_segment(unrelated_match, tmp_path / "segment2", 2)
    with pytest.raises(ValueError, match="lack a clear shared player identity"):
        stitch_confirmed([first, second], excluded={})


def test_explicit_rehost_allows_long_downtime(tmp_path):
    first = segment(tmp_path, "segment1", [0])
    second = segment(tmp_path, "segment2", [1])
    next_day = "2026-10-01T21:00:00Z"
    second = replace(second, match=replace(second.match, timestamp=next_day),
                     rounds=tuple(replace(round_, timestamp=next_day) for round_ in second.rounds))
    logical = stitch_confirmed([first, second], excluded={}, expected_final_scores=(1, 1))
    assert len(logical.match.rounds) == 2


@pytest.mark.parametrize("field,value", [("map_name", "Villa"),
                                         ("game_mode", "Secure Area"),
                                         ("match_type", "Ranked")])
def test_explicit_rehost_rejects_incompatible_segments(tmp_path, field, value):
    first = segment(tmp_path, "segment1", [0])
    second = segment(tmp_path, "segment2", [1])
    second = replace(second, match=replace(second.match, **{field: value}))
    with pytest.raises(ValueError, match="disagree on map or game type"):
        stitch_confirmed([first, second], excluded={})


def test_source_registry_prevents_importing_a_segment_again(tmp_path):
    first = segment(tmp_path, "segment1", [0])
    second = segment(tmp_path, "segment2", [1])
    logical = stitch_confirmed([first, second], excluded={}, expected_final_scores=(1, 1))
    source_rows = [{"replay_id": item.match.replay_id,
                    "fingerprint": source_fingerprint(tmp_path / f"segment{index}"),
                    "source_name": f"segment{index}"}
                   for index, item in enumerate((first, second), start=1)]
    with closing(repo.connect(tmp_path / "tracker.sqlite")) as db:
        repo.season_create(db, "Fall 2026")
        for index in range(5):
            repo.roster_add(db, f"Our{index}")
        map_id = repo.insert_map(db, logical.match, "logical-fingerprint", 0, "Opponent",
                                 rehost_manifest={"mapping": []}, source_segments=source_rows)
        assert db.execute("SELECT count(*) FROM map_segments WHERE map_id=?", (map_id,)).fetchone()[0] == 2
        with pytest.raises(ValueError, match="already been imported"):
            repo.insert_map(db, first.match, source_rows[0]["fingerprint"], 0, "Opponent")


def test_rehost_archive_keeps_excluded_physical_round_and_verifies_all_segments(tmp_path):
    first = segment(tmp_path, "segment1", [0, 1, 0])
    second = segment(tmp_path, "segment2", [0, 1])
    paths = [tmp_path / "segment1", tmp_path / "segment2"]
    with patch("r6stats.parser.confirmed_rehost.parse_match",
               side_effect=[first.match, second.match]):
        logical, manifest, fingerprint = assemble_rehost(
            paths, [{"segment": 1, "physical_number": 3, "reason": "abandoned"}], (2, 2))
    archive_root = tmp_path / "archive"
    with closing(repo.connect(tmp_path / "tracker.sqlite")) as db:
        repo.season_create(db, "Fall 2026")
        for index in range(5):
            repo.roster_add(db, f"Our{index}")
        map_id = repo.insert_map(db, logical.match, fingerprint, 0, "Opponent",
                                 rehost_manifest=manifest, source_segments=manifest["segments"])
        prepared = replay_archive.prepare_rehost(paths, archive_root, fingerprint, manifest)
        try:
            target = replay_archive.commit_rehost(prepared, archive_root, db, map_id)
        finally:
            prepared.cleanup()
        assert (target / "segment-01/segment1-R03.rec").exists()
        assert (target / "segment-02/segment2-R01.rec").exists()
        assert replay_archive.verify(db, archive_root, map_id)["status"] == "Healthy"
        stored = (target / "segment-01/segment1-R03.rec").read_bytes()
        (target / "segment-01/segment1-R03.rec").write_bytes(b"tampered")
        assert replay_archive.verify(db, archive_root, map_id)["status"] == "Hash mismatch"
        (target / "segment-01/segment1-R03.rec").write_bytes(stored)
        replay_archive.delete_map_and_archive(db, archive_root, map_id)
        assert not target.exists()
        assert db.execute("SELECT count(*) FROM players").fetchone()[0] == 5
