"""Verify the authorized live transition without rewriting old research seals.

No evaluations or derivation. Original guards still describe the old live state.
The four pre-existing legacy differences are recorded explicitly, not regraded.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECORD = ROOT / "research/objective-history-migration-checkpoint.json"
WORK = ROOT / "data/research/objective-migration"
CATEGORIES = ("source_hashes", "binary_hashes", "result_hashes", "input_hashes",
              "evidence_hashes", "support_hashes")


def digest(path, source=False):
    data = path.read_bytes()
    return hashlib.sha256(data.replace(b"\r\n", b"\n") if source else data).hexdigest()


def inventory():
    files = [ROOT / "data/r6stats.sqlite", *sorted((ROOT / "data/replay-archive").rglob("*")),
             *sorted((ROOT / "web/public/data").rglob("*.json"))]
    return {p.relative_to(ROOT).as_posix(): digest(p) for p in files if p.is_file()}


def prior_records(paths=None):
    # The original v3 freeze has two source versions superseded by its corrected
    # candidate, and launcher setup rebuilt the default executable before this
    # task. Expected values stay in the original records, unchanged.
    count, exceptions, seals = 0, [], {}
    selected = [ROOT / p for p in paths] if paths is not None else (ROOT / "research").glob("*.json")
    for path in sorted(selected):
        if path == RECORD:
            continue
        document = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(document, dict) or not any(k in document for k in CATEGORIES):
            continue
        seals[path.relative_to(ROOT).as_posix()] = digest(path, source=True)
        for category in CATEGORIES:
            for name, expected in document.get(category, {}).items():
                actual = digest(ROOT / name, source=category == "source_hashes")
                count += 1
                if actual != expected:
                    exceptions.append({"record": path.name, "category": category, "file": name,
                                       "expected": expected, "actual": actual})
    return {"checked_references": count, "seals": seals, "legacy_exceptions": exceptions}


def main():
    args = argparse.ArgumentParser()
    args.add_argument("--record", action="store_true", help="Create the one-time authorized transition checkpoint")
    recording = args.parse_args().record
    if recording:
        if RECORD.exists():
            raise ValueError("Never overwrite the authorized transition checkpoint.")
        evidence = json.loads((WORK / "applied.json").read_text(encoding="utf-8"))
        before = evidence["before_hashes"]
        after = inventory()
        if after != evidence["after_hashes"]:
            raise ValueError("Live state differs from verified migration result.")
        if any(after[p] != h for p, h in before.items() if p.startswith("data/replay-archive/")):
            raise ValueError("Replay archives changed.")
        prior = prior_records()
        allowed = {
            ("objective-bonus-body-asia-freeze.json", "binary_hashes", ".local-tools/bin/siege-dissect.exe"),
            ("objective-bonus-body-oce-freeze.json", "binary_hashes", ".local-tools/bin/siege-dissect.exe"),
            ("v3-frozen-objective-candidate.json", "source_hashes", "research/v3_final_pipeline.py"),
            ("v3-frozen-objective-candidate.json", "source_hashes", "tests/test_v3_objective_research_gates.py"),
        }
        if {(e["record"], e["category"], e["file"]) for e in prior["legacy_exceptions"]} != allowed:
            raise ValueError("Unexpected legacy research differences.")
        sources = ["r6stats/objective_refresh.py", "r6stats/export.py", "r6stats/db/repository.py",
                   "r6stats/admin/server.py", "r6stats/stats/calculate.py", "tests/test_objective_refresh.py",
                   "web/src/admin.tsx", "web/src/ratingFormula.tsx", "docs/OBJECTIVE_HISTORY_MIGRATION.md",
                   "research/verify_objective_history_checkpoint.py"]
        artifacts = ["preview.json", "applied.json", "approved-core.exe", "backup/r6stats.sqlite",
                     "backup/checkpoint.json", "audit.py", "apply_verified.py", "live-verification.json"]
        record = {"status": "authorized_core_objective_history_transition",
                  "production_parser_commit": "7d4bc8a", "credited_kill_migration_applied": False,
                  "v2_original_input_snapshots": 5, "original_v2_final_mae": 0.03623,
                  "before_database_sha256": before["data/r6stats.sqlite"],
                  "after_database_sha256": after["data/r6stats.sqlite"], "protected_hashes": after,
                  "source_hashes": {p: digest(ROOT / p, True) for p in sources},
                  "artifact_hashes": {str((WORK / p).relative_to(ROOT)).replace('\\', '/'): digest(WORK / p) for p in artifacts},
                  "prior_research": prior}
        RECORD.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    record = json.loads(RECORD.read_text(encoding="utf-8"))
    for name, expected in record["source_hashes"].items():
        if digest(ROOT / name, True) != expected:
            raise ValueError("Objective transition source changed: " + name)
    for name, expected in record["artifact_hashes"].items():
        if digest(ROOT / name) != expected:
            raise ValueError("Objective transition evidence changed: " + name)
    if inventory() != record["protected_hashes"]:
        raise ValueError("Authorized live baseline changed.")
    if prior_records(record["prior_research"]["seals"]) != record["prior_research"]:
        raise ValueError("Original research seals or recorded historical differences changed.")
    print("Authorized objective baseline, archives, original research/results and v2 inputs verified; no evaluation repeated")


if __name__ == "__main__":
    main()
