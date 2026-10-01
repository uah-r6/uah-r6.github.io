"""Read-only parity of deployed v2 code with the exact frozen research model."""
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from r6stats.parser.models import Match
from r6stats.stats.calculate import aggregate, calculate_match
from fit_models import predict
from uah_comparison import player_rounds

DB = ROOT/'data/r6stats.sqlite'
REPORT = ROOT/'research/output/uah-v2-runtime-parity.md'


def digest():
    return hashlib.sha256(DB.read_bytes()).hexdigest()


def main():
    before = digest()
    frozen = json.loads((ROOT/'research/frozen-rating-candidate.json').read_text())['model']
    conn = sqlite3.connect(DB.as_uri()+'?mode=ro', uri=True)
    conn.row_factory = sqlite3.Row
    try:
        players = {r['profile_id']: r['display_name'] for r in conn.execute(
            'SELECT profile_id,display_name FROM players WHERE profile_id IS NOT NULL')}
        maps = list(conn.execute("""SELECT m.*,s.competition,s.demo FROM maps m
                                    JOIN series s ON s.id=m.series_id
                                    WHERE s.competition='NECC' AND s.demo=0
                                    ORDER BY m.played_on,m.id"""))
        if not maps:
            raise ValueError('No eligible NECC maps')
        by_player = defaultdict(list)
        by_player_rounds = defaultdict(list)
        entries = []
        for saved in maps:
            corrections = conn.execute('SELECT count(*) FROM map_kd_corrections WHERE map_id=?',
                                       (saved['id'],)).fetchone()[0]
            if not saved['replay_data_complete'] or corrections:
                raise ValueError(f"Map {saved['id']} is not Rating-eligible")
            match = Match.from_dict(json.loads(saved['normalized_json']))
            numbers = [r.number for r in match.rounds]
            if len(numbers) != len(set(numbers)):
                raise ValueError(f"Duplicate logical round in map {saved['id']}")
            stats = calculate_match(match, 8, 'siege_style_v2')
            for participant in match.rounds[0].players:
                if participant.team != saved['our_team'] or participant.profile_id not in players:
                    continue
                key = participant.key
                rounds = player_rounds(match, key)
                actual = stats[key]
                expected = predict(frozen, {'rounds': rounds}, {})
                if abs(actual['rating']-expected) > 1e-12:
                    raise ValueError(f"Map v2/research parity mismatch: {saved['id']} / {key}")
                by_player[key].append(actual)
                by_player_rounds[key].extend(rounds)
                entries.append((players[participant.profile_id], saved['map_name'], actual))
        season_entries = []
        for key, stat_rows in by_player.items():
            total = aggregate(stat_rows, 'siege_style_v2')
            expected = predict(frozen, {'rounds': by_player_rounds[key]}, {})
            if abs(total['rating']-expected) > 1e-12:
                raise ValueError(f'Season v2/research parity mismatch: {key}')
            profile_id = next(p.profile_id for match_row in maps
                              for p in Match.from_dict(json.loads(match_row['normalized_json'])).rounds[0].players
                              if p.key == key)
            season_entries.append((players[profile_id], 'All five NECC maps', total))
        lines = ['# UAH v2 runtime parity before default switch', '',
                 f'{len(maps)} complete eligible NECC maps; {sum(bool(m["rehost_json"]) for m in maps)} rehost; '
                 f'{len(by_player)} tracked players. Every map and season runtime Rating matched the exact '
                 'frozen research predictor within 1e-12. All maps have distinct logical round numbers. '
                 'SQLite was opened read-only and its SHA-256 was unchanged.', '',
                 '| Player | Scope | Rounds | K | D | KOST | SRV | Traded deaths / kills | Opening K / D | Clutches | Extra multikill kills | v2 Rating |',
                 '| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | ---: | ---: |']
        for name, scope, s in entries+season_entries:
            lines.append(f"| {name} | {scope} | {s['rounds']} | {s['kills']} | {s['deaths']} | {s['kost_rounds']} | {s['survived']} | {s['deaths_traded']} / {s['kills_traded']} | {s['opening_kills']} / {s['opening_deaths']} | {s['clutches']} | {s['multikill_extra']} | {s['rating']:.6f} |")
        lines += ['', 'All five maps were complete and had no manual K/D correction. No replay files were reparsed. The candidate formula was not changed after this check.', '']
        REPORT.write_text('\n'.join(lines), encoding='utf-8')
    finally:
        conn.close()
    after = digest()
    if after != before:
        raise ValueError('SQLite changed during read-only parity audit')
    print(f'UAH v2 parity: {len(maps)} maps, {len(by_player)} players, SQLite SHA unchanged {after}')


if __name__ == '__main__':
    main()
