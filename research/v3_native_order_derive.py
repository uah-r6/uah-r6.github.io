"""Separate consumed development cohort; verify cached native order, never refit old studies."""
from collections import Counter,defaultdict
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys

from credited_late_history_development import immutable_write
from r6stats.parser.models import Match
from r6stats.stats.calculate import chronological
from v3_cnl_order_audit import ordered_states,verify_native
from v3_cnl_final import DATA as CNL,RESULT
from v3_credited_derive import DATA as PRIOR,map_inputs
from v3_final_reserve import ROOT,sha,source_sha

DATA=ROOT/'data/research/v3-native-order-development-v1'


def updated_rows(match,rows,observations):
    states={};totals=Counter()
    for r in match.rounds:
        offsets=verify_native(r,observations[r.number])
        if any(x<=0 for x in offsets):
            raise ValueError('Missing physical event offset; native ordinal not promoted without an independent offset control')
        states[r.number]=ordered_states(r)
        totals['rounds']+=1;totals['eliminations']+=len(offsets)
        totals['legacy_reordered_rounds']+=[k.sequence for k in chronological(r.kills)]!=sorted(k.sequence for k in r.kills)
    result=[]
    for prior in rows:
        row=deepcopy(prior)
        key=next(p.key for p in match.rounds[0].players if p.username==row['player'])
        row['legacy_corrected_rounds']=deepcopy(row['rounds'])
        for r in row['rounds']:
            state=states[r['number']];opening=state['opening'];clutch=state['clutch']
            r['opening_kills']=int(opening is not None and opening[0]==key)
            r['opening_deaths']=int(opening is not None and opening[1]==key)
            for x in range(1,6):r[f'clutch_1v{x}']=int(clutch is not None and clutch==(key,x))
            r['clutches']=sum(r[f'clutch_1v{x}'] for x in range(1,6))
        row.update(consumed_development=True,reserved_for_final_test=False,native_event_order_complete=True)
        result.append(row)
    return result,dict(totals)


def main():
    result_path=DATA/'dataset.json'
    if result_path.exists():raise ValueError('Native cohort already sealed; do not derive again')
    subprocess.run([sys.executable,str(ROOT/'research/verify_production_kill_checkpoint.py')],check=True)
    old=json.loads((PRIOR/'dataset.json').read_text(encoding='utf-8'))
    eligible={m['key']:m for m in old['maps'] if m['clean_rows']}
    oldrows=defaultdict(list)
    for r in old['rows']:
        if r['fit_eligible']:oldrows[f"{r['match_id']}-{r['game_id']}"].append(r)
    files=defaultdict(list)
    for p in (ROOT/'data/research/extracted').rglob('*.rec'):files[p.parent.name,p.name].append(p)
    allrows=[];reports=[];inputs={str((PRIOR/'dataset.json').relative_to(ROOT)):sha(PRIOR/'dataset.json'),str(RESULT.relative_to(ROOT)):sha(RESULT)}
    frozen=json.loads((CNL/'prelabel-quality-seal.json').read_text(encoding='utf-8'))
    cnl_rows=defaultdict(list)
    for row in frozen['rows']:cnl_rows[row['match_id'],row['game_id']].append(row)
    candidates=[]
    for m in map_inputs():
        if m['key'] not in eligible:continue
        summary=eligible[m['key']];obs_by_digest={}
        for path,digest in summary['inputs'].items():
            p=ROOT/path
            if sha(p)!=digest:raise ValueError('Sealed map input changed')
            if '/raw/' not in path and '/observations/' not in path:continue
            obs=json.loads(p.read_text(encoding='utf-8'))
            if 'credit' in obs:obs_by_digest[obs['replay_sha256']]=obs;inputs[path]=digest
        observed={}
        for physical in m['physical']:
            n=physical.get('physical_round',physical.get('physical_number'))
            logical=physical.get('logical_round',physical.get('logical_number'))
            filename=physical.get('filename',f"{physical['folder']}-R{n:02d}.rec")
            paths=files[physical['folder'],filename];hashes={sha(p):p for p in paths}
            if len(hashes)!=1:raise ValueError('Physical replay absent or ambiguous')
            digest,p=next(iter(hashes.items()));inputs[p.relative_to(ROOT).as_posix()]=digest
            observed[logical]=obs_by_digest[digest]
        candidates.append((m['key'],m['event'],m['match'],oldrows[m['key']],observed))
    for p in sorted(CNL.glob('*/prelabel-replays.json')):
        payload=json.loads(p.read_text(encoding='utf-8'));inputs[p.relative_to(ROOT).as_posix()]=sha(p)
        for m in payload['maps']:
            key=(payload['siegegg_match_id'],m['game_id'])
            if key not in cnl_rows:continue
            observed={}
            for physical in m['physical_mapping']:
                path=CNL/'raw'/(physical['sha256']+'.json')
                inputs[path.relative_to(ROOT).as_posix()]=sha(path)
                observed[physical['logical_round']]=json.loads(path.read_text(encoding='utf-8'))
            target_path=CNL/'targets'/f'{key[0]}.json';inputs[target_path.relative_to(ROOT).as_posix()]=sha(target_path)
            targets=json.loads(target_path.read_text(encoding='utf-8'));rows=deepcopy(cnl_rows[key])
            for r in rows:r.update(public=targets[str(key[1])][str(r['player_id'])],rating=float(targets[str(key[1])][str(r['player_id'])]['rating']))
            candidates.append((f'{key[0]}-{key[1]}',rows[0]['event'],Match.from_dict(m['normalized']),rows,observed))
    for key,event,match,rows,obs in candidates:
        try:
            prepared,totals=updated_rows(match,rows,obs)
            allrows+=prepared
            reports.append(dict(key=key,event=event,clean_rows=len(prepared),totals=totals))
        except ValueError as e:reports.append(dict(key=key,event=event,clean_rows=0,refusal=str(e)))
        print('NATIVE ORDER',key,reports[-1]['clean_rows'],reports[-1].get('refusal',''),flush=True)
    result=dict(rows=allrows,maps=reports,input_hashes=inputs,source_sha256=source_sha(Path(__file__)),
        prior_final_result_sha256=sha(RESULT),quality_policy='Original clean rows only; entire map refused if event parity/positive offset control fails. No public-target-dependent selection.',
        feature_policy='Credited K/MK/KOSTKill and supported objectives unchanged. Opening is explicitly native first opposing FINISHER, not inferred credited owner. Clutches use first sole-alive/native final elimination order and actual round winner. Legacy trade/KOST trade flags unchanged.',
        current_final_event_used_as_development=True,new_untouched_targets_opened=False)
    immutable_write(result_path,result)
    print('COHORT',len(allrows),'maps',sum(bool(m['clean_rows']) for m in reports),'events',len({r['event'] for r in allrows}),
        'clutch sizes',{x:sum(t[f'clutch_1v{x}'] for r in allrows for t in r['rounds']) for x in range(1,6)},flush=True)
    subprocess.run([sys.executable,str(ROOT/'research/verify_production_kill_checkpoint.py')],check=True)


if __name__=='__main__':main()
