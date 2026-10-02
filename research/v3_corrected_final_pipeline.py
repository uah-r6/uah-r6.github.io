"""Separate corrected-KOST final study; original APAC model/results immutable."""
import argparse
from collections import Counter
import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shutil
import subprocess
from urllib.parse import urlparse, unquote
import zipfile

from objective_production_check import candidate_raw
from r6stats.parser.models import Match
from r6stats.parser.siege_dissect import normalize, physical_round_numbers
from r6stats.stats.calculate import calculate_match
from fit_models import predict
from uah_comparison import player_rounds
from uah_guarded_actor_readonly import snapshot
from v3_corrected_final_reserve import ROOT, FREEZE, RESERVE, sha, source_sha
from v3_objective_fit import metrics

DATA=ROOT/'data/research/v3-corrected-final-sal-stage2'
RESULT=DATA/'one-shot-result.json'


def verify():
    frozen=json.loads(FREEZE.read_text(encoding='utf-8'))
    if source_sha(RESERVE)!=frozen['reservation_sha256']:raise ValueError('Reservation changed after freeze')
    expected=dict(frozen['source_hashes'])
    amendments=list((ROOT/'research').glob('v3-corrected-final-prelabel-implementation-addendum*.json'))
    latest_alias_digest=None
    def amendment_order(path):
        suffix=path.stem.removeprefix('v3-corrected-final-prelabel-implementation-addendum')
        return int(suffix.removeprefix('-')) if suffix else 0
    for addendum in sorted(amendments,key=amendment_order):
        amendment=json.loads(addendum.read_text(encoding='utf-8'))
        if amendment['original_freeze_sha256']!=source_sha(FREEZE) or amendment['rating_targets_opened']:
            raise ValueError('Invalid prospective implementation addendum')
        allowed={'research/v3_corrected_final_pipeline.py','tests/test_v3_corrected_final_gates.py'}
        if not set(amendment['source_overrides']).issubset(allowed):raise ValueError('Model/stat/parser changes prohibited by implementation addendum')
        expected.update(amendment['source_overrides'])
        latest_alias_digest=amendment.get('verified_aliases_sha256',latest_alias_digest)
    aliases_path=ROOT/'research/v3-corrected-final-verified-aliases.json'
    if aliases_path.exists() and (not latest_alias_digest or source_sha(aliases_path)!=latest_alias_digest):
        raise ValueError('Prospectively verified alias manifest changed')
    for filename,digest in expected.items():
        if source_sha(ROOT/filename)!=digest:raise ValueError('Frozen dependency changed: '+filename)
    if sha(ROOT/frozen['parser_binary'])!=frozen['parser_sha256']:raise ValueError('Frozen parser changed')
    return frozen,json.loads(RESERVE.read_text(encoding='utf-8'))


def cache_url(url,path):
    if path.exists() and path.stat().st_size:return
    path.parent.mkdir(parents=True,exist_ok=True)
    partial=path.with_name(path.name+'.partial')
    subprocess.run(['curl.exe','--fail','--location','--retry','3','--continue-at','-',
        '--output',str(partial),url],check=True,capture_output=True)
    partial.replace(path)


