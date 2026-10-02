"""Reserve six ungraded actor maps from cached SLC/EWC archives, metadata only."""
from collections import defaultdict
import hashlib
import json

from objective_production_check import candidate_raw
from objective_transition_probe import ROOT


SPECS = [
    (3554,6678,'Bank',None),(3554,6679,'Chalet',None),
    (3563,6674,'Chalet','2. Chalet'),
    (6156,10424,'Nighthaven Labs','1 - Nighthaven Labs'),
    (6157,10427,'Bank','1 - Bank'),(6157,10429,'Fortress','3 - Fortress'),
]


def main():
    sources = json.loads((ROOT/'research/sources.json').read_text())['matches']
    prior = defaultdict(set)
    for source in sources:
        for name,pid in source.get('players',{}).items():
            prior[name.casefold()].add(pid)
    consumed = set()
    for name in ('development','extension'):
        for r in json.loads((ROOT/f'data/research/diagnostics/objective-score-structure-{name}.json').read_text()):
            consumed.add(r['folder'])
    for path in ('objective-actor-reserve.json','objective-si-final-reserve.json'):
        for m in json.loads((ROOT/'research'/path).read_text())['maps']:
            consumed.update(s['folder'] for s in m['physical_segments'])
    maps,excluded,aliases = [],[],defaultdict(dict)
    for mid,gid,label,parent in SPECS:
        source = next(s for s in sources if s.get('siegegg_match_id')==mid)
        meta = json.loads((ROOT/f'data/research/targets/siegegg-match-{mid}-api.json').read_text())
        game = next(g for g in meta['games'] if g['id']==gid)
        # Only map/score/roster fields are accessed, never game['rounds'].
        public_ids = {p['id'] for p in meta['players']}
        by_pid = {p['id']:p['roster_id'] for p in meta['players']}
        canonical = defaultdict(set)
        for p in meta['players']:
            for field in ('ign','stylized_name'):
                if p.get(field):
                    canonical[p[field].casefold()].add(p['id'])
        expected = {game['win_roster_id']:game['win_score'],game['loss_roster_id']:game['loss_score']}
        order = sorted(expected)
        extraction = ROOT/'data/research/extracted'/source.get('extraction_label',source['label'])
        if parent:
            folders = sorted({p.parent for p in extraction.rglob('*-R01.rec') if p.parent.parent.name==parent})
        else:
            mapping = next(m for m in source['maps'] if m['siegegg_game_id']==gid)
            folders = [next(p for p in extraction.rglob(mapping['folder']) if p.is_dir())]
        if not folders or any(p.name in consumed for p in folders):
            raise ValueError('Missing or already actor-consumed physical map')
        last = [0,0]
        segments,files = [],[]
        for folder in folders:
            raw = candidate_raw(folder)
            recs = sorted(folder.glob('*.rec'))
            if len(raw['rounds'])!=len(recs):
                raise ValueError('Physical/parser row count mismatch')
            included = []
            for rec,round_ in zip(recs,raw['rounds']):
                header = round_.get('header',round_)
                delta = [t['score']-t['startingScore'] for t in header['teams']]
                if sorted(delta)!=[0,1]:
                    excluded.append(dict(folder=folder.name,filename=rec.name,reason='no_unique_completed_score_increment'))
                    continue
                for player in header['players']:
                    name = player['username']
                    pid = source.get('players',{}).get(name)
                    if pid not in public_ids:
                        choices = (canonical[name.casefold()] | prior[name.casefold()]) & public_ids
                        if len(choices)!=1:
                            raise ValueError('Alias needs independent review: '+name)
                        pid = next(iter(choices))
                    aliases[str(mid)][name]=pid
                physical_rosters = []
                for index in (0,1):
                    players = [p for p in header['players'] if p['teamIndex']==index]
                    rosters = {by_pid[aliases[str(mid)][p['username']]] for p in players}
                    if len(players)!=5 or len(rosters)!=1:
                        raise ValueError('Incomplete/mixed physical team roster')
                    physical_rosters.append(next(iter(rosters)))
                start,end = [None,None],[None,None]
                for index,roster in enumerate(physical_rosters):
                    target = order.index(roster)
                    start[target]=header['teams'][index]['startingScore']
                    end[target]=header['teams'][index]['score']
                if start!=last:
                    raise ValueError(f'Rehost chronology differs: {mid}/{gid} {rec.name} {start} expected {last}')
                last=end
                included.append(rec.name)
                files.append(dict(folder=folder.name,filename=rec.name,sha256=hashlib.sha256(rec.read_bytes()).hexdigest()))
            segments.append(dict(folder=folder.name,included_round_files=included))
        if last!=[expected[r] for r in order] or len(files)!=sum(expected.values()):
            raise ValueError('Completed map differs from official final score')
        maps.append(dict(match_id=mid,game_id=gid,event=source['event'],map=label,rounds=len(files),
                         expected_score_by_roster={str(r):expected[r] for r in order},
                         logical_folder=f'actor-cached-map-{gid}',physical_segments=segments,exact_replay_sha256=files,
                         official_page=source['official_page'] if 'official_page' in source else source['archive_reference_page'],
                         archive_url=source['archive_url']))
        print('reserved metadata',mid,gid,label,len(files),'completed rounds',len(segments),'segments',flush=True)
    result = dict(status='reserved_actor_labels_ungraded',candidate='unchanged cd28f76; independent-sole wrapper NOT used',
                  independence_scope='Actor labels ungraded. Prior K/D, multikill and occurrence metadata may have been examined. Same studied SLC/EWC events; not new event-disjoint Rating data.',
                  maps=maps,player_aliases_by_match=dict(aliases),excluded_incomplete_rounds=excluded,
                  public_round_events_used=False,actor_labels_opened=False)
    path = ROOT/'research/objective-cached-map-reserve.json'
    if path.exists():
        raise ValueError('Existing reserve must not be overwritten')
    path.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('reserved total',len(maps),sum(m['rounds'] for m in maps),'excluded incomplete',len(excluded))


if __name__=='__main__':
    main()
