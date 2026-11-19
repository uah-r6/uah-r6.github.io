"""Sealed Rating-only credited inputs; historical display sidecars stay intact.

Used for proven empty replay slots or exact missing-Death boundary recovery.
No inferred counts, legacy finisher replacement or complete-evidence overwrite.
"""
import hashlib
import json
from copy import deepcopy
from pathlib import Path

from r6stats import credited_refresh
from r6stats.kill_credit import SOURCE, validate_map_credit
from r6stats.parser.models import Match
from r6stats.participant_inventory import inventory_valid, RECONNECT_SOURCE
from r6stats.replay_archive import verify, sha256

SCHEMA = '''CREATE TABLE IF NOT EXISTS map_v3_kill_evidence (
 map_id TEXT PRIMARY KEY REFERENCES maps(id) ON DELETE CASCADE,
 fingerprint TEXT NOT NULL, normalized_sha256 TEXT NOT NULL,
 evidence_json TEXT NOT NULL, evidence_sha256 TEXT NOT NULL,
 parser_sha256 TEXT NOT NULL, archive_manifest_sha256 TEXT NOT NULL)'''

UID_ZERO_SOURCE = 'in_round_uid_replacement_zero_counters_next_round_anchor_v1'


def apply_uid_zero_recovery(prior_records, raw_records):
    """Bridge two native zero samples for one R01 UID replacement to R02 zero.

    The old sidecar must be byte-equivalent to the new reader except for this
    additive native proof. No missing value is derived from the kill feed.
    """
    if len(prior_records) < 2 or len(prior_records) != len(raw_records):
        return None
    raw_without_proof = deepcopy(raw_records)
    gaps = []
    for n, record in enumerate(raw_without_proof):
        for i, player in enumerate(record['credit']['players']):
            if player.pop('counterGap', None) is not None:
                gaps.append((n, i))
    if len(gaps) != 1 or gaps[0][0] != 0:
        return None
    if raw_without_proof != prior_records:
        return None
    first, second = raw_records[:2]
    if (first['logical_round'] != 1 or first['physical_round'] != 1 or
            second['logical_round'] != 2 or second['physical_round'] != 2 or
            first['segment'] != second['segment'] or first['credit']['complete'] is not False or
            second['credit']['complete'] is not True):
        return None
    i = gaps[0][1]
    player = first['credit']['players'][i]
    proof = player['counterGap']
    if (set(proof) != {'source','owner','oldUID','newUID','oldUIDOffset','newUIDOffset',
                       'oldScoreComponent','newScoreComponent','oldScoreOffset','newScoreOffset',
                       'oldSampleOffset','newSampleOffset'} or
            proof['source'] != 'in_round_uid_replacement_zero_counters_v1' or
            any(type(proof[key]) is not int or proof[key] <= 0 for key in set(proof)-{'source'}) or
            proof['oldUID'] != player['uid'] or proof['oldUID'] == proof['newUID'] or
            proof['oldScoreComponent'] == proof['newScoreComponent'] or
            not (proof['oldScoreOffset'] < proof['oldSampleOffset'] < proof['oldUIDOffset'] < first['credit']['actionStartOffset'] <
                 proof['newScoreOffset'] < proof['newSampleOffset'] < proof['newUIDOffset']) or
            player['reason'] != 'missing_direct_uid_counter' or player['samples'] or
            any(player[k] is not None for k in ('initial','terminal','kills'))):
        return None
    current = {p['profileID']: p for p in first['credit']['players']}
    following = {p['profileID']: p for p in second['credit']['players']}
    if (len(current) != 10 or len(following) != 10 or current.keys() != following.keys() or
            any(q['username'] != p['username'] or q['team'] != p['team'] or
                (q['uid'] != p['uid'] if p is not player else q['uid'] != proof['newUID']) or
                (p is not player and (p['initial'] != 0 or p['kills'] is None or p['terminal'] != q['initial']))
                for key, p in current.items() for q in [following[key]]) or
            following[player['profileID']]['initial'] != 0 or
            not following[player['profileID']]['samples'] or
            following[player['profileID']]['samples'][0]['value'] != 0 or
            following[player['profileID']]['samples'][0]['offset'] >= second['credit']['actionStartOffset']):
        return None
    recovered = deepcopy(raw_records)
    p = recovered[0]['credit']['players'][i]
    p.update(initial=0, terminal=0, kills=0, reason=UID_ZERO_SOURCE,
             counterRecovery={'source': UID_ZERO_SOURCE, 'next_round': 2})
    recovered[0]['credit'].update(complete=True, reason=SOURCE)
    if not validate_map_credit(recovered)['complete']:
        return None
    return recovered


