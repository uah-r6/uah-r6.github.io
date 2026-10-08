"""Supported objective-only archive upgrades, with immutable historical v2 inputs."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from r6stats.db import repository as repo
from r6stats.parser.models import Match
from r6stats.parser.siege_dissect import parse_match
from r6stats.replay_archive import map_record, verify
from r6stats.stats.calculate import COUNTS, calculate_match

SOURCE = "completing_timer_owner_v1"


def overlay(original: Match, parsed: Match) -> tuple[Match, list[dict]]:
    """Use only guarded completing-owner occurrences; retain unsupported history."""
    if (original.replay_id, original.map_name, original.match_type) != (
            parsed.replay_id, parsed.map_name, parsed.match_type):
        raise ValueError("Objective refresh replay identity differs.")
    if [r.number for r in original.rounds] != [r.number for r in parsed.rounds]:
        raise ValueError("Objective refresh logical rounds differ.")
    result = deepcopy(original)
    changes = []
    for old, current, target in zip(original.rounds, parsed.rounds, result.rounds):
        if old.winner != current.winner:
            raise ValueError("Objective refresh winner differs.")
        for occurrence in current.objective_occurrences:
            if not occurrence.actor or occurrence.actor_source != SOURCE or occurrence.actor_reason != SOURCE:
                continue
            kind = occurrence.kind
            expected = {"plant": "Attack", "disable": "Defense"}.get(kind)
            expected_source = {"plant": "defuser_state_v1", "disable": "defuser_state_and_defense_win_v1"}.get(kind)
            actor = next((p for p in current.players if p.key == occurrence.actor), None)
            stable = next((p for p in old.players if actor and p.key == actor.key), None)
            objectives = [o for o in current.objectives if o.kind == kind]
            if (not actor or not stable or not actor.profile_id or actor.key != actor.profile_id or
                    actor.side != expected or stable.side != actor.side or stable.team != actor.team or
                    type(occurrence.actor_uid) is not int or occurrence.actor_uid <= 0 or
                    occurrence.source != expected_source or occurrence.plant_state_offset <= 0 or
                    len(current.players) != 10 or len({p.key for p in current.players}) != 10 or
                    any(sum(p.team == team for p in current.players) != 5 for team in (0, 1)) or
                    len([o for o in current.objective_occurrences if o.kind == kind]) != 1 or
                    len(objectives) != 1 or objectives[0].player != actor.key or objectives[0].team != actor.team or
                    (kind == "disable" and actor.team != current.winner)):
                raise ValueError("Objective refresh lacks a unique supported stable actor.")
            prior = [o.player for o in old.objectives if o.kind == kind]
            if prior == [actor.key]:
                continue
            target.objectives = [o for o in target.objectives if o.kind != kind] + deepcopy(objectives)
            target.objective_occurrences = [o for o in target.objective_occurrences if o.kind != kind] + [deepcopy(occurrence)]
            changes.append({"round": old.number, "kind": kind, "before": prior,
                            "actor": actor.key, "actor_uid": occurrence.actor_uid})
    before, after = calculate_match(original), calculate_match(result)
    if before.keys() != after.keys():
        raise ValueError("Objective refresh changed participation.")
    for key in before:
        if any(before[key][c] != after[key][c] for c in COUNTS if c not in ("plants", "disables", "kost_rounds")):
            raise ValueError("Objective refresh changed unrelated statistics.")
    return result, changes


def parse_archive(db, archive_root: Path, map_id: str, parser=None) -> Match:
    parser = parser or parse_match
    status = verify(db, archive_root, map_id)
    if status["status"] != "Healthy":
        raise ValueError(f"Archive is {status['status']}: {status['message']}")
    row = map_record(db, map_id)
    original = Match.from_dict(json.loads(row["normalized_json"]))
    path = Path(status["path"])
    if not row["rehost_json"]:
        return parser(path)
    # Preserve the confirmed mapping, including incomplete historical rounds;
    # do not rerun rehost inference or synthesize missing players.
    source = json.loads(row["rehost_json"])
    rounds = []
    for segment in source["segments"]:
        parsed = parser(path / f"segment-{segment['segment']:02d}", allow_incomplete=True)
        if parsed.replay_id != segment["replay_id"] or parsed.map_name != original.map_name:
            raise ValueError("Objective refresh rehost identity differs.")
        detail = next(d for d in source["segment_details"] if d["segment"] == segment["segment"])
        remap = detail["team_mapping"]
        if sorted(remap) != [0, 1]:
            raise ValueError("Objective refresh rehost team mapping is invalid.")
        for entry in source["mapping"]:
            if entry["segment"] != segment["segment"] or entry["logical_number"] is None:
                continue
            round_ = deepcopy(next(r for r in parsed.rounds if r.number == entry["physical_number"]))
            round_.number = entry["logical_number"]
            round_.winner = remap[round_.winner]
            for player in round_.players:
                player.team = remap[player.team]
            for kill in round_.kills:
                if kill.killer_team in (0, 1):
                    kill.killer_team = remap[kill.killer_team]
                kill.victim_team = remap[kill.victim_team]
            for objective in round_.objectives:
                objective.team = remap[objective.team]
            old_round = next(r for r in original.rounds if r.number == round_.number)
            old_teams = {p.key: p.team for p in old_round.players}
            if any(old_teams.get(p.key) != p.team for p in round_.players):
                raise ValueError("Objective refresh rehost player/team identity differs.")
            rounds.append(round_)
    result = deepcopy(original)
    result.rounds = sorted(rounds, key=lambda r: r.number)
    return result


def apply(db, map_id: str, parsed: Match, *, preserve_rounds=False, audit=None) -> list[dict]:
    """Save snapshot and overlay in one transaction using existing map replacement."""
    row = db.execute("SELECT normalized_json,fingerprint FROM maps WHERE id=?", (map_id,)).fetchone()
    if not row:
        raise ValueError("NECC map not found.")
    original = Match.from_dict(json.loads(row["normalized_json"]))
    updated, changes = overlay(original, parsed)
    if not changes:
        return []
    if preserve_rounds:
        # Rating maintenance may correct supported actors while keeping every
        # round ID, player binding, kill row and frozen appearance unchanged.
        from r6stats.rating_inputs_v3 import validate_objectives
        validate_objectives(updated)
        with db:
            db.execute('BEGIN IMMEDIATE')
            current = db.execute('SELECT normalized_json,fingerprint FROM maps WHERE id=?', (map_id,)).fetchone()
            if current is None or tuple(current) != tuple(row):
                raise ValueError('Objective inputs changed during repair; retry the audit.')
            db.execute('''INSERT OR IGNORE INTO rating_input_snapshots(map_id,version,normalized_json,source_sha256)
                VALUES(?,?,?,?)''', (map_id, 'siege_style_v2', row['normalized_json'], hashlib.sha256(row['normalized_json'].encode()).hexdigest()))
            payload = json.dumps(updated.to_dict())
            db.execute('UPDATE maps SET normalized_json=? WHERE id=?', (payload, map_id))
            for number in {c['round'] for c in changes}:
                round_id = db.execute('SELECT id FROM rounds WHERE map_id=? AND number=?', (map_id, number)).fetchone()[0]
                db.execute('DELETE FROM objective_events WHERE round_id=?', (round_id,))
                for sequence, objective in enumerate(next(r for r in updated.rounds if r.number == number).objectives):
                    db.execute('INSERT INTO objective_events VALUES(?,?,?,?,?,?)',
                        (round_id, sequence, objective.kind, objective.player, objective.team, objective.remaining))
            from r6stats.rating_inputs_v3 import load_inputs
            inputs, reason = load_inputs(db, map_id)
            if inputs is None:
                raise ValueError('Objective correction did not pass full v3 validation: '+str(reason))
            if audit is not None:
                from r6stats.rating_evidence import record_audit
                record_audit(db, map_id, 'objective_actor_correction',
                    dict(normalized_json=row['normalized_json']), dict(normalized_json=payload, changes=changes, **audit),
                    'Healthy archive; completing timer owner; fully validated objectives and v3 inputs; only supported objective actors/counts corrected. Round IDs and unrelated historical rows retained.')
        return changes
    # reparse_map's transaction includes the pending snapshot insertion and
    # rolls both back if replacement fails. No independent snapshot commit.
    with db:
        db.execute("""INSERT OR IGNORE INTO rating_input_snapshots(map_id,version,normalized_json,source_sha256)
            VALUES(?,?,?,?)""", (map_id, "siege_style_v2", row["normalized_json"],
                                  hashlib.sha256(row["normalized_json"].encode()).hexdigest()))
        repo.reparse_map(db, map_id, updated, row["fingerprint"])
    return changes


def rating_stats(db, map_id: str, current: dict, window: float, version: str) -> dict:
    """Separate corrected display objectives/KOST from the frozen v2 baseline."""
    row = db.execute("SELECT normalized_json,source_sha256 FROM rating_input_snapshots WHERE map_id=? AND version=?",
                     (map_id, version)).fetchone()
    if not row:
        return current
    if hashlib.sha256(row["normalized_json"].encode()).hexdigest() != row["source_sha256"]:
        raise ValueError("Historical Rating input snapshot failed integrity check.")
    baseline = calculate_match(Match.from_dict(json.loads(row["normalized_json"])), window, version)
    if baseline.keys() != current.keys() or any(
        baseline[key][c] != current[key][c] for key in baseline
        for c in COUNTS if c not in ("plants", "disables", "kost_rounds")):
        raise ValueError("Historical Rating inputs changed outside the objective refresh; review required.")
    return baseline
