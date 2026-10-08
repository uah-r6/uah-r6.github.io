"""Whole-map credited count overlays; raw finish events and Rating remain intact.

Only count-derived features are upgraded. Event-level credit/shot ownership and
timing are unresolved: openings, trades, pivots and headshots retain the original
finisher semantics, including their existing chronological limitations.
"""
from collections import Counter
from copy import deepcopy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import subprocess
from uuid import UUID

from r6stats.kill_credit import SOURCE, validate_map_credit
from r6stats.parser.models import Match
from r6stats.replay_archive import verify, sha256
from r6stats.stats.calculate import aggregate, calculate_match

LEGACY = 'legacy_finisher_v1'
SCHEMA = '''CREATE TABLE IF NOT EXISTS map_kill_credit (
 map_id TEXT PRIMARY KEY REFERENCES maps(id) ON DELETE CASCADE,
 fingerprint TEXT NOT NULL, evidence_json TEXT NOT NULL,
 evidence_sha256 TEXT NOT NULL, parser_sha256 TEXT NOT NULL)'''


def round_counts(match, credit):
    if not credit['complete'] or [r.number for r in match.rounds] != [r['number'] for r in credit['rounds']]:
        raise ValueError('Whole-map complete credited round inventory required.')
    result = {}
    for normalized, observed in zip(match.rounds, credit['rounds']):
        try:
            profiles = {str(UUID(p.profile_id)): p for p in normalized.players if UUID(p.profile_id).int}
        except (ValueError, TypeError, AttributeError):
            raise ValueError('Credited participation requires exact nonnil profiles.') from None
        rows = observed['players']
        if len(profiles) != len(normalized.players) or len(profiles) != 10 or profiles.keys() != rows.keys():
            raise ValueError('Credited and normalized participation differ.')
        pairs = {(rows[key]['team'], p.team) for key, p in profiles.items()}
        if pairs not in ({(0, 0), (1, 1)}, {(0, 1), (1, 0)}):
            raise ValueError('Credited team mapping is not a complete bijection.')
        result[normalized.number] = {p.key: rows[key]['kills'] for key, p in profiles.items()}
    return result


def aggregate_display(rows, version):
    total = aggregate(rows, version)
    sources = Counter()
    for s in rows:
        sources.update(s.get('kill_source_rounds', {LEGACY: s['rounds']}))
    total['kill_source_rounds'] = dict(sources)
    total['kill_source'] = (next(iter(sources)) if len(sources) == 1 else 'mixed_whole_map_sources' if sources else LEGACY)
    total['finisher_kills'] = sum(s.get('finisher_kills', s['kills']) for s in rows)
    total['hs'] = total['headshots']/total['finisher_kills'] if total['finisher_kills'] else 0
    total['headshot_source'] = LEGACY
    total['event_feature_source'] = LEGACY
    total['multikill_sizes'] = {str(n): sum(s.get('multikill_sizes', {}).get(str(n), 0) for s in rows) for n in range(2, 6)}
    return total


def display_stats(match, credit, window=8, version='siege_style_v2'):
    """Return count overlay, with original Rating and every unrelated count."""
    baseline = calculate_match(match, window, version)
    counts = round_counts(match, credit) if credit is not None else None
    per_player = {key: [] for key in baseline}
    for round_ in match.rounds:
        old = calculate_match(replace(match, rounds=[round_]), window, version)
        sides = {p.key: p.side for p in round_.players}
        for key, original in old.items():
            s = deepcopy(original)
            s['finisher_kills'] = s['kills']
            if counts is not None:
                kills = counts[round_.number][key]
                s['kills'] = kills
                s['multikill_extra'] = max(kills - 1, 0)
                s['kost_rounds'] = int(bool(kills or s['plants'] or s['disables'] or s['survived'] or s['deaths_traded']))
                if sides[key] in s['sides']:
                    s['sides'][sides[key]]['kills'] = kills
            s['multikill_sizes'] = {str(n): int(s['kills'] == n) for n in range(2, 6)}
            s['kill_source_rounds'] = {SOURCE if counts is not None else LEGACY: 1}
            per_player[key].append(s)
    result = {}
    for key, rows in per_player.items():
        s = aggregate_display(rows, version)
        s.pop('maps', None)
        s['rating'] = baseline[key]['rating']
        result[key] = s
    return result


