"""Read-only UAH order sensitivity; never computes revised Rating values."""
from collections import Counter
from dataclasses import replace
import json
from pathlib import Path
import sqlite3
from types import FunctionType
from uuid import UUID

from credited_kill_evidence import inspect
from r6stats.parser.models import Match
import r6stats.stats.calculate as engine
from uah_guarded_actor_readonly import snapshot, physical_rounds
from v3_final_reserve import ROOT, sha, source_sha


def count_calculator(*, packet_order):
    # Isolate function globals. Never monkeypatch the live module, and never
    # evaluate either rating formula using the hypothetical changed inputs.
    environment = vars(engine).copy()
    environment['calculate_rating'] = lambda *_: None
    environment['finalize'] = FunctionType(engine.finalize.__code__, environment,
                                           argdefs=engine.finalize.__defaults__)
    if packet_order:
        environment['chronological'] = lambda kills: sorted(kills, key=lambda k: k.sequence)
    return FunctionType(engine.calculate_match.__code__, environment,
                        argdefs=engine.calculate_match.__defaults__)


def verify_physical_order(round_, observation):
    raw = observation['credit']['finishes']; header = observation['header']
    names = {p['username'].strip().casefold(): str(UUID(p['profileID'])) for p in header['players']}
    if len(names) != 10 or set(names.values()) != {str(UUID(p.profile_id)) for p in round_.players}:
        raise ValueError('Complete exact normalized/replay profile binding required')
    if any(not UUID(key).int for key in names.values()):
        raise ValueError('Nil profiles cannot establish order parity')
    if any(e['offset'] <= 0 for e in raw) or len({e['offset'] for e in raw}) != len(raw):
        raise ValueError('Unknown/duplicated physical death source')
    ledger = []
    for e in sorted(raw, key=lambda e: e['offset']):
        f = e['feedback']; kind = f['type']['name']
        ledger.append((names[f['username'].strip().casefold()] if kind == 'Kill' else '',
                       names[(f['target'] if kind == 'Kill' else f['username']).strip().casefold()],
                       float(f['timeInSeconds']), bool(f.get('headshot'))))
    normalized = [(k.killer, k.victim, k.remaining, k.headshot) for k in sorted(round_.kills, key=lambda k: k.sequence)]
    if len({k.sequence for k in round_.kills}) != len(round_.kills) or normalized != ledger:
        raise ValueError('Stored sequence is not the exact archived physical death order')


