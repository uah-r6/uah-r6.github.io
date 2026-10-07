"""Separate corrected professional features; reuse cached inputs, not old jobs."""
from collections import Counter, defaultdict
from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
import re
import subprocess
import sys
from uuid import UUID

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from credited_round_dataset import cached_index, cached_observation
from credited_late_history_development import immutable_write
from r6stats.credited_refresh import round_counts
from r6stats.kill_credit import SOURCE, validate_map_credit
from r6stats.parser.models import Match
from r6stats.stats.calculate import calculate_match
from uah_comparison import player_rounds
from v3_final_reserve import ROOT,sha,source_sha
from v3_objective_derive import physical_mapping

DATA=ROOT/'data/research/v3-credited-development-v1'
EXE=ROOT/'.local-tools/bin/siege-kill-credit.exe'


def bind_lan_counts(match, credit):
    """Explicit research LAN adapter, never associate an unknown profile."""
    if not credit['complete'] or [r.number for r in match.rounds]!=[r['number'] for r in credit['rounds']]:
        raise ValueError('Whole-map complete credit required')
    if all(p.profile_id and UUID(p.profile_id).int for r in match.rounds for p in r.players):
        return round_counts(match,credit)
    out={}
    for r,c in zip(match.rounds,credit['rounds']):
        if any(p.profile_id and UUID(p.profile_id).int for p in r.players):
            raise ValueError('Mixed unknown/nonzero profiles need a separate identity adapter')
        observed=list(c['players'].values())
        if any(p.get('profileID') and UUID(p['profileID']).int for p in observed):
            raise ValueError('Counter profile cannot be replaced by a name')
        names={p.username:p for p in r.players};by_name={p['username']:p for p in observed}
        if len(names)!=10 or len(by_name)!=10 or names.keys()!=by_name.keys() or len({p.key for p in r.players})!=10:
            raise ValueError('Exact unique LAN header UID/name participation required')
        pairs={(by_name[n]['team'],p.team) for n,p in names.items()}
        if pairs not in ({(0,0),(1,1)},{(0,1),(1,0)}):raise ValueError('LAN team bijection differs')
        out[r.number]={p.key:by_name[n]['kills'] for n,p in names.items()}
    return out


