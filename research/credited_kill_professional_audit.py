"""New Go counter validation on already-consumed SAL/APAC evidence, no refit."""
import argparse
from collections import Counter
import json

from credited_kill_evidence import inspect, DATA
from r6stats.kill_credit import validate_map_credit
from uah_guarded_actor_readonly import snapshot
from v3_final_reserve import ROOT, sha


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--limit',type=int,default=32)
    args=parser.parse_args(); protected=snapshot(); records=[]
    for event, old_folder, extraction in (
        ('SAL', 'v3-sal-kill-credit', 'v3-corrected-final-sal'),
        ('APAC', 'v3-apac-kill-credit', 'v3-final-apac-n')):
        for path in sorted((ROOT/'data/research/diagnostics'/old_folder).glob('*.json')):
            if not path.stem.isdigit(): continue
            if len(records)>=args.limit: break
            old=json.loads(path.read_text()); mid=old['official_match_id']; rounds=[]
            for r in old['rounds']:
                files=[p for p in (ROOT/f'data/research/extracted/{extraction}-{mid}').rglob(r['filename'])
                       if p.parent.name==r['folder']]
                if len(files)!=1 or sha(files[0])!=r['replay_sha256']: raise ValueError('Consumed physical identity mismatch')
                observation=inspect(files[0])
                for p in observation['credit']['players']:
                    previous=r['players'].get(p['username'])
                    if previous and p['kills'] is not None and p['kills']!=previous['delta']:
                        raise ValueError('New Go credited delta differs from existing direct counter audit')
                rounds.append(dict(logical_round=r['logical_round'],physical_round=r['physical_round'],
                                   segment=r['folder'],credit=observation['credit']))
            validated=validate_map_credit(rounds)
            primary_rows={};primary_sha=None
            if event=='SAL':
                primary_path=ROOT/'data/research/v3-corrected-final-sal-stage2/independent-kd-audit.json'
                primary_rows={r['player']:r for r in json.loads(primary_path.read_text(encoding='utf-8'))['rows'] if r['official_match_id']==mid}
                prediction_path=ROOT/f'data/research/v3-corrected-final-sal-stage2/{mid}/replay-predictions.json'
            else:
                primary_path=ROOT/f'data/research/v3-final-apac-n-stage2/consumed-primary-review-v2/{mid}.json'
                reviewed=json.loads(primary_path.read_text(encoding='utf-8'))
                primary_rows={r['player']:r for r in reviewed['primary_kd_rows']}
                page=ROOT/f'data/research/diagnostics/v3-event-metadata/match-{mid}.html'
                if sha(page)!=reviewed['source_sha256']:raise ValueError('Previously verified APAC primary page changed')
                prediction_path=ROOT/f'data/research/v3-final-apac-n-stage2/{mid}/replay-predictions.json'
            primary_sha=sha(primary_path)
            prediction=json.loads(prediction_path.read_text(encoding='utf-8'))
            compared=[]
            for p in old['summary']:
                name=p['player']
                credit=sum(next(q for q in r['credit']['players'] if q['username']==name)['kills']
                           for r in rounds) if validated['complete'] else None
                official=p.get('official_kills',p.get('independent_official_kills'))
                public=p.get('public_kills',p.get('original_public_kills'))
                verified=primary_rows.get(name)
                official_deaths=verified['official_kd'][1] if verified else None
                if verified:
                    official=verified['official_kd'][0]
                    if public!=verified['public_kd'][0]:raise ValueError('Independent/public historical counts differ')
                victim_deaths=next(r['derived']['deaths'] for r in prediction['players'] if r['player']==name)
                compared.append(dict(player=name,credited=credit,official=official,public=public,
                                     victim_deaths=victim_deaths,official_deaths=official_deaths,
                                     death_match=None if official_deaths is None else victim_deaths==official_deaths,
                                     official_match=None if official is None or credit is None else official==credit,
                                     public_match=None if public is None or credit is None else public==credit))
            records.append(dict(event=event,official_match_id=mid,map=old['map'],
                old_audit_sha256=sha(path),complete=validated['complete'],issues=validated['issues'],
                independent_primary_review_sha256=primary_sha,
                resets=validated['resets'],rounds=len(rounds),comparisons=compared))
            print('Go credit audit',event,mid,len(rounds),'rounds; complete',validated['complete'],flush=True)
    counts=Counter(maps=len(records),rounds=sum(r['rounds'] for r in records),
        complete_maps=sum(r['complete'] for r in records),player_maps=sum(len(r['comparisons']) for r in records))
    for r in records:
        for p in r['comparisons']:
            counts['official_matches']+=p['official_match'] is True
            counts['official_mismatches']+=p['official_match'] is False
            counts['official_unavailable']+=p['official_match'] is None
            counts['public_matches']+=p['public_match'] is True
            counts['public_mismatches']+=p['public_match'] is False
            counts['official_death_matches']+=p['death_match'] is True
            counts['official_death_mismatches']+=p['death_match'] is False
            counts['official_death_unavailable']+=p['death_match'] is None
    result=dict(counts=dict(counts),maps=records,protected_hashes=protected,
                scope='Consumed development data only; old final results/inputs untouched.')
    DATA.mkdir(parents=True,exist_ok=True)
    (DATA/'professional-audit.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    lines=['# Credited kills: new Go validation on consumed professional maps','',
           'Reuses cached decoded UID/declaration/property/finish evidence. It does not rerun old collection, '
           'parsing pipelines, fits, targets or final evaluations. All official comparisons use already-consumed '
           'independent target caches; missing official identity/counts remain unavailable.','',str(dict(counts)), '',
           '| Event / official map | Rounds | Complete counters | Issues | Explicit resets |',
           '| --- | ---: | --- | --- | --- |']
    for r in records: lines.append(f"| {r['event']}/{r['official_match_id']} {r['map']} | {r['rounds']} | {r['complete']} | {r['issues']} | {r['resets']} |")
    lines += ['', 'No victim association is inferred from counter timing. Reconnects/changed participation '
              'without continuity are explicit refusals. Original raw feed and all protected files remain intact.', '']
    (ROOT/'research/output/credited-kill-professional-audit.md').write_text('\n'.join(lines),encoding='utf-8')
    if snapshot()!=protected: raise ValueError('Protected live data changed')
    print(dict(counts),flush=True)


if __name__=='__main__':main()
