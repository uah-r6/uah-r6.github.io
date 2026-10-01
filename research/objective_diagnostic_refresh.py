"""Refresh ignored objective packet diagnostics from cached development replays."""
import argparse
import contextlib
import io
import json
from pathlib import Path

from objective_timer_audit import ROOT, audit


def main(match_ids):
    sources = json.loads((ROOT / "research/sources.json").read_text(encoding="utf-8"))["matches"]
    diagnostics = ROOT / "data/research/diagnostics"
    for match_id in match_ids:
        matches = [entry for entry in sources if entry.get("siegegg_match_id") == match_id]
        if len(matches) != 1:
            raise ValueError(f"Expected one source entry for {match_id}: {len(matches)}")
        source = matches[0]
        if len(source["maps"]) != 1:
            raise ValueError(f"Expected one configured map for {match_id}")
        folder_name = source["maps"][0]["folder"]
        folders = list((ROOT / "data/research/extracted").rglob(folder_name))
        folders = [path for path in folders if path.is_dir()]
        if len(folders) != 1:
            raise ValueError(f"Expected one cached folder for {folder_name}: {len(folders)}")
        mapping = [item for item in source["maps"] if item.get("folder") == folder_name]
        if len(mapping) != 1:
            raise ValueError(f"Expected one game ID for {folder_name}")
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            audit(folders[0], match_id, mapping[0]["siegegg_game_id"])
        target = diagnostics / f"objective-timer-{match_id}.jsonl"
        target.write_text(stream.getvalue(), encoding="utf-8")
        print(match_id, folders[0].name, len(stream.getvalue().splitlines()), "rounds")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("match_ids", nargs="+", type=int)
    args = parser.parse_args()
    main(args.match_ids)
