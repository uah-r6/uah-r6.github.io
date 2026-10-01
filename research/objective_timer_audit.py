"""Read-only audit of defuser progress packets in development replay rounds.

Uses siege-dissect --dump and reports packet-level timer runs. This diagnostic
does not infer a completed plant or disable and never writes normalized data.
"""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PARSER = ROOT / ".local-tools/bin/siege-dissect.exe"
TAG = bytes.fromhex("22a9c858d9")


def packets(data: bytes) -> list[dict]:
    result = []
    offset = 0
    while (at := data.find(TAG, offset)) >= 0:
        offset = at + len(TAG)
        if offset >= len(data):
            break
        size = data[offset]
        if size > 16 or offset + 1 + size + 38 > len(data):
            continue
        value = data[offset + 1:offset + 1 + size].decode("ascii", errors="replace")
        try:
            seconds = float(value)
        except ValueError:
            continue
        identity = data[offset + 1 + size + 34:offset + 1 + size + 38].hex()
        result.append({"offset": at, "timer": seconds, "player_id": identity})
    return result


def runs(entries: list[dict]) -> list[dict]:
    groups = []
    current = []
    for entry in entries:
        if current and (entry["timer"] > current[-1]["timer"] + .5 or
                        entry["offset"] - current[-1]["offset"] > 100000):
            groups.append(current)
            current = []
        current.append(entry)
    if current:
        groups.append(current)
    return [{"n": len(group), "first": group[0]["timer"],
             "last": group[-1]["timer"], "min": min(p["timer"] for p in group),
             "max": max(p["timer"] for p in group),
             "ids": sorted(set(p["player_id"] for p in group)),
             "first_offset": group[0]["offset"], "last_offset": group[-1]["offset"]}
            for group in groups]


def scoreboard_events(data: bytes, players: dict[str, str]) -> list[dict]:
    """Read Y11 per-entity score snapshots for attribution diagnostics only."""
    identities = {name: int.from_bytes(bytes.fromhex(value), "little")
                  for name, value in players.items() if value}
    tag = bytes.fromhex("ecda4f80")
    offset = 0
    previous = {}
    events = []
    while (at := data.find(tag, offset)) >= 0:
        offset = at + len(tag)
        if (at < 9 or at + 9 > len(data) or data[at - 9] != 0x23 or
                data[at - 4:at] != bytes(4) or data[at + 4] != 4):
            continue
        entity = int.from_bytes(data[at - 8:at - 4], "little")
        matches = sorted((identity - entity, name) for name, identity in identities.items()
                         if 0 <= identity - entity <= 64)
        if not matches:
            continue
        delta_entity, name = matches[0]
        value = int.from_bytes(data[at + 5:at + 9], "little")
        old = previous.get(name)
        previous[name] = value
        if old is not None and value > old:
            events.append({"offset": at, "player": name, "delta": value - old,
                           "score": value, "entity_delta": delta_entity})
    return events


def killcount_events(data: bytes, players: dict[str, str]) -> list[dict]:
    """Read Y11 cumulative kill-count changes for score-collision diagnostics."""
    identities = {name: int.from_bytes(bytes.fromhex(value), "little")
                  for name, value in players.items() if value}
    tag = bytes.fromhex("1cd2b19d")
    offset = 0
    previous = {}
    events = []
    while (at := data.find(tag, offset)) >= 0:
        offset = at + len(tag)
        if (at < 9 or at + 9 > len(data) or data[at - 9] != 0x23 or
                data[at - 4:at] != bytes(4) or data[at + 4] != 4):
            continue
        entity = int.from_bytes(data[at - 8:at - 4], "little")
        matches = sorted((identity - entity, name) for name, identity in identities.items()
                         if 0 <= identity - entity <= 64)
        if not matches:
            continue
        _, name = matches[0]
        value = int.from_bytes(data[at + 5:at + 9], "little")
        old = previous.get(name)
        previous[name] = value
        if old is not None and value > old:
            events.append({"offset": at, "player": name, "delta": value - old,
                           "kill_count": value})
    return events


def audit(folder: Path, siegegg_match_id: int | None = None, game_id: int | None = None):
    public_rounds = []
    round_identities = {}
    if siegegg_match_id is not None:
        target = json.loads((ROOT / "data/research/targets" /
                             f"siegegg-match-{siegegg_match_id}-api.json").read_text())
        game = next(g for g in target["games"] if g["id"] == game_id)
        public_rounds = game["rounds"]
        identity_file = ROOT / "data/research/diagnostics" / f"defuser-ids-{siegegg_match_id}.json"
        if identity_file.exists():
            round_identities = json.loads(identity_file.read_text(encoding="utf-8-sig"))
    with tempfile.TemporaryDirectory() as temporary:
        dumped = Path(temporary) / "round.dump"
        for number, rec in enumerate(sorted(folder.glob("*.rec")), start=1):
            subprocess.run([str(PARSER), "--dump", "-o", str(dumped), str(rec)],
                           check=True, capture_output=True, text=True)
            data = dumped.read_bytes()
            entries = packets(data)
            timer_runs = runs(entries)
            scores = scoreboard_events(data, round_identities.get(rec.name, {}))
            kills = killcount_events(data, round_identities.get(rec.name, {}))
            for run in timer_runs:
                if run["min"] >= .2:
                    continue
                nearby = [event for event in scores if
                          run["last_offset"] - 2000 <= event["offset"] <=
                          run["last_offset"] + 20000]
                run["near_completion_score_increases"] = nearby
                run["near_completion_killcount_increases"] = [event for event in kills if
                    run["last_offset"] - 2000 <= event["offset"] <= run["last_offset"] + 20000]
            public = public_rounds[number - 1] if public_rounds else None
            objectives = ([{"type": event["type"], "time": event.get("time"),
                           "description": event.get("html", "").split("</a>")[-1].strip()}
                          for event in public["events"]
                          if event["type"] in ("plant", "disable")]
                          if public else [])
            print(json.dumps({"round": number, "physical_file": rec.name,
                              "packet_count": len(entries), "public_objectives": objectives,
                              "timer_runs": timer_runs}))


if __name__ == "__main__":
    if len(sys.argv) not in (2, 4):
        raise SystemExit("Usage: objective_timer_audit.py FOLDER [SIEGEGG_MATCH_ID GAME_ID]")
    audit(Path(sys.argv[1]), *(map(int, sys.argv[2:]) if len(sys.argv) == 4 else ()))
