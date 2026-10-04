"""Verify case timelines, failed harness and prior protected evidence."""
import subprocess
import sys

from credited_round_dataset import read
from v3_final_reserve import ROOT,sha,source_sha


def main():
    seal=read(ROOT/"research/credited-clock-case-checkpoint.json")
    for n,h in seal["source_hashes"].items():
        if source_sha(ROOT/n)!=h:
            raise ValueError("Clock-case source changed: "+n)
    for n,h in seal["artifact_hashes"].items():
        if sha(ROOT/n)!=h:
            raise ValueError("Clock-case evidence changed: "+n)
    subprocess.run([sys.executable,str(ROOT/"research/verify_clock_prefix_checkpoint.py")],check=True)
    print("Ten raw clock case timelines and original harness failure verified; no causal attribution")


if __name__=="__main__":
    main()
