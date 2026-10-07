"""Cached target-blind complete APAC N Stage1 BO1 collection for new v3 final."""
import argparse
from collections import defaultdict
from copy import deepcopy
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from urllib.parse import unquote,urlparse
import zipfile

from credited_late_history_development import immutable_write
from fit_models import predict as baseline_predict
from pipeline import cache_url,canonical_map
from r6stats.kill_credit import validate_map_credit
from r6stats.parser.siege_dissect import physical_round_numbers
from uah_comparison import player_rounds
from v3_apac1_metadata import nextdata
from v3_apac1_reserve import RESERVE,EVENT
from v3_cnl_metadata import DATA as METADATA,fetch
from v3_cnl_pipeline import candidate_raw,stitch,PARSER,BASELINE,COUNTER
from v3_credited_derive import bind_lan_counts
from v3_final_reserve import ROOT,sha,source_sha
from v3_native_order_derive import updated_rows
from v3_native_order_fit import predict

DATA=ROOT/'data/research/v3-native-final-apac-n-stage1'
ALIASES=ROOT/'research/v3-final-verified-aliases.json'
ADDITIONAL_ALIASES=ROOT/'research/v3-native-final-apac1-aliases.json'
EXTRA_ALIASES=ROOT/'research/v3-native-final-apac1-extra-aliases.json'


def identity_aliases():
    aliases=json.loads(ALIASES.read_text(encoding='utf-8'))['aliases']
    extra=json.loads(ADDITIONAL_ALIASES.read_text(encoding='utf-8'))['aliases'] if ADDITIONAL_ALIASES.exists() else {}
    if aliases.keys() & extra.keys():raise ValueError('Separate alias registry cannot overwrite historical alias evidence')
    aliases=aliases|extra
    further=json.loads(EXTRA_ALIASES.read_text(encoding='utf-8'))['aliases'] if EXTRA_ALIASES.exists() else {}
    if aliases.keys() & further.keys():raise ValueError('Extra alias registry cannot overwrite existing evidence')
    return aliases|further


def bind_person(player,meta,people,aliases):
    """Exact basename or independently proved UUID identity, never statistic matching."""
    basename=player.username.split('.')[0].casefold()
    public=[p for p in meta['players'] if basename in {p['ign'].casefold(),p['stylized_name'].casefold()}]
    independent=[a for a in aliases.values() if a['independently_verified'] and player.profile_id and a['replay_profile_id']==player.profile_id]
    if len({a['siegegg_player_id'] for a in independent})>1:raise ValueError('Conflicting independently verified profile aliases')
    if not public and independent:public=[p for p in meta['players'] if p['id']==independent[0]['siegegg_player_id']]
    if len(public)!=1:return None,None,'Independent public identity unresolved'
    person=public[0]
    if independent and any(a['siegegg_player_id']!=person['id'] for a in independent):raise ValueError('Public direct name conflicts with exact UUID history')
    names={basename,person['ign'].casefold(),person['stylized_name'].casefold()}
    for a in independent:names.add(a['name'].casefold());names.update(n.split('.')[0].casefold() for n in a['observed_names'])
    primary=[p for p in people if p['name'].casefold() in names]
    if len(primary)!=1:return person,None,'Independent primary identity unresolved'
    return person,primary[0],None


def observe(rec):
    digest=sha(rec);path=DATA/'raw'/(digest+'.json')
    if not path.exists():
        result=subprocess.run([str(COUNTER),str(rec)],capture_output=True,text=True,encoding='utf-8',check=True)
        immutable_write(path,json.loads(result.stdout)|dict(replay_sha256=digest,executable_sha256=sha(COUNTER)))
    obs=json.loads(path.read_text(encoding='utf-8'))
    if obs['replay_sha256']!=digest or obs['executable_sha256']!=sha(COUNTER):raise ValueError('Counter cache provenance differs')
    return obs,path


