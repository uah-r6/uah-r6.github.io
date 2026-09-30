"""Refresh committed sample website JSON without touching the user's database."""
import tempfile
from pathlib import Path

from r6stats.db import repository as repo
from r6stats.demo import run


config = {
    "team": {"name": "NECC Rainbow Six", "short_name": "TEAM", "accent": "#82e3db"},
    "stats": {"trade_window_seconds": 8},
}
with tempfile.TemporaryDirectory() as directory:
    db = repo.connect(Path(directory) / "sample.sqlite")
    run(db, config)
    db.close()
