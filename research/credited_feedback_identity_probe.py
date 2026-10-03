"""Inspect exact native callback bytes for direct credited-player references.

Two independently broadcast-reviewed DBNO/finisher disagreements; all other
callbacks in the same rounds are controls. Literal matches are not semantics.
"""
from collections import Counter
import json
from pathlib import Path
import subprocess
import sys

from credited_native_envelope_audit import native
from v3_final_reserve import ROOT, sha, source_sha

DATA = ROOT / "data/research/credited-feedback-identity-probe"
PARSER = ROOT / ".local-tools/bin/siege-dissect-actors.exe"
CASES = ((8580, 6, "Stk.INTZ", "Maia.TLAW", "Kheyze.TLAW"),
         (8583, 2, "resetz.LOUD", "pino.L5", "Neskin.L5"))


def direct_references(packet: bytes, players: list[dict]) -> dict:
    """Evidence only: exact nonzero header uint64s and literal UTF-8 usernames."""
    numeric, names = [], []
    for player in players:
        uid = player.get("id")
        if type(uid) is int and 0 < uid < 2 ** 64:
            pattern = uid.to_bytes(8, "little")
            cursor = 0
            while (at := packet.find(pattern, cursor)) >= 0:
                numeric.append({"player": player["username"], "uid": uid, "relative_offset": at})
                cursor = at + 1
        name = player["username"].encode("utf-8")
        if name:
            cursor = 0
            while (at := packet.find(name, cursor)) >= 0:
                names.append({"player": player["username"], "relative_offset": at})
                cursor = at + 1
    return {"literal_numeric_uid_references": numeric, "literal_username_references": names}


def main():
    guard = [sys.executable, str(ROOT / "research/verify_objective_history_checkpoint.py")]
    subprocess.run(guard, check=True)
    DATA.mkdir(parents=True, exist_ok=True)
    records = []
    for mid, number, victim, finisher, credited in CASES:
        old_path = ROOT / f"data/research/diagnostics/v3-sal-kill-credit/{mid}.json"
        old = json.loads(old_path.read_text(encoding="utf-8"))
        row = next(r for r in old["rounds"] if r["logical_round"] == number)
        sources = [p for p in (ROOT / f"data/research/extracted/v3-corrected-final-sal-{mid}").rglob(row["filename"])
                   if p.parent.name == row["folder"]]
        if len(sources) != 1 or sha(sources[0]) != row["replay_sha256"]:
            raise ValueError("Consumed replay identity differs")
        observed = native(sources[0])
        actual = [e for e in observed["nativeEnvelopes"] if e["feedback"].get("target") == victim]
        if len(actual) != 1 or actual[0]["feedback"].get("username") != finisher:
            raise ValueError("Independently reviewed finish differs")
        # Dump only provides the exact decompressed reader buffer; no new
        # Python replay decoder or changes to default callbacks/operators.
        path = DATA / (row["replay_sha256"] + ".dump")
        if not path.exists():
            subprocess.run([str(PARSER), "--dump", "-o", str(path), str(sources[0])], check=True, capture_output=True)
        data = path.read_bytes()
        for e in observed["nativeEnvelopes"]:
            start, end = e["startOffset"], e["endOffset"]
            if (not e["markerValid"] or not 0 < start < end <= len(data) or
                    data[start:start+5] != bytes.fromhex("5934e58b04")):
                raise ValueError("Exact native callback envelope invalid")
            references = direct_references(data[start:end], observed["header"]["players"])
            reviewed = e == actual[0]
            records.append({"map_id": mid, "round": number, "replay_sha256": row["replay_sha256"],
                            "start": start, "end": end, "feedback": e["feedback"], "reviewed_dbno_finish": reviewed,
                            "independent_credited_player": credited if reviewed else None, **references,
                            "credited_player_numeric_reference": any(r['player'] == credited for r in references['literal_numeric_uid_references']) if reviewed else None,
                            "credited_player_username_reference": any(r['player'] == credited for r in references['literal_username_references']) if reviewed else None,
                            "packet_hex": data[start:end].hex()})
        print('callback identity probe', mid, number, len(observed['nativeEnvelopes']), flush=True)
    result = {"status": "consumed_exact_callback_identity_probe_no_victim_credit_mapping", "records": records,
              "helper_sha256": source_sha(Path(__file__)), "parser_sha256": sha(PARSER),
              "limits": "Only exact existing decoder callback bounds and literal header numeric UIDs/usernames. No class semantics, indirect owner/entity references, separate damage packets or encoded IDs assessed; no actor inferred from absence or proximity."}
    target = DATA / "result.json"
    if target.exists():
        if json.loads(target.read_text(encoding="utf-8")) != result:
            raise ValueError("Never rewrite a consumed identity result")
    else:
        target.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    for row in records:
        if row['reviewed_dbno_finish']:
            print(row['map_id'], row['feedback'], row['literal_numeric_uid_references'], row['literal_username_references'], flush=True)
    subprocess.run(guard, check=True)


if __name__ == "__main__":
    main()
