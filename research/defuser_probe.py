"""Count the current siege-dissect defuser listener tag in raw round payloads.

This diagnostic does not infer plants or modify normalized data. It compares
the packet marker used by readDefuserTimer with decompressed replay bytes.
"""
from __future__ import annotations

from pathlib import Path
from collections import Counter
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PARSER = ROOT / ".local-tools/bin/siege-dissect.exe"
TAG = bytes.fromhex("22a9c858d9")  # reader.go's readDefuserTimer listener


def scan(folder: Path) -> None:
    recs = sorted(folder.glob("*.rec"))
    if not recs:
        raise ValueError(f"No round files in {folder}")
    with tempfile.TemporaryDirectory() as directory:
        output = Path(directory) / "round.dump"
        counts = []
        timers = Counter()
        for rec in recs:
            subprocess.run([str(PARSER), "--dump", "-o", str(output), str(rec)],
                           check=True, capture_output=True, text=True)
            data = output.read_bytes()
            counts.append((rec.name, data.count(TAG)))
            start = 0
            while (position := data.find(TAG, start)) >= 0:
                start = position + len(TAG)
                if start >= len(data):
                    continue
                size = data[start]
                if size <= 16 and start + 1 + size <= len(data):
                    timer = data[start + 1:start + 1 + size].decode("ascii", errors="replace")
                    timers[timer] += 1
    print(folder.name, "rounds", len(counts), "tag_total", sum(value for _, value in counts))
    print("round_tag_counts", [value for _, value in counts])
    print("timer_values", timers.most_common(15))
    print("zero_timer_values", {value: count for value, count in timers.items()
                                if value.startswith(("0.00", "0:00", "0.0"))})


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("Usage: defuser_probe.py MATCH_FOLDER [...]")
    for path in sys.argv[1:]:
        scan(Path(path))