def acquire(source,frozen):
    mid=source['official_match_id'];out=DATA/str(mid);out.mkdir(parents=True,exist_ok=True)
    manifest=out/'replay-predictions.json'
    if manifest.exists():
        existing=json.loads(manifest.read_text(encoding='utf-8'))
        if existing['freeze_sha256']!=source_sha(FREEZE):raise ValueError('Prediction cache has different freeze')
        return existing
    archive=ROOT/'data/research/pro-replays'/unquote(Path(urlparse(source['archive_url']).path).name)
    cache_url(source['archive_url'],archive)
    extraction=ROOT/'data/research/extracted'/f'v3-corrected-final-sal-{mid}'
    extraction.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(archive) as bundle:
        bad=bundle.testzip()
        if bad:raise ValueError('Archive CRC failure: '+bad)
        for member in bundle.infolist():
            target=(extraction/member.filename).resolve()
            if not target.is_relative_to(extraction.resolve()):raise ValueError('Unsafe ZIP member')
            if member.is_dir():target.mkdir(parents=True,exist_ok=True);continue
            if target.exists() and target.stat().st_size==member.file_size:continue
            target.parent.mkdir(parents=True,exist_ok=True)
            with bundle.open(member) as src,target.open('wb') as dst:shutil.copyfileobj(src,dst)
    physical=[]
    for folder in sorted({p.parent for p in extraction.rglob('*.rec')}):
        files=sorted(folder.glob('*.rec'));numbers=physical_round_numbers(files)
        raw=candidate_raw(folder,ROOT/frozen['parser_binary'])
        if len(files)!=len(raw['rounds']):raise ValueError('Physical/raw count differs')
        for file,n,row in zip(files,numbers,raw['rounds']):
            physical.append(dict(folder=folder.name,filename=file.name,physical_round=n,
                sha256=sha(file),raw=row))
    # Scope is BO1; rehosts must follow a unique score-contiguous chronology.
    # Incomplete rounds may be excluded only by explicit zero score increment.
    chronology=sorted(physical,key=lambda x:(x['folder'],x['physical_round']))
    canonical=None;last=(0,0);rounds=[];mapping=[];base=None;excluded=[]
    for item in chronology:
        row=item['raw'];h=row.get('header',row);teams=h['teams']
        groups=[tuple(sorted(p['username'] for p in h['players'] if p['teamIndex']==i)) for i in (0,1)]
        if any(len(g)!=5 for g in groups) or len(set(sum((list(g) for g in groups),[])))!=10:
            raise ValueError('Full distinct 5v5 roster required')
        if canonical is None:canonical=sorted(groups)
        if sorted(groups)!=canonical:raise ValueError('Rehost roster changed or ambiguous')
        remap={i:canonical.index(groups[i]) for i in (0,1)}
        start=[0,0];end=[0,0]
        for i,t in enumerate(teams):start[remap[i]]=t['startingScore'];end[remap[i]]=t['score']
        delta=[e-s for s,e in zip(start,end)]
        info={k:v for k,v in item.items() if k!='raw'}
        if delta==[0,0]:
            excluded.append(info|dict(reason='Explicit zero score increment; unfinished physical attempt'))
            continue
        if sorted(delta)!=[0,1] or tuple(start)!=last:raise ValueError('Ambiguous or discontinuous completed score chronology')
        m=normalize([row],round_numbers=[len(rounds)+1]);r=m.rounds[0]
        if base is None:base=m
        if base.map_name!=m.map_name:raise ValueError('BO1 map differs across physical segments')
        for p in r.players:p.team=remap[p.team]
        remap_kills(r,remap)
        for o in r.objectives:o.team=remap[o.team]
        r.winner=remap[r.winner];r.starting_scores=tuple(start);r.ending_scores=tuple(end)
        rounds.append(r);last=tuple(end);mapping.append(info|dict(logical_round=r.number))
    if base is None:raise ValueError('No completed rounds')
    if len(source['official_scores'])!=1 or sorted(last)!=source['official_scores'][0] or sum(last)!=len(rounds):
        raise ValueError('Official complete BO1 score/round count differs')
    base.rounds=rounds
    # Unique stable per-player keys must persist through every physical segment.
    identities={p.username:p.key for p in rounds[0].players}
    if any({p.username:p.key for p in r.players}!=identities for r in rounds):raise ValueError('Replay identity changes across rounds')
    old=copy.deepcopy(base)
    for r in old.rounds:r.objectives=[]
    unresolved=[dict(round=r.number,kind=o.kind,reason=o.actor_reason) for r in rounds
        for o in r.objective_occurrences if not o.actor or o.actor_source!='completing_timer_owner_v1' or o.actor_reason!='completing_timer_owner_v1']
    objective_counts=Counter(o.kind for r in rounds for o in r.objective_occurrences)
    players=[]
    new_stats=calculate_match(base,rating_version='collegiate_v1')
    for p in rounds[0].players:
        paired=player_rounds(base,p.key);verified=player_rounds(base,p.key)
        for a,b in zip(paired,verified):
            for key in a:
                if key not in ('plants','disables','kost_rounds') and a[key]!=b[key]:raise ValueError('Unrelated input changed')
            a['plants']=b['plants'];a['disables']=b['disables']
        row=dict(rounds=paired)
        players.append(dict(player=p.username,profile_id=p.profile_id,team=p.team,rounds=paired,
            derived=new_stats[p.key],v2_prediction=predict(frozen['baseline_model'],row,{}),
            v3_prediction=predict(frozen['model'],row,{})))
    result=dict(official_match_id=mid,siegegg_match_id=source['siegegg_match_id'],event=source.get('event'),
        map=base.map_name,round_count=len(rounds),score=list(last),team_members=canonical,
        freeze_sha256=source_sha(FREEZE),archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,
        normalized=base.to_dict(),physical_mapping=mapping,excluded_physical_attempts=excluded,
        objectives=dict(objective_counts),unresolved_objectives=unresolved,objective_complete=not unresolved,
        players=players,ratings_read=False)
    manifest.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('Replay predictions sealed',mid,base.map_name,len(rounds),'rounds','objectives',dict(objective_counts),'unresolved',len(unresolved),flush=True)
    return result


