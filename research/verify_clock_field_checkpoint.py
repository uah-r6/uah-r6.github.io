"""Check raw clock hypothesis results and all prior protected evidence."""
import subprocess
import sys

from credited_round_dataset import read
from v3_final_reserve import ROOT,sha,source_sha


def main():
    seal=read(ROOT/"research/credited-clock-field-checkpoint.json")
    for name,expected in seal["source_hashes"].items():
        if source_sha(ROOT/name)!=expected:
            raise ValueError("Clock-field source changed: "+name)
    for name,expected in seal["artifact_hashes"].items():
        if sha(ROOT/name)!=expected:
            raise ValueError("Clock-field artifact changed: "+name)
    subprocess.run([sys.executable,str(ROOT/"research/verify_owned_property_checkpoint.py")],check=True)
    print("Six clock/header inventories and scale/refusal evidence verified; no elapsed-time promotion")


if __name__=="__main__":
    main()
