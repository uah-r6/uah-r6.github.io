"""Verify late-history discovery without decoding/evaluating it again."""
import subprocess
import sys

from credited_round_dataset import read
from v3_final_reserve import ROOT, sha, source_sha


def main():
    record = read(ROOT/"research/credited-late-history-checkpoint.json")
    for name, expected in record["source_hashes"].items():
        if source_sha(ROOT/name) != expected:
            raise ValueError("Late-history source changed: "+name)
    for name, expected in record["artifact_hashes"].items():
        if sha(ROOT/name) != expected:
            raise ValueError("Late-history evidence changed: "+name)
    subprocess.run([sys.executable, str(ROOT/"research/verify_credited_semantics_checkpoint.py")], check=True)
    print("Late history field/framing/body/clock controls verified; no event migration or scalar seconds assumed")


if __name__ == "__main__":
    main()
