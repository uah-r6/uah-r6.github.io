import json
from copy import deepcopy
from contextlib import closing
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from r6stats import objective_refresh as refresh
from r6stats.admin.server import create_app
from r6stats.db import repository as repo
from r6stats.export import export
from r6stats.parser.models import Objective
from r6stats.parser.siege_dissect import normalize
from r6stats.replay_archive import commit, prepare, replay_fingerprint, verify
from r6stats.stats.calculate import calculate_match
from test_admin import match_fixture


def fixture():
    raw = match_fixture("CustomGameOnline", "objective-refresh")
    r = raw["rounds"][0]
    for i, p in enumerate(r["players"], 1):
        p["id"] = i
    r["matchFeedback"] = [{"type": {"name": "Kill"}, "username": "Enemy0",
                           "target": "Player0", "timeInSeconds": 30}]
    raw["rounds"].append(deepcopy(r))
    raw["rounds"][1]["roundNumber"] = 2
    original = normalize(raw)
    r["objectiveOccurrences"] = [{"kind": "plant", "source": "defuser_state_v1",
        "plantStateOffset": 100, "actor": "Player0", "actorID": 1,
        "actorSource": refresh.SOURCE, "actorReason": refresh.SOURCE}]
    return original, normalize(raw)


def setup_map(root, original):
    (root / "config").mkdir()
    config = {"team": {"name": "Test", "short_name": "T", "accent": "#82e3db"},
              "stats": {"trade_window_seconds": 8, "rating_version": "siege_style_v2"},
              "replays": {"path": ""}, "publishing": {"enabled": False, "branch": "main"}}
    (root / "config/settings.json").write_text(json.dumps(config), encoding="utf-8")
    source = root / "Match-test"
    source.mkdir()
    for n in (1, 2):
        (source / f"Match-test-R{n:02d}.rec").write_bytes(f"physical round {n}".encode())
    db = repo.connect(root / "data/r6stats.sqlite")
    repo.season_create(db, "Fall 2026")
    repo.roster_add(db, "Player0", team_id=1)
    digest = replay_fingerprint(sorted(source.glob("*.rec")))
    map_id = repo.insert_map(db, original, digest, 0, "Opponent", "Week 2", "Preserve", organization_team_id=1)
    prepared = prepare(source, root / "data/replay-archive", digest, 2)
    try:
        commit(prepared, root / "data/replay-archive", db, map_id)
    finally:
        prepared.cleanup()
    return db, map_id, config


def test_admin_stale_import_archive_refresh_recalculate_and_frozen_rating(tmp_path):
    original, parsed = fixture()
    with closing(setup_map(tmp_path, original)[0]) as db:
        map_id = db.execute("SELECT id FROM maps").fetchone()[0]
        before = dict(db.execute("SELECT * FROM maps").fetchone())
        original_rating = calculate_match(original)["ours-0"]["rating"]
    with TestClient(create_app(tmp_path)) as client:
        headers = {"X-R6-Admin-Token": client.get("/api/admin/session").json()["token"]}
        stale = client.post("/api/admin/recalculate", json={}, headers=headers)
        assert stale.status_code == 200
        path = tmp_path / f"web/public/data/matches/{map_id}.json"
        assert json.loads(path.read_text())["players"][0]["plants"] == 0
        with patch("r6stats.objective_refresh.parse_match", return_value=parsed):
            result = client.post(f"/api/admin/matches/{map_id}/reparse", json={
                "from_archive": True, "objectives_only": True, "confirm_map_id": map_id}, headers=headers)
        assert result.status_code == 200, result.text
        assert len(result.json()["changes"]) == 1
        assert client.post("/api/admin/recalculate", json={}, headers=headers).status_code == 200
        assert client.post("/api/admin/regenerate", json={}, headers=headers).status_code == 200
        shown = json.loads(path.read_text())["players"][0]
        assert shown["plants"] == 1 and shown["kost_rounds"] == 1
        assert shown["rating"] == original_rating
        season = json.loads((tmp_path / "web/public/data/seasons/fall-2026.json").read_text())
        career = json.loads((tmp_path / "web/public/data/players/player0/career.json").read_text())
        assert season["players"][0]["rating"] == career["rating"] == original_rating
    with closing(repo.connect(tmp_path / "data/r6stats.sqlite")) as db:
        after = dict(db.execute("SELECT * FROM maps").fetchone())
        assert {k: v for k, v in before.items() if k != "normalized_json"} == {k: v for k, v in after.items() if k != "normalized_json"}
        assert db.execute("SELECT count(*) FROM objective_events").fetchone()[0] == 1
        assert db.execute("SELECT count(*) FROM rating_input_snapshots").fetchone()[0] == 1
        assert verify(db, tmp_path / "data/replay-archive", map_id)["status"] == "Healthy"
        assert refresh.apply(db, map_id, parsed) == []


