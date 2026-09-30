"""Cache preflighted official replay ZIPs and corresponding SiegeGG targets.

Usage: python research/collect_candidates.py UBISOFT_ID:SIEGEGG_ID [...]
Only downloads/extracts into ignored data/research; it does not add observations.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys
from urllib.parse import unquote, urlparse
import zipfile

from pipeline import DATA, cache_url
from preflight_ubisoft import details


def collect(ubisoft_id: int, siegegg_id: int) -> dict:
    official = details(ubisoft_id)
    if not official or not official["replay_url"]:
        raise ValueError(f"Official match {ubisoft_id} has no replay URL")
    archive = DATA / "pro-replays" / unquote(Path(urlparse(official["replay_url"]).path).name)
    cache_url(official["replay_url"], archive)
    extraction = DATA / "extracted" / f"candidate-{ubisoft_id}"
    with zipfile.ZipFile(archive) as bundle:
        bad = bundle.testzip()
        if bad:
            raise ValueError(f"Corrupt ZIP member {bad} in {archive}")
        for member in bundle.infolist():
            if member.is_dir():
                continue
            target = (extraction / member.filename).resolve()
            if not target.is_relative_to(extraction.resolve()):
                raise ValueError(f"Unsafe ZIP member {member.filename}")
            if not target.exists() or target.stat().st_size != member.file_size:
                target.parent.mkdir(parents=True, exist_ok=True)
                with bundle.open(member) as source, target.open("wb") as output:
                    import shutil
                    shutil.copyfileobj(source, output)
    for suffix, endpoint in (("api", ""), ("player-stats", "/player-stats")):
        cache_url(f"https://siege.gg/api/stats/matches/{siegegg_id}{endpoint}",
                  DATA / "targets" / f"siegegg-match-{siegegg_id}-{suffix}.json")
    target = json.loads((DATA / "targets" / f"siegegg-match-{siegegg_id}-api.json").read_text())
    result = {"official": official, "siegegg_match_id": siegegg_id,
              "siegegg_games": [{"id": game["id"], "map": game["map"]["name"],
                                  "score": [game["win_score"], game["loss_score"]]}
                                 for game in target["games"]],
              "archive": str(archive.relative_to(DATA)),
              "extraction_label": extraction.name,
              "replay_folders": [folder.name for folder in extraction.rglob("Match-*") if folder.is_dir()]}
    report = DATA / "diagnostics" / f"candidate-{ubisoft_id}.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("Usage: collect_candidates.py UBISOFT_ID:SIEGEGG_ID [...]")
    for pair in sys.argv[1:]:
        ubisoft_id, siegegg_id = map(int, pair.split(":"))
        print(json.dumps(collect(ubisoft_id, siegegg_id)), flush=True)


if __name__ == "__main__":
    main()
