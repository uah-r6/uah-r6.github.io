"""Local archive-backed evidence maintenance. Never forces v3 eligibility."""
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sqlite3

from r6stats import credited_refresh, objective_refresh, replay_archive
from r6stats.kill_credit import validate_map_credit
from r6stats.parser.models import Match
from r6stats.parser.siege_dissect import parser_executable
from r6stats.rating_inputs_v3 import load_inputs, prepare, store_objective_evidence, validate_objectives

AUDIT_SCHEMA = '''CREATE TABLE IF NOT EXISTS rating_evidence_audit (
 id INTEGER PRIMARY KEY, map_id TEXT NOT NULL REFERENCES maps(id) ON DELETE CASCADE,
 at TEXT NOT NULL, operation TEXT NOT NULL, before_json TEXT NOT NULL,
 after_json TEXT NOT NULL, explanation TEXT NOT NULL)'''


def record_audit(db, map_id, operation, before, after, explanation):
    db.execute(AUDIT_SCHEMA)
    db.execute('INSERT INTO rating_evidence_audit(map_id,at,operation,before_json,after_json,explanation) VALUES(?,?,?,?,?,?)',
        (map_id, datetime.now(timezone.utc).isoformat(), operation, json.dumps(before, sort_keys=True), json.dumps(after, sort_keys=True), explanation))


def failure_audit(db, archive_root, map_id, operation, state, blockers):
    """Keep secondary failures reviewable even when evidence cannot be read."""
    provenance = dict(changes=[], blockers=list(blockers), parser_sha256=None, archive_manifest_sha256=None)
    executable = parser_executable()
    if executable and Path(executable).is_file():
        provenance['parser_sha256'] = replay_archive.sha256(Path(executable))
    archive = replay_archive.verify(db, archive_root, map_id)
    manifest = Path(archive['path']) / 'manifest.json' if archive.get('path') else None
    if manifest and manifest.is_file():
        provenance['archive_manifest_sha256'] = replay_archive.sha256(manifest)
    with db:
        record_audit(db, map_id, operation, state, state, json.dumps(provenance, sort_keys=True))


def audit_map(db, archive_root, map_id):
    row = db.execute('SELECT * FROM maps WHERE id=?', (map_id,)).fetchone()
    if not row:
        raise ValueError('NECC map not found.')
    inputs, reason = load_inputs(db, map_id)
    prior = db.execute('SELECT * FROM map_kill_credit WHERE map_id=?', (map_id,)).fetchone() if db.execute("SELECT 1 FROM sqlite_master WHERE name='map_kill_credit'").fetchone() else None
    credit = validate_map_credit(json.loads(prior['evidence_json'])) if prior else None
    sidecar = db.execute('SELECT 1 FROM map_v3_objective_evidence WHERE map_id=?', (map_id,)).fetchone() if db.execute("SELECT 1 FROM sqlite_master WHERE name='map_v3_objective_evidence'").fetchone() else None
    scope = db.execute('SELECT s.opponent,t.name AS team FROM series s JOIN teams t ON t.id=s.team_id WHERE s.id=?', (row['series_id'],)).fetchone()
    return dict(map_id=map_id, map=row['map_name'], series_id=row['series_id'], team=scope['team'], opponent=scope['opponent'],
        rounds=len(json.loads(row['normalized_json'])['rounds']), eligible=inputs is not None, exclusion=reason,
        archive=replay_archive.verify(db, archive_root, map_id),
        credited_status='complete' if credit and credit['complete'] else 'incomplete' if credit else 'absent',
        credited_issues=credit['issues'] if credit else [], objective_status='sidecar present' if sidecar else 'normalized only')


def objective_source(original, parsed):
    """Exact identity guard shared by backfill and supported actor correction."""
    if (original.replay_id, original.map_name, original.match_type, original.game_mode) != (parsed.replay_id, parsed.map_name, parsed.match_type, parsed.game_mode):
        raise ValueError('Objective evidence replay identity differs.')
    if [r.number for r in original.rounds] != [r.number for r in parsed.rounds]:
        raise ValueError('Objective evidence logical rounds differ.')
    for old, new in zip(original.rounds, parsed.rounds):
        if old.winner != new.winner or sorted((p.key, p.username, p.team, p.side) for p in old.players) != sorted((p.key, p.username, p.team, p.side) for p in new.players):
            raise ValueError('Objective evidence winner/player/team identity differs.')


