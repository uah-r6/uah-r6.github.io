"""Verify the frozen consumed credit hypothesis without executing it."""
import subprocess
import sys

from credited_round_dataset import read
from v3_final_reserve import ROOT, sha, source_sha


def main():
    record=read(ROOT/"research/credited-history-credit-hypothesis-checkpoint.json")
    for name,expected in record["source_hashes"].items():
        if source_sha(ROOT/name)!=expected:
            raise ValueError("Credit hypothesis source changed: "+name)
    for name,expected in record["artifact_hashes"].items():
        if sha(ROOT/name)!=expected:
            raise ValueError("Credit hypothesis evidence changed: "+name)
    subprocess.run([sys.executable,str(ROOT/"research/verify_late_history_checkpoint.py")],check=True)
    print("Six-round credit hypothesis and opaque-item refusals verified; no live migration")


if __name__=="__main__":
    main()
