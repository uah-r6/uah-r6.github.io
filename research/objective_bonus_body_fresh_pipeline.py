"""Cached ASIA actor-only acquisition; no labels before the complete seal."""
import argparse
from collections import Counter
from datetime import datetime, timezone
from dataclasses import asdict
import json
from pathlib import Path
import shutil
from urllib.parse import urlparse, unquote
import zipfile

from objective_bonus_body_candidate import candidate as proposed
from objective_plant_owner_candidate import candidate as original
from objective_completer_consumed_audit import observation
from objective_player_component_fields import observe
from objective_actor_liveness import feedback
from objective_production_check import candidate_raw
from objective_bonus_body_reserve import RESERVE, FREEZE
from r6stats.parser.siege_dissect import normalize, physical_round_numbers
from uah_guarded_actor_readonly import snapshot
from v3_final_pipeline import cache_url
from v3_final_reserve import ROOT, sha, source_sha

DATA = ROOT/'data/research/objective-bonus-body-asia'
SEAL = DATA/'prelabel-prediction-seal.json'


def verify():
    frozen = json.loads(FREEZE.read_text(encoding='utf-8'))
    if source_sha(RESERVE) != frozen['reservation_sha256']: raise ValueError('Actor reservation changed')
    for name, digest in frozen['source_hashes'].items():
        if source_sha(ROOT/name) != digest: raise ValueError('Frozen actor source changed:'+name)
    for name, digest in frozen['binary_hashes'].items():
        if sha(ROOT/name) != digest: raise ValueError('Frozen observer binary changed:'+name)
    if snapshot() != frozen['protected_hashes']: raise ValueError('Protected live file changed')
    return frozen, json.loads(RESERVE.read_text(encoding='utf-8'))


def chronology(items, official_scores):
    """Complete BO1 score path and stable profiles, independent of actor outcomes."""
    canonical = None; last = [0,0]; completed = []; excluded = []; map_name = None
    seen_sources = set()
    for item in sorted(items, key=lambda x:(x['folder'],x['physical_round'])):
        if item['sha256'] in seen_sources: raise ValueError('Duplicate physical round source')
        seen_sources.add(item['sha256'])
        h = item['header']; people = item['players']
        groups = [tuple(sorted(p['profile_id'] for p in people if p['team']==i)) for i in (0,1)]
        if (len(people)!=10 or any(len(g)!=5 for g in groups) or
            len(set(sum((list(g) for g in groups),[])))!=10 or
            any(not p['profile_id'] or p['profile_id']=='00000000-0000-0000-0000-000000000000' for p in people) or
            len({p['username'] for p in people})!=10 or
            len({p.get('id') for p in h['players']})!=10 or any(not p.get('id') for p in h['players'])):
            raise ValueError('Full distinct stable10-player profiles and round UIDs required')
        if canonical is None: canonical = sorted(groups)
        if sorted(groups)!=canonical: raise ValueError('Rehost profile roster changed')
        if map_name is None: map_name = item['map']
        if item['map'] != map_name: raise ValueError('BO1 map changed across physical fragments')
        remap = {i:canonical.index(groups[i]) for i in (0,1)}
        start = [0,0]; end = [0,0]; teams = [None,None]
        for i,t in enumerate(h['teams']):
            start[remap[i]]=t['startingScore']; end[remap[i]]=t['score']; teams[remap[i]]=t
        delta = [e-s for s,e in zip(start,end)]
        if delta == [0,0]:
            excluded.append({k:item[k] for k in ('folder','filename','physical_round','sha256')} |
                            dict(reason='Explicit zero score increment; unfinished physical attempt'))
            continue
        if sorted(delta)!=[0,1] or start!=last: raise ValueError('Incomplete/discontinuous completed score path')
        completed.append(item | dict(logical_round=len(completed)+1, start=start, end=end,
            canonical_teams=teams, winner=delta.index(1),
            canonical_players=[p|dict(team=remap[p['team']]) for p in people]))
        last=end
    if not completed or len(official_scores)!=1 or sorted(last)!=official_scores[0] or sum(last)!=len(completed):
        raise ValueError('Official complete BO1 score/count differs')
    return completed, excluded, canonical, last