def canonical_name(value):
    return str(value).strip().casefold()


def remap_kills(round_,remap):
    for k in round_.kills:
        # Existing normalized Death uses an unknown killer team of -1.
        # Preserve it; this is team-index relabeling, not kill reconstruction.
        k.killer_team=remap[k.killer_team] if k.killer_team in remap else k.killer_team
        k.victim_team=remap[k.victim_team]


def quality(source,predictions,reservation):
    out=DATA/str(source['official_match_id']);file=quality_path(out)
    if file.exists():return json.loads(file.read_text(encoding='utf-8'))
    api=out/'siegegg-api-sealed.json';stats=out/'siegegg-player-stats-sealed.json'
    cache_url(f"https://siege.gg/api/stats/matches/{source['siegegg_match_id']}",api)
    cache_url(f"https://siege.gg/api/stats/matches/{source['siegegg_match_id']}/player-stats",stats)
    meta=json.loads(api.read_text(encoding='utf-8'))
    # Actor labels and Rating values are not projected or used in this phase.
    if meta['competition_id']!=reservation['siegegg_competition_id'] or meta['date'][:10]!=source['date'][:10]:
        raise ValueError('Independent target competition/date mapping differs')
    if len(meta['games'])!=1:raise ValueError('Expected one BO1 target game')
    game=meta['games'][0];gid=game['id']
    def map_name(s):return re.sub(r'[^a-z0-9]','',s.lower()).replace('kafedostoyevsky','kafe')
    if map_name(game['map']['name'])!=map_name(predictions['map']) or sorted([game['win_score'],game['loss_score']])!=sorted(predictions['score']):
        raise ValueError('Target map/score differs')
    target_stats=json.loads(stats.read_text(encoding='utf-8'))[str(gid)]
    aliases_path=ROOT/'research/v3-corrected-final-verified-aliases.json'
    aliases=json.loads(aliases_path.read_text(encoding='utf-8'))['aliases'] if aliases_path.exists() else {}
    decisions=[]
    for row in predictions['players']:
        basename=canonical_name(row['player'].split('.')[0])
        matches=[p for p in meta['players'] if basename in {canonical_name(p['ign']),canonical_name(p['stylized_name'])}]
        alias=aliases.get(row['player'])
        if alias and alias['replay_profile_id']==row.get('profile_id') and alias.get('independently_verified') is True:
            matches=[p for p in meta['players'] if p['id']==alias['siegegg_player_id']]
        issues=[]
        if len(matches)!=1:
            decisions.append(dict(player=row['player'],eligible=False,issues=['Unresolved unique public IGN identity; no fuzzy alias inference']));continue
        p=matches[0];public=target_stats[str(p['id'])]
        kd=re.fullmatch(r'(\d+)-(\d+)(?:\s+\([+-]?\d+\))?',public['kd'])
        if not kd or tuple(map(int,kd.groups()))!=(row['derived']['kills'],row['derived']['deaths']):issues.append('Exact K/D mismatch')
        if row['derived']['rounds']!=public['rounds']:issues.append('Exact round count mismatch')
        if not predictions['objective_complete']:issues.append('Entire map excluded: unresolved objective actor')
        decisions.append(dict(player=row['player'],player_id=p['id'],roster_id=p['roster_id'],team=row['team'],
            game_id=gid,eligible=not issues,issues=issues,public_kd=public['kd'],public_rounds=public['rounds']))
    for team in (0,1):
        members=[d for d in decisions if d.get('team')==team]
        if len(members)!=5 or len({d['player_id'] for d in members})!=5 or len({d['roster_id'] for d in members})!=1:
            for d in decisions:d['eligible']=False;d['issues'].append('Full unique five-player team identity not established')
    result=dict(official_match_id=source['official_match_id'],game_id=gid,
        prediction_sha256=sha(out/'replay-predictions.json'),api_sha256=sha(api),target_stats_sha256=sha(stats),
        decisions=decisions,ratings_inspected=False,actor_labels_inspected=False)
    file.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('Label-free quality',source['official_match_id'],sum(d['eligible'] for d in decisions),'/10 clean',flush=True)
    return result


