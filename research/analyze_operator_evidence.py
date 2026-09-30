"""Summarize structural operator evidence from operator_diagnostics.py output."""
from collections import Counter
import json
from pathlib import Path
import re
import sys
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data/research/diagnostics/operator-all-pro-packets.json"


def canonical(name: str) -> str:
    # siege-dissect's JSON replaces invalid single-byte accented header chars.
    name = name.upper().replace("CAPIT�O", "CAPITAO").replace("N�KK", "NOKK")
    name = name.replace("Ø", "O")
    name = "".join(c for c in unicodedata.normalize("NFKD", name) if not unicodedata.combining(c))
    return re.sub(r"[^A-Z0-9]", "", name)


def operator_ids() -> dict[str, int]:
    header = (ROOT / "third_party/siege-dissect/dissect/header.go").read_text(encoding="utf-8")
    names = {canonical(name): int(value) for name, value in
             re.findall(r"^\s*(\w+)\s+Operator\s*=\s*(\d+)", header, re.M)}
    names["SOLIDSNAKE"] = 444310693746  # Header RoleName + Ubisoft operator listing.
    return names


def summarize(rows: list[dict]) -> dict:
    ids = operator_ids()
    counts = Counter()
    by_build = {}
    failures = []
    for item in rows:
        build = item["game_version"]
        build_counts = by_build.setdefault(build, Counter())
        counts["rounds"] += 1
        build_counts["rounds"] += 1
        action = item.get("action_start")
        if action and action["previous_seconds"] == 0 and action["seconds"] == 179:
            counts["structural_action_start"] += 1
            build_counts["structural_action_start"] += 1
        pre_action = {p["operator_id"] for p in item.get("pre_action_operator_packets", [])}
        for player in item["players"]:
            if player["side"] != "Attack":
                continue
            counts["attacker_player_rounds"] += 1
            build_counts["attacker_player_rounds"] += 1
            initial = player["header_operator_name"]
            final = player["header_role_name"] or ""
            if canonical(initial) != canonical(final):
                counts["initial_differs_from_header_role"] += 1
                build_counts["initial_differs_from_header_role"] += 1
            op = ids.get(canonical(final))
            if not op:
                counts["unmapped_header_role"] += 1
                failures.append((item["file"], player["username"], "unmapped", final))
            elif op not in pre_action:
                counts["final_id_unseen_before_action"] += 1
                failures.append((item["file"], player["username"], "unseen", final, op))
            else:
                counts["final_id_seen_before_action"] += 1
                build_counts["final_id_seen_before_action"] += 1
    return {"counts": dict(counts), "by_build": {k: dict(v) for k, v in by_build.items()},
            "failures": failures}


if __name__ == "__main__":
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_INPUT
    result = summarize(json.loads(path.read_text(encoding="utf-8")))
    print(json.dumps(result, indent=2))
