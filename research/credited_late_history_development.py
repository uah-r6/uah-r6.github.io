"""Frozen hypothesis on the fixed consumed cohort; no evaluation or promotion.

New hypothesis-specific dumps only. Per-source results, including refusals,
are immutable; progress is resumable. No original parsing pipeline rerun.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from credited_feedback_identity_probe import direct_references
from credited_uid_pair_inventory import paired_at
from credited_late_event_layout_probe import candidate_at, compare_finishes
from credited_late_credit_hypothesis import reconstruct
from credited_round_dataset import read, cached_index, cached_observation
from v3_final_reserve import ROOT, sha, source_sha

DATA = ROOT/"data/research/credited-late-history-development"
SELECTION = ROOT/"data/research/credited-native-boundary-controls/selection.json"
PARSER = ROOT/".local-tools/bin/siege-dissect-actors.exe"
SOURCES = ("research/credited_late_history_development.py", "research/credited_feedback_identity_probe.py",
           "research/credited_uid_pair_inventory.py", "research/credited_late_event_layout_probe.py",
           "research/credited_late_credit_hypothesis.py", "research/credited_round_dataset.py",
           "research/v3_final_reserve.py", "r6stats/kill_credit.py")


def interleave(selection):
    """Alternate SAL/APAC while preserving each sealed cohort's original order."""
    if any(r["event"] not in ("SAL", "APAC") for r in selection):
        raise ValueError("Unexpected fixed cohort")
    groups = [[r for r in selection if r["event"] == e] for e in ("SAL", "APAC")]
    rows = [g[i] for i in range(max(map(len, groups))) for g in groups if i < len(g)]
    if len({r["replay_sha256"] for r in rows}) != len(rows):
        raise ValueError("Repeated physical source")
    return rows


def immutable_write(path, value):
    if path.exists():
        if read(path) != value:
            raise ValueError("Never replace development evidence: " + str(path))
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix+".partial")
    temporary.write_text(json.dumps(value, indent=2)+"\n", encoding="utf-8")
    temporary.replace(path)


def analyze(candidates, observation):
    """Missing history, feed mismatch and bad counters cannot become success."""
    credit = observation["credit"]
    try:
        parity = compare_finishes(candidates, credit["finishes"])
    except ValueError as exc:
        parity = {"exact_identity_weapon_headshot_order_match": False, "unresolved": str(exc)}
    refusal = []
    if not parity["exact_identity_weapon_headshot_order_match"]:
        refusal.append("Independent finisher identity/weapon/headshot/order parity failed")
    if not credit["complete"]:
        refusal.append("Original counter source incomplete: "+credit.get("reason", ""))
    try:
        proposed = reconstruct(candidates, {p["uid"]: p["team"] for p in credit["players"]})
    except ValueError as exc:
        proposed = {"unresolved": str(exc), "production_authoritative": False}
        refusal.append(str(exc))
    compared = []
    if not refusal:
        compared = [{"uid": p["uid"], "username": p["username"], "counter_kills": p["kills"],
                     "hypothesis_kills": proposed["counts"].get(p["uid"], 0),
                     "match": proposed["counts"].get(p["uid"], 0) == p["kills"]}
                    for p in credit["players"]]
    return {"comparison": parity, "reconstructed": proposed, "comparisons": compared,
            "quality_refusals": refusal, "status": "quality_refused" if refusal else (
                "counter_mismatch" if any(not c["match"] for c in compared) else "counter_agreement")}


def reserve(selection):
    reservation = {"base_head": "6e18e5c", "selection_sha256": sha(SELECTION),
                   "selection_order": "SAL/APAC alternating original order, exhausted cohort omitted",
                   "selection": selection, "source_hashes": {p: source_sha(ROOT/p) for p in SOURCES},
                   "parser_sha256": sha(PARSER),
                   "hypothesis": "Frozen last_opponent_kind5_cleared_on_kind7_v1; exact finisher parity required; no elapsed seconds",
                   "scope": "Consumed development, not independent targets/final evaluation or production admission"}
    immutable_write(DATA/"reservation.json", reservation)
    return reservation


