"""Independent primary K/D constraints on consumed SAL; no revised eligibility."""
from collections import Counter
import json
import re

from v3_corrected_final_pipeline import DATA, RESULT, ROOT, verify, quality_path, sha
from uah_guarded_actor_readonly import snapshot


def main():
    protected, permanent_sha = snapshot(), sha(RESULT)
    _, reservation = verify()
    aliases = json.loads((ROOT/'research/v3-corrected-final-verified-aliases.json').read_text())['aliases']
    supplement = json.loads((ROOT/'research/v3-corrected-final-consumed-primary-aliases.json').read_text())['aliases']
    rows, categories, sources = [], Counter(), {}
    for source in reservation['matches']:
        if not source['selected']:
            continue
        mid = source['official_match_id']
        out = DATA / str(mid)
        p = json.loads((out/'replay-predictions.json').read_text())
        q = json.loads(quality_path(out).read_text())
        meta = json.loads((out/'siegegg-api-sealed.json').read_text())
        primary = ROOT / f'data/research/diagnostics/v3-sal-official-kd/{mid}.html'
        payload = json.loads(re.search(r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>',
                             primary.read_text(encoding='utf-8'), re.S).group(1))['props']['pageProps']['pageData']['match']
        if payload['id'] != mid or len(payload['games']) != 1:
            raise ValueError('Independent official map identity differs')
        game = payload['games'][0]
        official = [dict(name=x['name'], team_id=t['id'], kills=x['stats']['kills']['count'],
                         deaths=x['stats']['deaths']['count'])
                    for t in game['teams'] for x in t['players'] or []]
        if len(official) != 10 or sorted(t['id'] for t in game['teams']) != source['team_ids']:
            raise ValueError('Independent official full roster differs')
        sources[str(mid)] = dict(url=source['official_page'], sha256=sha(primary),
                                vod_link=payload.get('youtubeLink'), fields_projected=['player_name','team_id','kills','deaths'])
        for decision in q['decisions']:
            player = next(x for x in p['players'] if x['player'] == decision['player'])
            alias = aliases.get(player['player'], {})
            if alias and alias['replay_profile_id'] != player['profile_id']:
                raise ValueError('Independent alias UID differs')
            names = {player['player'].split('.')[0].casefold(), alias.get('name','').casefold()}
            names.update(n.split('.')[0].casefold() for n in alias.get('observed_names',[]))
            public_identity = next(x for x in meta['players'] if x['id'] == decision['player_id'])
            # Exact already-bound public IGN/stylized-name spellings, e.g.
            # public WIZARD. and official Wizard.; no punctuation stripping.
            names.update(public_identity[k].casefold() for k in ('ign','stylized_name'))
            extra = supplement.get(player['player'])
            if extra:
                if extra['replay_profile_id'] != player['profile_id']:
                    raise ValueError('Consumed supplemental identity UID differs')
                names.update(n.split('.')[0].casefold() for n in extra['observed_names'])
            matches = [x for x in official if x['name'].casefold() in names]
            kd = re.fullmatch(r'(\d+)-(\d+)(?:\s+\([+-]?\d+\))?', decision['public_kd'])
            if not kd:
                raise ValueError('Unrecognized already-frozen public K/D format')
            public_kd = tuple(map(int,kd.groups()))
            replay_kd = (player['derived']['kills'], player['derived']['deaths'])
            primary_kd = (matches[0]['kills'],matches[0]['deaths']) if len(matches)==1 else None
            if primary_kd is None:
                category = 'primary identity unresolved; no fuzzy inference'
            elif primary_kd == public_kd == replay_kd:
                category = 'three sources agree'
            elif primary_kd == public_kd:
                category = 'official and public agree; replay differs'
            elif primary_kd == replay_kd:
                category = 'official and replay agree; public differs'
            elif public_kd == replay_kd:
                category = 'public and replay agree; official differs'
            else:
                category = 'all three differ'
            categories[category] += 1
            rows.append(dict(official_match_id=mid,player=player['player'],profile_id=player['profile_id'],
                             replay_kd=replay_kd,public_kd=public_kd,official_kd=primary_kd,
                             primary_identity_candidates=matches,category=category,
                             identity_spellings_considered=sorted(names),
                             teamkills=sum(x['teamkills'] for x in player['rounds']),
                             frozen_eligible=decision['eligible'],frozen_issues=decision['issues']))
    mismatches = [r for r in rows if 'Exact K/D mismatch' in r['frozen_issues']]
    clean_conflicts = [r for r in rows if r['frozen_eligible'] and
                      r['category'] in ('public and replay agree; official differs','all three differ')]
    record = dict(status='consumed_independent_constraints_no_metrics_or_eligibility_revision',
                  categories=dict(categories), rows=rows, official_sources=sources,
                  clean_primary_conflicts=clean_conflicts, permanent_result_sha256=permanent_sha)
    (DATA/'independent-kd-audit.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    lines = ['# Consumed SAL independent K/D constraints', '',
             'No kills/deaths, accepted rows, target Ratings, coefficients or frozen final metrics change. '
             'Independent official player-map totals constrain the source disagreement; they do not identify '
             'a specific bad replay packet or independently validate every round kill. '
             'Primary names use exact already-bound public IGN/stylized spellings and sealed exact-UUID history. '
             'An explicitly separate consumed Nuxxga/Nuxga UUID-history review adds an official-name spelling only; '
             'it never changes frozen aliases or eligibility. No fuzzy or K/D-based identity matching.', '',
             f'All200 candidate player-map rows: {dict(categories)}.', '',
             f'Frozen K/D issue incidences: {len(mismatches)}; teamkill-positive issues: '
             f'{sum(r["teamkills"]>0 for r in mismatches)}. '
             f'Already-eligible rows with a resolved contradictory official total: {len(clean_conflicts)}.', '',
             '| Official / player | Replay K/D | Public K/D | Official K/D | TK | Frozen eligible | Independent constraint |',
             '| --- | --- | --- | --- | ---: | --- | --- |']
    for r in rows:
        if r in mismatches or r['category'] != 'three sources agree':
            lines.append(f"| {r['official_match_id']}/{r['player']} | {r['replay_kd']} | {r['public_kd']} | "
                         f"{r['official_kd'] or 'unresolved identity'} | {r['teamkills']} | {r['frozen_eligible']} | {r['category']} |")
    lines += ['', 'Unresolved primary identity is not evidence of a K/D discrepancy. '
              'Agreement between official and public sources may reflect shared upstream telemetry; '
              'independent broadcast review is needed before diagnosing a particular parser error. '
              'No excluded row is admitted retrospectively, and the original failed gate stands.', '', '## Primary source provenance', '']
    for mid,s in sources.items():
        lines.append(f"- [{mid} official match]({s['url']}); cached SHA256 `{s['sha256']}`.")
    lines += ['', f'Permanent result SHA256 `{permanent_sha}` and all{len(protected)} live file hashes unchanged. '
              'No actor/kill/operator/stat logic, database, archive or public export modifications.', '']
    (ROOT/'research/output/v3-corrected-final-sal-kd-constraints.md').write_text('\n'.join(lines),encoding='utf-8')
    if sha(RESULT) != permanent_sha or snapshot() != protected:
        raise ValueError('Permanent result or protected live data changed')
    print('Independent consumed K/D constraints',dict(categories),'clean conflicts',len(clean_conflicts),flush=True)


if __name__ == '__main__':
    main()
