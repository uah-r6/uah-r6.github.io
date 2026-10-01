"""Y11S3 MatchReplay structure, reduced from a locally generated September 2026 replay.

Only the schema and round metadata are retained; real player IDs stay out of Git.
"""
import json
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from r6stats.admin.server import create_app
from r6stats.db import repository as repo
from r6stats.parser.siege_dissect import map_label, normalize, parse_match, physical_round_numbers
from r6stats.stats.calculate import calculate_match


NAME = "Match-2026-09-28_20-43-56-29164"


def test_occurrence_metadata_survives_normalization_without_player_credit():
    from r6stats.parser.models import Match

    raw = round_json(0, 1)
    baseline = normalize([raw])
    raw['objectiveOccurrences'] = [
        {'kind': 'plant', 'source': 'defuser_state_v1', 'actor': None, 'plantStateOffset': 123},
        {'kind': 'disable', 'source': 'defuser_state_and_defense_win_v1', 'actor': None, 'plantStateOffset': 123}]
    parsed = normalize([raw])
    assert [o.kind for o in parsed.rounds[0].objective_occurrences] == ['plant', 'disable']
    assert parsed.rounds[0].objectives == []
    assert calculate_match(parsed) == calculate_match(baseline)
    restored = Match.from_dict(parsed.to_dict())
    assert restored == parsed
    old = baseline.to_dict()
    old['rounds'][0].pop('objective_occurrences')
    assert Match.from_dict(old).rounds[0].objective_occurrences == []


def test_occurrence_metadata_cannot_smuggle_unverified_actor_credit():
    raw = round_json(0, 0)
    raw['objectiveOccurrences'] = [
        {'kind': 'plant', 'source': 'defuser_state_v1', 'actor': 'ExampleTeammate', 'plantStateOffset': 123}]
    parsed = normalize([raw])
    assert parsed.rounds[0].objectives == []
    assert parsed.rounds[0].objective_occurrences == []


def test_4139_r7_occurrence_leaves_rejected_aiden_actor_unresolved():
    raw = round_json(6, 0)
    raw['players'][0]['username'] = 'Aiden.SSG'
    raw['players'].append({'profileID': 'raid', 'username': 'Raid.SSG', 'teamIndex': 0,
                           'operator': {'name': 'Ace'}})
    raw['matchFeedback'] = [{'type': 'DefuserPlantComplete', 'username': 'Aiden.SSG',
                              'timeInSeconds': 25}]
    raw['objectiveOccurrences'] = [{'kind': 'plant', 'source': 'defuser_state_v1',
                                    'actor': None, 'plantStateOffset': 61871641}]
    parsed = normalize([raw], round_numbers=[7])
    assert parsed.rounds[0].objectives == []
    assert parsed.rounds[0].objective_occurrences[0].actor is None


def round_json(parser_number: int, winner: int) -> dict:
    return {"gameVersion": "Y11S3_Alpha04", "timestamp": "2026-09-28T20:45:14Z",
            "matchID": "example-match", "roundNumber": parser_number,
            "overtimeRoundNumber": 0, "matchType": {"name": "Ranked", "id": 2},
            "map": {"name": "Map(409325881472)", "id": 409325881472},
            "gamemode": {"name": "Bomb"}, "site": "2F Aviator Room, 2F Games Room",
            "teams": [{"won": winner == 0, "role": "Attack"},
                      {"won": winner == 1, "role": "Defense"}],
            "players": [{"profileID": "ours", "username": "ExampleTeammate", "teamIndex": 0,
                         "operator": {"name": "Buck"}},
                        {"profileID": "theirs", "username": "ExampleOpponent", "teamIndex": 1,
                         "operator": {"name": "Mute"}}],
            "matchFeedback": []}