def store(db, map_id, records, parser_sha256):
    """Atomic sidecar insertion; original maps/events/snapshots stay untouched."""
    row = db.execute('SELECT normalized_json,fingerprint FROM maps WHERE id=?', (map_id,)).fetchone()
    if not row:
        raise ValueError('NECC map not found.')
    if db.execute('SELECT 1 FROM map_kd_corrections WHERE map_id=?', (map_id,)).fetchone():
        raise ValueError('Manual K/D overrides require separate credited-count reconciliation.')
    credit = validate_map_credit(records)
    if credit['complete']:
        round_counts(Match.from_dict(json.loads(row['normalized_json'])), credit)
    payload = json.dumps(records, sort_keys=True, separators=(',', ':'), allow_nan=False)
    digest = hashlib.sha256(payload.encode()).hexdigest()
    with db:
        db.execute(SCHEMA)
        db.execute('''INSERT OR IGNORE INTO rating_input_snapshots
            (map_id,version,normalized_json,source_sha256) VALUES(?,?,?,?)''',
            (map_id,'siege_style_v2',row['normalized_json'],hashlib.sha256(row['normalized_json'].encode()).hexdigest()))
        prior = db.execute('SELECT evidence_sha256 FROM map_kill_credit WHERE map_id=?', (map_id,)).fetchone()
        if prior and prior['evidence_sha256'] != digest:
            raise ValueError('Existing credited evidence differs; explicit reconciliation required.')
        db.execute('INSERT OR IGNORE INTO map_kill_credit VALUES(?,?,?,?,?)',
                   (map_id,row['fingerprint'],payload,digest,parser_sha256))
    return credit


def load(db, map_id):
    if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='map_kill_credit'").fetchone():
        return None
    row = db.execute('SELECT c.*,m.fingerprint AS current_fingerprint FROM map_kill_credit c JOIN maps m ON m.id=c.map_id WHERE c.map_id=?', (map_id,)).fetchone()
    if not row:
        return None
    if row['fingerprint'] != row['current_fingerprint'] or hashlib.sha256(row['evidence_json'].encode()).hexdigest() != row['evidence_sha256']:
        raise ValueError('Credited evidence integrity check failed.')
    credit = validate_map_credit(json.loads(row['evidence_json']))
    return credit if credit['complete'] else None


def read_archive(db, archive_root, map_id, executable=None):
    """Use the validated Go reader, with a private binary/replay keyed cache."""
    executable = Path(executable) if executable else Path(__file__).resolve().parents[1]/'.local-tools/bin/siege-kill-credit.exe'
    if not executable.is_file():
        return None  # Explicit public legacy source; never substitute zero credit.
    status = verify(db, archive_root, map_id)
    if status['status'] != 'Healthy':
        raise ValueError('Credited-count collection requires a healthy replay archive.')
    path = Path(status['path'])
    manifest = json.loads((path/'manifest.json').read_text(encoding='utf-8'))
    if manifest['archive_format_version'] == 1:
        sources = [(f['physical_round_number'],f['physical_round_number'],'original',path/f['filename'],f['sha256']) for f in manifest['files']]
    else:
        sources = [(r['logical_number'],r['physical_number'],f"segment-{r['segment']:02d}",path/f"segment-{r['segment']:02d}"/r['filename'],r['sha256'])
                   for r in manifest['source_manifest']['mapping'] if r['logical_number'] is not None]
    binary = sha256(executable)
    cache_root = Path(archive_root).parent/'kill-credit-cache'
    cache_root.mkdir(parents=True, exist_ok=True)
    records = []
    for logical, physical, segment, replay, digest in sorted(sources):
        key = hashlib.sha256((binary+digest).encode()).hexdigest()
        cache = cache_root/(key+'.json')
        if cache.exists():
            saved = json.loads(cache.read_text(encoding='utf-8'))
            observation = saved['observation']
            payload = json.dumps(observation, sort_keys=True, separators=(',', ':'))
            if (saved['binary_sha256'] != binary or saved['replay_sha256'] != digest or
                    saved['payload_sha256'] != hashlib.sha256(payload.encode()).hexdigest()):
                raise ValueError('Credited reader cache integrity check failed.')
        else:
            run = subprocess.run([str(executable),str(replay)],capture_output=True,text=True,check=True)
            observation = json.loads(run.stdout)
            payload = json.dumps(observation, sort_keys=True, separators=(',', ':'))
            cache.write_text(json.dumps(dict(observation=observation,binary_sha256=binary,replay_sha256=digest,
                payload_sha256=hashlib.sha256(payload.encode()).hexdigest()),sort_keys=True),encoding='utf-8')
        records.append(dict(logical_round=logical,physical_round=physical,segment=segment,credit=observation['credit']))
    return records, binary


