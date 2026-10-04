"""Verify fixed cached lifecycle controls and prior production/study guards."""
import subprocess
import sys

from credited_round_dataset import read
from v3_final_reserve import ROOT,sha,source_sha


def main():
    record=read(ROOT/"research/credited-history-lifecycle-checkpoint.json")
    for name,expected in record["source_hashes"].items():
        if source_sha(ROOT/name)!=expected:
            raise ValueError("Lifecycle source changed: "+name)
    for name,expected in record["artifact_hashes"].items():
        if sha(ROOT/name)!=expected:
            raise ValueError("Lifecycle evidence changed: "+name)
    subprocess.run([sys.executable,str(ROOT/"research/verify_history_go_interface_checkpoint.py")],check=True)
    print("74 lifecycle views, unmatched interval and eight missing kind5 targets verified; no migration")


if __name__=="__main__":
    main()
