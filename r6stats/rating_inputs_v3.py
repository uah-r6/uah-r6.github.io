"""Guarded v3 inputs from stored normalized rounds and validated Go evidence.

No replay parsing, clock sorting changes, or mutation of historical statistics.
Missing/unsupported evidence makes the entire map ineligible. Historical core
occurrence evidence is stored privately and bound to current input hashes.
"""
from collections import Counter, defaultdict
from dataclasses import replace
import hashlib
import json

from r6stats.credited_refresh import load as load_credit, round_counts
from r6stats.kill_credit import validate_map_credit
from r6stats.parser.models import Match
from r6stats.stats.calculate import aggregate, calculate_match

SCHEMA = '''CREATE TABLE IF NOT EXISTS map_v3_objective_evidence (
 map_id TEXT PRIMARY KEY REFERENCES maps(id) ON DELETE CASCADE,
 fingerprint TEXT NOT NULL, normalized_sha256 TEXT NOT NULL,
 evidence_json TEXT NOT NULL, evidence_sha256 TEXT NOT NULL)'''
CORE = 'completing_timer_owner_v1'


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def native_state(round_, report):
    players = {p.key: p for p in round_.players}
    names = {p.username: p for p in round_.players}
    if (len(players) != 10 or len(names) != 10 or round_.winner not in (0, 1)
            or Counter(p.team for p in players.values()) != Counter({0: 5, 1: 5})
            or len({k.sequence for k in round_.kills}) != len(round_.kills)):
        raise ValueError('Distinct full roster and native event ordinals required.')
    finishes = report.get('finishes')
    if finishes is None:
        raise ValueError('Native elimination evidence missing.')
    offsets = [f['offset'] for f in finishes]
    if any(type(x) is not int or x <= 0 for x in offsets) or offsets != sorted(set(offsets)):
        raise ValueError('Native physical offsets missing, duplicated or reordered.')
    expected = []
    for f in finishes:
        feedback = f['feedback']; kind = feedback['type']['name']
        if kind not in ('Kill', 'Death'):
            raise ValueError('Unknown native elimination type.')
        victim = names.get(feedback['target'] if kind == 'Kill' else feedback['username'])
        killer = names.get(feedback['username']) if kind == 'Kill' else None
        if victim is None or (kind == 'Kill' and killer is None):
            raise ValueError('Unbound native elimination identity.')
        expected.append((killer.key if killer else '', victim.key,
                         float(feedback['timeInSeconds']), bool(feedback.get('headshot'))))
    kills = sorted(round_.kills, key=lambda k: k.sequence)
    actual = [(k.killer, k.victim, k.remaining, k.headshot) for k in kills]
    if expected != actual:
        raise ValueError('Exact normalized/native elimination parity differs.')
    alive = set(players); candidates = {}; opening = None
    for k in kills:
        if k.victim not in alive or (k.killer and k.killer not in players):
            raise ValueError('Duplicate death or unbound player.')
        if (k.victim_team != players[k.victim].team or
                (k.killer and k.killer_team != players[k.killer].team)):
            raise ValueError('Elimination team identity differs.')
        if opening is None and k.killer and not k.teamkill and k.killer != k.victim:
            opening = (k.killer, k.victim)
        alive.remove(k.victim)
        team = players[k.victim].team
        survivors = [key for key in alive if players[key].team == team]
        enemies = sum(players[key].team != team for key in alive)
        if len(survivors) == 1 and 1 <= enemies <= 5 and team not in candidates:
            candidates[team] = (survivors[0], enemies)
    return opening, candidates.get(round_.winner)


def validate_objectives(match):
    for r in match.rounds:
        verified = []
        players = {p.key: p for p in r.players}
        for o in r.objective_occurrences:
            actor = players.get(o.actor)
            side = {'plant': 'Attack', 'disable': 'Defense'}.get(o.kind)
            source = {'plant': 'defuser_state_v1', 'disable': 'defuser_state_and_defense_win_v1'}.get(o.kind)
            if (not actor or not side or actor.side != side or o.source != source
                    or o.actor_source != CORE or o.actor_reason != CORE
                    or type(o.actor_uid) is not int or o.actor_uid <= 0
                    or o.plant_state_offset <= 0
                    or (o.kind == 'disable' and actor.team != r.winner)):
                raise ValueError('Whole map has unsupported core objective evidence.')
            verified.append((o.kind, o.actor, actor.team))
        stored = [(o.kind, o.player, o.team) for o in r.objectives]
        if (Counter(stored) != Counter(verified) or
                any(n > 1 for n in Counter(o.kind for o in r.objective_occurrences).values())):
            raise ValueError('Objective credits lack complete unique core occurrence evidence.')


