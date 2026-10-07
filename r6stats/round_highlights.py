"""Small public round highlights from existing sealed evidence, without parsing.

Evidence refusals are per type/round. No legacy finisher multikill fallback,
no replacement clutch detector, no guessed objective actors and no event logs.
"""
from collections import Counter, defaultdict
from dataclasses import replace
import json

from r6stats.credited_refresh import round_counts
from r6stats.parser.models import Match
from r6stats.rating_inputs_v3 import digest, native_state, validate_objectives

PRIORITY = {'ACE': 0, '4K': 1, '1v2': 2, '1v3': 2, '1v4': 2, '1v5': 2,
            '3K': 3, '1v1': 4, 'Disable': 5, 'Plant': 6}


def select_groups(candidates):
    groups = []
    for slug, candidate in candidates.items():
        labels = sorted(set(candidate['labels']), key=lambda label: (PRIORITY[label], label))[:2]
        if labels:
            groups.append({'player_slug': slug, 'player_name': candidate['name'], 'labels': labels,
                           'emphasis': 'strong' if PRIORITY[labels[0]] <= 2 else
                                       'notable' if PRIORITY[labels[0]] <= 4 else 'objective'})
    return sorted(groups, key=lambda g: (PRIORITY[g['labels'][0]], g['player_slug']))[:2]


def objective_match(db, row, original):
    """Use current fingerprint-bound core occurrences; stale seals never qualify."""
    if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='map_v3_objective_evidence'").fetchone():
        return original
    saved = db.execute('SELECT * FROM map_v3_objective_evidence WHERE map_id=?', (row['id'],)).fetchone()
    if not saved:
        return original
    if digest(saved['evidence_json']) != saved['evidence_sha256']:
        raise ValueError('Highlight objective evidence integrity check failed.')
    if saved['fingerprint'] != row['fingerprint'] or saved['normalized_sha256'] != digest(row['normalized_json']):
        return original
    evidence = Match.from_dict(json.loads(saved['evidence_json']))
    a, b = original.to_dict(), evidence.to_dict()
    for value in (a, b):
        for r in value['rounds']:
            r.pop('objective_occurrences')
    if a != b:
        raise ValueError('Highlight evidence changes normalized historical data.')
    return evidence


def curate(match, credit, records, bindings, identities, our_team):
    """Bindings/identities are historical internal-ID bindings, not usernames."""
    counts = round_counts(match, credit) if credit is not None else {}
    observed = {r['logical_round']: r['credit'] for r in records} if credit is not None else {}
    result = {}
    for r in match.rounds:
        candidates = defaultdict(lambda: {'name': '', 'labels': []})
        roster = {p.key: p for p in r.players}

        def add(key, label):
            player_id = bindings.get(key)
            player = roster.get(key)
            if player_id not in identities or not player or player.team != our_team:
                return
            public = identities[player_id]
            candidates[public['slug']]['name'] = public['name']
            candidates[public['slug']]['labels'].append(label)

        for key, kills in counts.get(r.number, {}).items():
            if kills in (3, 4, 5):
                add(key, {3: '3K', 4: '4K', 5: 'ACE'}[kills])
        report = observed.get(r.number)
        if report is not None:
            try:
                if {(p.profile_id, p.username) for p in r.players} != {
                        (p['profileID'], p['username']) for p in report['players']}:
                    raise ValueError('Native roster identity differs.')
                _, clutch = native_state(r, report)
                if clutch:
                    add(clutch[0], f'1v{clutch[1]}')
            except (ValueError, KeyError, TypeError):
                pass  # No native-order clutch assertion on uncertain evidence.
        # The production core validator checks unique, fully corroborated actor
        # credits. Isolate each kind so one unsupported kind does not hide another.
        if (len(roster) == 10 and Counter(p.team for p in r.players) == Counter({0: 5, 1: 5})
                and all(p.profile_id and p.key == p.profile_id for p in r.players)):
            for kind, label in (('disable', 'Disable'), ('plant', 'Plant')):
                objectives = [o for o in r.objectives if o.kind == kind]
                occurrences = [o for o in r.objective_occurrences if o.kind == kind]
                try:
                    isolated = replace(r, objectives=objectives, objective_occurrences=occurrences)
                    validate_objectives(replace(match, rounds=[isolated]))
                    for o in objectives:
                        add(o.player, label)
                except (ValueError, KeyError, TypeError):
                    pass
        result[r.number] = select_groups(candidates)
    return result