def collect_archive(db, archive_root, map_id, executable=None):
    observation = read_archive(db, archive_root, map_id, executable)
    if observation is None:
        return None
    records, binary = observation
    return store(db, map_id, records, binary)


def reconcile_incomplete(db, map_id, records, parser_sha256, *, archive_root, fingerprint, prior_sha256):
    """Explicit, compare-and-swap replacement of incomplete evidence only.

    The caller collects from a verified archive using read_archive. Retain the
    entire prior record in the private audit; store() still refuses overwrites.
    """
    from r6stats.rating_evidence import AUDIT_SCHEMA, record_audit
    trusted = read_archive(db, archive_root, map_id)
    if trusted is None or trusted != (records, parser_sha256):
        raise ValueError('Reconciliation must use exact current healthy-archive reader evidence.')
    if db.execute('SELECT 1 FROM map_kd_corrections WHERE map_id=?', (map_id,)).fetchone():
        raise ValueError('Manual K/D overrides require separate credited-count reconciliation.')
    row = db.execute('SELECT * FROM maps WHERE id=?', (map_id,)).fetchone()
    prior = db.execute('SELECT * FROM map_kill_credit WHERE map_id=?', (map_id,)).fetchone()
    if not row or row['fingerprint'] != fingerprint or not prior or prior['fingerprint'] != fingerprint:
        raise ValueError('Reconciliation source identity differs.')
    if prior['evidence_sha256'] != prior_sha256 or hashlib.sha256(prior['evidence_json'].encode()).hexdigest() != prior_sha256:
        raise ValueError('Prior credited evidence changed or failed integrity.')
    old = json.loads(prior['evidence_json'])
    old_credit = validate_map_credit(old)
    if old_credit['complete']:
        raise ValueError('Complete credited evidence cannot be reconciled by this operation.')
    new = validate_map_credit(records)
    match = Match.from_dict(json.loads(row['normalized_json']))
    round_counts(match, new)
    source = lambda r: (r['logical_round'], r['physical_round'], r['segment'])
    if [source(r) for r in old] != [source(r) for r in records]:
        raise ValueError('Reconciliation physical/logical round sources differ.')
    for a, b in zip(old, records):
        current = {p['profileID']: p for p in b['credit']['players']}
        for p in a['credit']['players']:
            q = current.get(p['profileID'])
            if not q or any(p[k] != q[k] for k in ('username', 'team', 'uid')):
                raise ValueError('Reconciliation player/team identity differs.')
            if a['credit']['complete'] and any(p[k] != q[k] for k in ('initial', 'terminal', 'kills')):
                raise ValueError('Reconciliation conflicts with complete round counts.')
    # Evidence repair must not silently change any displayed historical count.
    preserve_display(match, new)
    payload = json.dumps(records, sort_keys=True, separators=(',', ':'), allow_nan=False)
    digest = hashlib.sha256(payload.encode()).hexdigest()
    with db:
        db.execute(AUDIT_SCHEMA)
        cursor = db.execute('UPDATE map_kill_credit SET evidence_json=?,evidence_sha256=?,parser_sha256=? WHERE map_id=? AND evidence_sha256=? AND fingerprint=?',
            (payload, digest, parser_sha256, map_id, prior_sha256, fingerprint))
        if cursor.rowcount != 1:
            raise ValueError('Credited evidence changed during reconciliation.')
        record_audit(db, map_id, 'credited_reconciliation', dict(prior),
            dict(fingerprint=fingerprint, evidence_json=payload, evidence_sha256=digest, parser_sha256=parser_sha256),
            'Healthy archive; same physical/logical sources and identities; complete counters; display statistics preserved.')
    return new


def preserve_display(match, credit):
    """Evidence-only maintenance refuses changes to historical count features."""
    a, b = display_stats(match, credit), display_stats(match, None)
    for s in (*a.values(), *b.values()):
        s.pop('kill_source', None); s.pop('kill_source_rounds', None)
    if a != b:
        raise ValueError('Evidence repair would change historical display statistics; separate review required.')


def collect_after_import(db, archive_root, map_id):
    """Secondary compatibility failures retain the already-valid imported map."""
    try:
        credit = collect_archive(db, archive_root, map_id)
        return {'source': SOURCE if credit and credit['complete'] else LEGACY,
                'complete': bool(credit and credit['complete'])}
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        return {'source': LEGACY, 'complete': False, 'reason': str(error)}
