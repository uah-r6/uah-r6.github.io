"""Exact single-item append boundaries in all fixed consumed history sources."""
from collections import Counter
import json
from pathlib import Path
import subprocess
import sys

from credited_history_append_inventory import append_inventory
from credited_history_framing_v2 import DATA as FRAMING_DATA
from credited_late_history_development import immutable_write
from credited_round_dataset import read
from v3_final_reserve import ROOT, sha, source_sha

DATA = ROOT/"data/research/credited-history-append-development"


def main():
    guard = [sys.executable, str(ROOT/"research/verify_history_development_checkpoint.py")]
    subprocess.run(guard, check=True)
    paths = [FRAMING_DATA/("result-"+cohort+".json") for cohort in ("six", "68")]
    reserved = {"base_head": "33cb8f2", "framing_result_hashes": {str(p.relative_to(ROOT)).replace("\\", "/"):sha(p) for p in paths},
                "helper_hashes": {"research/credited_history_append_development.py":source_sha(Path(__file__)),
                                  "research/credited_history_append_inventory.py":source_sha(ROOT/"research/credited_history_append_inventory.py")},
                "hypothesis": "Exact unchanged prefix and count increment1 reveal a whole bounded item; no roles inferred"}
    immutable_write(DATA/"reservation.json", reserved)
    records, inputs = [], {}
    for path in paths:
        for source in read(path)["records"]:
            record_path = FRAMING_DATA/"records"/(source["replay_sha256"]+".json")
            row = read(record_path)
            dump = ROOT/row["dump_path"]
            if sha(dump) != row["dump_sha256"]:
                raise ValueError("Fixed dump identity changed")
            appends = append_inventory(dump.read_bytes(), row["containers"])
            records.append({k: row[k] for k in ("event","map_id","round","replay_sha256")} | {"appends":appends})
            for p in (record_path,dump):
                inputs[str(p.relative_to(ROOT)).replace("\\", "/")] = sha(p)
    kinds = Counter((a["kind_byte"],a["width"]) for r in records for a in r["appends"] if a["single_item_append"])
    tails = Counter((a["width"], int(a["raw_hex"][-2:],16)) for r in records for a in r["appends"] if a["single_item_append"] and a["kind_byte"] == 10)
    result = {"source_sha256":source_sha(Path(__file__)),"records":records,"inputs":inputs,
              "kind_widths":[{"kind":k,"width":w,"count":n} for (k,w),n in sorted(kinds.items())],
              "kind10_width_tail_values":[{"width":w,"opaque_tail":t,"count":n} for (w,t),n in sorted(tails.items())],
              "status":"consumed_exact_append_layouts_not_event_roles_or_seconds"}
    immutable_write(DATA/"result.json", result)
    print('Exact appended kind/width inventory',result['kind_widths'],flush=True)
    print('Opaque kind10 tail inventory',result['kind10_width_tail_values'],flush=True)
    subprocess.run(guard,check=True)


if __name__ == "__main__":
    main()
