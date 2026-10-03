"""Compare preserved finisher trade aggregates to consumed primary statistics.

No victim assignment, trade-window tuning, feature change or Rating fit.
"""
from collections import Counter
import json
from pathlib import Path
import re

from uah_guarded_actor_readonly import snapshot
from v3_final_reserve import ROOT, sha, source_sha


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def main():
    protected = snapshot(); rows = []; sources = {}; counts = Counter()
    directory = ROOT / 'data/research/v3-corrected-final-sal-stage2'
    identities = read(directory / 'independent-kd-audit.json')['rows']
    for path in sorted((ROOT / 'data/research/diagnostics/v3-sal-kill-credit').glob('*.json')):
        if not path.stem.isdigit():
            continue
        old = read(path); mid = old['official_match_id']
        prediction_path = directory / str(mid) / 'replay-predictions.json'
        prediction = read(prediction_path)
        primary_path = ROOT / f'data/research/diagnostics/v3-sal-official-kd/{mid}.html'
        match = json.loads(re.search(r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>',
            primary_path.read_text(encoding='utf-8'), re.S)[1])['props']['pageProps']['pageData']['match']
        if match['id'] != mid or len(match['games']) != 1:
            raise ValueError('Consumed primary map identity differs')
        sources[primary_path.relative_to(ROOT).as_posix()] = sha(primary_path)
        sources[prediction_path.relative_to(ROOT).as_posix()] = sha(prediction_path)
        for p in prediction['players']:
            identity = next(i for i in identities if i['official_match_id'] == mid and i['player'] == p['player'])
            candidates = identity['primary_identity_candidates']
            if len(candidates) != 1:
                raise ValueError('Independent exact primary player binding required')
            target = [q for team in match['games'][0]['teams'] for q in team['players']
                      if team['id'] == candidates[0]['team_id'] and q['name'] == candidates[0]['name']]
            if len(target) != 1:
                raise ValueError('Primary identity ambiguity')
            stats = target[0]['stats']; original = p['derived']
            row = dict(official_match_id=mid, player=p['player'],
                original_refrags=original['refrag_kills'], official_trade_kills=stats['tradeKills']['count'],
                original_deaths_traded=original['deaths_traded'], official_deaths_by_traded_kill=stats['deathsByTradedKill']['count'],
                original_kills_traded=original['kills_traded'],
                credit_changed_rounds=[r['logical_round'] for r in old['rounds']
                                       if r['players'][p['player']]['delta'] != r['players'][p['player']]['feed_finishes']])
            rows.append(row); counts['player_maps'] += 1
            counts['refrag_trade_count_agreements'] += row['original_refrags'] == row['official_trade_kills']
            counts['traded_death_count_agreements'] += row['original_deaths_traded'] == row['official_deaths_by_traded_kill']
            counts['both_aggregate_agreements'] += (
                row['original_refrags'] == row['official_trade_kills'] and
                row['original_deaths_traded'] == row['official_deaths_by_traded_kill'])
            counts['player_maps_with_credit_finisher_difference'] += bool(row['credit_changed_rounds'])
    result = dict(status='consumed_independent_trade_aggregate_controls_no_definition_tuning',
        counts=dict(counts), rows=rows, source_hashes=sources,
        helper_sha256=source_sha(Path(__file__)), protected_hashes=protected,
        limits='Compared similarly named primary aggregate fields, not a verified event-level equivalence. Target trade window and DBNO/finisher owner policy are unknown. No public full trade ledger or generic victim/downer relation exists in these caches. Agreements/disagreements cannot determine cause or justify changing a window, owner, clock, Rating or exclusion.')
    destination = ROOT / 'data/research/credited-kills-v1/trade-aggregate-audit.json'
    if destination.exists() and read(destination) != result:
        raise ValueError('Never overwrite changed consumed trade audit')
    destination.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    lines = ['# Preserved trade-count evidence versus consumed primary aggregates', '',
        str(dict(counts)), '',
        'Replay values are the original frozen finisher/timer-order8s features, read from sealed predictions. '
        'Official identity/name/team bindings reuse the independent primary K/D review. '
        'No revised kill-credit or clock logic is substituted and no alternate windows are searched.', '',
        '| Map / player | Original refrags / official tradeKills | Original deaths traded / official deathsByTradedKill | Credit/finish differing rounds |',
        '| --- | --- | --- | --- |']
    lines.extend(f'| {r["official_match_id"]}/{r["player"]} | {r["original_refrags"]}/{r["official_trade_kills"]} | '
                 f'{r["original_deaths_traded"]}/{r["official_deaths_by_traded_kill"]} | {r["credit_changed_rounds"]} |'
                 for r in rows if r['original_refrags'] != r['official_trade_kills'] or
                 r['original_deaths_traded'] != r['official_deaths_by_traded_kill'])
    lines += ['', result['limits'], '',
        'The independent opening HUD controls demonstrate two timer-order reversals across plant resets '
        'and one opening-credit/finisher split. They do not establish a generic trade owner or window start. '
        'Keep traded-death KOST and v2 trade inputs at their original semantics until explicit event evidence '
        'supports a separately versioned change. Aggregate mismatch alone is not evidence of a specific bug.', '']
    (ROOT / 'research/output/credited-kill-trade-aggregate-audit.md').write_text('\n'.join(lines), encoding='utf-8')
    if snapshot() != protected:
        raise ValueError('Protected state changed')
    print(dict(counts))


if __name__ == '__main__':
    main()
