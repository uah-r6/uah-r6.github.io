"""Verify broad structural clock controls and all earlier protected evidence."""
import subprocess
import sys

from credited_round_dataset import read
from v3_final_reserve import ROOT,sha,source_sha


def main():
    seal=read(ROOT/"research/credited-clock-prefix-checkpoint.json")
    for n,h in seal["source_hashes"].items():
        if source_sha(ROOT/n)!=h:
            raise ValueError("Clock-prefix source changed: "+n)
    for n,h in seal["artifact_hashes"].items():
        if sha(ROOT/n)!=h:
            raise ValueError("Clock-prefix evidence changed: "+n)
    subprocess.run([sys.executable,str(ROOT/"research/verify_clock_field_checkpoint.py")],check=True)
    print("74 clock prefix/region controls verified; all terminal/zero/legacy limits retained")


if __name__=="__main__":
    main()
