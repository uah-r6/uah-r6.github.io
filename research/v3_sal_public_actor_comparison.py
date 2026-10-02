"""Preserve the lower-confidence original actor comparison as a separate tier."""
from collections import Counter
from datetime import datetime, timezone
from html import unescape
import json
import re

from v3_corrected_final_pipeline import DATA, RESULT, ROOT, verify, quality_path, sha
from v3_corrected_final_reserve import FREEZE, source_sha
from v3_consumed_cohort_integrity import sealed_sal_cache
from r6stats.parser.models import Match
from uah_guarded_actor_readonly import snapshot


def main():
    protected, permanent = snapshot(), sha(RESULT)
    frozen, reservation = verify()
    sealed_sal_cache()
    primary = json.loads((DATA/'independent-actor-constraints.json').read_text())
    for record in primary['records']:
        path = ROOT / f"data/research/diagnostics/v3-sal-official-kd/{record['official_match_id']}.html"
        if sha(path) != record['source_sha256']:
            raise ValueError('Independent official actor source changed')
    destination = DATA/'original-public-actor-comparison.json'
    if destination.exists():
        report = json.loads(destination.read_text())
        if (report['freeze_sha256'] != source_sha(FREEZE)
                or report['parser_sha256'] != frozen['parser_sha256']
                or report['permanent_rating_result_sha256'] != permanent
                or primary['permanent_rating_result_sha256'] != permanent):
            raise ValueError('Existing actor comparison provenance differs')
        for row in report['rows']:
            directory = DATA / str(row['official_match_id'])
            if (sha(directory/'replay-predictions.json') != row['prediction_sha256']
                    or sha(directory/'siegegg-api-sealed.json') != row['public_api_sha256']):
                raise ValueError('Existing actor comparison input changed')
            official = next(r for r in primary['records']
                            if r['official_match_id'] == row['official_match_id'])
            constraint = next((c for c in primary['independently_constrained_objectives']
                               if c['official_match_id'] == row['official_match_id']
                               and c['round'] == row['round'] and c['kind'] == row['kind']), None)
            if (row['primary_aggregate_counts'] != official['player_totals']
                    or row['primary_round_constraint'] != constraint):
                raise ValueError('Existing independent actor evidence changed')
    else:
        rows, occurrence_mismatches = [], []
        for source in reservation['matches']:
            if not source['selected']:
                continue
            mid = source['official_match_id']; directory = DATA/str(mid)
            prediction = json.loads((directory/'replay-predictions.json').read_text())
            match = Match.from_dict(prediction['normalized'])
            q = json.loads(quality_path(directory).read_text())
            api = directory/'siegegg-api-sealed.json'
            if sha(api)!=q['api_sha256']:
                raise ValueError('Original public target changed')
            target = json.loads(api.read_text())
            ids = {d['player']:d['player_id'] for d in q['decisions']}
            official = next(r for r in primary['records'] if r['official_match_id']==mid)
            for r in match.rounds:
                public_round = target['games'][0]['rounds'][r.number-1]
                for kind in ('plant','disable'):
                    events = [e for e in public_round['events'] if e['type']==kind]
                    occurrences = [o for o in r.objective_occurrences if o.kind==kind]
                    if len(events)!=len(occurrences):
                        occurrence_mismatches.append(dict(official_match_id=mid,round=r.number,kind=kind,
                                                         original_public=len(events),replay=len(occurrences)))
                        continue
                    if not events:
                        continue
                    text = unescape(re.sub('<[^>]+>',' ',events[0]['html']))
                    parsed = re.search(r'([A-Za-z0-9_.-]+) (?:plants|disables) defuser',text)
                    if not parsed:
                        raise ValueError('Cannot project original actor text')
                    name = parsed.group(1)
                    candidates = [p['id'] for p in target['players'] if name.casefold() in
                                  {p['ign'].casefold(),p['stylized_name'].casefold()}]
                    actor = next((p for p in r.players if p.key==occurrences[0].actor),None)
                    actual = ids.get(actor.username) if actor else None
                    verdict = ('unresolved' if actual is None else 'identity review' if len(candidates)!=1
                               else 'agreement' if actual==candidates[0] else 'disagreement')
                    constraint = next((c for c in primary['independently_constrained_objectives']
                                       if c['official_match_id']==mid and c['round']==r.number and c['kind']==kind),None)
                    row = dict(official_match_id=mid,siegegg_match_id=source['siegegg_match_id'],
                               round=r.number,kind=kind,replay_proposal=actor.username if actor else None,
                               replay_public_player_id=actual,original_public_actor=name,
                               original_public_player_ids=candidates,original_verdict=verdict,
                               primary_round_constraint=constraint,
                               primary_aggregate_counts=official['player_totals'],
                               prediction_sha256=sha(directory/'replay-predictions.json'),
                               public_api_sha256=sha(api),source_url=source['siegegg_page'])
                    rows.append(row)
        counts = {kind:dict(Counter(r['original_verdict'] for r in rows if r['kind']==kind))
                  for kind in ('plant','disable')}
        report = dict(created_at=datetime.now(timezone.utc).isoformat(),freeze_sha256=source_sha(FREEZE),
                      parser_sha256=frozen['parser_sha256'],original_comparison=counts,
                      rows=rows,occurrence_mismatches=occurrence_mismatches,
                      permanent_rating_result_sha256=permanent,
                      interpretation='Original third-party labels retained verbatim as names. Independent primary constraints stay separate. No actor rule adjusted to match labels.')
        destination.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    provenance = dict(comparison_sha256=sha(destination),
                      primary_constraints_sha256=sha(DATA/'independent-actor-constraints.json'),
                      prospective_seal_sha256=sha(DATA/'prelabel-quality-seal.json'),
                      freeze_sha256=source_sha(FREEZE), parser_sha256=frozen['parser_sha256'],
                      permanent_rating_result_sha256=permanent)
    manifest = DATA/'original-public-actor-comparison-provenance.json'
    if manifest.exists():
        if json.loads(manifest.read_text()) != provenance:
            raise ValueError('Preserved actor comparison/evidence provenance changed')
    else:
        manifest.write_text(json.dumps(provenance,indent=2)+'\n',encoding='utf-8')
    lines = ['# Fixed SAL actor port: original public comparison retained separately', '',
             'Replay actor proposals were fixed before third-party actor text was projected. '
             'The parser/model freeze and original targets remain unchanged. This is additional fixed-port evidence '
             'on the consumed SAL Rating event, not a newly reserved Rating experiment or a relaxed production gate.', '',
             f'Original lower-confidence comparison: {report["original_comparison"]}. '
             f'Occurrence mismatches: {report["occurrence_mismatches"]}.', '',
             'Independent primary-source round constraints are recorded separately in '
             '[official actor constraints](v3-sal-official-actor-constraints.md); aggregate equality alone does not '
             'assign every round. Do not force timer ownership to agree with the public actor field.', '',
             '| Official / round | Kind | Replay owner | Original public actor | Original comparison | Separate primary round inference |',
             '| --- | --- | --- | --- | --- | --- |']
    for row in report['rows']:
        if row['original_verdict'] != 'agreement':
            c = row['primary_round_constraint']
            description = f"{c['official_actor']} / {c['verdict']}" if c else 'Multiple-player aggregate; no unique round inference'
            lines.append(f"| [{row['official_match_id']}]({row['source_url']})/R{row['round']:02d} | {row['kind']} | "
                         f"{row['replay_proposal'] or 'unresolved'} | {row['original_public_actor']} | {row['original_verdict']} | {description} |")
    lines += ['', 'The table preserves disagreements even where an independent primary constraint supports '
              'the replay owner. Unknown body-state actors remain unresolved; no public label or official remaining '
              'count fills a missing replay UID. Additional VOD review is required where primary multi-player totals '
              'cannot independently resolve a specific disagreement.', '',
              f'Permanent failed SAL Rating result SHA256 `{permanent}` and all{len(protected)} live hashes unchanged. '
              'No changes to frozen original actor/Rating evaluations, parser, statistics, database, archive, public export or publishing.', '']
    (ROOT/'research/output/v3-sal-original-public-actor-comparison.md').write_text('\n'.join(lines),encoding='utf-8')
    if sha(RESULT)!=permanent or snapshot()!=protected:
        raise ValueError('Protected result/live data changed')
    print('Preserved original SAL public actor comparison',report['original_comparison'],
          'occurrence differences',len(report['occurrence_mismatches']),flush=True)


if __name__=='__main__':main()
