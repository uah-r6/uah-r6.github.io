"""Local archive-backed evidence maintenance. Never forces v3 eligibility."""
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path

from r6stats import credited_refresh, objective_refresh, replay_archive
from r6stats.kill_credit import validate_map_credit
from r6stats.parser.models import Match
from r6stats.parser.siege_dissect import parser_executable
from r6stats.rating_inputs_v3 import load_inputs, store_objective_evidence, validate_objectives

AUDIT_SCHEMA = '''CREATE TABLE IF NOT EXISTS rating_evidence_audit (
 id INTEGER PRIMARY KEY, map_id TEXT NOT NULL REFERENCES maps(id) ON DELETE CASCADE,
 at TEXT NOT NULL, operation TEXT NOT NULL, before_json TEXT NOT NULL,
 after_json TEXT NOT NULL, explanation TEXT NOT NULL)'''


def record_audit(db, map_id, operation, before, after, explanation):
    db.execute(AUDIT_SCHEMA)
    db.execute('INSERT INTO rating_evidence_audit(map_id,at,operation,before_json,after_json,explanation) VALUES(?,?,?,?,?,?)',
        (map_id, datetime.now(timezone.utc).isoformat(), operation, json.dumps(before, sort_keys=True), json.dumps(after, sort_keys=True), explanation))


def audit_map(db, archive_root, map_id):
    row = db.execute('SELECT * FROM maps WHERE id=?', (map_id,)).fetchone()
    if not row:
        raise ValueError('NECC map not found.')
    inputs, reason = load_inputs(db, map_id)
    prior = db.execute('SELECT * FROM map_kill_credit WHERE map_id=?', (map_id,)).fetchone() if db.execute("SELECT 1 FROM sqlite_master WHERE name='map_kill_credit'").fetchone() else None
    credit = validate_map_credit(json.loads(prior['evidence_json'])) if prior else None
    sidecar = db.execute('SELECT 1 FROM map_v3_objective_evidence WHERE map_id=?', (map_id,)).fetchone() if db.execute("SELECT 1 FROM sqlite_master WHERE name='map_v3_objective_evidence'").fetchone() else None
    return dict(map_id=map_id, map=row['map_name'], series_id=row['series_id'],
        rounds=len(json.loads(row['normalized_json'])['rounds']), eligible=inputs is not None, exclusion=reason,
        archive=replay_archive.verify(db, archive_root, map_id),
        credited_status='complete' if credit and credit['complete'] else 'incomplete' if credit else 'absent',
        credited_issues=credit['issues'] if credit else [], objective_status='sidecar present' if sidecar else 'normalized only')


def objective_candidate(original, parsed):
    """Attach occurrences only after exact replay/round/roster/winner validation."""
    if (original.replay_id, original.map_name, original.match_type, original.game_mode) != (parsed.replay_id, parsed.map_name, parsed.match_type, parsed.game_mode):
        raise ValueError('Objective evidence replay identity differs.')
    if [r.number for r in original.rounds] != [r.number for r in parsed.rounds]:
        raise ValueError('Objective evidence logical rounds differ.')
    candidate = deepcopy(original)
    for old, new, target in zip(original.rounds, parsed.rounds, candidate.rounds):
        if old.winner != new.winner or sorted((p.key, p.username, p.team, p.side) for p in old.players) != sorted((p.key, p.username, p.team, p.side) for p in new.players):
            raise ValueError('Objective evidence winner/player/team identity differs.')
        target.objective_occurrences = deepcopy(new.objective_occurrences)
    validate_objectives(candidate)
    return candidate


def repair(db, archive_root: Path, map_id):
    before = audit_map(db, archive_root, map_id)
    if before['archive']['status'] != 'Healthy':
        raise ValueError('Rating evidence repair requires a Healthy archive.')
    if before['eligible']:
        return dict(before=before, after=before, changes=[], blockers=[], message='Already eligible; existing evidence and Rating preserved.')
    changes, blockers = [], []
    manifest_path = Path(before['archive']['path']) / 'manifest.json'
    source_hash = replay_archive.sha256(manifest_path)
    executable = parser_executable()
    parser_hash = replay_archive.sha256(Path(executable)) if executable else None
    if before['credited_status'] != 'complete':
        observation = credited_refresh.read_archive(db, archive_root, map_id)
        if observation is None:
            blockers.append('Trusted credited reader unavailable.')
        else:
            records, binary = observation
            credit = validate_map_credit(records)
            if not credit['complete']:
                blockers.append('Archive reader still lacks complete credited evidence: '+json.dumps(credit['issues'], sort_keys=True))
            else:
                prior = db.execute('SELECT * FROM map_kill_credit WHERE map_id=?', (map_id,)).fetchone()
                if prior:
                    credited_refresh.reconcile_incomplete(db, map_id, records, binary,
                        archive_root=archive_root, fingerprint=prior['fingerprint'], prior_sha256=prior['evidence_sha256'])
                else:
                    match = Match.from_dict(json.loads(replay_archive.map_record(db, map_id)['normalized_json']))
                    credited_refresh.round_counts(match, credit)
                    credited_refresh.preserve_display(match, credit)
                    credited_refresh.store(db, map_id, records, binary)
                    with db: record_audit(db, map_id, 'credited_backfill', None, dict(parser_sha256=binary), 'Complete healthy-archive collection through the existing trusted reader.')
                changes.append('credited evidence')
    # Never reparse or replace stored normalized rounds in this evidence-only operation.
    row = replay_archive.map_record(db, map_id)
    original = Match.from_dict(json.loads(row['normalized_json']))
    try:
        validate_objectives(original)
    except ValueError:
        parsed = objective_refresh.parse_archive(db, archive_root, map_id)
        try:
            candidate = objective_candidate(original, parsed)
        except ValueError as error:
            blockers.append(str(error))
            for old, new in zip(original.rounds, parsed.rounds):
                expected = {(o.kind, o.player) for o in old.objectives}
                supported = {(o.kind, o.actor) for o in new.objective_occurrences if o.actor_source == 'completing_timer_owner_v1'}
                if expected != supported:
                    blockers.append(f'Logical R{old.number}: stored credits {sorted(expected)}; trusted occurrences {sorted(supported)}; reasons {[o.actor_reason for o in new.objective_occurrences]}')
        else:
            store_objective_evidence(db, map_id, candidate,
                audit=dict(parser_sha256=parser_hash, archive_manifest_sha256=source_hash))
            changes.append('objective evidence')
    after = audit_map(db, archive_root, map_id)  # Full prepare path, including native offsets/parity/opening/clutch.
    with db: record_audit(db, map_id, 'archive_repair_check', before, after,
        json.dumps(dict(changes=changes, blockers=blockers, archive_manifest_sha256=source_hash, parser_sha256=parser_hash), sort_keys=True))
    return dict(before=before, after=after, changes=changes, blockers=blockers,
        message='Rating evidence repaired; full v3 validation passed.' if after['eligible'] else 'Map remains unrated: '+str(after['exclusion']))
