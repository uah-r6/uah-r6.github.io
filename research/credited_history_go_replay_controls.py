"""Two fixed real inputs validate the new opt-in Go --replay path.

This is a new reader-interface control, not an old pipeline/evaluation rerun.
No SQLite, source replay, archive, statistics or public output is modified.
"""
import json
from pathlib import Path
import subprocess
import sys

from credited_history_go_controls import DATA,EXE
from credited_late_history_development import immutable_write
from credited_round_dataset import inventory,read
from v3_final_reserve import ROOT,sha,source_sha

SELECTION = (("SAL",8583,2),("UAH","d64d5478cdb3",4))


def main():
    guard = [sys.executable,str(ROOT/"research/verify_history_typed_checkpoint.py")]
    subprocess.run(guard,check=True)
    maps = {(m["cohort"],m["map_id"]):m for m in inventory()}
    sources = []
    for cohort,mid,number in SELECTION:
        source = next(s for s in maps[cohort,mid]["sources"] if s["logical_round"] == number)
        path = source["path"]
        if sha(path) != source["replay_sha256"]:
            raise ValueError("Fixed interface-control replay changed")
        sources.append({"event":cohort,"map_id":mid,"logical_round":number,
                        "path":str(path.relative_to(ROOT)).replace("\\","/"),"replay_sha256":source["replay_sha256"]})
    reservation = {"base_head":"3caf344","sources":sources,"binary_sha256":sha(EXE),
                   "source_sha256":source_sha(Path(__file__)),
                   "hypothesis":"Explicit --replay reader path must reproduce cached --buffer structural evidence; no runtime promotion"}
    immutable_write(DATA/"replay-interface-reservation.json",reservation)
    results = []
    for source in sources:
        path = ROOT/source["path"]
        expected_path = DATA/"raw"/(source["replay_sha256"]+".json")
        expected = read(expected_path)
        target = DATA/"replay-interface"/(source["replay_sha256"]+".json")
        if target.exists():
            result = read(target)
            if result["binary_sha256"] != sha(EXE) or result["source_sha256"] != source_sha(Path(__file__)):
                raise ValueError("Cached interface control source/binary changed")
            if result["expected_sha256"] != sha(expected_path):
                raise ValueError("Cached interface expected evidence changed")
        else:
            call = subprocess.run([str(EXE),"--replay",str(path)],capture_output=True)
            actual = json.loads(call.stdout) if call.returncode == 0 else {"returncode":call.returncode,"error":call.stderr.decode("utf-8",errors="replace")}
            result = {**source,"binary_sha256":sha(EXE),"source_sha256":source_sha(Path(__file__)),
                      "expected_sha256":sha(expected_path),"complete_exact_buffer_parity":actual == expected,
                      "actual":actual,"status":"fixed_new_reader_interface_control_not_pipeline_rerun"}
            immutable_write(target,result)
        results.append(result)
        print(source["event"],source["map_id"],source["logical_round"],"actual replay/buffer parity",result["complete_exact_buffer_parity"],flush=True)
    immutable_write(DATA/"replay-interface-result.json",{"records":results,"all_exact":all(r["complete_exact_buffer_parity"] for r in results)})
    subprocess.run(guard,check=True)


if __name__ == "__main__":
    main()