def map_inputs():
    prior=[json.loads(l) for l in (ROOT/'data/research/experiments/v3-player-maps.jsonl').read_text(encoding='utf-8').splitlines()]
    grouped=defaultdict(list)
    for r in prior:grouped[r['match_id'],r['game_id']].append(r)
    sources=json.loads((ROOT/'research/sources.json').read_text(encoding='utf-8'))['matches']
    for source in sources:
        if not source.get('siegegg_match_id'):continue
        for mapping in source['maps']:
            key=(source['siegegg_match_id'],mapping['siegegg_game_id'])
            if key not in grouped:continue
            p=ROOT/'data/research/experiments/v3-normalized'/f'{key[0]}-{key[1]}.json'
            match=Match.from_dict(json.loads(p.read_text(encoding='utf-8')))
            original=Match.from_dict(json.loads((ROOT/'data/research/derived'/f"{mapping['folder']}.json").read_text(encoding='utf-8')))
            physical=physical_mapping(source,mapping,original)
            if any('filename' not in r for r in physical):
                for r in physical:r['filename']=f"{r['folder']}-R{r['physical_number']:02d}.rec"
            yield dict(event=grouped[key][0]['event'],key=f'{key[0]}-{key[1]}',match=match,rows=grouped[key],physical=physical,
                objective_complete=all(r['objective_map_complete'] for r in grouped[key]),inputs={p.relative_to(ROOT).as_posix():sha(p)})
    for dirname in ('v3-final-apac-n-stage2','v3-corrected-final-sal-stage2'):
        root=ROOT/'data/research'/dirname
        result=json.loads((root/'one-shot-result.json').read_text(encoding='utf-8'))
        seal=json.loads((root/'prelabel-quality-seal.json').read_text(encoding='utf-8'))
        for s in seal['matches']:
            directory=root/str(s['official_match_id']);predpath=directory/'replay-predictions.json'
            expected=s.get('hashes',{})
            if sha(predpath)!=expected.get('predictions',s.get('prediction_sha256')):raise ValueError('Historical prediction seal differs')
            qualities=[p for p in directory.glob('quality*.json') if (source_sha(p) if 'apac' in dirname else sha(p))==expected.get('quality',s.get('quality_sha256'))]
            if not qualities:raise ValueError('Original final quality seal missing')
            # Some pre-label implementation revisions saved byte-identical
            # decisions at multiple filenames. Their sealed content is the
            # identity; do not select a different decision based on eligibility.
            if any(json.loads(p.read_text(encoding='utf-8')) != json.loads(qualities[0].read_text(encoding='utf-8')) for p in qualities):
                raise ValueError('Multiple differing decisions match original seal')
            qualities=[sorted(qualities)[0]]
            quality=json.loads(qualities[0].read_text(encoding='utf-8'))
            api=directory/'siegegg-api-sealed.json';target=directory/'siegegg-player-stats-sealed.json'
            if sha(api)!=quality['api_sha256'] or sha(target)!=quality['target_stats_sha256']:raise ValueError('Historical target seal differs')
            prediction=json.loads(predpath.read_text(encoding='utf-8'));targets=json.loads(target.read_text(encoding='utf-8'))
            gid=quality['game_id'];rows=[]
            for d in quality['decisions']:
                p=next(p for p in prediction['players'] if p['player']==d['player'])
                public=targets[str(gid)].get(str(d.get('player_id')))
                rows.append(dict(event=result['event'],match_id=prediction['siegegg_match_id'],game_id=gid,map=prediction['map'],
                    player=p['player'],player_id=d.get('player_id'),roster_id=d.get('roster_id'),rating=float(public['rating']) if public else None,
                    public=public,rounds=p['rounds'],derived=p['derived'],quality_issues=d['issues'],
                    identity_known=public is not None,fit_eligible=d['eligible']))
            yield dict(event=result['event'],key=f"{prediction['siegegg_match_id']}-{gid}",match=Match.from_dict(prediction['normalized']),
                rows=rows,physical=prediction['physical_mapping'],objective_complete=prediction['objective_complete'],
                inputs={p.relative_to(ROOT).as_posix():sha(p) for p in (predpath,qualities[0],api,target,root/'one-shot-result.json')})


