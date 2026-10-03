"""Verify additive count/chronology preview without rerunning any research."""
import subprocess
import sys

from credited_round_dataset import read
from v3_final_reserve import ROOT, sha, source_sha


def main():
    record = read(ROOT/"research/credited-basic-semantics-checkpoint.json")
    for name, expected in record["source_hashes"].items():
        if source_sha(ROOT/name) != expected:
            raise ValueError("Credited semantics source changed: "+name)
    for name, expected in record["artifact_hashes"].items():
        if sha(ROOT/name) != expected:
            raise ValueError("Credited semantics evidence changed: "+name)
    subprocess.run([sys.executable, str(ROOT/"research/verify_global_uid_checkpoint.py")], check=True)
    print("Canonical credited round evidence, whole-map preview, gap and batch controls verified; no live migration")


if __name__ == "__main__":
    main()
