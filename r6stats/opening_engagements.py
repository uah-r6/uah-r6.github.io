"""Team opening results from the existing public Entry calculation, not Rating.

The normalized Match already contains the selected logical rehost rounds and
historical team identities. Delegate eligibility/order to calculate_match; never
reconstruct an opener from aggregated player totals or credited kill counters.
"""
from dataclasses import replace

from r6stats.stats.calculate import calculate_match


def round_facts(match, our_team, window=8, display_version='siege_style_v2'):
    result = {}
    for round_ in match.rounds:
        if round_.number in result:
            raise ValueError('Duplicate logical round in opening engagement facts.')
        stats = calculate_match(replace(match, rounds=[round_]), window, display_version)
        killers = [key for key, s in stats.items() if s['opening_kills']]
        victims = [key for key, s in stats.items() if s['opening_deaths']]
        roster = {p.key: p for p in round_.players}
        opening = None
        if killers or victims:
            if len(killers) != 1 or len(victims) != 1:
                raise ValueError('Ambiguous public Entry facts in logical round.')
            killer, victim = roster[killers[0]], roster[victims[0]]
            if killer.team == victim.team or our_team not in (killer.team, victim.team):
                raise ValueError('Public Entry team identity is inconsistent.')
            opening = 'kill' if killer.team == our_team else 'death'
        side = next((p.side for p in round_.players if p.team == our_team), 'Unknown')
        result[round_.number] = {'number': round_.number, 'side': side,
                                'result': 'Win' if round_.winner == our_team else 'Loss',
                                'opening': opening}
    return result


def empty_counts():
    return dict(eligible_rounds=0, opening_kills=0, opening_kill_wins=0,
                opening_deaths=0, opening_death_wins=0)


def finish(counts):
    def ratio(numerator, denominator):
        return counts[numerator] / counts[denominator] if counts[denominator] else None
    return {**counts, 'opening_kill_pct': ratio('opening_kills', 'eligible_rounds'),
            'conversion_pct': ratio('opening_kill_wins', 'opening_kills'),
            'recovery_pct': ratio('opening_death_wins', 'opening_deaths')}


def summarize(rounds):
    """Sum raw logical-round counts before dividing; no averaging percentages."""
    counts = {scope: empty_counts() for scope in ('overall', 'attack', 'defense', 'unknown_side')}
    for round_ in rounds:
        opening = round_.get('opening')
        if opening is None:
            continue
        if opening not in ('kill', 'death') or round_['result'] not in ('Win', 'Loss'):
            raise ValueError('Invalid opening engagement round fact.')
        side = {'Attack': 'attack', 'Defense': 'defense'}.get(round_['side'], 'unknown_side')
        for scope in ('overall', side):
            record = counts[scope]
            record['eligible_rounds'] += 1
            record['opening_kills' if opening == 'kill' else 'opening_deaths'] += 1
            if round_['result'] == 'Win':
                record['opening_kill_wins' if opening == 'kill' else 'opening_death_wins'] += 1
    return {scope: finish(record) for scope, record in counts.items()}


def summarize_maps(matches):
    """Deduplicate identical logical maps; refuse conflicting sources/rounds."""
    unique = {}
    for match in matches:
        if match['id'] in unique and unique[match['id']] != match:
            raise ValueError('Conflicting duplicate logical map in opening engagements.')
        unique[match['id']] = match
    rounds = []
    for match in unique.values():
        seen = set()
        for round_ in match['rounds']:
            if round_['number'] in seen:
                raise ValueError('Duplicate logical round in opening engagements.')
            seen.add(round_['number'])
            rounds.append(round_)
    return summarize(rounds)
