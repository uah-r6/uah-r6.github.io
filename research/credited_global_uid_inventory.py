"""Literal UID discovery inventory outside exact feedback callbacks.

Reuses the two existing decoded buffers. No packet ownership or damage relation
is inferred from an occurrence, prefix, offset or proximity to another UID.
"""
from collections import Counter
import json
from pathlib import Path
import subprocess
import sys

from credited_feedback_identity_probe import CASES, DATA, direct_references
from credited_native_envelope_audit import native
from v3_final_reserve import ROOT, sha, source_sha


def main():
    guard = [sys.executable, str(ROOT / "research/verify_native_boundary_checkpoint.py")]
    subprocess.run(guard, check=True)
    records = []
    for mid, number, *_ in CASES:
        old_file = ROOT / f"data/research/diagnostics/v3-sal-kill-credit/{mid}.json"
        old = json.loads(old_file.read_text(encoding="utf-8"))
        row = next(r for r in old["rounds"] if r["logical_round"] == number)
        sources = [p for p in (ROOT / f"data/research/extracted/v3-corrected-final-sal-{mid}").rglob(row["filename"])
                   if p.parent.name == row["folder"]]
        if len(sources) != 1 or sha(sources[0]) != row["replay_sha256"]:
            raise ValueError("Consumed physical replay identity differs")
        dump = DATA / (row["replay_sha256"] + ".dump")
        buffer = dump.read_bytes()
        players = native(sources[0])["header"]["players"]
        references = direct_references(buffer, players)["literal_numeric_uid_references"]
        for ref in references:
            at = ref["relative_offset"]
            ref["five_bytes_before"] = buffer[max(0, at-5):at].hex()
            # This observed prefix is the existing typed numeric UID binding.
            # Other raw occurrences receive no semantic label.
            ref["known_uid_property_prefix"] = ref["five_bytes_before"] == "eed445c808"
        counts = Counter(r["player"] for r in references)
        prefixes = Counter(r["five_bytes_before"] for r in references)
        records.append({"map_id": mid, "round": number, "dump_sha256": sha(dump),
                        "replay_sha256": row["replay_sha256"], "bytes_scanned": len(buffer),
                        "player_occurrences": dict(counts), "prefix_counts": dict(prefixes),
                        "matches": references, "known_uid_property_prefixes": sum(r["known_uid_property_prefix"] for r in references),
                        "unclassified_literal_matches": sum(not r["known_uid_property_prefix"] for r in references)})
        print(mid, number, len(references), 'literal UID matches;', records[-1]['known_uid_property_prefixes'], 'known prefixes', flush=True)
    result = {"status": "consumed_global_uid_discovery_not_damage_or_owner_mapping", "records": records,
              "source_sha256": source_sha(Path(__file__)),
              "limitation": "Literal raw UID bytes only. Repeated player snapshots/other serialization may contain these IDs; no typed envelope/attacker/victim relation established for unclassified matches. Never assign a downer or damage owner by nearest UID, co-occurrence or offset."}
    target = DATA / "global-uid-inventory.json"
    if target.exists():
        if json.loads(target.read_text(encoding="utf-8")) != result:
            raise ValueError("Never overwrite a changed consumed inventory")
    else:
        target.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    subprocess.run(guard, check=True)


if __name__ == "__main__":
    main()
