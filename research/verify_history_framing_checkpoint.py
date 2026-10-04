"""Verify fixed cumulative framing/append trials and preserved baseline."""
import subprocess
import sys

from credited_round_dataset import read
from v3_final_reserve import ROOT, sha, source_sha


def main():
    record = read(ROOT/"research/credited-history-framing-checkpoint.json")
    for name, expected in record["source_hashes"].items():
        if source_sha(ROOT/name) != expected:
            raise ValueError("Framing source changed: "+name)
    for name, expected in record["artifact_hashes"].items():
        if sha(ROOT/name) != expected:
            raise ValueError("Framing evidence changed: "+name)
    subprocess.run([sys.executable,str(ROOT/"research/verify_history_development_checkpoint.py")],check=True)
    print("Cumulative framing variants/refusals and exact single-item append boundaries verified")


if __name__ == "__main__":
    main()
