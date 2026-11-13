"""First recorded opponent elimination by the selected team in each logical round."""

from r6stats.stats.calculate import chronological


def round_facts(match, our_team: int, bindings: dict, identities: dict) -> list[dict]:
    facts = []
    seen = set()
    for round_ in match.rounds:
        if round_.number in seen:
            raise ValueError('Duplicate logical round in team first-kill facts.')
        seen.add(round_.number)
        players = {p.key: p for p in round_.players}
        alive = set(players)
        first = None
        for kill in chronological(round_.kills):
            if kill.victim not in players or (kill.killer and kill.killer not in players):
                continue
            if kill.victim not in alive:
                continue
            if (first is None and kill.killer and kill.killer != kill.victim and
                    not kill.teamkill and players[kill.killer].team == our_team and
                    players[kill.victim].team != our_team):
                identity = identities.get(bindings.get(kill.killer))
                first = {'player_slug': identity['slug'] if identity else None,
                         'player_name': identity['name'] if identity else None}
            alive.remove(kill.victim)
        side = next((p.side for p in round_.players if p.team == our_team), 'Unknown')
        facts.append({'number': round_.number, 'side': side, 'result': 'Win' if round_.winner == our_team else 'Loss',
                      **(first or {'player_slug': None, 'player_name': None}),
                      'status': 'recorded' if first and first['player_slug'] else 'unresolved' if first else 'no_kill'})
    return facts
