"""Verify historical Go trial sources/results, including failed replay path."""
import subprocess
import sys

from credited_round_dataset import read
from v3_final_reserve import ROOT,sha,source_sha


def main():
    record=read(ROOT/"research/credited-history-go-checkpoint.json")
    historical=record["historical_source_locations"]
    for name,expected in record["source_hashes"].items():
        path=ROOT/historical.get(name,name)
        if source_sha(path)!=expected:
            raise ValueError("Historical Go trial source changed: "+str(path))
    for name,expected in record["artifact_hashes"].items():
        if sha(ROOT/name)!=expected:
            raise ValueError("Go trial evidence changed: "+name)
    subprocess.run([sys.executable,str(ROOT/"research/verify_history_typed_checkpoint.py")],check=True)
    print("74 cached Go agreements and both original replay-interface failures verified; no promotion")


if __name__=="__main__":
    main()
