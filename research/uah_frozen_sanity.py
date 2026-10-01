"""Read-only UAH comparison of the frozen professional model."""
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from r6stats.parser.models import Match
from r6stats.stats.calculate import calculate_match
from fit_models import predict
from uah_comparison import player_rounds

FROZEN = ROOT/'research/frozen-rating-candidate.json'
DB = ROOT/'data/r6stats.sqlite'
OUTPUT = ROOT/'research/output/uah-frozen-sanity.md'


def sha():
    return hashlib.sha256(DB.read_bytes()).hexdigest()


def main():
    before = sha()
    frozen = json.loads(FROZEN.read_text())
    connection = sqlite3.connect(f'{DB.as_uri()}?mode=ro', uri=True)
    connection.row_factory = sqlite3.Row
    try:
        players = {r['profile_id']: r['display_name'] for r in connection.execute(
            'SELECT profile_id,display_name FROM players WHERE profile_id IS NOT NULL')}
        saved = list(connection.execute("""SELECT m.id,m.map_name,m.our_team,m.normalized_json,
                                          t.name season_name FROM maps m
                                          JOIN series s ON s.id=m.series_id
                                          JOIN seasons t ON t.id=s.season_id
                                          WHERE s.competition='NECC' AND s.demo=0
                                          ORDER BY m.played_on,m.id"""))
        if not saved:
            raise ValueError('No NECC maps in read-only database')
        all_rounds = defaultdict(list)
        all_matches = []
        entries = []
        for record in saved:
            match = Match.from_dict(json.loads(record['normalized_json']))
            all_matches.append(match)
            aggregate = calculate_match(match, rating_version="collegiate_v1")
            for participant in match.rounds[0].players:
                if participant.team != record['our_team'] or participant.profile_id not in players:
                    continue
                rounds = player_rounds(match, participant.key)
                all_rounds[participant.profile_id].extend(rounds)
                entries.append((players[participant.profile_id], record['map_name'], len(rounds),
                                aggregate[participant.key]['rating'],
                                predict(frozen['model'], {'rounds': rounds}, {})))
        combined = Match('uah-combined', '', 'Season', 'Custom Game', 'Bomb',
                         [r for m in all_matches for r in m.rounds])
        season = calculate_match(combined, rating_version="collegiate_v1")
        for profile_id, rounds in all_rounds.items():
            entries.append((players[profile_id], 'All stored NECC maps', len(rounds),
                            season[profile_id]['rating'],
                            predict(frozen['model'], {'rounds': rounds}, {})))
        lines = ['# Frozen-model UAH sanity comparison', '',
                 f"Frozen model `{frozen['baseline_experiment_id']}`; {len(saved)} stored NECC maps. "
                 'All comparisons are read-only. UAH results were not used for fitting or candidate selection.', '',
                 '| Player | Scope | Rounds | collegiate_v1 | Frozen candidate | Difference |',
                 '| --- | --- | ---: | ---: | ---: | ---: |']
        for name, scope, rounds, collegiate, candidate in entries:
            lines.append(f'| {name} | {scope} | {rounds} | {collegiate:.3f} | {candidate:.3f} | {candidate-collegiate:+.3f} |')
        lines += ['', 'This is a sanity comparison of different Rating scales, not a SiegeGG target or a validation result. The frozen model has no effective objective-credit coefficient, and unresolved replay actors remain uncredited. The current live Rating and historical statistics were not changed.', '']
        OUTPUT.write_text('\n'.join(lines), encoding='utf-8')
    finally:
        connection.close()
    after = sha()
    if before != after:
        raise ValueError('Unexpected SQLite file change during read-only comparison')
    print(f'{len(saved)} maps, {len(all_rounds)} tracked players; SQLite SHA unchanged {after}')


if __name__ == '__main__':
    main()
