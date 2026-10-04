"""Verify successful retained-buffer interface and immutable original failures."""
import subprocess
import sys

from credited_round_dataset import read
from v3_final_reserve import ROOT,sha,source_sha


def main():
    record=read(ROOT/"research/credited-history-go-interface-checkpoint.json")
    for name,expected in record["source_hashes"].items():
        if source_sha(ROOT/name)!=expected:
            raise ValueError("Go interface source changed: "+name)
    for name,expected in record["artifact_hashes"].items():
        if sha(ROOT/name)!=expected:
            raise ValueError("Go interface evidence changed: "+name)
    subprocess.run([sys.executable,str(ROOT/"research/verify_history_go_checkpoint.py")],check=True)
    print("Retained-buffer Go interface: six cached and two actual inputs verified; default behavior unchanged")


if __name__=="__main__":
    main()