def test_current_zero_based_parser_rounds_use_physical_sources(tmp_path: Path):
    folder = tmp_path / NAME
    folder.mkdir()
    files = [folder / f"{NAME}-R{number:02}.rec" for number in (1, 2, 3)]
    for number, file in enumerate(files, 1):
        file.write_bytes(f"replay placeholder {number}".encode())
    raw = {"rounds": [round_json(0, 0), round_json(1, 1), round_json(2, 0)], "stats": []}

    def fake_parser(_command, *, capture_output, text, timeout):
        assert Path(_command[1]) == folder
        Path(_command[3]).write_text(json.dumps(raw), encoding="utf-8")
        return type("Result", (), {"returncode": 0, "stderr": "", "stdout": ""})()

    with patch("r6stats.parser.siege_dissect.parser_executable", return_value="siege-dissect"), \
         patch("r6stats.parser.siege_dissect.subprocess.run", side_effect=fake_parser):
        match = parse_match(folder)
    assert [round_.number for round_ in match.rounds] == [1, 2, 3]
    assert match.map_name == "Villa"
    assert match.match_type == "Ranked"
    assert [sum(round_.winner == team for round_ in match.rounds) for team in (0, 1)] == [2, 1]


def test_duplicate_or_missing_physical_rounds_still_rejected(tmp_path: Path):
    first = tmp_path / "Match-one-R01.rec"
    duplicate = tmp_path / "Match-two-R01.rec"
    second = tmp_path / "Match-one-R02.rec"
    third = tmp_path / "Match-one-R03.rec"
    assert physical_round_numbers([first, second, third]) == [1, 2, 3]
    with pytest.raises(ValueError, match="duplicate physical"):
        physical_round_numbers([first, duplicate])
    with pytest.raises(ValueError, match="complete"):
        physical_round_numbers([first, third])
    with pytest.raises(ValueError, match="suffix"):
        physical_round_numbers([tmp_path / "round1.rec"])


def test_copied_round_contents_are_rejected(tmp_path: Path):
    folder = tmp_path / NAME
    folder.mkdir()
    for number in (1, 2):
        (folder / f"{NAME}-R{number:02}.rec").write_bytes(b"same physical round")
    with patch("r6stats.parser.siege_dissect.parser_executable", return_value="siege-dissect"), \
         patch("r6stats.parser.siege_dissect.subprocess.run") as parser:
        with pytest.raises(ValueError, match="duplicate physical .rec file contents"):
            parse_match(folder)
        parser.assert_not_called()


def test_parser_round_count_and_duplicate_numbers_rejected():
    raw = {"rounds": [round_json(0, 0), round_json(1, 1)]}
    with pytest.raises(ValueError, match="round count"):
        normalize(raw, round_numbers=[1])
    with pytest.raises(ValueError, match="duplicate physical"):
        normalize(raw, round_numbers=[1, 1])
    assert [r.number for r in normalize(raw).rounds] == [1, 2]


def test_one_round_is_visible_for_scan_but_cannot_be_imported(tmp_path: Path):
    folder = tmp_path / NAME
    folder.mkdir()
    (folder / f"{NAME}-R01.rec").write_bytes(b"replay placeholder")
    raw = round_json(0, 0)

    def fake_parser(command, *, capture_output, text, timeout):
        Path(command[3]).write_text(json.dumps(raw), encoding="utf-8")
        return type("Result", (), {"returncode": 0, "stderr": "", "stdout": ""})()

    with patch("r6stats.parser.siege_dissect.parser_executable", return_value="siege-dissect"), \
         patch("r6stats.parser.siege_dissect.subprocess.run", side_effect=fake_parser):
        assert len(parse_match(folder, allow_incomplete=True).rounds) == 1
        with pytest.raises(ValueError, match="multiple .rec"):
            parse_match(folder)


def test_current_map_ids_from_replay_metadata():
    assert map_label({"name": "Map(409325881472)", "id": 409325881472}) == "Villa"
    assert map_label({"name": "Map(398899676157)", "id": 398899676157}) == "Fortress"
    assert map_label({"name": "Map(436375283234)", "id": 436375283234}) == "Coastline"
    assert map_label({"name": "Map(123)", "id": 123}) == "Map(123)"


