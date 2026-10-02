"""Independent, already-consumed actor review from cached Ubisoft objective data.

This is a label review, never replay actor logic. Map totals can constrain a
round label only when all disable wins for a team belong to one player. Multiple
nonzero players do not identify individual rounds. Original targets and frozen
results remain immutable. No Rating fields are projected or used.
"""
import hashlib
import json
from pathlib import Path

from objective_transition_probe import ROOT
from uah_guarded_actor_readonly import snapshot


def objective_projection(game):
    return dict(
        game_id=game['id'], map=game['map']['name'],
        rounds=[{k:r[k] for k in ('id', 'index', 'winMethod', 'winnerId', 'attackerId', 'defenderId')}
                for r in game['rounds']],
        teams=[dict(id=t['id'], score=t['score'], players=[
            dict(id=p['id'], name=p['name'], disables=p['stats']['diffuserDisabled']['count'])
            for p in t['players']]) for t in game['teams']])


def constrained_disable_labels(game):
    """Use official Defuser=3 enum and complete map totals, with no replay input."""
    teams, rounds = game['teams'], game['rounds']
    ids = [t['id'] for t in teams]
    if len(ids) != 2 or len(set(ids)) != 2:
        raise ValueError('Expected two distinct teams')
    indexes = [r['index'] for r in rounds]
    if sorted(indexes) != list(range(1, len(rounds)+1)):
        raise ValueError('Round indexes must be complete, unique and one-based')
    if len({r['id'] for r in rounds}) != len(rounds):
        raise ValueError('Duplicate official round identity')
    players = [p for t in teams for p in t['players']]
    if any(len(t['players']) != 5 for t in teams) or len({p['id'] for p in players}) != 10:
        raise ValueError('Expected ten distinct players')
    for r in rounds:
        if {r['attackerId'], r['defenderId']} != set(ids) or r['winnerId'] not in ids:
            raise ValueError('Invalid round side or winner identity')
        if r['winMethod'] == 3 and r['winnerId'] != r['defenderId']:
            raise ValueError('Defuser win must belong to Defense')
    results = []
    for team in teams:
        counts = [p['disables'] for p in team['players']]
        if any(type(c) is not int or c < 0 for c in counts):
            raise ValueError('Invalid disable count')
        wins = [r for r in rounds if r['winMethod'] == 3 and r['winnerId'] == team['id']]
        if sum(counts) != len(wins):
            raise ValueError('Official map disable totals and round win methods disagree')
        if team['score'] != sum(r['winnerId'] == team['id'] for r in rounds):
            raise ValueError('Official score and round winners disagree')
        credited = [p for p in team['players'] if p['disables']]
        unique = credited[0] if len(credited) == 1 else None
        results.append(dict(team_id=team['id'], disable_rounds=[r['index'] for r in wins],
                            player_totals=[dict(player=p['name'], id=p['id'], count=p['disables']) for p in credited],
                            constrained_round_labels=[dict(round=r['index'], player=unique['name'], id=unique['id'])
                                                      for r in wins] if unique else [],
                            inference='single_player_accounts_for_all_team_disables' if unique
                                      else 'multiple_players_round_assignment_unresolved' if credited
                                      else 'no_team_disables'))
    return results


