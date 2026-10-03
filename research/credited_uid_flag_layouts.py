"""Bounded opaque UID-entry forms observed in the two consumed buffers.

Widths are explicit observed local byte layouts, not server packet semantics.
No payload field is named health/damage/life/attacker/victim/entity/time. Keep
the narrow three-form discovery separately immutable.
"""
from collections import Counter
import json
from pathlib import Path
import subprocess
import sys

from credited_uid_variable_frames import entry_at as narrow_entry
from credited_feedback_identity_probe import DATA, direct_references
from v3_final_reserve import ROOT, sha, source_sha

# Prefix includes three opaque bytes following the UID. Width excludes UID.
WIDTHS = {
    "2200ff": 3, "2010ff": 11, "2110ff": 11,
    "2104ff": 11, "2204ff": 11,
    "6001ff": 12, "6101ff": 12, "6011ff": 20, "6111ff": 20,
    "e001ff": 13, "e101ff": 13, "e011ff": 21, "e111ff": 21,
    "a010ff": 12,
}


def entry_at(data, at, expected):
    found = narrow_entry(data, at, expected)
    if found:
        return found
    if at < 0 or at+11 > len(data):
        return None
    uid = int.from_bytes(data[at:at+8], "little")
    if uid not in expected:
        return None
    prefix = data[at+8:at+11].hex()
    width = WIDTHS.get(prefix)
    tail = data[at+8:at+13]
    if width is None and len(tail) == 5 and tail[:2] == b"\x39\x04" and tail[2] <= 4 and tail[3:] == b"\x00\xff":
        width = 13
    if width is None or at+8+width > len(data):
        return None
    end = at+8+width
    return {"uid": uid, "offset": at, "end": end, "form": "observed_opaque_"+prefix,
            "opaque_bytes": data[at+8:end].hex()}


def frame_at(data, start, expected):
    if len(expected) != 10 or start < 0 or start >= len(data) or data[start] != 10:
        return None
    at, entries = start+1, []
    for _ in range(10):
        e = entry_at(data, at, expected)
        if e is None:
            return None
        entries.append(e)
        at = e["end"]
    if {e["uid"] for e in entries} != expected:
        return None
    return {"start": start, "end": at, "entries": entries}


def main():
    guard = [sys.executable, str(ROOT/"research/verify_credited_semantics_checkpoint.py")]
    subprocess.run(guard, check=True)
    inventory_path = DATA/"global-uid-inventory.json"
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    results = []
    for old in inventory["records"]:
        dump = DATA/(old["replay_sha256"]+".dump")
        if sha(dump) != old["dump_sha256"]:
            raise ValueError("Sealed buffer changed")
        data = dump.read_bytes()
        expected = {r["uid"] for r in old["matches"]}
        names = [{"id": uid, "username": str(uid)} for uid in expected]
        starts = sorted({r["relative_offset"]-1 for r in old["matches"] if r["relative_offset"] > 0 and data[r["relative_offset"]-1] == 10})
        found, rejected = [], []
        for start in starts:
            frame = frame_at(data, start, expected)
            if frame:
                if found and start < found[-1]["end"]:
                    raise ValueError("Overlapping opaque UID lists refused")
                found.append(frame)
            else:
                rejected.append(start)
        covered = {e["offset"] for f in found for e in f["entries"]}
        # Examine all opaque payloads for literal full UIDs; absence is scoped.
        extra_uid_references = []
        for f in found:
            for e in f["entries"]:
                refs = direct_references(data[e["offset"]+8:e["end"]], names)["literal_numeric_uid_references"]
                if refs:
                    extra_uid_references.append({"entry": e["offset"], "references": refs})
        anchors = ([74255864, 74275879, 74275897, 74276292] if old["map_id"] == 8580 else
                   [86443440, 86448083, 86448101, 86448473])
        contexts = [{"anchor": a, "frames": [f for f in found if abs(f["start"]-a) <= 50000], "elapsed_time": None}
                    for a in anchors]
        result = {"map_id": old["map_id"], "round": old["round"], "frames": found,
                  "frame_count": len(found), "candidate_count": len(starts), "rejected_starts": rejected,
                  "covered_uid_occurrences": len(covered), "opaque_payload_literal_uids": extra_uid_references,
                  "remaining_unclassified": sum(not r["known_uid_property_prefix"] and r["relative_offset"] not in covered for r in old["matches"]),
                  "forms": dict(Counter(e["form"] for f in found for e in f["entries"])),
                  "orders": len({tuple(e["uid"] for e in f["entries"]) for f in found}),
                  "reviewed_anchor_contexts": contexts, "dump_sha256": sha(dump)}
        results.append(result)
        print(old["map_id"], len(found), "of", len(starts), "count10 candidates; remaining", result["remaining_unclassified"],
              "payload UID refs", len(extra_uid_references), flush=True)
    result = {"source_sha256": source_sha(Path(__file__)), "inventory_sha256": sha(inventory_path), "records": results,
              "status": "consumed_opaque_entry_framing_not_directed_damage_or_life_semantics",
              "widths": WIDTHS, "limitation": "Raw count/known UID/observed opaque prefix widths establish local lists only. Outer packet/type, payload meanings, indirect/encoded references and elapsed time unresolved. No downer/credited victim by proximity or array order."}
    target = DATA/"uid-flag-layouts.json"
    if target.exists() and json.loads(target.read_text(encoding="utf-8")) != result:
        raise ValueError("Never overwrite opaque layout evidence")
    if not target.exists():
        target.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    subprocess.run(guard, check=True)


if __name__ == "__main__":
    main()
