"""New frozen interface controls; preserve the initial failed Go trial."""
import json
from pathlib import Path
import subprocess
import sys

from credited_late_history_development import immutable_write
from credited_round_dataset import read
from v3_final_reserve import ROOT,sha,source_sha

EXE = ROOT/".local-tools/bin/siege-history-inspect-v2.exe"
OLD = ROOT/"data/research/credited-history-go-controls"
DATA = ROOT/"data/research/credited-history-go-interface-v2"
SOURCES = ("research/credited_history_go_interface_v2.py",
           "third_party/siege-dissect/dissect/event_history_evidence.go",
           "third_party/siege-dissect/dissect/event_history_replay_evidence.go",
           "third_party/siege-dissect/dissect/event_history_replay_evidence_test.go",
           "third_party/siege-dissect/cmd/history-inspect/main.go")


def main():
    guard = [sys.executable,str(ROOT/"research/verify_history_go_checkpoint.py")]
    subprocess.run(guard,check=True)
    selection = []
    for r in read(OLD/"sample-06.json")["records"]:
        input_record = read(OLD/"records"/(r["replay_sha256"]+".json"))
        dump = [n for n in input_record["inputs"] if n.endswith(".dump")]
        if len(dump) != 1:
            raise ValueError("Exact cached buffer required")
        selection.append({k:r[k] for k in ("event","map_id","round","replay_sha256")} |
                         {"mode":"buffer","args":["--buffer",str(OLD/"headers"/(r["replay_sha256"]+".json")),str(ROOT/dump[0])]})
    for r in read(OLD/"replay-interface-reservation.json")["sources"]:
        if sha(ROOT/r["path"]) != r["replay_sha256"]:
            raise ValueError("Fixed actual replay changed")
        selection.append({k:r[k] for k in ("event","map_id","replay_sha256")} |
                         {"round":r["logical_round"],"mode":"replay","args":["--replay",str(ROOT/r["path"])]})
    reservation = {"base_head":"849f740","binary_sha256":sha(EXE),"selection":selection,
                   "source_hashes":{p:source_sha(ROOT/p) for p in SOURCES},
                   "hypothesis":"Locally retained buffer during normal Read reproduces unchanged typed evidence; default release stays unchanged",
                   "limits":"New interface only; no credited owner/elapsed seconds/default normalization/stat/SQL/public change"}
    immutable_write(DATA/"reservation.json",reservation)
    results = []
    for r in selection:
        expected_path = OLD/"raw"/(r["replay_sha256"]+".json")
        expected = read(expected_path)
        input_paths = [Path(a) for a in r["args"][1:]]
        target = DATA/"records"/(r["replay_sha256"]+"-"+r["mode"]+".json")
        if target.exists():
            result = read(target)
            if result["binary_sha256"] != sha(EXE) or result["source_sha256"] != source_sha(Path(__file__)):
                raise ValueError("Cached interface source/binary changed")
            for n,h in result["inputs"].items():
                if sha(ROOT/n) != h:
                    raise ValueError("Cached interface evidence changed: "+n)
        else:
            call = subprocess.run([str(EXE),*r["args"]],capture_output=True)
            actual = json.loads(call.stdout) if call.returncode == 0 else {"returncode":call.returncode,"error":call.stderr.decode("utf-8",errors="replace")}
            result = ({k:r[k] for k in ("event","map_id","round","replay_sha256","mode")} |
                     {"binary_sha256":sha(EXE),"source_sha256":source_sha(Path(__file__)),
                      "complete_exact_parity":actual == expected,"actual":actual,
                      "inputs":{str(p.relative_to(ROOT)).replace("\\","/"):sha(p) for p in [expected_path,*input_paths]}})
            immutable_write(target,result)
        results.append(result)
        print(r["event"],r["map_id"],r["round"],r["mode"],"v2 exact parity",result["complete_exact_parity"],flush=True)
    immutable_write(DATA/"result.json",{"records":results,"all_exact":all(r["complete_exact_parity"] for r in results),
                                       "status":"new_reader_lifetime_control_not_credited_migration"})
    subprocess.run(guard,check=True)


if __name__ == "__main__":
    main()