def acquire(source, frozen):
    mid=source['official_match_id']; out=DATA/str(mid); out.mkdir(parents=True,exist_ok=True)
    path=out/'replay-predictions.json'
    if path.exists():
        saved=json.loads(path.read_text(encoding='utf-8'))
        if saved['freeze_sha256']!=source_sha(FREEZE): raise ValueError('Prediction cache freeze differs')
        for r in saved['rounds']:
            rec=ROOT/r['replay_path']
            if sha(rec)!=r['replay_sha256']: raise ValueError('Cached fresh physical replay changed')
        return saved
    archive=ROOT/'data/research/pro-replays'/unquote(Path(urlparse(source['archive_url']).path).name)
    cache_url(source['archive_url'],archive)
    extraction=ROOT/f'data/research/extracted/bonus-body-asia-{mid}'; extraction.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(archive) as bundle:
        bad=bundle.testzip()
        if bad: raise ValueError('Archive CRC error:'+bad)
        for member in bundle.infolist():
            target=(extraction/member.filename).resolve()
            if not target.is_relative_to(extraction.resolve()): raise ValueError('Unsafe archive member')
            if member.is_dir(): target.mkdir(parents=True,exist_ok=True); continue
            if target.exists() and target.stat().st_size==member.file_size: continue
            target.parent.mkdir(parents=True,exist_ok=True)
            with bundle.open(member) as src,target.open('wb') as dst: shutil.copyfileobj(src,dst)
    prior=json.loads((ROOT/'data/research/diagnostics/bonus-body-consumed-audit/summary-all-consumed.json').read_text())
    consumed={r['replay_sha256'] for r in prior['records']}
    items=[]
    for folder in sorted({p.parent for p in extraction.rglob('*.rec')}):
        files=sorted(folder.glob('*.rec')); numbers=physical_round_numbers(files)
        if numbers!=list(range(1,len(files)+1)): raise ValueError('Physical R## sources must be contiguous')
        raw=candidate_raw(folder,ROOT/'.local-tools/bin/siege-dissect-actors.exe')
        if len(raw['rounds'])!=len(files): raise ValueError('Parser/physical count differs')
        for rec,n,row in zip(files,numbers,raw['rounds']):
            digest=sha(rec)
            if digest in consumed: raise ValueError('Previously consumed physical replay in fresh reserve')
            normalized=normalize([row],round_numbers=[n])
            items.append(dict(folder=folder.name,filename=rec.name,physical_round=n,sha256=digest,
                replay_path=str(rec.relative_to(ROOT)).replace('\\','/'),header=row.get('header',row),
                full_feedback=row['matchFeedback'],players=[asdict(p) for p in normalized.rounds[0].players],map=normalized.map_name))
    complete,excluded,canonical,score=chronology(items,source['official_scores'])
    rounds=[]
    for item in complete:
        rec=ROOT/item['replay_path']; h=item['header']
        state,owners,slots,fields=observe(rec); feed=feedback(rec)['events']
        expected=[e for e in item['full_feedback'] if e['type']['name'] in ('Kill','Death')]
        if [e['feedback'] for e in feed]!=expected: raise ValueError('Existing feedback observer differs')
        data=dict(header=h, observed=observation(h,owners,slots,fields),owners=owners,slots=slots,
                  properties=state['properties'],deaths=feed,full_feedback=item['full_feedback'])
        before=original(**data); after=proposed(**data,body_fields=fields)
        if before[0] and after!=before: raise ValueError('Already-resolved actor changed')
        occurrence=any(o['kind']=='plant' for o in h.get('objectiveOccurrences',[]))
        if after[0] and not occurrence: raise ValueError('Actor false positive without verified plant')
        rounds.append(dict(round=item['logical_round'], physical_round=item['physical_round'], folder=item['folder'],
            filename=item['filename'], replay_path=item['replay_path'],replay_sha256=item['sha256'],
            build=h['codeVersion'],players=item['canonical_players'],teams=item['canonical_teams'],winner=item['winner'],
            occurrences=h.get('objectiveOccurrences',[]),verified_plant=occurrence,
            original=dict(actor=before[0],reason=before[1],context=before[2]),
            proposed=dict(actor=after[0],reason=after[1],context=after[2])))
    record=dict(official_match_id=mid,event='ASIA Stage2 isolated actor reserve',freeze_sha256=source_sha(FREEZE),
        archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,map=complete[0]['map'],score=score,
        canonical_profile_rosters=canonical,rounds=rounds,excluded_physical_attempts=excluded,
        labels_read=False,ratings_read=False,interpretation='Prospective sealed actor proposals only; no stats/model/database correction.')
    with path.open('x',encoding='utf-8') as dst: dst.write(json.dumps(record,indent=2)+'\n')
    print('Fresh actor prediction',mid,record['map'],len(rounds),'rounds',
          'plants',sum(r['verified_plant'] for r in rounds),
          'bonus',sum(r['proposed']['actor']!=r['original']['actor'] for r in rounds),flush=True)
    return record


def seal(frozen, reservation):
    selected=[m for m in reservation['matches'] if m['selected']]
    paths=[DATA/str(m['official_match_id'])/'replay-predictions.json' for m in selected]
    if not all(p.exists() for p in paths): raise ValueError('All12 predictions required before any target actor')
    records=[json.loads(p.read_text(encoding='utf-8')) for p in paths]
    if any(r['freeze_sha256']!=source_sha(FREEZE) or r['labels_read'] for r in records): raise ValueError('Prelabel prediction contract differs')
    record=dict(status='all12_fresh_actor_predictions_sealed_before_labels',created_at=datetime.now(timezone.utc).isoformat(),
        freeze_sha256=source_sha(FREEZE),predictions={str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in paths},
        protected_hashes=frozen['protected_hashes'])
    if SEAL.exists():
        prior=json.loads(SEAL.read_text(encoding='utf-8'));record['created_at']=prior['created_at']
        if prior!=record: raise ValueError('Never overwrite changed prelabel actor seal')
    else:
        with SEAL.open('x',encoding='utf-8') as out: out.write(json.dumps(record,indent=2)+'\n')
    print('Sealed all12 before target actors:',sum(len(r['rounds']) for r in records),'rounds',flush=True)
    return record


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--limit',type=int,default=1);parser.add_argument('--seal',action='store_true');args=parser.parse_args()
    frozen,reservation=verify();selected=[m for m in reservation['matches'] if m['selected']]
    for source in selected[:args.limit]: acquire(source,frozen)
    if args.seal: seal(frozen,reservation)
    verify()


if __name__=='__main__': main()
