"""Inspect replay operator evidence without modifying normalized matches.

Outputs compact diagnostics under ignored data/research/diagnostics/. Raw
decompressed replay bytes are held in a temporary file only while inspected.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import struct
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PARSER = ROOT / ".local-tools/bin/siege-dissect.exe"
DEST = ROOT / "data/research/diagnostics"
TIME_TAG = bytes.fromhex("1f07efc9")
OP_TAG = bytes.fromhex("22a9260be4")


def occurrences(data: bytes, tag: bytes):
    position = 0
    while (position := data.find(tag, position)) >= 0:
        yield position
        position += len(tag)


def inspect(source: Path, include_packets: bool = True) -> dict:
    DEST.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=DEST) as directory:
        temporary = Path(directory)
        parsed = temporary / "round.json"
        subprocess.run([str(PARSER), str(source), "-o", str(parsed)], check=True,
                       capture_output=True, text=True)
        raw = json.loads(parsed.read_text(encoding="utf-8"))
        header = raw.get("header", raw)
        teams = header["teams"]
        players = []
        for index, player in enumerate(header["players"]):
            op = player.get("operator") or {}
            players.append({"header_index": index, "username": player["username"],
                            "team": player["teamIndex"],
                            "side": teams[player["teamIndex"]].get("role"),
                            "profile_id": player.get("profileID"),
                            "header_operator_id": op.get("id") if isinstance(op, dict) else None,
                            "header_operator_name": op.get("name") if isinstance(op, dict) else str(op),
                            "header_role_name": player.get("roleName"),
                            "header_role_image": player.get("roleImage"),
                            "header_role_portrait": player.get("rolePortrait"),
                            "operator_source": player.get("operatorSource"),
                            "operator_seen_before_action": player.get("operatorSeenBeforeAction")})
        output = {"file": source.name, "game_version": header["gameVersion"],
                  "code_version": header["codeVersion"],
                  "action_phase_detected_by_parser": header.get("actionPhaseDetected", False),
                  "players": players}
        if include_packets:
            dumped = temporary / "round.dump"
            subprocess.run([str(PARSER), "--dump", "-o", str(dumped), str(source)],
                           check=True, capture_output=True, text=True)
            data = dumped.read_bytes()
            timers = [(pos, struct.unpack_from("<I", data, pos + 5)[0])
                      for pos in occurrences(data, TIME_TAG)
                      if pos + 9 <= len(data) and data[pos + 4] == 4]
            transitions = [{"previous_offset": prev[0], "previous_seconds": prev[1],
                            "offset": current[0], "seconds": current[1]}
                           for prev, current in zip(timers, timers[1:])
                           if prev[1] <= 60 and current[1] >= 120 and
                           current[1] > prev[1] + 5]
            action = next((item for item in transitions if item["seconds"] >= 120), None)
            cutoff = action["offset"] if action else len(data)
            candidates = [{"offset": pos, "operator_id": struct.unpack_from("<Q", data, pos + 6)[0],
                           "after_id_hex": data[pos + 14:pos + 38].hex(),
                           "before_action": pos < cutoff}
                          for pos in occurrences(data, OP_TAG)
                          if pos + 14 <= len(data) and data[pos + 5] == 8]
            output.update({"timer_transitions": transitions, "action_start": action,
                           "pre_action_operator_packets": [p for p in candidates if p["before_action"]],
                           "post_action_operator_packets": [p for p in candidates if not p["before_action"]],
                           "timer_sample": timers[:5], "decompressed_bytes": len(data)})
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", type=Path, help="Complete match folders or .rec files")
    parser.add_argument("--limit", type=int, default=5, help="Maximum rounds per folder")
    parser.add_argument("--headers-only", action="store_true")
    parser.add_argument("--output", default="operator-sample.json")
    args = parser.parse_args()
    sources = []
    for path in args.paths:
        sources.extend(sorted(path.glob("*.rec"))[:args.limit] if path.is_dir() else [path])
    results = [inspect(path, include_packets=not args.headers_only) for path in sources]
    target = DEST / args.output
    target.write_text(json.dumps(results, indent=2), encoding="utf-8")
    counts = Counter((item["game_version"], bool(item.get("action_start")),
                      item["action_phase_detected_by_parser"]) for item in results)
    print(f"Wrote {len(results)} rounds to {target}")
    print(dict(counts))
    for item in results:
        attackers = [p for p in item["players"] if p["side"] == "Attack"]
        names = [(p["username"], p["header_operator_name"], p["header_role_name"])
                 for p in attackers]
        print(item["file"], item.get("action_start"), "attacker header:", names)


if __name__ == "__main__":
    main()