def test_y11_attack_operator_uses_confirmed_action_start_selection():
    raw = round_json(0, 0)
    raw["matchType"] = {"name": "CustomGameOnline", "id": 4}
    raw["actionPhaseDetected"] = True
    attacker = raw["players"][0]
    attacker["initialOperator"] = {"name": "Deimos", "id": 374667787816}
    attacker["operator"] = {"name": "Zofia", "id": 92270644189}
    attacker["operatorSource"] = "action_start_header"
    attacker["operatorSeenBeforeAction"] = True
    match = normalize(raw)
    assert match.rounds[0].players[0].operator == "Zofia"
    stats = calculate_match(match)["ours"]
    assert stats["operators"]["Attack"] == {"Zofia": 1}

    # A stale parser or a missing Y11 snapshot must not count the initial pick.
    attacker.pop("operatorSource")
    match = normalize(raw)
    assert match.rounds[0].players[0].operator == "Unknown"
    stats = calculate_match(match)["ours"]
    assert stats["sides"]["Attack"]["rounds"] == 1
    assert stats["operators"]["Attack"] == {}


def test_admin_scan_endpoint_uses_physical_rounds_for_zero_based_parser_output(tmp_path: Path):
    folder = tmp_path / "replays" / NAME
    folder.mkdir(parents=True)
    for number in range(1, 7):
        (folder / f"{NAME}-R{number:02}.rec").write_bytes(f"round {number}".encode())
    config = tmp_path / "config"
    config.mkdir()
    (config / "settings.json").write_text(json.dumps({
        "team": {"name": "Test", "short_name": "T", "accent": "#82e3db"},
        "replays": {"path": str(folder.parent)},
        "stats": {"trade_window_seconds": 8, "rating_version": "collegiate_v1"},
        "publishing": {"enabled": False, "branch": "main"},
    }), encoding="utf-8")
    raw = {"rounds": [round_json(number, 0 if number < 2 else 1)
                      for number in range(6)]}
    for row in raw["rounds"]:
        row["players"].extend({"profileID": f"ours-{number}", "username": f"Teammate{number}",
                               "teamIndex": 0, "operator": {"name": "Buck"}}
                              for number in (2, 3))
    with repo.connect(tmp_path / "data/r6stats.sqlite") as db:
        for username in ("ExampleTeammate", "Teammate2", "Teammate3"):
            repo.roster_add(db, username)

    def fake_parser(command, *, capture_output, text, timeout):
        assert Path(command[1]) == folder
        Path(command[3]).write_text(json.dumps(raw), encoding="utf-8")
        return type("Result", (), {"returncode": 0, "stderr": "", "stdout": ""})()

    with patch("r6stats.parser.siege_dissect.parser_executable", return_value="siege-dissect"), \
         patch("r6stats.parser.siege_dissect.subprocess.run", side_effect=fake_parser), \
         TestClient(create_app(tmp_path)) as client:
        response = client.get("/api/admin/replays")
        assert response.status_code == 200
        assert response.headers["Cache-Control"] == "no-store"
        replay = response.json()[0]
        assert replay["name"] == NAME
        assert replay["map"] == "Villa"
        assert replay["rounds"] == 6
        assert replay["match_type"] == "Ranked"
        assert replay["eligible"] is False
        assert replay["status"] == "INELIGIBLE - Ranked"
        assert replay["score"] == [2, 4]
        assert replay["our_team"] == 0
        assert replay["tracked_count"] == 3
        assert "duplicate round numbers" not in json.dumps(response.json())

    import sqlite3
    with sqlite3.connect(tmp_path / "data/r6stats.sqlite") as db:
        assert db.execute("SELECT count(*) FROM maps").fetchone()[0] == 0