def summarize(records, total):
    return {"status": "incremental_consumed_development_not_promoted", "fixed_total_sources": total,
            "completed_sources": len(records), "statuses": dict(Counter(r["status"] for r in records)),
            "cohorts": dict(Counter(r["event"] for r in records)),
            "counter_agreements": sum(c["match"] for r in records for c in r["comparisons"]),
            "counter_mismatches": sum(not c["match"] for r in records for c in r["comparisons"]),
            "mismatch_records": [r["record_path"] for r in records if r["status"] == "counter_mismatch"],
            "refused_records": [r["record_path"] for r in records if r["status"] == "quality_refused"],
            "records": [{k: r[k] for k in ("event", "map_id", "segment", "round", "record_path", "status")} for r in records]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=8)
    args = parser.parse_args()
    guard = [sys.executable, str(ROOT/"research/verify_credit_hypothesis_checkpoint.py")]
    subprocess.run(guard, check=True)
    selection = interleave(read(SELECTION)["selection"])
    if not 1 <= args.limit <= len(selection):
        raise ValueError("Limit outside fixed selection")
    reservation = reserve(selection)
    signature = hashlib.sha256(json.dumps(reservation, sort_keys=True).encode()).hexdigest()
    index, records = cached_index(), []
    for i, source in enumerate(selection[:args.limit], 1):
        rec = ROOT/source["path"]
        if sha(rec) != source["replay_sha256"]:
            raise ValueError("Fixed source identity changed")
        target = DATA/"records"/(source["replay_sha256"]+".json")
        if target.exists():
            record = read(target)
            if record["reservation_signature"] != signature or record["source"] != source:
                raise ValueError("Cached reservation differs")
            for name, expected in record["inputs"].items():
                if sha(ROOT/name) != expected:
                    raise ValueError("Cached evidence changed: "+name)
        else:
            cache, observation = cached_observation(index, source["replay_sha256"])
            key = hashlib.sha256(PARSER.read_bytes()+bytes.fromhex(source["replay_sha256"])).hexdigest()
            dump = DATA/"dumps"/(key+".dump")
            dump.parent.mkdir(parents=True, exist_ok=True)
            if not dump.exists():
                staging = dump.with_suffix(".dump.partial")
                subprocess.run([str(PARSER), "--dump", "-o", str(staging), str(rec)], check=True, capture_output=True)
                staging.replace(dump)
            data, players = dump.read_bytes(), observation["header"]["players"]
            refs = direct_references(data, players)["literal_numeric_uid_references"]
            pairs = [p for at in sorted({r["relative_offset"] for r in refs}) if (p := paired_at(data, at, players))]
            candidates = [c for p in pairs if (c := candidate_at(data, p))]
            grouped = {}
            for c in candidates:
                grouped.setdefault(c["raw_hex"], []).append(c)
            unique = [{"candidate": values[0], "physical_copies": [c["start"] for c in values]} for values in grouped.values()]
            unique.sort(key=lambda r: r["candidate"]["opaque_scalar"])
            record = {**source, "source": source, "reservation_signature": signature,
                      "build": observation["header"]["codeVersion"],
                      "action_start": observation["header"]["actionPhaseStartOffset"],
                      "literal_uid_reference_count": len(refs), "pair_count": len(pairs),
                      "unique_payloads": unique, "original_feed": observation["credit"]["finishes"],
                      "original_counter_complete": observation["credit"]["complete"],
                      "inputs": {str(p.relative_to(ROOT)).replace("\\", "/"): sha(p) for p in (rec, cache, dump)},
                      "record_path": str(target.relative_to(ROOT)).replace("\\", "/"), **analyze(candidates, observation)}
            immutable_write(target, record)
        records.append(record)
        (DATA/"progress.json").write_text(json.dumps(summarize(records, len(selection)), indent=2)+"\n", encoding="utf-8")
        print(i, "/", args.limit, source["event"], source["map_id"], source["round"], record["status"],
              "agreements", sum(c["match"] for c in record["comparisons"]), "refusals", record["quality_refusals"], flush=True)
    immutable_write(DATA/(f"sample-{args.limit:02}.json"), summarize(records, len(selection)))
    subprocess.run(guard, check=True)


if __name__ == "__main__":
    main()
