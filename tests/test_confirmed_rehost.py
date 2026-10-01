"""Explicit local rehosts preserve physical evidence and count only selected rounds."""
from dataclasses import replace
from pathlib import Path
from contextlib import closing
from unittest.mock import patch

import pytest

from r6stats.db import repository as repo
from r6stats.parser.confirmed_rehost import (assemble_rehost, physical_segment,
                                             source_fingerprint, stitch_confirmed)
from r6stats.parser.logical_map import PhysicalSegment
from r6stats.parser.models import Kill, Match, Player, Round
from r6stats import replay_archive
from r6stats.stats.calculate import calculate_match


def segment(root: Path, name: str, winners: list[int], *, swapped: bool = False):
    folder = root / name
    folder.mkdir()
    rounds = []
    for number, winner in enumerate(winners, start=1):
        (folder / f"{name}-R{number:02d}.rec").write_bytes(f"{name}:{number}".encode())
        players = [Player(f"ours-{i}", f"Our{i}", int(swapped), "Buck", "Attack")
                   for i in range(5)] + [
            Player(f"foe-{i}", f"Foe{i}", int(not swapped), "Wamai", "Defense")
            for i in range(5)]
        kill = Kill(0, 100, "ours-0", "foe-0", int(swapped), int(not swapped))
        rounds.append(Round(number, "Site", winner, "KilledOpponents", players, [kill]))
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


def test_rehost_rejects_unrelated_or_duplicate_sources(tmp_path):
    first = segment(tmp_path, "segment1", [0])
    second = segment(tmp_path, "segment2", [1])
    with pytest.raises(ValueError, match="once"):
        stitch_confirmed([first, first], excluded={})
    with pytest.raises(ValueError, match="not found"):
        stitch_confirmed([first, second], excluded={("segment-02", 9): "abandoned"})
    rosters = second.rounds[0].rosters
    unrelated = replace(second.rounds[0], rosters=(('unrelated', *rosters[0][1:]), rosters[1]))
    second = PhysicalSegment(second.match, (unrelated,))
    with pytest.raises(ValueError, match="different player identities"):
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