def objective_candidate(original, parsed):
    """Attach occurrences only after exact replay/round/roster/winner validation."""
    objective_source(original, parsed)
    candidate = deepcopy(original)
    for new, target in zip(parsed.rounds, candidate.rounds):
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
                has_credit = db.execute("SELECT 1 FROM sqlite_master WHERE name='map_kill_credit'").fetchone()
                prior = db.execute('SELECT * FROM map_kill_credit WHERE map_id=?', (map_id,)).fetchone() if has_credit else None
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
    # Exact metadata-only backfill first; independently proven actor corrections
    # use the existing objective overlay and retain every unrelated database row.
    row = replay_archive.map_record(db, map_id)
    original = Match.from_dict(json.loads(row['normalized_json']))
    try:
        validate_objectives(original)
    except ValueError:
        parsed = None
        try:
            parsed = objective_refresh.parse_archive(db, archive_root, map_id)
            candidate = objective_candidate(original, parsed)
        except ValueError as error:
            blockers.append(str(error))
            if parsed is not None:
                try:
                    objective_source(original, parsed)
                    updated, corrections = objective_refresh.overlay(original, parsed)
                    if not corrections:
                        raise ValueError('No independently supported objective actor correction is available.')
                    validate_objectives(updated)
                    has_sidecar = db.execute("SELECT 1 FROM sqlite_master WHERE name='map_v3_objective_evidence'").fetchone()
                    if has_sidecar and db.execute('SELECT 1 FROM map_v3_objective_evidence WHERE map_id=?', (map_id,)).fetchone():
                        raise ValueError('Existing objective sidecar requires explicit reconciliation before an actor correction.')
                    if credited_refresh.load(db, map_id) is None:
                        raise ValueError('Objective correction requires complete trusted credited evidence.')
                    records = json.loads(db.execute('SELECT evidence_json FROM map_kill_credit WHERE map_id=?', (map_id,)).fetchone()[0])
                    prepare(updated, records)
                    objective_refresh.apply(db, map_id, parsed, preserve_rounds=True,
                        audit=dict(parser_sha256=parser_hash, archive_manifest_sha256=source_hash))
                except ValueError as correction_error:
                    blockers.append(str(correction_error))
                    for old, new in zip(original.rounds, parsed.rounds):
                        expected = {(o.kind, o.player) for o in old.objectives}
                        supported = {(o.kind, o.actor) for o in new.objective_occurrences if o.actor_source == 'completing_timer_owner_v1'}
                        unresolved = [o for o in new.objective_occurrences if o.actor_source != 'completing_timer_owner_v1']
                        if expected != supported or unresolved:
                            blockers.append(f'Logical R{old.number}: stored credits {sorted(expected)}; trusted occurrences {sorted(supported)}; reasons {[o.actor_reason for o in new.objective_occurrences]}')
                else:
                    changes.append('supported objective actor correction')
                    blockers.clear()
        except (OSError, subprocess.SubprocessError) as error:
            blockers.append('Archive objective reader failed: '+str(error))
        else:
            store_objective_evidence(db, map_id, candidate,
                audit=dict(parser_sha256=parser_hash, archive_manifest_sha256=source_hash))
            changes.append('objective evidence')
    after = audit_map(db, archive_root, map_id)  # Full prepare path, including native offsets/parity/opening/clutch.
    with db: record_audit(db, map_id, 'archive_repair_check', before, after,
        json.dumps(dict(changes=changes, blockers=blockers, archive_manifest_sha256=source_hash, parser_sha256=parser_hash), sort_keys=True))
    return dict(before=before, after=after, changes=changes, blockers=blockers,
        message='Rating evidence repaired; full v3 validation passed.' if after['eligible'] else 'Map remains unrated: '+str(after['exclusion']))


def repair_all(db, archive_root):
    """Isolate map failures; eligible maps never reparse or replace evidence."""
    results = []
    for row in db.execute('SELECT id FROM maps ORDER BY id').fetchall():
        try:
            result = repair(db, archive_root, row['id'])
        except (ValueError, OSError, subprocess.SubprocessError, sqlite3.Error) as error:
            try:
                state = audit_map(db, archive_root, row['id'])
            except (ValueError, OSError, sqlite3.Error) as audit_error:
                state = dict(map_id=row['id'], map=row['id'], eligible=False, exclusion=str(audit_error))
            result = dict(before=state, after=state, changes=[], blockers=[str(error)], message='Repair blocked: '+str(error))
            try:
                failure_audit(db, archive_root, row['id'], 'archive_repair_error', state, result['blockers'])
            except Exception as audit_error:
                result['blockers'].append('Repair audit could not be saved: '+str(audit_error))
        results.append(result)
    return dict(results=results, audited=len(results),
        already_eligible=sum(r['before']['eligible'] for r in results),
        repaired=sum(not r['before']['eligible'] and r['after']['eligible'] for r in results),
        blocked=sum(not r['after']['eligible'] for r in results))


def after_import(db, archive_root, map_id):
    """Secondary evidence collection cannot undo a successful map/archive import."""
    try:
        credit = credited_refresh.collect_after_import(db, archive_root, map_id)
    except Exception as error:
        credit = dict(source=credited_refresh.LEGACY, complete=False, reason=str(error))
    try:
        result = repair(db, archive_root, map_id)
        if credit.get('reason') and not result['after']['eligible']:
            result['blockers'].append('Initial credited evidence collection: '+credit['reason'])
        return dict(eligible=result['after']['eligible'], status='ELIGIBLE' if result['after']['eligible'] else 'UNAVAILABLE',
            reason=result['after']['exclusion'], changes=result['changes'], blockers=result['blockers'], kill_credit=credit)
    except Exception as error:
        try:
            inputs, reason = load_inputs(db, map_id)
        except Exception as input_error:
            inputs, reason = None, str(input_error)
        blockers = [str(error)]
        if credit.get('reason'):
            blockers.append('Initial credited evidence collection: '+credit['reason'])
        state = dict(map_id=map_id, eligible=inputs is not None, exclusion=reason)
        try:
            failure_audit(db, archive_root, map_id, 'post_import_evidence_error', state, blockers)
        except Exception as audit_error:
            blockers.append('Repair audit could not be saved: '+str(audit_error))
        return dict(eligible=inputs is not None, status='ELIGIBLE' if inputs is not None else 'UNAVAILABLE',
            reason=reason, changes=[], blockers=blockers, kill_credit=credit)
