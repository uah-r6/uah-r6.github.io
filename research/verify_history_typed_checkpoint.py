"""Verify typed history layouts/missing actor without replay processing."""
import subprocess
import sys

from credited_round_dataset import read
from v3_final_reserve import ROOT, sha, source_sha


def main():
    record=read(ROOT/"research/credited-history-typed-checkpoint.json")
    for name, expected in record["source_hashes"].items():
        if source_sha(ROOT/name) != expected:
            raise ValueError("Typed history source changed: "+name)
    for name, expected in record["artifact_hashes"].items():
        if sha(ROOT/name) != expected:
            raise ValueError("Typed history evidence changed: "+name)
    subprocess.run([sys.executable,str(ROOT/"research/verify_history_framing_checkpoint.py")],check=True)
    print("74 typed histories, original feed parity and missing Aokayu actor evidence verified")


if __name__ == "__main__":
    main()
