"""Cached, target-blind BO3 replay collection for the prospective CNL final.

All selected archives receive terminal decisions. No player-stat API is used
until a separate clean-source/row freeze and one-shot evaluator permits it.
"""
import argparse
from collections import Counter,defaultdict
from copy import deepcopy
from dataclasses import asdict
import json
import hashlib
from pathlib import Path
import re
import shutil
import subprocess
import sys
from urllib.parse import unquote,urlparse
import zipfile

from credited_late_history_development import immutable_write
from fit_models import predict
from pipeline import cache_url,canonical_map
from r6stats.kill_credit import validate_map_credit
from r6stats.parser.siege_dissect import normalize,physical_round_numbers,map_label
from uah_comparison import player_rounds
from v3_cnl_metadata import DATA as METADATA,fetch
from v3_cnl_reserve import RESERVE
from v3_credited_derive import bind_lan_counts
from v3_final_reserve import ROOT,sha,source_sha

DATA=ROOT/'data/research/v3-credited-final-cnl-stage1'
PARSER=ROOT/'.local-tools/bin/siege-dissect.exe'
BASELINE=ROOT/'.local-tools/bin/siege-dissect-objectives.exe'
COUNTER=ROOT/'.local-tools/bin/siege-kill-credit.exe'


def candidate_raw(folder,executable):
    # Reuse the existing exact binary/replay cache, but explicitly decode UTF-8
    # for international player names. Do not modify sealed older helpers.
    files=sorted(folder.glob('*.rec'))
    key=hashlib.sha256(executable.read_bytes()+b''.join(hashlib.sha256(p.read_bytes()).digest() for p in files)).hexdigest()
    path=ROOT/'data/research/diagnostics/objective-production-check'/(key+'.json')
    if not path.exists():
        path.parent.mkdir(parents=True,exist_ok=True)
        subprocess.run([str(executable),'-f','json','-o',str(path),str(folder)],check=True,capture_output=True)
    return json.loads(path.read_text(encoding='utf-8'))


def stitch(physical,map_name):
    """One map, explicit score-contiguous completed attempts; no inferred gaps."""
    groups=None;last=(0,0);base=None;rounds=[];mapping=[];excluded=[]
    for item in sorted(physical,key=lambda x:(x['folder'],x['physical_round'])):
        raw=item['raw'];h=raw.get('header',raw)
        observed=[tuple(sorted(p['username'] for p in h['players'] if p['teamIndex']==i)) for i in (0,1)]
        if any(len(g)!=5 for g in observed) or len(set(sum((list(g) for g in observed),[])))!=10:
            raise ValueError('Full distinct ten-player roster required')
        if groups is None:groups=sorted(observed)
        if sorted(observed)!=groups:raise ValueError('Roster differs across physical rounds')
        remap={i:groups.index(observed[i]) for i in (0,1)}
        start=[0,0];end=[0,0]
        for i,t in enumerate(h['teams']):start[remap[i]]=t['startingScore'];end[remap[i]]=t['score']
        delta=[e-s for s,e in zip(start,end)]
        info={k:v for k,v in item.items() if k!='raw'}
        if delta==[0,0]:
            excluded.append(info|dict(reason='Explicit zero score increment; unfinished physical attempt'));continue
        if sorted(delta)!=[0,1] or tuple(start)!=last:raise ValueError('Ambiguous/discontinuous completed score chronology')
        match=normalize([raw],round_numbers=[len(rounds)+1]);r=match.rounds[0]
        if canonical_map(match.map_name)!=canonical_map(map_name):raise ValueError('Physical map differs')
        if base is None:base=match
        for p in r.players:p.team=remap[p.team]
        for k in r.kills:
            if k.killer_team in remap:k.killer_team=remap[k.killer_team]
            k.victim_team=remap[k.victim_team]
        for o in r.objectives:o.team=remap[o.team]
        r.winner=remap[r.winner];r.starting_scores=tuple(start);r.ending_scores=tuple(end)
        if r.winner!=delta.index(1):raise ValueError('Winner/score delta differs')
        rounds.append(r);last=tuple(end);mapping.append(info|dict(logical_round=r.number))
    if base is None:raise ValueError('No completed rounds')
    base.rounds=rounds
    keys={p.username:p.key for p in rounds[0].players}
    if any({p.username:p.key for p in r.players}!=keys for r in rounds):raise ValueError('Unstable physical identity')
    return base,mapping,excluded,groups,last


