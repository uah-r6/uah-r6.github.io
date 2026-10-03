"""Count-prefixed UID framing with observed variable-width opaque forms.

This is research of local byte structure, not a network packet decoder. The
outer message type, opaque payload and directed damage relation are unknown.
No floats/entities/life states are inferred from convenient payload widths.
"""
import json
from pathlib import Path
import subprocess
import sys
from collections import Counter

from credited_feedback_identity_probe import DATA
from v3_final_reserve import ROOT, sha, source_sha


def entry_at(data, at, expected):
    if at < 0 or at+11 > len(data):
        return None
    uid = int.from_bytes(data[at:at+8], "little")
    if uid not in expected:
        return None
    tail = data[at+8:at+13]
    if tail[:3] in (b"\x20\x00\xff", b"\x21\x00\xff"):
        end, form = at+11, "opaque_short_20_21"
    elif len(tail) == 5 and tail[:2] == b"\xf9\x01" and tail[2] <= 4 and tail[3:] == b"\x01\xff":
        end, form = at+23, "opaque_f901_index_01ff_payload10"
    elif len(tail) == 5 and tail[:2] == b"\x39\x14" and tail[2] <= 4 and tail[3:] == b"\x00\xff":
        end, form = at+29, "opaque_3914_index_00ff_payload16"
    else:
        return None
    if end > len(data):
        return None
    return {"uid": uid, "offset": at, "end": end, "form": form,
            "opaque_bytes": data[at+8:end].hex()}


def frame_at(data, start, expected):
    if len(expected) != 10 or start < 0 or start >= len(data) or data[start] != 10:
        return None
    at, entries = start+1, []
    for _ in range(10):
        entry = entry_at(data, at, expected)
        if entry is None:
            return None
        entries.append(entry)
        at = entry["end"]
    if {e["uid"] for e in entries} != expected:
        return None
    return {"start": start, "end": at, "entries": entries}


def discover(data, references):
    expected = {r["uid"] for r in references}
    starts = sorted({r["relative_offset"]-1 for r in references if r["relative_offset"] > 0 and data[r["relative_offset"]-1] == 10})
    result = []
    for start in starts:
        frame = frame_at(data, start, expected)
        if frame:
            if result and start < result[-1]["end"]:
                raise ValueError("Overlapping count-prefixed structures refused")
            result.append(frame)
    return result


def main():
    guard = [sys.executable, str(ROOT/"research/verify_credited_semantics_checkpoint.py")]
    subprocess.run(guard, check=True)
    inventory_path = DATA/"global-uid-inventory.json"
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    results = []
    for old in inventory["records"]:
        dump = DATA/(old["replay_sha256"]+".dump")
        if sha(dump) != old["dump_sha256"]:
            raise ValueError("Sealed buffer differs")
        data = dump.read_bytes()
        found = discover(data, old["matches"])
        covered = {e["offset"] for f in found for e in f["entries"]}
        variable = [f for f in found if any(e["form"] != "opaque_short_20_21" for e in f["entries"])]
        anchors = ([74255864, 74275879, 74275897, 74276292] if old["map_id"] == 8580 else
                   [86443440, 86448083, 86448101, 86448473])
        controls = [{"anchor": a, "frames_in_plus_minus_50000_bytes": [f for f in variable if abs(f["start"]-a) <= 50000],
                     "elapsed_time": None} for a in anchors]
        results.append({"map_id": old["map_id"], "round": old["round"], "frames": found,
                        "frame_count": len(found), "variable_frames": len(variable),
                        "covered_uid_occurrences": len(covered),
                        "remaining_unclassified": sum(not r["known_uid_property_prefix"] and r["relative_offset"] not in covered for r in old["matches"]),
                        "form_counts": dict(Counter(e["form"] for f in found for e in f["entries"])),
                        "orders": len({tuple(e["uid"] for e in f["entries"]) for f in found}),
                        "reviewed_anchor_contexts": controls, "dump_sha256": sha(dump),
                        "interpretation": "Observed bounded local list forms only; outer packet/type, payload/life/damage meaning and actor roles remain unknown."})
        print(old["map_id"], len(found), "lists including", len(variable), "variable; remaining", results[-1]["remaining_unclassified"], flush=True)
    result = {"source_sha256": source_sha(Path(__file__)), "inventory_sha256": sha(inventory_path),
              "status": "consumed_variable_uid_framing_no_damage_semantics", "records": results}
    target = DATA/"uid-variable-frames.json"
    if target.exists() and json.loads(target.read_text(encoding="utf-8")) != result:
        raise ValueError("Never overwrite variable framing evidence")
    if not target.exists():
        target.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    subprocess.run(guard, check=True)


if __name__ == "__main__":
    main()