def quality_path(directory):
    # Preserve earlier decisions and automatically invalidate only quality
    # semantics after the explicitly recorded pre-label formatting correction.
    alias=ROOT/'research/v3-corrected-final-verified-aliases.json'
    signature=source_sha(Path(__file__))[:12]+('-'+source_sha(alias)[:12] if alias.exists() else '')
    return directory/f'quality-decisions-{signature}.json'


def evaluate(frozen,reservation):
    if RESULT.exists():raise ValueError('Final event already evaluated; never reopen or overwrite')
    selected=[s for s in reservation['matches'] if s['selected']]
    sealed=[]
    # Every archive must have a terminal, label-free quality decision before
    # the first Rating read. Failure cannot silently remove a selected match.
    for source in selected:
        out=DATA/str(source['official_match_id'])
        pred=json.loads((out/'replay-predictions.json').read_text(encoding='utf-8'))
        q=json.loads(quality_path(out).read_text(encoding='utf-8'))
        if q['prediction_sha256']!=sha(out/'replay-predictions.json') or q['target_stats_sha256']!=sha(out/'siegegg-player-stats-sealed.json'):
            raise ValueError('Sealed predictions/targets changed before final evaluation')
        sealed.append((source,pred,q))
    # Persist consumption BEFORE target outcomes, including crash recovery.
    marker=DATA/'rating-targets-opened.json'
    if marker.exists():raise ValueError('Rating targets already opened; inspect immutable outputs, do not retry evaluation')
    marker.write_text(json.dumps(dict(opened_at=datetime.now(timezone.utc).isoformat(),freeze_sha256=source_sha(FREEZE),
        selected_matches=[s['official_match_id'] for s,_,_ in sealed]),indent=2),encoding='utf-8')
    rows=[];a=[];b=[];details=[]
    for source,pred,q in sealed:
        stats=json.loads((DATA/str(source['official_match_id'])/'siegegg-player-stats-sealed.json').read_text(encoding='utf-8'))
        for d in q['decisions']:
            if not d['eligible']:continue
            r=next(r for r in pred['players'] if r['player']==d['player'])
            rating=float(stats[str(d['game_id'])][str(d['player_id'])]['rating'])
            rows.append(dict(event=reservation['event'],map=pred['map'],player=r['player'],rating=rating))
            a.append(r['v2_prediction']);b.append(r['v3_prediction'])
            details.append(d|dict(official_match_id=source['official_match_id'],map=pred['map'],rating=rating,
                v2=r['v2_prediction'],v3=r['v3_prediction'],objectives=r['derived']['plants']+r['derived']['disables']))
    if not rows:raise ValueError('No eligible rows; consumption marker records insufficient evidence')
    ma,mb=metrics(rows,a),metrics(rows,b);gate=frozen['acceptance']
    evidence=dict(clean_rows=len(rows),clean_maps=len({d['official_match_id'] for d in details}),
        distinct_rosters=len({d['roster_id'] for d in details}),objective_positive_rows=sum(d['objectives']>0 for d in details))
    checks={k:evidence[k.removeprefix('min_')]>=gate[k] for k in ('min_clean_rows','min_clean_maps','min_distinct_rosters','min_objective_positive_rows')}
    checks.update(max_mae=mb['mae']<=gate['max_mae'],relative_mae_improvement=(ma['mae']-mb['mae'])/ma['mae']>=gate['min_relative_mae_improvement_vs_frozen_v2'],
        within_005=mb['within_0.05']>=gate['min_within_005'],max_abs_error=mb['max_abs_error']<=gate['max_abs_error'],rmse_not_worse=mb['rmse']<=ma['rmse'])
    result=dict(experiment_id=datetime.now(timezone.utc).strftime('v3-corrected-final-sal-%Y%m%dT%H%M%SZ'),
        event=reservation['event'],freeze_sha256=source_sha(FREEZE),baseline=ma,candidate=mb,evidence=evidence,
        gates=checks,passed=all(checks.values()),details=details,final_test_evaluated=True,production_deployed=False,
        note='Permanently consumed; no refit using this event. Snapshot of all prospectively linked archives, not unavailable later matches or playoffs.')
    RESULT.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    with (ROOT/'research/experiment-log.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(result)+'\n')
    lines=['# One-shot corrected-KOST v3 South America Stage 2 final evaluation','',f"Experiment `{result['experiment_id']}`. Event permanently consumed; no automatic deployment.",'',
        f"Evidence: {evidence}. Gates: {checks}. Passed: {result['passed']}.",'',
        '| Model | N | MAE | RMSE | Median AE | Max AE | within .01 | .02 | .03 | .05 | .10 |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for name,m in [('Frozen v2',ma),('Frozen v3 objectives',mb)]:
        lines.append(f"| {name} | {m['n']} | {m['mae']:.5f} | {m['rmse']:.5f} | {m['median_abs_error']:.5f} | {m['max_abs_error']:.5f} | "+' | '.join(f"{m[f'within_{t:.2f}']:.1%}" for t in (.01,.02,.03,.05,.10))+' |')
    lines+=['','Inputs keep fully objective-corrected KOST identical in both arms and add verified objectives only. No actor labels or Rating residuals used for eligibility. Missing actors exclude entire maps. All prospectively selected archives had predictions and quality decisions saved before the first Rating read. Scope is the linked-archive snapshot, not every event match. Live v2 and historical data unchanged.','']
    (ROOT/'research/output/v3-corrected-final-sal-stage2.md').write_text('\n'.join(lines),encoding='utf-8')
    print('Permanent one-shot result',evidence,'MAE',ma['mae'],mb['mae'],'passed',result['passed'],flush=True)


def main():
    args=argparse.ArgumentParser();args.add_argument('command',choices=['acquire','quality','evaluate']);args.add_argument('--limit',type=int);args=args.parse_args()
    protected=snapshot();frozen,reservation=verify();DATA.mkdir(parents=True,exist_ok=True)
    if args.command=='evaluate':evaluate(frozen,reservation)
    else:
        selected=[s for s in reservation['matches'] if s['selected']]
        if args.limit:selected=selected[:args.limit]
        for source in selected:
            source=source|dict(event=reservation['event'])
            predictions=acquire(source,frozen)
            if args.command=='quality':quality(source,predictions,reservation)
    if snapshot()!=protected:raise ValueError('Protected live file hashes changed')


if __name__=='__main__':main()
