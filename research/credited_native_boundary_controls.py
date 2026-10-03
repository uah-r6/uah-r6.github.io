"""Consumed-only native-reader parity controls; no credit migration or targets.

Fixed first/last rounds of every physical segment in the recorded 32-map pool,
plus all known missing legacy offsets. No outcome-driven sample expansion.
"""
import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys

from credited_native_envelope_audit import native, original_reader, EXE, SOURCE
from v3_final_reserve import ROOT, sha, source_sha

DATA = ROOT / "data/research/credited-native-boundary-controls"


def verify_live():
    subprocess.run([sys.executable, str(ROOT / "research/verify_objective_history_checkpoint.py")], check=True)


def compare(observed, original):
    if observed["header"] != original["header"]:
        raise ValueError("Native observer changed header/operator/action output")
    if observed["originalFinishes"] != original["credit"]["finishes"]:
        raise ValueError("Native observer changed original feedback/offsets")
    current, prior = observed["credit"], original["credit"]
    if current["source"] != SOURCE:
        raise ValueError("Unexpected native source")
    if prior["complete"] and (not current["complete"] or current["players"] != prior["players"]):
        raise ValueError("Native observer changed supported counters")
    if len(current["finishes"]) != len(observed["originalFinishes"]):
        raise ValueError("Native observer changed finish count")
    recovered = []
    for old, new in zip(observed["originalFinishes"], current["finishes"]):
        if old["feedback"] != new["feedback"]:
            raise ValueError("Native observer changed victim/finisher feedback")
        if old["offset"] == new["offset"]:
            continue
        if old["offset"] != 0 or old["feedback"]["type"]["name"] != "Death":
            raise ValueError("Native observer changed a known offset")
        envelope = [e for e in observed["nativeEnvelopes"]
                    if e["feedback"] == old["feedback"] and e["legacyOffset"] == 0]
        if (len(envelope) != 1 or not envelope[0]["markerValid"] or
                envelope[0]["startOffset"] != new["offset"] or
                not 0 < envelope[0]["startOffset"] < envelope[0]["endOffset"]):
            raise ValueError("Recovered unknown Death lacks unique valid native envelope")
        recovered.append({"victim": old["feedback"]["username"], "offset": new["offset"],
                          "end": envelope[0]["endOffset"]})
    return {"original_complete": prior["complete"], "native_complete": current["complete"],
            "original_reason": prior["reason"], "native_reason": current["reason"],
            "finishes": len(current["finishes"]), "recovered": recovered,
            "header_operator_action_parity": True, "original_feedback_parity": True,
            "supported_counter_parity": True}


def selection():
    result = []
    for event, folder, extraction in (
            ("SAL", "v3-sal-kill-credit", "v3-corrected-final-sal"),
            ("APAC", "v3-apac-kill-credit", "v3-final-apac-n")):
        for path in sorted((ROOT / "data/research/diagnostics" / folder).glob("*.json")):
            if not path.stem.isdigit():
                continue
            old = json.loads(path.read_text(encoding="utf-8"))
            segments = defaultdict(list)
            for row in old["rounds"]:
                segments[row["folder"]].append(row)
            for segment, rows in segments.items():
                chosen = {rows[0]["physical_round"], rows[-1]["physical_round"]}
                chosen.update(r["physical_round"] for r in rows if any(f["offset"] <= 0 for f in r["feed"]))
                for row in rows:
                    if row["physical_round"] not in chosen:
                        continue
                    files = [p for p in (ROOT / f"data/research/extracted/{extraction}-{old['official_match_id']}").rglob(row["filename"])
                             if p.parent.name == segment]
                    if len(files) != 1 or sha(files[0]) != row["replay_sha256"]:
                        raise ValueError("Consumed replay identity differs")
                    result.append({"event": event, "map_id": old["official_match_id"],
                                   "segment": segment, "round": row["physical_round"],
                                   "path": str(files[0].relative_to(ROOT)).replace('\\', '/'),
                                   "replay_sha256": row["replay_sha256"], "original_record_sha256": sha(path)})
    if len(result) != 68 or len({(r["event"], r["map_id"]) for r in result}) != 32:
        raise ValueError("Fixed consumed boundary cohort changed")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=68)
    args = parser.parse_args()
    if not 1 <= args.limit <= 68:
        raise ValueError("Limit must be within the fixed cohort")
    # New guard replaces old live-state assertions, not old research semantics.
    verify_live()
    DATA.mkdir(parents=True, exist_ok=True)
    chosen = selection()
    reservation = {"scope": "Consumed decoder controls only; no actor/Rating target or final evaluation",
                   "selection": chosen, "native_binary_sha256": sha(EXE),
                   "helper_sha256": source_sha(Path(__file__))}
    path = DATA / "selection.json"
    if path.exists():
        if json.loads(path.read_text(encoding="utf-8")) != reservation:
            raise ValueError("Never revise the fixed boundary selection")
    else:
        path.write_text(json.dumps(reservation, indent=2) + "\n", encoding="utf-8")

    def inspect(row):
        rec = ROOT / row["path"]
        new, old = native(rec), original_reader(rec)
        checked = compare(new, old)
        print(f"native boundary {row['event']}/{row['map_id']} R{row['round']:02d}: parity", flush=True)
        return {**row, **checked}

    with ThreadPoolExecutor(max_workers=2) as pool:
        rows = list(pool.map(inspect, chosen[:args.limit]))
    counts = Counter(rounds=len(rows), maps=len({(r['event'], r['map_id']) for r in rows}),
                     original_complete=sum(r['original_complete'] for r in rows),
                     native_complete=sum(r['native_complete'] for r in rows),
                     recovered_deaths=sum(len(r['recovered']) for r in rows),
                     finishes=sum(r['finishes'] for r in rows))
    if args.limit == 68:
        result = {"status": "consumed_native_boundary_controls_no_migration", "counts": dict(counts),
                  "rows": rows, "selection_sha256": sha(path),
                  "helper_sha256": source_sha(Path(__file__)), "live_guard": "objective-history-migration-checkpoint"}
        destination = DATA / "result.json"
        if destination.exists():
            if json.loads(destination.read_text(encoding="utf-8")) != result:
                raise ValueError("Never rewrite an existing consumed result")
        else:
            destination.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    verify_live()
    print(dict(counts), flush=True)


if __name__ == "__main__":
    main()