def main():
    protected = snapshot()
    base = ROOT/'data/research/diagnostics/player-component-fields'
    # All four maps were consumed before this source was inspected.
    selection = {9026: ('Bank',), 7740: ('Bank', 'Fortress'), 9070: ('Bank',)}
    bundle = base/'official-match-bundle-3.js'
    text = bundle.read_text(encoding='utf-8')
    if 'e[e.Defuser=3]="Defuser"' not in text:
        raise ValueError('Cached primary website enum evidence missing')
    enum_url = ('https://static-esports.ubisoft.com/r6-website/_next/static/chunks/'
                '4112-0c4268865dc52bd7.js')
    reports = []
    for match_id, maps in selection.items():
        path = base/f'official-{match_id}-next.json'
        source = json.loads(path.read_text(encoding='utf-8'))
        match = source['props']['pageProps']['pageData']['match']
        for name in maps:
            candidates = [g for g in match['games'] if g['map']['name'] == name]
            if len(candidates) != 1:
                raise ValueError('Ambiguous official map identity')
            projection = objective_projection(candidates[0])
            constraints = constrained_disable_labels(projection)
            reports.append(dict(match_id=match_id,
                source=f'https://www.ubisoft.com/en-us/esports/rainbow-six/siege/match/{match_id}',
                cache_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                node='props.pageProps.pageData.match.games', projection=projection, constraints=constraints,
                enum_source=enum_url, enum_cache_sha256=hashlib.sha256(bundle.read_bytes()).hexdigest(),
                original_target_changed=False, replay_actor=None))
            print(match_id, name, constraints, flush=True)
    if snapshot() != protected:
        raise ValueError('Protected database/archive/public files changed')
    (base/'official-disable-review.json').write_text(json.dumps(reports,indent=2),encoding='utf-8')
    lines = ['# Independent Ubisoft disable label constraints', '',
        'Already-consumed maps only. Cached official page JSON exposes objective map totals and one-based '
        'round indexes, but `roundsStats` is an Attack/Defense aggregate, not per-round player telemetry. '
        'The primary website [enum bundle]('+enum_url+') explicitly defines Defuser=3. '
        'The review checks complete round identities, sides, winners, score and total disables. '
        'Where exactly one player accounts for every disable for a team, their map total constrains '
        'those round labels. This is an inference from a separate primary source, not a direct '
        'per-round actor field and not new independent replay accuracy.', '',
        '| Official match / map | Team | Disable rounds | Nonzero player map totals | Constrained labels |',
        '| --- | --- | --- | --- | --- |']
    for report in reports:
        for row in report['constraints']:
            if not row['disable_rounds']:
                continue
            totals=', '.join(f"{p['player']}={p['count']}" for p in row['player_totals'])
            labels=', '.join(f"R{p['round']:02d} {p['player']}" for p in row['constrained_round_labels']) or 'unresolved'
            lines.append(f"| [{report['match_id']}]({report['source']}) / {report['projection']['map']} | "
                         f"{row['team_id']} | {row['disable_rounds']} | {totals} | {labels} |")
    lines += ['', 'Bank9026: DarkZero has one Defuser win, R02; njr has one disable and J9O zero. '
        'This is new primary evidence supporting njr and contradicting the original SiegeGG J9O label. '
        'That original label and every primary validation result remain preserved. The mandatory '
        'research control stays unresolved while the separate reviewed inference is documented. '
        'No resolver has been changed to emit njr.', '',
        'SI7740: Bank has only one FaZe Defuser win, R03, and only Kds has a disable. Fortress has '
        'only one FaZe Defuser win, R17, and only Handyy has a disable. This independently supports '
        'the owners observed before explicit slot clears, despite missing global state0/component state2. '
        'It does not make slot clear alone a valid completion rule.', '',
        'EWC9070: FURIA Bank Defuser wins are R01/R04; Loira has two disables and Dias zero. '
        'This agrees with the separately reviewed R01 Counter-Defusing HUD and contradicts the '
        'original Dias round label. Original outcomes are not rewritten. The official data pipeline '
        'may share underlying telemetry with other statistics sites; source independence does not '
        'prove measurement independence.', '',
        'VOD limits: official Salt Lake final pTsWYqy7H2k shows Surf planting BankR02 at7080, '
        '7088,7090,7093, then cuts to player camera by7095 before the disable HUD is visible. '
        'SI final hMJcW8s94Tk BankR03 at5900 shows postplant44.56, followed by stage/player '
        'cameras5903-5920. FortressR17 at12650 shows Mowwwgli planting;12656 postplant44.56, '
        '12658 postplant42.55, then player cameras12661/12664/12670/12680. These samples do '
        'not visually verify kds or handyy counter-defusing. Do not infer an actor from the camera subject.', '',
        'Reproduce with `.venv/Scripts/python.exe research/objective_official_disable_review.py`. '
        'Detailed source cache SHA256, enum SHA256 and objective-only projections remain ignored. '
        f'{len(protected)} protected local file hashes unchanged. No target, Rating, SQLite, archive, '
        'public JSON or runtime change.', '']
    (ROOT/'research/output/objective-official-disable-review.md').write_text('\n'.join(lines),encoding='utf-8')


if __name__ == '__main__':
    main()
