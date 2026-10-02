"""Check consumed APAC round credit without changing its frozen experiment."""
import argparse
from collections import Counter
import json
import re
from pathlib import Path

from objective_production_check import candidate_raw
from v3_consumed_kill_credit_probe import round_evidence, counter_continuity
from v3_consumed_cohort_integrity import PERMANENT_RESULTS, sealed_sal_cache
from v3_final_pipeline import DATA, verify, quality_path
from v3_final_reserve import ROOT, FREEZE, source_sha, sha
from uah_guarded_actor_readonly import snapshot


def sealed_apac_cache():
    frozen, reservation = verify()
    seal = json.loads((DATA/'prelabel-quality-seal.json').read_text())
    if seal['freeze_sha256'] != source_sha(FREEZE):
        raise ValueError('Original APAC seal freeze changed')
    cached = {}
    selected = [s for s in reservation['matches'] if s['selected']]
    if {s['official_match_id'] for s in selected} != {s['official_match_id'] for s in seal['matches']}:
        raise ValueError('Original APAC cohort changed')
    for source in selected:
        mid = source['official_match_id']; directory = DATA/str(mid)
        sealed = next(s for s in seal['matches'] if s['official_match_id'] == mid)
        files = dict(predictions=directory/'replay-predictions.json', quality=quality_path(directory),
                     api=directory/'siegegg-api-sealed.json', stats=directory/'siegegg-player-stats-sealed.json')
        quality = json.loads(files['quality'].read_text())
        expected = dict(predictions=sealed['prediction_sha256'], quality=sealed['quality_sha256'],
                        stats=sealed['target_stats_sha256'], api=quality['api_sha256'])
        # Original APAC seal used source_sha for quality JSON, normalizing
        # Windows CRLF to LF; the other three digests are raw-file hashes.
        # Match that recorded hash contract, not an arbitrary fallback.
        actual = {name:(source_sha(path) if name == 'quality' else sha(path))
                  for name,path in files.items()}
        if actual != expected:
            raise ValueError('Original APAC sealed input changed: '+str(mid))
        if (quality['prediction_sha256'] != expected['predictions']
                or quality['target_stats_sha256'] != expected['stats']):
            raise ValueError('Original APAC quality provenance differs')
        cached[mid] = dict(source=source, prediction=json.loads(files['predictions'].read_text()),
                           quality=quality)
    return frozen, cached


