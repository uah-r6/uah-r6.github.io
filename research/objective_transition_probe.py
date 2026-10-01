"""Read-only comparison of entity properties near disputed defuser timer ends.

This is a discovery diagnostic. Nearby property hashes alone do not establish
objective completion or identify an actor. Output stays in ignored research data.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import subprocess
import tempfile

from objective_timer_audit import PARSER, ROOT


CASES = ((4139, 7), (4141, 6), (4141, 14), (4138, 9), (3880, 10))
DEVELOPMENT_MATCHES = (4150, 4132, 3585, 6156, 3073, 3554, 4112,
                       3637, 4140, 4118, 4141, 4134, 4135, 3745, 4148,
                       4139, 3639, 4127, 4129, 4137, 4138, 4119, 4120,
                       4133, 3880, 3879)
STATE_HASH = "ff39f408"  # raw little-endian bytes; semantic meaning unverified
EXCLUDE = {"ecda4f80", "1cd2b19d", "4d737f9e", "b6f474a3", "1837466c"}


def replay_file(match_id: int, round_number: int) -> tuple[Path, dict]:
    sources = json.loads((ROOT / "research/sources.json").read_text(encoding="utf-8"))["matches"]
    source = next(row for row in sources if row.get("siegegg_match_id") == match_id)
    rows = (ROOT / "data/research/diagnostics" / f"objective-timer-{match_id}.jsonl")
    diagnostic = next(json.loads(line) for line in rows.read_text(encoding="utf-8-sig").splitlines()
                      if json.loads(line)["round"] == round_number)
    folders = [p for mapping in source["maps"]
               for p in (ROOT / "data/research/extracted").rglob(mapping["folder"])
               if p.is_dir() and (p / diagnostic["physical_file"]).is_file()]
    if len(folders) != 1:
        raise ValueError(f"Expected one cached replay folder, found {len(folders)}")
    return folders[0] / diagnostic["physical_file"], diagnostic


def properties(data: bytes, start: int, end: int) -> list[dict]:
    """Collect complete 0x23 entity TLVs only; avoid arbitrary hash-byte hits."""
    rows = []
    cursor = start
    while (at := data.find(b"\x23", cursor, min(len(data), end))) >= 0:
        cursor = at + 1
        if at + 14 > len(data) or data[at + 5:at + 9] != b"\0" * 4:
            continue
        type_byte = data[at + 13]
        if type_byte not in (1, 2, 4, 8):
            continue
        rows.append({"offset": at, "entity": int.from_bytes(data[at + 1:at + 5], "little"),
                     "hash": data[at + 9:at + 13].hex(), "type": type_byte,
                     "value": data[at + 14:at + 14 + type_byte].hex()})
    return rows


def state_events(data: bytes) -> list[dict]:
    """Find this exact typed property throughout a decompressed round."""
    result = []
    pattern = bytes.fromhex(STATE_HASH)
    cursor = 0
    while (at := data.find(pattern, cursor)) >= 0:
        cursor = at + 1
        marker = at - 9
        if (marker < 0 or at + 6 > len(data) or data[marker] != 0x23 or
                data[at - 4:at] != b"\0" * 4 or data[at + 4] != 1):
            continue
        result.append({"offset": at, "entity": int.from_bytes(data[at - 8:at - 4], "little"),
                       "value": data[at + 5]})
    return result


def entity_properties(data: bytes, entity: int) -> dict:
    """Summarize typed properties addressed to one candidate state entity."""
    marker = b"\x23" + entity.to_bytes(4, "little") + b"\0" * 4
    counts = Counter()
    examples = {}
    cursor = 0
    while (at := data.find(marker, cursor)) >= 0:
        cursor = at + 1
        if at + 14 > len(data):
            break
        kind = data[at + 13]
        if kind not in (1, 2, 4, 8):
            continue
        hash_ = data[at + 9:at + 13].hex()
        counts[hash_] += 1
        examples.setdefault(hash_, [])
        if len(examples[hash_]) < 5:
            examples[hash_].append({"offset": at, "type": kind,
                                    "value": data[at + 14:at + 14 + kind].hex()})
    return {"counts": dict(counts), "examples": examples}


def parent_links(data: bytes, entities: set[int]) -> list[dict]:
    """Check a documented probable parent/owner TLV without assuming its meaning."""
    pattern = bytes.fromhex("3eaad30a")  # 0x0AD3AA3E, little endian
    rows = []
    cursor = 0
    while (at := data.find(pattern, cursor)) >= 0:
        cursor = at + 1
        if (at < 9 or at + 13 > len(data) or data[at - 9] != 0x23 or
                data[at - 4:at] != b"\0" * 4 or data[at + 4] != 8):
            continue
        entity = int.from_bytes(data[at - 8:at - 4], "little")
        value = int.from_bytes(data[at + 5:at + 13], "little")
        if entity in entities or value in entities:
            rows.append({"offset": at, "entity": entity, "value": value})
    return rows


def player_refs_near_state(data: bytes, match_id: int, filename: str,
                           events: list[dict], radius: int = 512) -> list[dict]:
    """Report exact player IDs and score-entity refs, without assigning actors."""
    path = ROOT / "data/research/diagnostics" / f"defuser-ids-{match_id}.json"
    if not path.exists():
        return []
    identities = json.loads(path.read_text(encoding="utf-8-sig")).get(filename, {})
    result = []
    for event in events:
        lo, hi = max(0, event["offset"] - radius), min(len(data), event["offset"] + radius)
        window = data[lo:hi]
        hits = []
        for name, encoded in identities.items():
            identity = int.from_bytes(bytes.fromhex(encoded), "little")
            for kind, value in (("player_id", identity), ("score_entity", identity - 4)):
                cursor = 0
                while (at := window.find(value.to_bytes(4, "little"), cursor)) >= 0:
                    hits.append({"player": name, "kind": kind,
                                 "offset_from_state": lo + at - event["offset"]})
                    cursor = at + 1
        result.append({**event, "nearby_player_refs": sorted(
            hits, key=lambda row: abs(row["offset_from_state"]))})
    return result


def audit(match_id: int, round_number: int, before: int = 2048,
          after: int = 8192) -> dict:
    rec, diagnostic = replay_file(match_id, round_number)
    with tempfile.TemporaryDirectory() as directory:
        dump = Path(directory) / "round.dump"
        subprocess.run([str(PARSER), "--dump", "-o", str(dump), str(rec)],
                       check=True, capture_output=True, text=True)
        data = dump.read_bytes()
    runs = [run for run in diagnostic["timer_runs"] if run["min"] <= .10]
    events = state_events(data)
    result = {"match_id": match_id, "round": round_number,
              "physical_file": rec.name, "dump_bytes": len(data),
              "public_objectives": diagnostic["public_objectives"],
              "all_state_events": events,
              "state_player_proximity": player_refs_near_state(
                  data, match_id, rec.name, events),
              "state_entity_properties": {str(entity): entity_properties(data, entity)
                                          for entity in {event["entity"] for event in events}},
              "candidate_parent_links": parent_links(data, {event["entity"] for event in events}),
              "runs": []}
    for run in runs:
        center = run["last_offset"]
        nearby = properties(data, max(0, center - before), center + after)
        before_rows = [row for row in nearby if row["offset"] < center]
        after_rows = [row for row in nearby if row["offset"] >= center]
        before_hashes = Counter(row["hash"] for row in before_rows)
        after_hashes = Counter(row["hash"] for row in after_rows)
        changes = {hash_: count for hash_, count in after_hashes.items()
                   if hash_ not in EXCLUDE and count > before_hashes[hash_]}
        result["runs"].append({
            "terminal_offset": center, "min_timer": run["min"],
            "hashes_before": dict(before_hashes), "hashes_after": dict(after_hashes),
            "new_or_increased_hashes": changes, "properties": nearby,
            "state_flags": [{"offset_after_terminal": row["offset"] - center,
                             "entity": row["entity"], "value": row["value"]}
                            for row in after_rows if row["hash"] == STATE_HASH and
                            row["offset"] - center <= 1000],
            "nearby_state_events": [{**event, "offset_after_terminal": event["offset"] - center}
                                    for event in events if run["first_offset"] - 2000 <=
                                    event["offset"] <= center + 20000],
        })
    return result


def development_cases() -> list[tuple[int, int]]:
    result = []
    for match_id in DEVELOPMENT_MATCHES:
        path = ROOT / "data/research/diagnostics" / f"objective-timer-{match_id}.jsonl"
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            row = json.loads(line)
            if row["public_objectives"] or any(run["min"] <= .10 for run in row["timer_runs"]):
                result.append((match_id, row["round"]))
    return result


def main(cases: list[tuple[int, int]]) -> None:
    results = [audit(match_id, round_number) for match_id, round_number in cases]
    suffix = "-all" if len(cases) > 10 else ""
    destination = ROOT / "data/research/diagnostics" / f"objective-transition-probe{suffix}.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(results, indent=2), encoding="utf-8")
    summary = Counter()
    for item in results:
        for run in item["runs"]:
            expected = [event["type"] for event in item["public_objectives"]]
            flags = run["state_flags"]
            summary[(bool(expected), tuple(flag["value"] for flag in flags))] += 1
            print(item["match_id"], f"R{item['round']:02d}",
                  "public", expected, "timer", run["min_timer"],
                  "state_flags", flags,
                  "nearby_state_events", run["nearby_state_events"] if not flags else "")
    print("SUMMARY", dict((str(key), count) for key, count in summary.items()))
    print("Detailed entity/property records:", destination)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("cases", nargs="*", help="MATCH_ID:ROUND; defaults to five disputed cases")
    parser.add_argument("--all-development", action="store_true",
                        help="Inspect all existing development objective and near-zero timer rounds")
    args = parser.parse_args()
    main(development_cases() if args.all_development else
         [tuple(map(int, value.split(":"))) for value in args.cases] if args.cases else list(CASES))
