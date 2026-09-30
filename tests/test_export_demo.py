import json
import tempfile
import unittest
from pathlib import Path

from r6stats.db import repository as repo
from r6stats.demo import run
from r6stats.export import export


CONFIG = {"team": {"name": "Test Team", "short_name": "TT", "accent": "#abc123"},
          "stats": {"trade_window_seconds": 8}}


class ExportDemoTests(unittest.TestCase):
    def test_demo_export_is_private_and_clear_restores_roster(self):
        with tempfile.TemporaryDirectory() as directory:
            db = repo.connect(Path(directory) / "test.sqlite")
            repo.season_create(db, "Fall 2026")
            for i in range(5):
                repo.roster_add(db, f"Player{i}")
            root = Path(directory) / "public"
            from unittest.mock import patch
            # Demo's default destination is normally web/public/data.
            with patch("r6stats.demo.export", side_effect=lambda database, config: export(database, config, root)):
                run(db, CONFIG)
                index = json.loads((root / "index.json").read_text())
                self.assertEqual(index["active_season"], "fall-2026")
                public = "".join(p.read_text() for p in root.rglob("*.json"))
                self.assertNotIn("profile_id", public)
                self.assertNotIn("profileID", public)
                self.assertNotIn("DemoEnemy", public)
                self.assertTrue(json.loads((root / "seasons/fall-2026.json").read_text())["demo"])
                run(db, CONFIG, clear=True)
                self.assertEqual(db.execute("SELECT count(*) FROM maps").fetchone()[0], 0)
                self.assertEqual(db.execute("SELECT count(*) FROM players WHERE profile_id IS NOT NULL").fetchone()[0], 0)
                self.assertFalse(json.loads((root / "seasons/fall-2026.json").read_text())["demo"])
            db.close()


if __name__ == "__main__":
    unittest.main()