def main():
    subprocess.run([sys.executable,str(ROOT/'research/verify_production_kill_checkpoint.py')],check=True)
    inventory=list(map_inputs())
    if len({m['key'] for m in inventory})!=len(inventory):raise ValueError('Duplicate professional map')
    reservation=dict(base_commit='b1023d4',plan_sha256=source_sha(ROOT/'research/v3-credited-development-plan.json'),
        source_sha256=source_sha(Path(__file__)),maps=[dict(key=m['key'],event=m['event'],inputs=m['inputs']) for m in inventory],
        counter_binary_sha256=sha(EXE),rating_final_targets_used=False)
    immutable_write(DATA/'reservation.json',reservation)
    files=defaultdict(list)
    for p in (ROOT/'data/research/extracted').rglob('*.rec'):files[(p.parent.name,p.name)].append(p)
    index=cached_index();all_rows=[];maps=[]
    for m in inventory:
        cache=DATA/'maps'/(m['key']+'.json')
        if cache.exists():
            result=json.loads(cache.read_text(encoding='utf-8'));all_rows+=result['rows'];maps.append(result['summary']);continue
        records=[];inputs=dict(m['inputs'])
        for source in m['physical']:
            n=source.get('physical_round',source.get('physical_number'));logical=source.get('logical_round',source.get('logical_number'))
            choices=files[source['folder'],source['filename']]
            if not choices:raise ValueError('Cached physical source missing')
            digests={sha(p):p for p in choices}
            expected=source.get('sha256')
            if expected is None and len(digests)!=1:raise ValueError('Ambiguous unsealed physical replay')
            digest=expected or next(iter(digests));rec=digests[digest]
            if index.get(digest):
                obs_path,obs=cached_observation(index,digest);inputs[obs_path.relative_to(ROOT).as_posix()]=sha(obs_path)
            else:
                obs_path=DATA/'raw'/(digest+'.json')
                if obs_path.exists():obs=json.loads(obs_path.read_text(encoding='utf-8'))
                else:
                    run=subprocess.run([str(EXE),str(rec)],capture_output=True,text=True,check=True)
                    obs=json.loads(run.stdout);obs.update(replay_sha256=digest,executable_sha256=sha(EXE))
                    immutable_write(obs_path,obs)
                if obs['replay_sha256']!=digest or obs['executable_sha256']!=sha(EXE):raise ValueError('Counter observer provenance differs')
                inputs[obs_path.relative_to(ROOT).as_posix()]=sha(obs_path)
            records.append(dict(logical_round=logical,physical_round=n,segment=source['folder'],credit=obs['credit']))
        credit=validate_map_credit(records)
        counts=bind_lan_counts(m['match'],credit) if credit['complete'] else None
        rows=[]
        for prior in m['rows']:
            row=deepcopy(prior);player=next(p for p in m['match'].rounds[0].players if p.username==row['player'])
            verified=player_rounds(m['match'],player.key);new=deepcopy(verified)
            if counts is not None:
                for r in new:
                    r['kills']=counts[r['number']][player.key]
                    r['kost_rounds']=int(bool(r['kills'] or r['plants'] or r['disables'] or r['survived'] or r['deaths_traded']))
            issues=[i for i in row['quality_issues'] if i not in ('kills/deaths mismatch','Exact K/D mismatch')]
            if counts is None:issues.append('Whole map lacks complete credited counters')
            if not m['objective_complete']:issues.append('Whole map has unresolved core objective actor')
            public=row['public'];kd=re.fullmatch(r'(\d+)-(\d+)(?:\s+\([+-]?\d+\))?',public['kd']) if public else None
            if not kd or tuple(map(int,kd.groups()))!=(sum(r['kills'] for r in new),sum(r['deaths'] for r in new)):
                issues.append('Corrected exact K/D mismatch')
            if public is None or public['rounds']!=len(new):issues.append('Exact rounds mismatch')
            row.update(rounds=new,original_v2_rounds=prior.get('paired_v2_rounds',prior['rounds']),quality_issues=sorted(set(issues)),fit_eligible=not issues,
                reserved_for_final_test=False,consumed_development=True,credited_map_complete=credit['complete'],
                objective_map_complete=m['objective_complete'],kill_credit_affected=any(a['kills']!=b['kills'] for a,b in zip(verified,new)),
                credited_count_source=SOURCE if credit['complete'] else None,baseline_contract='original_cached_v2_compatible_rounds',
                operator_unresolved_rounds=sum(r['operator']=='Unknown' for r in new))
            rows.append(row)
        summary=dict(key=m['key'],event=m['event'],map=m['match'].map_name,rounds=len(m['match'].rounds),rows=len(rows),
            clean_rows=sum(r['fit_eligible'] for r in rows),credited_complete=credit['complete'],objective_complete=m['objective_complete'],
            credit_issues=credit['issues'],credit_resets=credit['resets'],inputs=inputs)
        immutable_write(cache,dict(rows=rows,summary=summary));all_rows+=rows;maps.append(summary)
        print(m['key'],m['event'],summary['clean_rows'],'/10 credit',credit['complete'],'objective',m['objective_complete'],flush=True)
    immutable_write(DATA/'dataset.json',dict(rows=all_rows,maps=maps,reservation_sha256=sha(DATA/'reservation.json')))
    print('DEVELOPMENT INVENTORY',len(maps),len(all_rows),'clean',sum(r['fit_eligible'] for r in all_rows),
          Counter(r['event'] for r in all_rows if r['fit_eligible']),flush=True)
    subprocess.run([sys.executable,str(ROOT/'research/verify_production_kill_checkpoint.py')],check=True)


if __name__=='__main__':main()
