"""Audit and seal the complete SAL cohort without projecting target Ratings."""
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path

from v3_corrected_final_pipeline import DATA, ROOT, FREEZE, verify, quality_path, sha
from v3_corrected_final_reserve import source_sha
from r6stats.parser.models import Match
from uah_comparison import player_rounds
from uah_guarded_actor_readonly import snapshot


def main():
    protected = snapshot()
    frozen, reservation = verify()
    if (DATA / 'rating-targets-opened.json').exists():
        raise ValueError('Final already consumed; do not create a new prospective seal')
    rows, eligible, issues, totals, rosters = [], [], Counter(), Counter(), set()
    for source in reservation['matches']:
        if not source['selected']:
            continue
        out = DATA / str(source['official_match_id'])
        pp, qp = out / 'replay-predictions.json', quality_path(out)
        p, q = json.loads(pp.read_text()), json.loads(qp.read_text())
        if p['freeze_sha256'] != source_sha(FREEZE):
            raise ValueError('Prediction freeze differs')
        files = {'predictions': pp, 'quality': qp,
                 'api': out / 'siegegg-api-sealed.json',
                 'stats': out / 'siegegg-player-stats-sealed.json'}
        hashes = {key: sha(path) for key, path in files.items()}
        for key, field in (('predictions', 'prediction_sha256'),
                           ('api', 'api_sha256'), ('stats', 'target_stats_sha256')):
            if hashes[key] != q[field]:
                raise ValueError('Cached quality input changed: ' + key)
        match = Match.from_dict(p['normalized'])
        count = Counter(o.kind for r in match.rounds for o in r.objective_occurrences)
        resolved = Counter(o.kind for r in match.rounds for o in r.objective_occurrences
                           if o.actor and o.actor_source == 'completing_timer_owner_v1'
                           and o.actor_reason == 'completing_timer_owner_v1')
        credited = Counter(o.kind for r in match.rounds for o in r.objectives)
        if credited != resolved:
            raise ValueError('Unverified/missing/duplicate objective credit')
        if p['objective_complete'] != (count == resolved):
            raise ValueError('Whole-map objective completeness inconsistent')
        if len(q['decisions']) != 10:
            raise ValueError('Missing terminal player quality decision')
        for player in match.rounds[0].players:
            r = next(r for r in p['players'] if r['player'] == player.username)
            if r['rounds'] != player_rounds(match, player.key):
                raise ValueError('Frozen inputs differ from fully corrected KOST/verified objectives')
            d = next(d for d in q['decisions'] if d['player'] == player.username)
            issues.update(d['issues'])
            if d['eligible']:
                if d['issues'] or not p['objective_complete']:
                    raise ValueError('Ineligible evidence leaked into final cohort')
                eligible.append(dict(official_match_id=source['official_match_id'],
                                     player=r['player'], roster_id=d['roster_id'],
                                     objectives=r['derived']['plants'] + r['derived']['disables']))
                rosters.add(d['roster_id'])
        clean = sum(d['eligible'] for d in q['decisions'])
        totals.update(rounds=p['round_count'], clean=clean)
        totals.update(count)
        totals.update({'resolved_' + k: v for k, v in resolved.items()})
        rows.append(dict(official_match_id=source['official_match_id'],
                         siegegg_match_id=source['siegegg_match_id'], map=p['map'],
                         rounds=p['round_count'], objectives=dict(count),
                         unresolved=p['unresolved_objectives'], clean_rows=clean,
                         archive_sha256=p['archive_sha256'], hashes=hashes))
    evidence = dict(clean_rows=len(eligible), clean_maps=sum(r['clean_rows'] > 0 for r in rows),
                    distinct_rosters=len(rosters),
                    objective_positive_rows=sum(r['objectives'] > 0 for r in eligible))
    coverage = {key: evidence[key.removeprefix('min_')] >= frozen['acceptance'][key]
                for key in ('min_clean_rows', 'min_clean_maps', 'min_distinct_rosters',
                            'min_objective_positive_rows')}
    result = dict(created_at=datetime.now(timezone.utc).isoformat(),
                  freeze_sha256=source_sha(FREEZE), helper_sha256=source_sha(Path(__file__)),
                  ratings_inspected=False, actor_labels_inspected=False,
                  matches=rows, totals=dict(totals), evidence=evidence,
                  coverage=coverage, issues=dict(issues), protected_hashes=protected)
    seal = DATA / 'prelabel-quality-seal.json'
    if seal.exists():
        previous = json.loads(seal.read_text())
        for key in result:
            if key != 'created_at' and previous[key] != result[key]:
                raise ValueError('Never overwrite a changed prospective cohort seal: ' + key)
    else:
        seal.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    lines = ['# Prospective corrected-KOST SAL final quality seal', '',
             'All 20 prospectively linked official archives have replay predictions and terminal quality decisions. '
             'Final Rating values and actor labels remain unopened. Exact model freeze and accuracy gates are unchanged.', '',
             '| Official / SiegeGG | Map | Rounds | Objectives | Unresolved | Clean rows |',
             '| --- | --- | ---: | --- | ---: | ---: |']
    for r in rows:
        lines.append(f"| {r['official_match_id']}/{r['siegegg_match_id']} | {r['map']} | {r['rounds']} | "
                     f"{r['objectives']} | {len(r['unresolved'])} | {r['clean_rows']} |")
    lines += ['', f'Totals: {dict(totals)}. Coverage: {evidence}; gates: {coverage}.', '',
              f'Exclusion issue incidences (overlapping): {dict(issues)}.', '',
              'Both arms use the same fully objective-corrected KOST and verified objectives. '
              'Every frozen per-round feature row was independently checked against normalized rounds. '
              'Objective credits equal the verified occurrence actors; no unverified legacy credit leaks into the feature. '
              'Missing actor evidence excludes the entire map. No identity mapping uses Rating or K/D outcomes.', '',
              'Eight explicit exact-UUID aliases are independently corroborated by profile histories and official rosters. '
              'Official roster GUIDs are blank: account histories support identity, not an official GUID binding. '
              'Earlier unaliased quality caches are preserved; the final cache key includes the sealed alias digest.', '',
              'Prediction, quality, API and sealed target digests for all 20 archives are stored in ignored '
              '`prelabel-quality-seal.json`. The snapshot does not include the 25 unavailable later group matches or playoffs; '
              'the entire event remains reserved. Accuracy gates are unevaluated. Live v2, SQLite, private archives and public JSON remain unchanged.', '',
              'Sources: [official schedule and archives](https://www.ubisoft.com/en-us/esports/rainbow-six/siege/competition/515/15020), '
              '[independent schedule](https://siege.gg/matches?competitions=187&tab=results&page=2), '
              '[independent alias registry](../v3-corrected-final-verified-aliases.json).', '',
              'NEXT: commit this prospective quality checkpoint before consuming the final once. Never refit on this event or deploy automatically.', '']
    (ROOT / 'research/output/v3-corrected-final-sal-prelabel-quality.md').write_text('\n'.join(lines), encoding='utf-8')
    if protected != snapshot():
        raise ValueError('Protected live files changed')
    print('Prospective cohort sealed', evidence, dict(totals), 'coverage', coverage, flush=True)


if __name__ == '__main__':
    main()
