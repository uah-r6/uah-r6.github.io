"""Verify frozen consumed extension and baseline; no replay job."""
import subprocess
import sys

from credited_round_dataset import read
from v3_final_reserve import ROOT, sha, source_sha


def main():
    record = read(ROOT/"research/credited-history-development-checkpoint.json")
    for name, expected in record["source_hashes"].items():
        if source_sha(ROOT/name) != expected:
            raise ValueError("Frozen development source changed: "+name)
    for name, expected in record["artifact_hashes"].items():
        if sha(ROOT/name) != expected:
            raise ValueError("Frozen development evidence changed: "+name)
    subprocess.run([sys.executable, str(ROOT/"research/verify_credit_hypothesis_checkpoint.py")], check=True)
    print("68-source frozen hypothesis, counter mismatches/refusals and bounded append controls verified")


if __name__ == "__main__":
    main()
