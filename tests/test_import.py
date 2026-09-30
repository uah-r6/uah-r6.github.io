import json
import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from r6stats.cli import import_path, scan
from r6stats.db import repository as repo
from r6stats.eligibility import is_custom_game
from r6stats.parser.models import Match, Player, Round
from r6stats.parser.siege_dissect import normalize


def fixture(kind="Custom Game"):
    return {"rounds": [{"matchID": "replay-1", "timestamp": "2026-09-29T20:00:00Z",
                        "matchType": {"name": kind}, "map": {"name": "Bank"},
                        "gamemode": {"name": "Bomb"}, "roundNumber": 1, "site": "B Lockers",
                        "teams": [{"won": True, "role": "Attack", "winCondition": "KilledOpponents"},
                                  {"won": False, "role": "Defense"}],
                        "players": [{"profileID": f"our-{i}", "username": f"Player{i}", "teamIndex": 0,
                                     "operator": {"name": "Buck"}} for i in range(5)] +
                                   [{"profileID": f"enemy-{i}", "username": f"Enemy{i}", "teamIndex": 1,
                                     "operator": {"name": "Wamai"}} for i in range(5)],
                        "matchFeedback": [{"type": "Kill", "username": "Player0", "target": "Enemy0",
                                           "timeInSeconds": 100, "headshot": True},
                                          {"type": "DefuserPlantComplete", "username": "Player1",
                                           "timeInSeconds": 60}]}]}


class ImportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = repo.connect(Path(self.tmp.name) / "test.sqlite")
        repo.season_create(self.db, "Fall 2026")
        for i in range(5):
            repo.roster_add(self.db, f"Player{i}")
        self.config = {"team": {"name": "Team", "short_name": "T", "accent": "#fff"},
                       "stats": {"trade_window_seconds": 8}}

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_adapter(self):
        m = normalize(fixture())
        self.assertEqual(m.map_name, "Bank")
        self.assertEqual(m.rounds[0].kills[0].killer, "our-0")
        self.assertEqual(m.rounds[0].objectives[0].kind, "plant")

    def test_adapter_rejects_unresolved_kill(self):
        raw = fixture()
        raw["rounds"][0]["matchFeedback"][0]["target"] = "MissingPlayer"
        with self.assertRaisesRegex(ValueError, "unresolved participant"):
            normalize(raw)

    def test_ranked_rejected_before_write(self):
        with patch("r6stats.cli.parse_match", return_value=normalize(fixture("Ranked"))):
            with self.assertRaisesRegex(ValueError, "Ranked"):
                import_path(self.db, self.config, "unused")
        self.assertEqual(self.db.execute("SELECT count(*) FROM maps").fetchone()[0], 0)
        with self.assertRaisesRegex(ValueError, "Only Custom Game"):
            repo.insert_map(self.db, normalize(fixture("Ranked")), "ranked-hash", 0, "Opponent")
        self.assertEqual(self.db.execute("SELECT count(*) FROM maps").fetchone()[0], 0)

    def test_only_custom_game_replays_are_eligible(self):
        self.assertTrue(is_custom_game("Custom Game"))
        self.assertTrue(is_custom_game("CustomGame"))
        self.assertTrue(is_custom_game("CustomGameLocal"))
        self.assertTrue(is_custom_game("CustomGameOnline"))
        for kind in ("Ranked", "Standard", "Quick Match", "QuickMatch", "NotCustomGame", "Unknown"):
            with self.subTest(kind=kind), patch("r6stats.cli.parse_match", return_value=normalize(fixture(kind))):
                with self.assertRaisesRegex(ValueError, "Import rejected"):
                    import_path(self.db, self.config, "unused")
                with self.assertRaisesRegex(ValueError, "Only Custom Game"):
                    repo.insert_map(self.db, normalize(fixture(kind)), kind, 0, "Opponent")
        self.assertEqual(self.db.execute("SELECT count(*) FROM series").fetchone()[0], 0)

    def test_scan_marks_custom_eligible_but_does_not_import_it(self):
        types = {"Custom": "Custom Game", "Online": "CustomGameOnline", "Local": "CustomGameLocal",
                 "Ranked": "Ranked", "Standard": "Standard", "Quick": "Quick Match"}
        for name in types:
            (Path(self.tmp.name) / name).mkdir()
        config = {**self.config, "replays": {"path": self.tmp.name}}
        output = io.StringIO()
        def parse(path, *, allow_incomplete=False):
            raw = fixture(types[path.name])
            raw["rounds"].append({**raw["rounds"][0], "roundNumber": 2})
            return normalize(raw)
        with patch("r6stats.cli.parse_match", side_effect=parse), redirect_stdout(output):
            scan(self.db, config)
        display = output.getvalue()
        self.assertIn("Custom Game - eligible for manual NECC import", display)
        self.assertIn("Custom Game (Online) - eligible for manual NECC import", display)
        self.assertIn("Custom Game (Local) - eligible for manual NECC import", display)
        for kind in ("Ranked", "Standard", "Quick Match"):
            self.assertIn(f"INELIGIBLE - {kind}", display)
        self.assertEqual(self.db.execute("SELECT count(*) FROM series").fetchone()[0], 0)

    def test_duplicate_and_season_isolation(self):
        m = normalize(fixture())
        team, names = repo.choose_team(self.db, m)
        self.assertEqual(team, 0)
        self.assertEqual(len(names), 5)
        repo.insert_map(self.db, m, "hash-1", team, "Opponent")
        with self.assertRaisesRegex(ValueError, "already been imported"):
            repo.insert_map(self.db, m, "hash-1", team, "Opponent")
        repo.season_create(self.db, "Spring 2027")
        repo.season_activate(self.db, "Spring 2027")
        m.replay_id = "replay-2"
        repo.insert_map(self.db, m, "hash-2", team, "Opponent")
        rows = self.db.execute("SELECT se.slug, count(*) FROM maps m JOIN series s ON s.id=m.series_id JOIN seasons se ON se.id=s.season_id GROUP BY se.slug").fetchall()
        self.assertEqual({r[0]: r[1] for r in rows}, {"fall-2026": 1, "spring-2027": 1})

    def test_confirmed_import_exports_and_second_import_is_idempotent(self):
        folder = Path(self.tmp.name) / "Match-1"
        folder.mkdir()
        (folder / "round1.rec").write_bytes(b"round one")
        (folder / "round2.rec").write_bytes(b"round two")
        output = Path(self.tmp.name) / "public"
        from r6stats.export import export
        with patch("r6stats.cli.parse_match", return_value=normalize(fixture("CustomGameOnline"))), \
             patch("builtins.input", side_effect=["Opponent", "Week 1", "", "NECC"]), \
             patch("r6stats.cli.export", side_effect=lambda database, config: export(database, config, output)):
            map_id = import_path(self.db, self.config, str(folder))
            self.assertTrue((output / "matches" / f"{map_id}.json").exists())
            self.assertEqual(self.db.execute("SELECT count(*) FROM maps").fetchone()[0], 1)
            self.assertEqual(self.db.execute("SELECT competition FROM series").fetchone()[0], "NECC")
            self.assertEqual(self.db.execute("SELECT count(*) FROM rounds").fetchone()[0], 1)
            self.assertEqual(self.db.execute("SELECT count(*) FROM round_players").fetchone()[0], 10)
            self.assertEqual(self.db.execute("SELECT count(*) FROM kill_events").fetchone()[0], 1)
            with self.assertRaisesRegex(ValueError, "already been imported"):
                import_path(self.db, self.config, str(folder))
            self.assertEqual(self.db.execute("SELECT count(*) FROM maps").fetchone()[0], 1)

    def test_custom_game_needs_necc_confirmation(self):
        output = io.StringIO()
        with patch("r6stats.cli.parse_match", return_value=normalize(fixture())), \
             patch("builtins.input", side_effect=["Opponent", "", "", "YES"]), \
             redirect_stdout(output):
            self.assertIsNone(import_path(self.db, self.config, "unused"))
        self.assertIn("Competition if confirmed: NECC", output.getvalue())
        self.assertEqual(self.db.execute("SELECT count(*) FROM series").fetchone()[0], 0)
        self.assertEqual(self.db.execute("SELECT count(*) FROM maps").fetchone()[0], 0)
        self.assertEqual(self.db.execute("SELECT count(*) FROM players WHERE profile_id IS NOT NULL").fetchone()[0], 0)

    def test_profile_id_survives_username_change(self):
        first = normalize(fixture())
        repo.insert_map(self.db, first, "first", 0, "Opponent")
        changed = fixture()
        changed["rounds"][0]["matchID"] = "replay-2"
        changed["rounds"][0]["players"][0]["username"] = "RenamedPlayer"
        changed["rounds"][0]["matchFeedback"][0]["username"] = "RenamedPlayer"
        second = normalize(changed)
        self.assertEqual(repo.choose_team(self.db, second)[0], 0)
        repo.insert_map(self.db, second, "second", 0, "Opponent")
        player = self.db.execute("SELECT id,username,profile_id FROM players WHERE profile_id='our-0'").fetchone()
        self.assertEqual(player["username"], "RenamedPlayer")
        self.assertEqual(self.db.execute("SELECT count(*) FROM aliases WHERE player_id=?", (player["id"],)).fetchone()[0], 2)


if __name__ == "__main__":
    unittest.main()