def acquire(source):
    mid=source['official_match_id'];path=DATA/str(mid)/'prelabel-replays-v3.json'
    if path.exists():return json.loads(path.read_text(encoding='utf-8'))
    archive=ROOT/'data/research/pro-replays'/unquote(Path(urlparse(source['archive_url']).path).name)
    print('ACQUIRE',mid,archive.name,flush=True);cache_url(source['archive_url'],archive)
    extraction=ROOT/'data/research/extracted'/f'v3-native-apac1-{mid}';extraction.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(archive) as z:
        if z.testzip():raise ValueError('ZIP CRC failure')
        for member in z.infolist():
            target=(extraction/member.filename).resolve()
            if not target.is_relative_to(extraction.resolve()):raise ValueError('Unsafe ZIP path')
            if member.is_dir():target.mkdir(parents=True,exist_ok=True);continue
            if target.exists() and target.stat().st_size==member.file_size:continue
            target.parent.mkdir(parents=True,exist_ok=True)
            with z.open(member) as src,target.open('wb') as dst:shutil.copyfileobj(src,dst)
    primary_path=METADATA/f'apac1-primary-{mid}.html'
    primary=nextdata(fetch(source['official_page'],primary_path))['match']
    if primary['id']!=mid:raise ValueError('Primary match differs')
    meta_path=METADATA/f"apac1-metadata-{source['siegegg_match_id']}.json"
    if sha(meta_path)!=source['metadata_sha256']:raise ValueError('Independent metadata seal changed')
    meta=json.loads(meta_path.read_text(encoding='utf-8'));aliases=identity_aliases()
    physical=[];old_physical=[];seen={};duplicates=[]
    for folder in sorted({p.parent for p in extraction.rglob('*.rec')}):
        files=sorted(folder.glob('*.rec'));numbers=physical_round_numbers(files)
        raw=candidate_raw(folder,PARSER);old=candidate_raw(folder,BASELINE)
        if len(files)!=len(raw['rounds']) or len(files)!=len(old['rounds']):raise ValueError('Raw/physical coverage differs')
        for rec,n,row,prior in zip(files,numbers,raw['rounds'],old['rounds']):
            item=dict(folder=folder.name,filename=rec.name,physical_round=n,replay_path=rec.relative_to(ROOT).as_posix(),sha256=sha(rec))
            key=folder.name,rec.name
            if key in seen:
                if seen[key]['sha256']!=item['sha256']:raise ValueError('Conflicting duplicate physical replay source')
                duplicates.append(item|dict(original_replay_path=seen[key]['replay_path']));continue
            seen[key]=item;physical.append(item|dict(raw=row));old_physical.append(item|dict(raw=prior))
    game=source['games'][0];inputs={};issues=[];rows=[]
    try:
        match,mapping,excluded,groups,score=stitch(physical,game['map'])
        original,old_mapping,old_excluded,old_groups,old_score=stitch(old_physical,game['map'])
        if (mapping,excluded,groups,score)!=(old_mapping,old_excluded,old_groups,old_score):raise ValueError('Exact v2 source chronology differs')
        if len(match.rounds)!=sum(score) or sorted(score)!=sorted([game['win_score'],game['loss_score']]):raise ValueError('Independent map score differs')
        for a,b in zip(match.rounds,original.rounds):
            if [asdict(k) for k in a.kills]!=[asdict(k) for k in b.kills] or [(p.key,p.username,p.team,p.side) for p in a.players]!=[(p.key,p.username,p.team,p.side) for p in b.players]:raise ValueError('Unrelated v2 event/identity change')
        records=[];observations={}
        for item in mapping:
            obs,p=observe(ROOT/item['replay_path']);inputs[p.relative_to(ROOT).as_posix()]=sha(p);observations[item['logical_round']]=obs
            records.append(dict(logical_round=item['logical_round'],physical_round=item['physical_round'],segment=item['folder'],credit=obs['credit']))
        credit=validate_map_credit(records);counts=bind_lan_counts(match,credit) if credit['complete'] else None
        if counts is None:issues.append('Whole-map credited counter evidence incomplete')
        occurrences=[o for r in match.rounds for o in r.objective_occurrences]
        if any(not o.actor or o.actor_source!=o.actor_reason or o.actor_source!='completing_timer_owner_v1' for o in occurrences):issues.append('Whole-map core objective actor unresolved')
        if sorted((r.number,o.kind,o.player) for r in match.rounds for o in r.objectives)!=sorted((r.number,o.kind,o.actor) for r in match.rounds for o in r.objective_occurrences if o.actor):issues.append('Normalized/core objective credit inventory differs')
        games=[g for g in primary['games'] if canonical_map(g['map']['name'])==canonical_map(game['map']) and g['rounds']]
        if len(games)!=1:raise ValueError('Unique independently completed primary game required')
        pg=games[0];people=[p|dict(team_id=t['id']) for t in pg['teams'] for p in t['players']]
        if len(people)!=10 or len({p['id'] for p in people})!=10:raise ValueError('Exact full primary participation required')
        team_ids=defaultdict(set);public_ids=defaultdict(set);rows=[]
        for player in match.rounds[0].players:
            sp,pp,problem=bind_person(player,meta,people,aliases);local=list(issues)
            if problem:local.append(problem)
            rounds=player_rounds(match,player.key)
            if counts is not None:
                for r in rounds:
                    r['kills']=counts[r['number']][player.key]
                    r['kost_rounds']=int(bool(r['kills'] or r['plants'] or r['disables'] or r['survived'] or r['deaths_traded']))
            if sp:public_ids[player.team].add(sp['roster_id'])
            if pp:
                team_ids[player.team].add(pp['team_id'])
                if [sum(r[k] for r in rounds) for k in ('kills','deaths')]!=[pp['stats'][k]['count'] for k in ('kills','deaths')]:local.append('Exact independent primary credited K/D mismatch')
                if [sum(r[k] for r in rounds) for k in ('plants','disables')]!=[pp['stats'][k]['count'] for k in ('diffuserPlanted','diffuserDisabled')]:local.append('Exact independent primary objective count mismatch')
            rows.append(dict(event=EVENT,match_id=source['siegegg_match_id'],game_id=game['id'],official_match_id=mid,map=match.map_name,
                player=player.username,profile_id=player.profile_id,team=player.team,player_id=sp['id'] if sp else None,
                roster_id=sp['roster_id'] if sp else None,primary_player_id=pp['id'] if pp else None,
                rounds=rounds,original_v2_rounds=player_rounds(original,player.key),quality_issues=local,fit_eligible=not local,
                objective_positive=any(r['plants'] or r['disables'] for r in rounds),
                kill_credit_affected=any(r['kills']!=old['kills'] for r,old in zip(rounds,player_rounds(match,player.key)))))
        if any(len(team_ids[t])!=1 or len(public_ids[t])!=1 for t in (0,1)) or len({r['player_id'] for r in rows if r['player_id'] is not None})!=10 or len({r['primary_player_id'] for r in rows if r['primary_player_id'] is not None})!=10:
            raise ValueError('Entire map lacks independently bound full public/primary team identity')
        primary_teams={t:next(iter(team_ids[t])) for t in (0,1)};public_teams={t:next(iter(public_ids[t])) for t in (0,1)}
        if {public_teams[t]:score[t] for t in (0,1)}!={game['win_roster_id']:game['win_score'],game['loss_roster_id']:game['loss_score']}:raise ValueError('Independent public team score orientation differs')
        if len(pg['rounds'])!=len(match.rounds):raise ValueError('Independent primary round count differs')
        for r,pr in zip(match.rounds,sorted(pg['rounds'],key=lambda r:r['index'])):
            if r.number!=pr['index'] or primary_teams[r.winner]!=pr['winnerId'] or any(primary_teams[p.team]!=(pr['attackerId'] if p.side=='Attack' else pr['defenderId']) for p in r.players):raise ValueError('Independent round winner/role differs')
        # An objective evidence failure excludes the entire map, never selected
        # objective-positive players only. K/D disagreement stays row-level.
        if any('objective' in i for r in rows for i in r['quality_issues']):
            for r in rows:r['quality_issues'].append('Whole map objective quality refusal');r['fit_eligible']=False
        native,totals=updated_rows(match,rows,observations)
        candidate=json.loads((ROOT/'research/v3-native-order-candidate.json').read_text(encoding='utf-8'))['model']
        baseline=json.loads((ROOT/'research/frozen-rating-candidate.json').read_text(encoding='utf-8'))['model']
        for r in native:
            r.update(consumed_development=False,reserved_for_final_test=True,
                v3_prediction=predict(candidate,r),v2_prediction=baseline_predict(baseline,r|dict(rounds=r['original_v2_rounds']),{}))
        m=dict(game_id=game['id'],map=match.map_name,rounds=len(match.rounds),score=list(score),normalized=match.to_dict(),original_normalized=original.to_dict(),
            physical_mapping=mapping,excluded_physical_attempts=excluded,rows=native,clean_rows=sum(r['fit_eligible'] for r in native),
            credit_complete=credit['complete'],credit_issues=credit['issues'],native_order_totals=totals,inputs=inputs)
    except ValueError as e:m=dict(game_id=game['id'],map=game['map'],whole_map_refusal=str(e),rows=[],diagnostic_rows=rows,clean_rows=0,inputs=inputs)
    result=dict(official_match_id=mid,siegegg_match_id=source['siegegg_match_id'],archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,
        primary_sha256=sha(primary_path),metadata_sha256=sha(meta_path),parser_sha256=sha(PARSER),baseline_parser_sha256=sha(BASELINE),counter_sha256=sha(COUNTER),
        aliases_sha256=source_sha(ALIASES),additional_aliases_sha256=source_sha(ADDITIONAL_ALIASES) if ADDITIONAL_ALIASES.exists() else None,
        extra_aliases_sha256=source_sha(EXTRA_ALIASES) if EXTRA_ALIASES.exists() else None,
        reservation_sha256=source_sha(RESERVE),maps=[m],duplicate_archive_copies=duplicates,ratings_opened=False,
        previous_prelabel_decisions={p.name:sha(p) for p in path.parent.glob('prelabel-replays*.json') if p!=path})
    immutable_write(path,result);print('PRELABEL',mid,m['map'],m['clean_rows'],'/10',m.get('whole_map_refusal',sorted({i for r in m['rows'] for i in r['quality_issues']})),flush=True)
    return result


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--limit',type=int,default=1);ap.add_argument('--start',type=int,default=0);args=ap.parse_args()
    subprocess.run([sys.executable,str(ROOT/'research/verify_production_kill_checkpoint.py')],check=True)
    reserve=json.loads(RESERVE.read_text(encoding='utf-8'));results=[]
    for source in [s for s in reserve['matches'] if s['selected']][args.start:args.start+args.limit]:results.append(acquire(source))
    clean=[r for s in results for m in s['maps'] for r in m['rows'] if r['fit_eligible']]
    print('PRELABEL COVERAGE',len(results),'maps',len(clean),'clean rows',len({r['roster_id'] for r in clean}),'rosters',sum(r['objective_positive'] for r in clean),'objective-positive',flush=True)
    subprocess.run([sys.executable,str(ROOT/'research/verify_production_kill_checkpoint.py')],check=True)


if __name__=='__main__':main()