def test_overlay_keeps_unrelated_parser_changes_and_unsupported_legacy_credit():
    original, parsed = fixture()
    original.rounds[1].objectives = [Objective("plant", "enemy-0", 1, 0)]
    parsed.rounds[0].players[0].operator = "Zofia"
    parsed.rounds[0].kills = []
    updated, changes = refresh.overlay(original, parsed)
    assert len(changes) == 1
    assert updated.rounds[0].kills == original.rounds[0].kills
    assert updated.rounds[0].players == original.rounds[0].players
    assert updated.rounds[1] == original.rounds[1]


@pytest.mark.parametrize("problem", ["bonus", "missing_uid", "wrong_side", "missing_identity", "duplicate"])
def test_untrusted_actor_never_migrates(problem):
    original, parsed = fixture()
    o = parsed.rounds[0].objective_occurrences[0]
    if problem == "bonus":
        o.actor_source = "bonus_health_research_only"
        assert refresh.overlay(original, parsed)[1] == []
        return
    if problem == "missing_uid": o.actor_uid = None
    if problem == "wrong_side": parsed.rounds[0].players[0].side = "Defense"
    if problem == "missing_identity": parsed.rounds[0].players.pop()
    if problem == "duplicate": parsed.rounds[0].objective_occurrences.append(deepcopy(o))
    with pytest.raises(ValueError): refresh.overlay(original, parsed)


def test_snapshot_and_replacement_rollback_together(tmp_path):
    original, parsed = fixture()
    db, map_id, _ = setup_map(tmp_path, original)
    with closing(db):
        with patch("r6stats.objective_refresh.repo.reparse_map", side_effect=ValueError("replacement failure")):
            with pytest.raises(ValueError): refresh.apply(db, map_id, parsed)
        assert db.execute("SELECT count(*) FROM rating_input_snapshots").fetchone()[0] == 0
        assert json.loads(db.execute("SELECT normalized_json FROM maps").fetchone()[0]) == json.loads(json.dumps(original.to_dict()))


def test_snapshot_blocks_unrelated_future_input_changes(tmp_path):
    original, parsed = fixture()
    db, map_id, config = setup_map(tmp_path, original)
    with closing(db):
        refresh.apply(db, map_id, parsed)
        current = calculate_match(parsed)
        current["ours-0"]["kills"] += 1
        with pytest.raises(ValueError, match="outside the objective refresh"):
            refresh.rating_stats(db, map_id, current, 8, "siege_style_v2")
        assert refresh.rating_stats(db, map_id, current, 8, "collegiate_v1") is current


def test_archive_refresh_preserves_confirmed_rehost_team_swap(tmp_path):
    original, parsed = fixture()
    second = deepcopy(parsed)
    second.replay_id = "second-lobby"
    for r in second.rounds:
        r.winner = 1 - r.winner
        for p in r.players: p.team = 1 - p.team
        for k in r.kills:
            k.killer_team = 1 - k.killer_team
            k.victim_team = 1 - k.victim_team
        for o in r.objectives: o.team = 1 - o.team
    # An unresolved nine-player later round remains exactly nine players.
    second.rounds[1].players.pop()
    logical = deepcopy(original)
    logical.rounds = deepcopy(second.rounds)
    for r in logical.rounds:
        r.winner = 1 - r.winner
        for p in r.players: p.team = 1 - p.team
        for k in r.kills:
            k.killer_team = 1 - k.killer_team
            k.victim_team = 1 - k.victim_team
        for o in r.objectives: o.team = 1 - o.team
    logical.rounds[0].objectives = []
    logical.rounds[0].objective_occurrences = []
    source = {"segments": [{"segment": 1, "replay_id": "second-lobby"}],
              "segment_details": [{"segment": 1, "team_mapping": [1, 0]}],
              "mapping": [{"segment": 1, "physical_number": n, "logical_number": n} for n in (1, 2)]}
    record = {"normalized_json": json.dumps(logical.to_dict()), "rehost_json": json.dumps(source)}
    with patch("r6stats.objective_refresh.verify", return_value={"status": "Healthy", "path": str(tmp_path)}), \
            patch("r6stats.objective_refresh.map_record", return_value=record):
        current = refresh.parse_archive(None, tmp_path, "test", parser=lambda *a, **kw: second)
    updated, changes = refresh.overlay(logical, current)
    assert len(changes) == 1
    assert updated.rounds[0].objectives[0].team == 0
    assert len(updated.rounds[1].players) == 9
    assert updated.rounds[1] == logical.rounds[1]