def uid_zero_recovery(prior_records, recovered_records):
    if not recovered_records:
        return False
    raw = deepcopy(recovered_records)
    first = raw[0]['credit']
    candidates = [p for p in first['players'] if p.pop('counterRecovery', None) is not None]
    if len(candidates) != 1:
        return False
    candidates[0].update(initial=None, terminal=None, kills=None, reason='missing_direct_uid_counter')
    first.update(complete=False, reason='unresolved_player_counters')
    return apply_uid_zero_recovery(prior_records, raw) == recovered_records


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def death_offset_recovery(prior_records, records):
    """Only complete callback-proven offsets may unlock this evidence-only path.

    Every original sample, identity, positive offset and feedback field stays
    exact. The current Healthy-archive binary is independently required by store.
    This never supplies a missing counter or guesses an elimination boundary.
    """
    recovered = False
    if len(prior_records) != len(records):
        return False
    for old, new in zip(prior_records, records):
        a, b = old['credit'], new['credit']
        if ({k:v for k,v in old.items() if k != 'credit'} != {k:v for k,v in new.items() if k != 'credit'} or
                a.get('source') != SOURCE or b.get('source') != SOURCE or b.get('complete') is not True or
                a.get('actionStartOffset') != b.get('actionStartOffset') or
                a.get('participantEvidence') != b.get('participantEvidence') or
                len(a['players']) != len(b['players']) or
                len(a.get('finishes', [])) != len(b.get('finishes', []))):
            return False
        for p, q in zip(a['players'], b['players']):
            if (not isinstance(p.get('samples'), list) or not p['samples'] or
                    any(p.get(k) != q.get(k) for k in ('uid', 'profileID', 'username', 'team', 'samples'))):
                return False
            if a['complete']:
                if p != q:
                    return False
            elif (p.get('reason') != 'baseline_not_before_first_elimination' or
                  any(p.get(k) is not None for k in ('initial', 'terminal', 'kills'))):
                return False
        round_recovered = False
        for f, g in zip(a.get('finishes', []), b.get('finishes', [])):
            if f == g:
                continue
            proof = g.get('offsetEvidence', {})
            if (set(f) != {'offset', 'feedback'} or set(g) != {'offset', 'feedback', 'offsetEvidence'} or
                    f['offset'] != 0 or f['feedback'].get('type', {}).get('name') != 'Death' or
                    f['feedback'] != g['feedback'] or proof.get('markerValid') is not True or
                    proof.get('feedback') != f['feedback'] or proof.get('legacyOffset') != 0 or
                    type(proof.get('feedbackIndex')) is not int or proof['feedbackIndex'] < 0 or
                    type(g['offset']) is not int or g['offset'] <= 0 or
                    proof.get('startOffset') != g['offset'] or
                    type(proof.get('endOffset')) is not int or proof['endOffset'] <= g['offset']):
                return False
            round_recovered = recovered = True
        if not a['complete'] and not round_recovered:
            return False
    return recovered


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
    prior_records = json.loads(old['evidence_json'])
    empty_slot = any(inventory_valid(r['credit']['players'],r['credit'].get('participantEvidence')) for r in records)
    native_death = death_offset_recovery(prior_records, records)
    uid_zero = uid_zero_recovery(prior_records, records)
    if not empty_slot and not native_death and not uid_zero:
        raise ValueError('Rating-only recovery requires complete native participation, Death boundary, or direct zero-counter bridge proof.')
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
        explanation = ('Two native zero kill-counter samples across one within-round UID replacement, plus exact R02 zero baseline and nine unchanged profile/counter bridges, prove the missing R01 credit. '
            'Original display sidecar remains incomplete and unchanged. '
            if uid_zero else
            'Exact single-emission native feedback callback proves each missing Death boundary. '
            'Original counter samples, identities and feedback preserved; no timing or credited-owner inference. '
            if native_death else
            'Complete ten-slot inventory proves nine active participants and one named inactive reconnect. '
            'Typed absent/zero-vitals body, late UID, restored counter and exact surrounding-round identity/counter continuity verified. '
            if any(r['credit'].get('participantEvidence',{}).get('source') == RECONNECT_SOURCE for r in records) else
            'Complete ten-slot inventory proves nine actual participants and one empty slot. '
            'Direct stable UID counters for every actual participant; no conservation or invented player. ')
        record_audit(db,map_id,'rating_only_credited_recovery',dict(old),dict(zip(
            ('map_id','fingerprint','normalized_sha256','evidence_json','evidence_sha256','parser_sha256','archive_manifest_sha256'),values)),
            explanation+'Historical display sidecar and finisher statistics preserved; v3-only inputs fully prepared.')