def observation(rec):
    digest=sha(rec);path=DATA/'raw'/(digest+'.json')
    if path.exists():obs=json.loads(path.read_text(encoding='utf-8'))
    else:
        result=subprocess.run([str(COUNTER),str(rec)],capture_output=True,text=True,encoding='utf-8',check=True)
        obs=json.loads(result.stdout)|dict(replay_sha256=digest,executable_sha256=sha(COUNTER))
        immutable_write(path,obs)
    if obs['replay_sha256']!=digest or obs['executable_sha256']!=sha(COUNTER):raise ValueError('Counter provenance differs')
    return obs,path


def official_primary(source):
    path=METADATA/f"cnl1-primary-{source['official_match_id']}.html"
    text=fetch(source['official_page'],path)
    payload=json.loads(re.search(r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>',text,re.S).group(1))['props']['pageProps']['pageData']['match']
    if payload['id']!=source['official_match_id']:raise ValueError('Official match identity differs')
    return payload,path


def acquire(source):
    mid=source['official_match_id'];out=DATA/str(mid);result_path=out/'prelabel-replays.json'
    if result_path.exists():return json.loads(result_path.read_text(encoding='utf-8'))
    archive=ROOT/'data/research/pro-replays'/unquote(Path(urlparse(source['archive_url']).path).name)
    print('ACQUIRE',mid,archive.name,flush=True);cache_url(source['archive_url'],archive)
    refusal_path=out/'archive-refusal.json'
    if refusal_path.exists():
        refusal=json.loads(refusal_path.read_text(encoding='utf-8'))
        if refusal['archive_sha256']!=sha(archive) or not all(p['matches_local'] and p['bytes']==65536 for p in refusal['range_probes']):
            raise ValueError('Independent failed-archive provenance differs')
        primary,primary_path=official_primary(source)
        meta_path=METADATA/f"cnl1-metadata-{source['siegegg_match_id']}.json"
        result=dict(official_match_id=mid,siegegg_match_id=source['siegegg_match_id'],archive_sha256=sha(archive),
            archive_bytes=archive.stat().st_size,primary_sha256=sha(primary_path),metadata_sha256=sha(meta_path),
            parser_sha256=sha(PARSER),baseline_parser_sha256=sha(BASELINE),counter_sha256=sha(COUNTER),
            reservation_sha256=source_sha(RESERVE),ratings_opened=False,archive_refusal_sha256=sha(refusal_path),
            maps=[dict(game_id=g['id'],map=g['map'],whole_map_refusal=refusal['reason'],rows=[],clean_rows=0) for g in source['games']])
        immutable_write(result_path,result)
        print('PRELABEL ARCHIVE REFUSED',mid,'all',len(result['maps']),'maps; independent payload/header evidence preserved',flush=True)
        return result
    extraction=ROOT/'data/research/extracted'/f'v3-credited-cnl-{mid}';extraction.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(archive) as z:
        if z.testzip():raise ValueError('ZIP CRC failure')
        for member in z.infolist():
            target=(extraction/member.filename).resolve()
            if not target.is_relative_to(extraction.resolve()):raise ValueError('Unsafe ZIP path')
            if member.is_dir():target.mkdir(parents=True,exist_ok=True);continue
            if target.exists() and target.stat().st_size==member.file_size:continue
            target.parent.mkdir(parents=True,exist_ok=True)
            with z.open(member) as src,target.open('wb') as dst:shutil.copyfileobj(src,dst)
    physical=defaultdict(list);old_physical=defaultdict(list);seen={};duplicate_copies=[]
    for folder in sorted({p.parent for p in extraction.rglob('*.rec')}):
        files=sorted(folder.glob('*.rec'));numbers=physical_round_numbers(files)
        raw=candidate_raw(folder,PARSER);old=candidate_raw(folder,BASELINE)
        if len(files)!=len(raw['rounds']) or len(files)!=len(old['rounds']):raise ValueError('Parser/physical round coverage differs')
        for rec,n,row,prior in zip(files,numbers,raw['rounds'],old['rounds']):
            item=dict(folder=folder.name,filename=rec.name,physical_round=n,replay_path=rec.relative_to(ROOT).as_posix(),sha256=sha(rec))
            key=(folder.name,rec.name)
            if key in seen:
                if seen[key]['sha256']!=item['sha256']:raise ValueError('Conflicting duplicate physical round source')
                duplicate_copies.append(item|dict(original_replay_path=seen[key]['replay_path'],reason='Byte-identical duplicate archive copy of the same physical filename'))
                continue
            seen[key]=item
            # Group from the parser's map label only. Explicit zero-score
            # unfinished attempts may have no winner; stitch decides whether
            # those sources can be excluded, before normalization.
            header=row.get('header',row)
            name=canonical_map(map_label(header.get('map') or header.get('mapName')))
            physical[name].append(item|dict(raw=row));old_physical[name].append(item|dict(raw=prior))
    primary,primary_path=official_primary(source)
    meta_path=METADATA/f"cnl1-metadata-{source['siegegg_match_id']}.json"
    if sha(meta_path)!=source['metadata_sha256']:raise ValueError('Schedule metadata changed')
    meta=json.loads(meta_path.read_text(encoding='utf-8'))
    if len(set(canonical_map(g['map']) for g in source['games']))!=len(source['games']):raise ValueError('Repeated map ambiguous in BO3')
    known={canonical_map(g['map']) for g in source['games']}
    if set(physical)-known:raise ValueError('Unmapped physical map; no outcome-based partition')
    candidate=json.loads((ROOT/'research/v3-credited-candidate.json').read_text(encoding='utf-8'))['model']
    baseline=json.loads((ROOT/'research/frozen-rating-candidate.json').read_text(encoding='utf-8'))['model']
    results=[]
    for game in source['games']:
        name=canonical_map(game['map']);issues=[]
        try:
            if not physical[name]:raise ValueError('Official completed map missing from replay archive')
            match,mapping,excluded,groups,score=stitch(physical[name],game['map'])
            original,old_mapping,old_excluded,old_groups,old_score=stitch(old_physical[name],game['map'])
            if mapping!=old_mapping or excluded!=old_excluded or groups!=old_groups or score!=old_score:raise ValueError('Exact v2 physical chronology differs')
            if sorted(score)!=sorted([game['win_score'],game['loss_score']]) or len(match.rounds)!=sum(score):raise ValueError('Independent public score differs')
            for a,b in zip(match.rounds,original.rounds):
                if [asdict(k) for k in a.kills]!=[asdict(k) for k in b.kills] or [(p.key,p.username,p.team,p.side) for p in a.players]!=[(p.key,p.username,p.team,p.side) for p in b.players]:
                    raise ValueError('Unrelated finisher or identity/side changed from exact v2 parser')
            records=[];inputs={}
            for item in mapping:
                obs,path=observation(ROOT/item['replay_path']);inputs[path.relative_to(ROOT).as_posix()]=sha(path)
                records.append(dict(logical_round=item['logical_round'],physical_round=item['physical_round'],segment=item['folder'],credit=obs['credit']))
            credit=validate_map_credit(records)
            counts=bind_lan_counts(match,credit) if credit['complete'] else None
            if counts is None:issues.append('Whole-map credited counters incomplete')
            unresolved=[dict(round=r.number,kind=o.kind,reason=o.actor_reason) for r in match.rounds for o in r.objective_occurrences if not o.actor or o.actor_source!=o.actor_reason or o.actor_source!='completing_timer_owner_v1']
            if unresolved:issues.append('Whole-map core objective actor unresolved')
            primary_games=[g for g in primary['games'] if canonical_map(g['map']['name'])==name and g['rounds']]
            if len(primary_games)!=1:raise ValueError('Unique primary game required')
            pg=primary_games[0];people=[p|dict(team_id=t['id']) for t in pg['teams'] for p in t['players']]
            if len(people)!=10 or len({p['id'] for p in people})!=10:raise ValueError('Complete primary participation required')
            rows=[];team_ids=defaultdict(set);public_ids=defaultdict(set)
            for player in match.rounds[0].players:
                # Only exact case-insensitive username basename/IGN/stylized name;
                # numeric suffixes and totals never establish an alias.
                basename=player.username.split('.')[0].casefold()
                public=[p for p in meta['players'] if basename in {p['ign'].casefold(),p['stylized_name'].casefold()}]
                primary_people=[p for p in people if p['name'].casefold()==basename]
                local_issues=list(issues)
                if len(public)!=1 or len(primary_people)!=1:local_issues.append('Independent exact public/primary identity unresolved')
                verified=player_rounds(match,player.key);new=deepcopy(verified)
                if counts is not None:
                    for r in new:
                        r['kills']=counts[r['number']][player.key]
                        r['kost_rounds']=int(bool(r['kills'] or r['plants'] or r['disables'] or r['survived'] or r['deaths_traded']))
                prior=player_rounds(original,player.key)
                pp=primary_people[0] if len(primary_people)==1 else None;sp=public[0] if len(public)==1 else None
                if pp:
                    team_ids[player.team].add(pp['team_id'])
                    if [sum(r[k] for r in new) for k in ('kills','deaths')]!=[pp['stats'][k]['count'] for k in ('kills','deaths')]:local_issues.append('Exact primary credited K/D mismatch')
                if sp:public_ids[player.team].add(sp['roster_id'])
                rows.append(dict(event='China League 2026 Stage 1',match_id=source['siegegg_match_id'],game_id=game['id'],official_match_id=mid,
                    map=match.map_name,player=player.username,profile_id=player.profile_id,team=player.team,
                    player_id=sp['id'] if sp else None,roster_id=sp['roster_id'] if sp else None,primary_player_id=pp['id'] if pp else None,
                    rounds=new,original_v2_rounds=prior,quality_issues=local_issues,fit_eligible=not local_issues,
                    v2_prediction=predict(baseline,dict(rounds=prior),{}),v3_prediction=predict(candidate,dict(rounds=new),{}),
                    objective_positive=any(r['plants'] or r['disables'] for r in new),kill_credit_affected=any(a['kills']!=b['kills'] for a,b in zip(verified,new))))
            bindings=(all(len(team_ids[t])==len(public_ids[t])==1 for t in (0,1)) and len({r['player_id'] for r in rows if r['player_id'] is not None})==10)
            if not bindings:
                for r in rows:r['quality_issues'].append('Entire map lacks independently bound full public/primary team identity');r['fit_eligible']=False
            elif len(pg['rounds'])!=len(match.rounds):raise ValueError('Primary round count differs')
            else:
                primary_teams={t:next(iter(team_ids[t])) for t in (0,1)};public_teams={t:next(iter(public_ids[t])) for t in (0,1)}
                expected={game['win_roster_id']:game['win_score'],game['loss_roster_id']:game['loss_score']}
                if {public_teams[t]:score[t] for t in (0,1)}!=expected:raise ValueError('Independent public team score orientation differs')
                for r,pr in zip(match.rounds,sorted(pg['rounds'],key=lambda r:r['index'])):
                    if r.number!=pr['index'] or primary_teams[r.winner]!=pr['winnerId']:raise ValueError('Independent primary round winner differs')
                    if any(primary_teams[p.team]!=(pr['attackerId'] if p.side=='Attack' else pr['defenderId']) for p in r.players):raise ValueError('Independent primary round role differs')
            result=dict(game_id=game['id'],map=match.map_name,rounds=len(match.rounds),score=list(score),normalized=match.to_dict(),
                original_normalized=original.to_dict(),physical_mapping=mapping,excluded_physical_attempts=excluded,
                rows=rows,clean_rows=sum(r['fit_eligible'] for r in rows),credit_complete=credit['complete'],credit_issues=credit['issues'],
                objective_complete=not unresolved,unresolved_objectives=unresolved,inputs=inputs)
        except ValueError as e:
            result=dict(game_id=game['id'],map=game['map'],whole_map_refusal=str(e),rows=[],clean_rows=0)
        results.append(result)
        print('PRELABEL',mid,game['id'],result['map'],result['clean_rows'],'/10',result.get('whole_map_refusal',result.get('credit_issues')),flush=True)
    result=dict(official_match_id=mid,siegegg_match_id=source['siegegg_match_id'],archive_sha256=sha(archive),
        archive_bytes=archive.stat().st_size,primary_sha256=sha(primary_path),metadata_sha256=sha(meta_path),
        parser_sha256=sha(PARSER),baseline_parser_sha256=sha(BASELINE),counter_sha256=sha(COUNTER),
        reservation_sha256=source_sha(RESERVE),maps=results,duplicate_archive_copies=duplicate_copies,ratings_opened=False)
    immutable_write(result_path,result);return result


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--limit',type=int,default=1);args=ap.parse_args()
    subprocess.run([sys.executable,str(ROOT/'research/verify_production_kill_checkpoint.py')],check=True)
    reservation=json.loads(RESERVE.read_text(encoding='utf-8'));results=[]
    for source in [s for s in reservation['matches'] if s['selected']][:args.limit]:results.append(acquire(source))
    maps=[m for s in results for m in s['maps']];rows=[r for m in maps for r in m['rows']];clean=[r for r in rows if r['fit_eligible']]
    print('PRELABEL COVERAGE',len(results),'series',len(maps),'maps',len(clean),'clean rows',len({r['roster_id'] for r in clean}),'rosters',sum(r['objective_positive'] for r in clean),'objective-positive',flush=True)
    subprocess.run([sys.executable,str(ROOT/'research/verify_production_kill_checkpoint.py')],check=True)


if __name__=='__main__':main()
