"""Check bounded property controls and all prior production/research evidence."""
import subprocess
import sys

from credited_round_dataset import read
from v3_final_reserve import ROOT,sha,source_sha


def main():
    seal=read(ROOT/"research/credited-owned-property-checkpoint.json")
    for name,expected in seal["source_hashes"].items():
        if source_sha(ROOT/name)!=expected:
            raise ValueError("Owned-property source changed: "+name)
    for name,expected in seal["artifact_hashes"].items():
        if sha(ROOT/name)!=expected:
            raise ValueError("Owned-property artifact changed: "+name)
    subprocess.run([sys.executable,str(ROOT/"research/verify_history_lifecycle_checkpoint.py")],check=True)
    print("Ten owned-prefix controls and absent candidate references verified; causal roles remain unresolved")


if __name__=="__main__":
    main()
