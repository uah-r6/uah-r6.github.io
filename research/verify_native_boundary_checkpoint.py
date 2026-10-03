"""Verify separate consumed decoder/identity controls and authorized live state."""
import json
import subprocess
import sys
from pathlib import Path

from v3_final_reserve import ROOT, sha, source_sha


def main():
    record = json.loads((ROOT / "research/credited-native-boundary-checkpoint.json").read_text(encoding="utf-8"))
    for name, expected in record["source_hashes"].items():
        if source_sha(ROOT / name) != expected:
            raise ValueError("Native boundary source changed: " + name)
    for name, expected in record["artifact_hashes"].items():
        if sha(ROOT / name) != expected:
            raise ValueError("Native boundary evidence changed: " + name)
    subprocess.run([sys.executable, str(ROOT / "research/verify_objective_history_checkpoint.py")], check=True)
    print("68-round native boundary and exact callback identity controls verified; source remains opt-in, no final evaluation")


if __name__ == "__main__":
    main()