def prepare(match, records):
    """Return exact research-compatible per-round features and map aggregates."""
    validate_objectives(match)
    credit = validate_map_credit(records)
    counts = round_counts(match, credit)
    features = defaultdict(list)
    for r, observed in zip(match.rounds, records):
        # Bind native feedback by the already-verified exact profile/name roster.
        if {(p.profile_id, p.username) for p in r.players} != {
                (p['profileID'], p['username']) for p in observed['credit']['players']}:
            raise ValueError('Exact native counter profile/name identity differs.')
        opening, clutch = native_state(r, observed['credit'])
        old = calculate_match(replace(match, rounds=[r]), 8, 'siege_style_v2')
        for key, s in old.items():
            s['kills'] = counts[r.number][key]
            s['multikill_extra'] = max(s['kills'] - 1, 0)
            s['kost_rounds'] = int(bool(s['kills'] or s['plants'] or s['disables']
                                       or s['survived'] or s['deaths_traded']))
            s['opening_kills'] = int(opening is not None and opening[0] == key)
            s['opening_deaths'] = int(opening is not None and opening[1] == key)
            for x in range(1, 6):
                s[f'clutch_1v{x}'] = int(clutch == (key, x))
            s['clutches'] = sum(s[f'clutch_1v{x}'] for x in range(1, 6))
            features[key].append(s)
    return {key: aggregate(rows, 'siege_style_v3') for key, rows in features.items()}, dict(features)


def store_objective_evidence(db, map_id, evidence, *, audit=None):
    row = db.execute('SELECT * FROM maps WHERE id=?', (map_id,)).fetchone()
    if not row:
        raise ValueError('NECC map not found.')
    original = Match.from_dict(json.loads(row['normalized_json']))
    a, b = original.to_dict(), evidence.to_dict()
    for value in (a, b):
        for r in value['rounds']:
            r.pop('objective_occurrences')
    if a != b:
        raise ValueError('V3 evidence must not change any normalized statistic or identity.')
    validate_objectives(evidence)
    payload = json.dumps(evidence.to_dict(), sort_keys=True, separators=(',', ':'), allow_nan=False)
    with db:
        db.execute(SCHEMA)
        prior = db.execute('SELECT * FROM map_v3_objective_evidence WHERE map_id=?', (map_id,)).fetchone()
        if prior and (prior['fingerprint'] != row['fingerprint'] or prior['normalized_sha256'] != digest(row['normalized_json'])
                      or prior['evidence_sha256'] != digest(payload) or digest(prior['evidence_json']) != prior['evidence_sha256']):
            raise ValueError('Existing objective evidence differs; explicit review required.')
        db.execute('INSERT OR IGNORE INTO map_v3_objective_evidence VALUES(?,?,?,?,?)',
                   (map_id, row['fingerprint'], digest(row['normalized_json']), payload, digest(payload)))
        if audit is not None and not prior:
            from r6stats.rating_evidence import record_audit
            record_audit(db, map_id, 'objective_backfill', None,
                dict(fingerprint=row['fingerprint'], normalized_sha256=digest(row['normalized_json']),
                     evidence_json=payload, evidence_sha256=digest(payload), **audit),
                'Healthy archive; exact replay, logical rounds, roster, sides and winners; every stored objective matches a unique trusted occurrence; normalized data unchanged.')


def load_inputs(db, map_id, window=8):
    """Stored-only export/recalculation path; abstain on a stale evidence seal."""
    if window != 8:
        raise ValueError('siege_style_v3 requires its frozen 8-second trade window.')
    row = db.execute('SELECT * FROM maps WHERE id=?', (map_id,)).fetchone()
    if not row or not row['replay_data_complete']:
        return None, 'Incomplete replay data'
    if db.execute('SELECT 1 FROM map_kd_corrections WHERE map_id=?', (map_id,)).fetchone():
        return None, 'Manual K/D correction'
    # Corrupt credited evidence raises through its integrity guard. Genuine
    # unsupported evidence is an eligibility refusal, never a zero substitution.
    if load_credit(db, map_id) is None:
        return None, 'Incomplete credited-kill evidence'
    records = json.loads(db.execute('SELECT evidence_json FROM map_kill_credit WHERE map_id=?', (map_id,)).fetchone()[0])
    match = Match.from_dict(json.loads(row['normalized_json']))
    if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='map_v3_objective_evidence'").fetchone():
        saved = db.execute('SELECT * FROM map_v3_objective_evidence WHERE map_id=?', (map_id,)).fetchone()
        if saved:
            if digest(saved['evidence_json']) != saved['evidence_sha256']:
                raise ValueError('V3 objective evidence integrity check failed.')
            if saved['fingerprint'] == row['fingerprint'] and saved['normalized_sha256'] == digest(row['normalized_json']):
                match = Match.from_dict(json.loads(saved['evidence_json']))
            else:
                return None, 'Stale V3 objective evidence; explicit review required.'
    try:
        return prepare(match, records)[0], None
    except (ValueError, KeyError, TypeError) as error:
        return None, str(error)