def primary_counts(mid, source):
    # Previously cached official pages only; missing pages stay not reviewed.
    page = ROOT/f'data/research/diagnostics/v3-event-metadata/match-{mid}.html'
    if not page.exists():
        return {}, None
    payload = json.loads(re.search(r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>',
                         page.read_text(encoding='utf-8'), re.S).group(1))['props']['pageProps']['pageData']
    players = [p for t in payload['match']['games'][0]['teams'] for p in t['players'] or []]
    return {p['name'].casefold():p['stats']['kills']['count'] for p in players}, dict(
        source=source['official_page'], sha256=sha(page))


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--limit', type=int, default=1)
    args = parser.parse_args()
    protected = snapshot()
    sealed_sal_cache()  # Also checks both permanent results and all protected live files.
    frozen, cached = sealed_apac_cache()
    destination = ROOT/'data/research/diagnostics/v3-apac-kill-credit'
    destination.mkdir(parents=True, exist_ok=True)
    aliases = json.loads((ROOT/'research/v3-final-verified-aliases.json').read_text())['aliases']
    records = []
    for mid, inputs in list(cached.items())[:args.limit]:
        prediction, quality = inputs['prediction'], inputs['quality']
        pp = DATA/str(mid)/'replay-predictions.json'
        provenance = dict(helper_sha256=source_sha(Path(__file__)),
                          counter_probe_sha256=source_sha(ROOT/'research/v3_consumed_kill_credit_probe.py'),
                          prediction_sha256=sha(pp), freeze_sha256=source_sha(FREEZE),
                          parser_sha256=frozen['parser_sha256'])
        path = destination/f'{mid}.json'
        if path.exists():
            record = json.loads(path.read_text())
            if record['provenance'] != provenance:
                raise ValueError('Existing APAC counter evidence changed; preserve it separately')
        else:
            extraction = ROOT/f'data/research/extracted/v3-final-apac-n-{mid}'
            raw_cache, rounds = {}, []
            for mapping in prediction['physical_mapping']:
                files = [r for r in extraction.rglob(mapping['filename']) if r.parent.name == mapping['folder']]
                if len(files)!=1 or sha(files[0])!=mapping['sha256']:
                    raise ValueError('Original APAC physical identity mismatch')
                rec = files[0]
                if rec.parent not in raw_cache:
                    raw_cache[rec.parent] = candidate_raw(rec.parent, ROOT/frozen['parser_binary'])
                raw = raw_cache[rec.parent]['rounds'][mapping['physical_round']-1]
                finishes = {p['player']:p['rounds'][mapping['logical_round']-1]['kills'] for p in prediction['players']}
                round_ = round_evidence(rec, raw, mapping['logical_round'], finishes)
                round_.update(folder=mapping['folder'], physical_round=mapping['physical_round'])
                rounds.append(round_)
                print('Consumed APAC counter',mid,'R',round_['logical_round'],
                      'bound',round_['full_counter_binding'],'differences',round_['differences'],flush=True)
            continuity, resets = counter_continuity(rounds)
            complete = not continuity and all(r['full_counter_binding'] for r in rounds)
            primary, source = primary_counts(mid, inputs['source'])
            decisions = {q['player']:q for q in quality['decisions']}
            summary = []
            if complete:
                for p in prediction['players']:
                    name = p['player']; decision = decisions[name]
                    kd = decision.get('public_kd')
                    public = int(re.match(r'(\d+)-',kd).group(1)) if kd else None
                    official_name = aliases.get(name,{}).get('name',name.split('.')[0]).casefold()
                    credit = sum(r['players'][name]['delta'] for r in rounds)
                    summary.append(dict(player=name, credited=credit, opponent_finishes=p['derived']['kills'],
                                        original_public_kills=public, independent_official_kills=primary.get(official_name),
                                        frozen_eligible=decision['eligible'],
                                        changed_rounds=[r['logical_round'] for r in rounds
                                                       if r['players'][name]['delta']!=r['players'][name]['feed_finishes']]))
            record = dict(official_match_id=mid, map=prediction['map'], rounds=rounds,
                          complete_counter_binding=complete, continuity_issues=continuity,
                          explicit_rehost_resets=resets, summary=summary, primary_source=source,
                          provenance=provenance, permanent_results=PERMANENT_RESULTS,
                          interpretation='Consumed evidence only. No new eligibility, final regrading, model fitting, '
                                         'credited victim assignment, runtime statistic or historical correction.')
            path.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
        records.append(record)
        print('Consumed APAC map complete',mid,record['complete_counter_binding'],record['summary'],flush=True)
    totals = Counter()
    for record in records:
        totals.update(maps=1, rounds=len(record['rounds']), player_maps=len(record['summary']),
                      complete_maps=int(record['complete_counter_binding']))
        totals.update(player_round_differences=sum(len(r['differences']) for r in record['rounds']),
                      player_map_patterns=sum(bool(p['changed_rounds']) for p in record['summary']),
                      map_total_differences=sum(p['credited']!=p['opponent_finishes'] for p in record['summary']),
                      eligible_player_map_patterns=sum(p['frozen_eligible'] and bool(p['changed_rounds'])
                                                      for p in record['summary']))
    lines = ['# Consumed APAC credited kills versus opponent finishes', '',
             'The original APAC prospective seal and both permanent failed v3 finals are unchanged. '
             'This extends the existing consumed SAL structural counter audit to a different event. '
             'No data-quality decision, frozen feature, normalized event or numerical Rating error is revised.', '',
             f'Current completed sample: `{dict(totals)}`.', '',
             '| Official / player | Direct UID credited kills | Opponent finishes | Original public kills | Cached independent official kills | Original eligible | Different rounds |',
             '| --- | ---: | ---: | ---: | --- | --- | --- |']
    for record in records:
        for p in record['summary']:
            if p['changed_rounds']:
                lines.append(f"| {record['official_match_id']}/{p['player']} | {p['credited']} | {p['opponent_finishes']} | "
                             f"{p['original_public_kills']} | {p['independent_official_kills']} | {p['frozen_eligible']} | {p['changed_rounds']} |")
    lines += ['', 'Official counts are shown only when an already-cached primary page and explicit bound name are available; '
              'missing primary evidence is not filled from public expected totals. Counter ownership is established first '
              'from typed temporal component/stable UID routes. Complete ten-player coverage and continuity are required. '
              'Physical rehost reset follows the same conservative negative-tested rule as SAL.', '',
              'Credit/finish differences do not establish which victim was downed by whom. '
              'The independent SAL broadcast review proves that distinction in one Y11 case, not every APAC discrepancy. '
              'Finisher identity and death timing remain separate; no last-update, nearest-player or aggregate-total inference.', '',
              f'Binding/continuity exclusions: {[(r["official_match_id"],r["continuity_issues"]) for r in records if not r["complete_counter_binding"]]}.', '',
              'Live v2, SQLite, private archives and public JSON are unchanged; no import, regeneration, push or publish.', '']
    (ROOT/'research/output/v3-consumed-apac-kill-credit.md').write_text('\n'.join(lines),encoding='utf-8')
    sealed_sal_cache(); sealed_apac_cache()
    if snapshot()!=protected:
        raise ValueError('Protected live state changed')
    print('Consumed APAC credit audit totals',dict(totals),flush=True)


if __name__ == '__main__':
    main()
