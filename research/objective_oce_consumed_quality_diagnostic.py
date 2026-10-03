"""Explain every sealed OCE quality refusal using cached pinned raw headers.

This is retrospective diagnostics, not a prelabel source seal amendment. It
never drops an unfinished/completed source or admits an excluded map.
"""
from collections import Counter
from dataclasses import asdict
import json

from objective_bonus_body_oce_cohort import DATA,verify
from objective_bonus_body_fresh_pipeline import chronology
from objective_production_check import candidate_raw
from r6stats.parser.siege_dissect import normalize,physical_round_numbers
from v3_final_reserve import ROOT,sha


def main():
    _,reservation=verify();checkpoint=json.loads((ROOT/'research/objective-bonus-body-oce-permanent-result-checkpoint.json').read_text(encoding='utf-8'))
    result=DATA/'one-shot-primary-result.json'
    if sha(result)!=checkpoint['result_sha256']:raise ValueError('Permanent OCE result changed')
    records=[]
    for source in reservation['matches']:
        mid=source['official_match_id'];failure=DATA/str(mid)/'whole-map-quality-failure.json'
        if not failure.exists():continue
        refused=json.loads(failure.read_text(encoding='utf-8'));extraction=ROOT/f'data/research/extracted/bonus-body-asia-{mid}'
        items=[];details=[];canonical=None;last=[0,0]
        for folder in sorted({p.parent for p in extraction.rglob('*.rec')}):
            files=sorted(folder.glob('*.rec'));numbers=physical_round_numbers(files)
            raw=candidate_raw(folder,ROOT/'.local-tools/bin/siege-dissect-actors.exe')
            for rec,n,row in zip(files,numbers,raw['rounds']):
                h=row.get('header',row);parsed=normalize([row],round_numbers=[n]);people=[asdict(p) for p in parsed.rounds[0].players]
                item=dict(folder=folder.name,filename=rec.name,physical_round=n,sha256=sha(rec),header=h,players=people,map=parsed.map_name)
                items.append(item);issues=[];dupes={}
                uids=Counter(p.get('id') for p in h['players'])
                for uid,count in uids.items():
                    if count>1:dupes[str(uid)]=[p['username'] for p in h['players'] if p.get('id')==uid]
                if dupes:issues.append('non_unique_numeric_UIDs')
                if len(people)!=10 or len({p['profile_id'] for p in people})!=10:issues.append('profile_roster_incomplete_or_non_unique')
                groups=[tuple(sorted(p['profile_id'] for p in people if p['team']==i)) for i in (0,1)]
                if canonical is None:canonical=sorted(groups)
                if sorted(groups)!=canonical:issues.append('profile_roster_changed')
                score_start=[None,None];score_end=[None,None]
                for i,t in enumerate(h['teams']):
                    if groups[i] not in canonical:continue
                    remap=canonical.index(groups[i]);score_start[remap]=t['startingScore'];score_end[remap]=t['score']
                delta=[e-s for s,e in zip(score_start,score_end)] if None not in score_start+score_end else None
                expected=last[:]
                if delta is not None and delta!=[0,0]:
                    if sorted(delta)!=[0,1] or score_start!=last:issues.append('completed_score_path_discontinuity')
                    last=score_end
                details.append(dict(folder=folder.name,physical_round=n,replay_sha256=item['sha256'],issues=issues,
                    duplicate_numeric_UIDs=dupes,canonical_start=score_start,canonical_end=score_end,
                    previous_completed_end=expected,unfinished_zero_increment=delta==[0,0]))
        try:chronology(items,source['official_scores'])
        except ValueError as exc:
            if str(exc)!=refused['reason']:raise ValueError('Cached pinned quality refusal differs') from exc
        else:raise ValueError('Historical quality failure unexpectedly passes')
        records.append(dict(official_match_id=mid,reason=refused['reason'],physical_sources=details,
                            historical_quality_sha256=sha(failure),diagnostic_only=True))
    report=dict(status='retrospective_consumed_quality_diagnostic_no_source_or_outcome_regrading',records=records,
                permanent_result_sha256=sha(result),maps=len(records),actors_read=False,rounds_removed=False)
    path=DATA/'consumed-quality-diagnostic.json'
    if path.exists():
        if json.loads(path.read_text(encoding='utf-8'))!=report:raise ValueError('Preserved quality diagnostic differs')
    else:path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    lines=['# All sealed OCE quality refusals: consumed diagnostics','',
           'All six historical refusals were reproduced through the unchanged pinned raw adapter and chronology guard. '
           'This retrospective physical/header inventory does not amend a prelabel seal or make a failed map eligible.','',
           '| Match | Frozen refusal | Physical evidence |','| --- | --- | --- |']
    for r in records:
        examples=[]
        for p in r['physical_sources']:
            if not p['issues']:continue
            detail=f'{p["folder"]}/R{p["physical_round"]:02d}: {p["issues"]}'
            if p['duplicate_numeric_UIDs']:detail+=f'; shared UIDs {p["duplicate_numeric_UIDs"]}'
            if 'completed_score_path_discontinuity' in p['issues']:detail+=f'; previous end{p["previous_completed_end"]}, start{p["canonical_start"]}, end{p["canonical_end"]}'
            if p['unfinished_zero_increment']:detail+='; unfinished zero score increment'
            examples.append(detail)
        lines.append(f'| {r["official_match_id"]} | {r["reason"]} | {"; ".join(examples) or "see cached complete physical inventory"} |')
    lines+=['','Numeric identity checks precede zero-score unfinished-attempt exclusion in the frozen loader. '
            'A bad UID on an unfinished round is therefore a whole-map refusal under this study. Completed score '
            'rollbacks are also refused; no overlapping completed round is selected away. No missing player is filled, '
            'timer/body safeguard weakened, actor result/target rewritten, Rating fit or live data mutation.','']
    (ROOT/'research/output/objective-bonus-body-oce-quality-refusals.md').write_text('\n'.join(lines),encoding='utf-8')
    verify()
    if sha(result)!=checkpoint['result_sha256']:raise ValueError('Permanent OCE result changed')
    print('Reproduced',len(records),'sealed quality refusals')


if __name__=='__main__':main()
