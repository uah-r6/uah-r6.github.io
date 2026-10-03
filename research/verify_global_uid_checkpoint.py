"""Verify consumed global UID discovery, without executing any study again."""
import json
import subprocess
import sys

from v3_final_reserve import ROOT, sha, source_sha


def main():
    record = json.loads((ROOT / "research/credited-global-uid-checkpoint.json").read_text(encoding="utf-8"))
    for name, expected in record["source_hashes"].items():
        if source_sha(ROOT / name) != expected:
            raise ValueError("Global UID inventory source changed: " + name)
    for name, expected in record["artifact_hashes"].items():
        if sha(ROOT / name) != expected:
            raise ValueError("Global UID inventory artifact changed: " + name)
    subprocess.run([sys.executable, str(ROOT / "research/verify_native_boundary_checkpoint.py")], check=True)
    print("Global literal UID discovery verified; no damage/DBNO identity semantics or migration claimed")


if __name__ == "__main__":
    main()
