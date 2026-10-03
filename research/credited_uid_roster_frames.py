"""Consumed raw framing discovery, never a damage/downer decoder.

Recognize only a count-prefixed, ten-entry fixed-width UID list observed in
the two sealed buffers. The trailing three bytes are opaque, NOT life state,
team, damage or timestamp. A roster list establishes no pairwise relation.
"""
from collections import Counter
import json
from pathlib import Path
import subprocess
import sys

from credited_feedback_identity_probe import DATA
from v3_final_reserve import ROOT, sha, source_sha


def frame_at(data: bytes, start: int, expected: set[int]):
    if len(expected) != 10 or len(data) - start < 111 or start < 0 or data[start] != 10:
        return None
    entries = []
    for i in range(10):
        at = start + 1 + i * 11
        uid = int.from_bytes(data[at:at+8], "little")
        suffix = data[at+8:at+11]
        if uid not in expected or suffix not in (b"\x20\x00\xff", b"\x21\x00\xff"):
            return None
        entries.append({"uid": uid, "offset": at, "opaque_suffix": suffix.hex()})
    if {e["uid"] for e in entries} != expected:
        return None
    return {"start": start, "end": start+111, "entries": entries}


def frames(data: bytes, expected: set[int]):
    result = []
    cursor = 0
    while (at := data.find(b"\x0a", cursor)) >= 0:
        cursor = at+1
        frame = frame_at(data, at, expected)
        if frame:
            if result and frame["start"] < result[-1]["end"]:
                raise ValueError("Overlapping candidate UID lists are ambiguous")
            result.append(frame)
    return result


def main():
    guard = [sys.executable, str(ROOT / "research/verify_global_uid_checkpoint.py")]
    subprocess.run(guard, check=True)
    inventory_path = DATA / "global-uid-inventory.json"
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    results = []
    for row in inventory["records"]:
        dump = DATA / (row["replay_sha256"] + ".dump")
        if sha(dump) != row["dump_sha256"]:
            raise ValueError("Sealed buffer changed")
        data = dump.read_bytes()
        names = {r["uid"]: r["player"] for r in row["matches"]}
        recognized = frames(data, set(names))
        covered = {e["offset"] for frame in recognized for e in frame["entries"]}
        controls = []
        # Independent reviewed transition offsets, not inferred from these lists.
        anchors = ({"dbno": 74255864, "credit_increment": 74275879, "elimination": 74275897,
                    "finish": 74276292} if row["map_id"] == 8580 else
                   {"dbno": 86443440, "credit_increment": 86448083, "elimination": 86448101,
                    "finish": 86448473})
        for label, offset in anchors.items():
            controls.append({"anchor": label, "offset": offset,
                             "lists_in_plus_minus_50000_bytes": sum(abs(f["start"]-offset) <= 50000 for f in recognized),
                             "elapsed_time": None})
        suffixes = Counter(e["opaque_suffix"] for f in recognized for e in f["entries"])
        results.append({"map_id": row["map_id"], "round": row["round"],
                        "dump_sha256": sha(dump), "frames": recognized,
                        "frame_count": len(recognized), "literal_uid_matches_covered": len(covered),
                        "remaining_unclassified": sum(not r["known_uid_property_prefix"] and r["relative_offset"] not in covered for r in row["matches"]),
                        "orders": len({tuple(e["uid"] for e in f["entries"]) for f in recognized}),
                        "opaque_suffix_counts": dict(suffixes), "reviewed_anchor_controls": controls,
                        "interpretation": "Repeated full-roster UID lists, no decoded life/damage/type or directed victim/attacker relation."})
        print(row["map_id"], results[-1]["frame_count"], "complete UID lists; remaining", results[-1]["remaining_unclassified"], flush=True)
    result = {"source_sha256": source_sha(Path(__file__)), "input_sha256": sha(inventory_path),
              "status": "consumed_framing_only_no_downer_or_credit_event_association", "records": results}
    target = DATA / "uid-roster-frames.json"
    if target.exists() and json.loads(target.read_text(encoding="utf-8")) != result:
        raise ValueError("Never overwrite changed consumed framing evidence")
    if not target.exists():
        target.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    subprocess.run(guard, check=True)


if __name__ == "__main__":
    main()
