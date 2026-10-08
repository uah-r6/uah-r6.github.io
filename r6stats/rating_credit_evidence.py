"""Sealed Rating-only credited inputs; historical display sidecars stay intact.

Used only for independently proven empty replay slots in a historical map.
No inferred counts, legacy finisher replacement or complete-evidence overwrite.
"""
import hashlib
import json
from pathlib import Path

from r6stats import credited_refresh
from r6stats.kill_credit import validate_map_credit
from r6stats.parser.models import Match
from r6stats.participant_inventory import inventory_valid
from r6stats.replay_archive import verify, sha256

SCHEMA = '''CREATE TABLE IF NOT EXISTS map_v3_kill_evidence (
 map_id TEXT PRIMARY KEY REFERENCES maps(id) ON DELETE CASCADE,
 fingerprint TEXT NOT NULL, normalized_sha256 TEXT NOT NULL,
 evidence_json TEXT NOT NULL, evidence_sha256 TEXT NOT NULL,
 parser_sha256 TEXT NOT NULL, archive_manifest_sha256 TEXT NOT NULL)'''


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def load(db, map_id):
    if not db.execute("SELECT 1 FROM sqlite_master WHERE name='map_v3_kill_evidence'").fetchone():
        return None, None
    saved = db.execute('SELECT * FROM map_v3_kill_evidence WHERE map_id=?', (map_id,)).fetchone()
    if not saved:
        return None, None
    row = db.execute('SELECT fingerprint,normalized_json FROM maps WHERE id=?', (map_id,)).fetchone()
    if digest(saved['evidence_json']) != saved['evidence_sha256']:
        raise ValueError('Rating-only credited evidence integrity check failed.')
    if saved['fingerprint'] != row['fingerprint'] or saved['normalized_sha256'] != digest(row['normalized_json']):
        return None, 'Stale Rating-only credited evidence; explicit review required.'
    records = json.loads(saved['evidence_json'])
    credited_refresh.round_counts(Match.from_dict(json.loads(row['normalized_json'])), validate_map_credit(records))
    return records, None


def store(db, archive_root, map_id, records, binary):
    """Caller owns the objective correction transaction; no independent commit."""
    from r6stats.rating_inputs_v3 import prepare
    from r6stats.rating_evidence import record_audit
    if credited_refresh.read_archive(db, archive_root, map_id) != (records, binary):
        raise ValueError('Rating evidence must match the current binary and Healthy archive.')
    row = db.execute('SELECT * FROM maps WHERE id=?', (map_id,)).fetchone()
    old = db.execute('SELECT * FROM map_kill_credit WHERE map_id=?', (map_id,)).fetchone()
    if (not old or old['fingerprint'] != row['fingerprint'] or digest(old['evidence_json']) != old['evidence_sha256']
            or validate_map_credit(json.loads(old['evidence_json']))['complete']):
        raise ValueError('Rating-only recovery requires intact incomplete historical credited evidence.')
    if not any(inventory_valid(r['credit']['players'],r['credit'].get('participantEvidence')) for r in records):
        raise ValueError('Rating-only recovery requires explicit complete empty-slot inventory.')
    prior_records = json.loads(old['evidence_json'])
    source = lambda r: (r['logical_round'],r['physical_round'],r['segment'])
    if [source(r) for r in prior_records] != [source(r) for r in records]:
        raise ValueError('Rating-only evidence physical/logical sources differ.')
    for a,b in zip(prior_records,records):
        players = {p['profileID']:p for p in b['credit']['players']}
        if len(players) != len(a['credit']['players']):
            raise ValueError('Rating-only evidence must preserve actual historical participation.')
        for p in a['credit']['players']:
            q = players.get(p['profileID'])
            if not q or any(p[k]!=q[k] for k in ('uid','profileID','username','team')):
                raise ValueError('Rating-only evidence identity differs.')
            if a['credit']['complete'] and any(p[k]!=q[k] for k in ('initial','terminal','kills')):
                raise ValueError('Rating-only evidence conflicts with complete round counts.')
    match = Match.from_dict(json.loads(row['normalized_json']))
    prepare(match, records)  # Complete objective, counter, native parity/order gates.
    status = verify(db, archive_root, map_id)
    if status['status'] != 'Healthy':
        raise ValueError('Rating-only recovery requires a Healthy archive.')
    payload = json.dumps(records,sort_keys=True,separators=(',',':'),allow_nan=False)
    db.execute(SCHEMA)
    prior = db.execute('SELECT * FROM map_v3_kill_evidence WHERE map_id=?',(map_id,)).fetchone()
    values = (map_id,row['fingerprint'],digest(row['normalized_json']),payload,digest(payload),binary,
              sha256(Path(status['path'])/'manifest.json'))
    if prior and tuple(prior) != values:
        raise ValueError('Existing Rating-only evidence differs; explicit review required.')
    if not prior:
        db.execute('INSERT INTO map_v3_kill_evidence VALUES(?,?,?,?,?,?,?)',values)
        record_audit(db,map_id,'rating_only_credited_recovery',dict(old),dict(zip(
            ('map_id','fingerprint','normalized_sha256','evidence_json','evidence_sha256','parser_sha256','archive_manifest_sha256'),values)),
            'Complete ten-slot inventory proves nine actual participants and one empty slot. Direct stable UID counters for every actual participant; no conservation or invented player. Historical display sidecar and finisher statistics preserved; v3-only inputs fully prepared.')
