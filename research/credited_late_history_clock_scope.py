"""Compare opaque event scalars to coarse countdowns without elapsed clocks."""
from pathlib import Path
import subprocess
import sys
import json

from credited_round_dataset import DATA as COUNT_DATA, read
from credited_feedback_identity_probe import DATA as UID_DATA
from v3_final_reserve import ROOT, sha, source_sha


def clock_scope(candidates, feed):
    unique = {}
    for c in candidates:
        if c["kind_byte"] == 1:
            unique.setdefault(c["raw_hex"], c)
    values = sorted(unique.values(), key=lambda c: c["opaque_scalar"])
    events = sorted(feed, key=lambda f: f["offset"])
    if len(values) != len(events):
        raise ValueError("Complete independently matched elimination inventory required")
    rows = []
    for c, e in zip(values, events):
        f = e["feedback"]
        if (c["first"]["username"], c["second"]["username"], c["weapon_id"], c["headshot"]) != (
                f["username"], f["target"], f["weaponID"], f.get("headshot", False)):
            raise ValueError("Cannot calibrate unmatched scalar to a feed event")
        rows.append({"scalar": c["opaque_scalar"], "remaining": f["timeInSeconds"],
                     "feed_offset": e["offset"], "finisher": f["username"], "victim": f["target"]})
    pairs = []
    for a, b in zip(rows, rows[1:]):
        delta_scalar = b["scalar"]-a["scalar"]
        delta_clock = a["remaining"]-b["remaining"]
        if delta_scalar <= 0:
            raise ValueError("Ambiguous/nonmonotonic event scalar")
        pairs.append({"earlier": a, "later": b, "delta_scalar": delta_scalar,
                      "delta_remaining": delta_clock,
                      "scalar_units_per_displayed_clock_second": delta_scalar/delta_clock if delta_clock > 0 else None,
                      "elapsed_seconds": None,
                      "status": "countdown_increased_not_elapsed_difference" if delta_clock < 0 else
                                "same_coarse_display_tick_not_elapsed_difference" if delta_clock == 0 else
                                "coarse_numeric_ratio_only_not_clock_calibration"})
    return {"events": rows, "pairs": pairs, "event_order_matches_known_feedback_offsets": True,
            "elapsed_time_resolved": False}


def main():
    guard = [sys.executable, str(ROOT/"research/verify_credited_semantics_checkpoint.py")]
    subprocess.run(guard, check=True)
    old_path = UID_DATA/"late-event-layout-probe.json"
    controls_path = ROOT/"data/research/credited-late-history-controls/result.json"
    old, controls = read(old_path), read(controls_path)
    dataset = read(COUNT_DATA/"dataset.json")
    records = []
    for row in old["records"]:
        canonical = next(m for m in dataset["maps"] if m["cohort"] == "SAL" and m["map_id"] == row["map_id"])
        events = next(r for r in canonical["rounds"] if r["logical_round"] == row["round"])["events"]
        feed = [{"offset": e["packet_offset"], "feedback": e["raw_feedback"]} for e in events]
        records.append({"cohort": "SAL", "map_id": row["map_id"], "round": row["round"],
                        **clock_scope(row["candidates"], feed)})
    for row in controls["records"]:
        records.append({"cohort": row["cohort"], "map_id": row["map_id"], "round": row["logical_round"],
                        **clock_scope([r["candidate"] for r in row["unique_payloads"]], row["original_feed"])})
    result = {"status": "opaque_scalar_order_validated_units_unresolved", "records": records,
              "source_sha256": source_sha(Path(__file__)), "inputs": {str(p.relative_to(ROOT)).replace("\\", "/"): sha(p) for p in (old_path, controls_path)},
              "limitation": "No assumed ticks/sec, no byte-distance time. Scalar magnitudes differ across professional/local samples. Need explicit replay recording/playback clock semantics and phase/overtime controls before trade seconds."}
    target = ROOT/"data/research/credited-late-history-controls/clock-scope.json"
    if target.exists() and read(target) != result:
        raise ValueError("Never overwrite scalar clock diagnostic")
    if not target.exists():
        target.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    for r in records:
        print(r["cohort"], r["map_id"], r["round"], "ratios",
              [round(p["scalar_units_per_displayed_clock_second"], 2) if p["scalar_units_per_displayed_clock_second"] is not None else None for p in r["pairs"]], flush=True)
    subprocess.run(guard, check=True)


if __name__ == "__main__":
    main()