def main():
    protected = snapshot(); original = count_calculator(packet_order=False); candidate = count_calculator(packet_order=True)
    source = ROOT / 'data/research/credited-kills-v1/uah-audit.json'
    prior = json.loads(source.read_text(encoding='utf-8'))
    excluded = {(r['map_id'], r['round']) for r in prior['unresolved']}
    counts = Counter(); deltas = {}; changes = []; maps = []
    database = ROOT / 'data/r6stats.sqlite'
    with sqlite3.connect(database.resolve().as_uri() + '?mode=ro', uri=True) as db:
        db.row_factory = sqlite3.Row
        roster = {r['profile_id']: r['display_name'] for r in db.execute('SELECT profile_id,display_name FROM players WHERE tracked=1')}
        stored = list(db.execute('''SELECT m.id,m.map_name,m.normalized_json,se.slug FROM maps m
            JOIN series s ON s.id=m.series_id JOIN seasons se ON se.id=s.season_id WHERE s.demo=0'''))
    for map_ in stored:
        match = Match.from_dict(json.loads(map_['normalized_json']))
        archive = ROOT / 'data/replay-archive' / map_['slug'] / map_['id']
        manifest = json.loads((archive / 'manifest.json').read_text(encoding='utf-8'))
        sources = {n: rec for n, rec, _ in physical_rounds(archive, manifest)}
        if set(sources) != {r.number for r in match.rounds}:
            raise ValueError('Stored/archive logical round inventory differs')
        used = 0; ordered = 0
        for round_ in match.rounds:
            if (map_['id'], round_.number) in excluded:
                counts['unavailable_rounds'] += 1
                continue
            observation = inspect(sources[round_.number])
            if not observation['credit']['complete']:
                raise ValueError('Prior accepted structure no longer complete')
            verify_physical_order(round_, observation)
            subset = replace(match, rounds=[round_])
            before, after = original(subset), candidate(subset)
            if any(p['rating'] is not None for p in (*before.values(), *after.values())):
                raise ValueError('Hypothetical Rating computation is forbidden')
            changed_order = engine.chronological(round_.kills) != sorted(round_.kills, key=lambda k: k.sequence)
            counts['supported_rounds'] += 1; counts['full_order_changed_rounds'] += changed_order
            used += 1; ordered += changed_order
            for key, label in roster.items():
                if key not in before:
                    continue
                a, b = before[key], after[key]
                immutable = ('rounds', 'kills', 'deaths', 'headshots', 'teamkills', 'plants', 'disables', 'survived', 'rounds_won')
                if any(a[k] != b[k] for k in immutable) or a['operators'] != b['operators'] or a['sides'] != b['sides']:
                    raise ValueError('Order diagnostic changed non-event counts/operator metadata')
                difference = {k: b[k]-a[k] for k in engine.COUNTS if b[k] != a[k]}
                deltas.setdefault(label, Counter()).update(difference)
                if difference:
                    changes.append(dict(map_id=map_['id'], map=map_['map_name'], round=round_.number,
                        player=label, original={k:a[k] for k in difference},
                        packet_order_only={k:b[k] for k in difference}, difference=difference))
        maps.append(dict(map_id=map_['id'], map=map_['map_name'], supported_rounds=used,
                         full_order_changed_rounds=ordered, complete_scope=used == len(match.rounds)))
    result = dict(status='read_only_packet_order_sensitivity_not_corrected_stats_or_new_rating_inputs',
        counts=dict(counts), maps=maps, tracked_known_round_deltas={k:dict(v) for k,v in deltas.items()},
        changes=changes, protected_hashes=protected, original_credit_audit_sha256=sha(source),
        helper_sha256=source_sha(Path(__file__)),
        original_statistics_source_sha256=source_sha(ROOT / 'r6stats/stats/calculate.py'),
        rating_computed=False, sqlite_open_mode='ro',
        limits='Packet order sensitivity only; retains legacy remaining-seconds8s trade predicate and raw finisher owner. Not a validated trade clock/credited event projection. Four incomplete Chalet rounds are excluded explicitly; deltas are not complete corrected season totals. No Rating computation, module monkeypatch, normalized event mutation, SQL write or public regeneration.')
    destination = ROOT / 'data/research/credited-kills-v1' / ('uah-order-impact-' + source_sha(Path(__file__))[:12] + '.json')
    if destination.exists() and json.loads(destination.read_text(encoding='utf-8')) != result:
        raise ValueError('Never overwrite changed consumed order diagnostic')
    destination.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    lines = ['# UAH packet-order sensitivity — read only', '', str(dict(counts)), '',
        'Exact normalized sequence is checked against archived physical feedback using complete profile '
        'bindings. Isolated copies of the existing pure calculator change only event ordering; both Rating '
        'formulas are suppressed. The live module and stored events remain unchanged. This measures '
        'sensitivity, not proposed correct trade statistics.', '',
        '| Player | Known-round event-feature deltas under packet ordering only |', '| --- | --- |']
    lines.extend(f'| {p} | {dict(d)} |' for p,d in deltas.items())
    lines += ['', '| Map / round / player | Original / packet-order-only |', '| --- | --- |']
    lines.extend(f'| {r["map"]}/{r["map_id"]}/R{r["round"]:02d}/{r["player"]} | {r["original"]} / {r["packet_order_only"]} |' for r in changes)
    lines += ['', result['limits'], '',
        'Kills, deaths, headshots, objectives, teamkills, survival, rounds/wins, side splits and operators '
        'are unchanged in all assessed tracked rounds. Event-derived differences must be separately '
        'reviewed/versioned; this report does not authorize changing original v2 inputs or live chronology.', '']
    (ROOT / 'research/output/credited-kill-uah-order-impact.md').write_text('\n'.join(lines), encoding='utf-8')
    if snapshot() != protected:
        raise ValueError('Protected state changed')
    print(dict(counts)); print(result['tracked_known_round_deltas'])


if __name__ == '__main__':
    main()
