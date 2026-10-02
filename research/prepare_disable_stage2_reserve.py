"""Reserve all cached NAL Stage2 maps for new actor labels, metadata only.

Their Rating data and limited objective totals were already examined. No round
actor labels or new timer-owner proposals are read by this preparer.
"""
import hashlib
import json

from objective_production_check import candidate_raw
from objective_transition_probe import ROOT
from uah_guarded_actor_readonly import snapshot


def main():
    destination=ROOT/'research/objective-disable-stage2-reserve.json'
    if destination.exists():
        raise ValueError('Existing prospective reserve cannot be overwritten')
    protected=snapshot()
    sources=json.loads((ROOT/'research/sources.json').read_text(encoding='utf-8'))['matches']
    selected=[s for s in sources if s['event']=='North America League Stage 2 2026']
    if {s['siegegg_match_id'] for s in selected}!={6168,6169,6170,6172,6173,6174,6175}:
        raise ValueError('Complete preselected seven-map cached set differs')
    consumed=json.loads((ROOT/'data/research/diagnostics/player-component-fields/disable-owner-consumed-result.json').read_text(encoding='utf-8'))
    used={r['folder'] for r in consumed['records']}
    aliases,maps={},[]
    for source in sorted(selected,key=lambda s:s['siegegg_match_id']):
        mid=source['siegegg_match_id']
        target=json.loads((ROOT/f'data/research/targets/siegegg-match-{mid}-api.json').read_text(encoding='utf-8'))
        # Only cached map, score and roster metadata; NEVER game['rounds'] or
        # target objective actors/player statistics during prospective choice.
        public_players={p['id']:p for p in target['players']}
        aliases[str(mid)]=source['players']
        for mapping in source['maps']:
            gid=mapping['siegegg_game_id']
            games=[g for g in target['games'] if g['id']==gid]
            if len(games)!=1: raise ValueError('Ambiguous target game')
            game=games[0]
            expected={game['win_roster_id']:game['win_score'],game['loss_roster_id']:game['loss_score']}
            order=sorted(expected)
            folder_name=mapping['folder']
            if folder_name in used: raise ValueError('Previously actor-consumed folder')
            folders=[p for p in (ROOT/'data/research/extracted').rglob(folder_name) if p.is_dir()]
            if len(folders)!=1: raise ValueError('Ambiguous cached physical map')
            folder=folders[0]
            parsed=candidate_raw(folder)
            files=sorted(folder.glob('*.rec'))
            if len(files)!=len(parsed['rounds']): raise ValueError('Parser/physical round count differs')
            last=[0,0]
            included,builds=[],set()
            for file,raw in zip(files,parsed['rounds']):
                header=raw.get('header',raw)
                physical=int(file.stem.rsplit('-R',1)[1])
                if physical!=len(included)+1: raise ValueError('Physical round ordering is not contiguous')
                delta=[t['score']-t['startingScore'] for t in header['teams']]
                if sorted(delta)!=[0,1]: raise ValueError('Incomplete physical round refused')
                roster=[]
                for index in (0,1):
                    players=[p for p in header['players'] if p['teamIndex']==index]
                    ids=[source['players'].get(p['username']) for p in players]
                    if len(players)!=5 or len(set(ids))!=5 or any(pid not in public_players for pid in ids):
                        raise ValueError('Incomplete verified alias roster')
                    team_ids={public_players[pid]['roster_id'] for pid in ids}
                    if len(team_ids)!=1: raise ValueError('Mixed team roster')
                    roster.append(next(iter(team_ids)))
                start,end=[None,None],[None,None]
                for index,rid in enumerate(roster):
                    target_index=order.index(rid)
                    start[target_index]=header['teams'][index]['startingScore']
                    end[target_index]=header['teams'][index]['score']
                if start!=last: raise ValueError('Score chronology differs')
                last=end
                builds.add(header['codeVersion'])
                included.append(dict(folder=folder_name,filename=file.name,physical_round=physical,
                                     logical_round=physical,sha256=hashlib.sha256(file.read_bytes()).hexdigest()))
            if last!=[expected[rid] for rid in order] or len(included)!=sum(expected.values()):
                raise ValueError('Complete cached map does not match public score')
            maps.append(dict(match_id=mid,game_id=gid,event=source['event'],folder=folder_name,
                map=game['map'],rounds=len(included),builds=sorted(builds),exact_replay_sha256=included,
                expected_score_by_roster={str(k):v for k,v in expected.items()},
                official_page=source.get('official_page',source.get('archive_reference_page'))))
            print('reserved metadata',mid,gid,game['map'],len(included),'rounds',sorted(builds),flush=True)
    if snapshot()!=protected: raise ValueError('Protected live files changed')
    reservation=dict(status='prospective_actor_labels_sealed',candidate='disable-only direct owner hypothesis',
        event='North America League Stage 2 2026',maps=maps,player_aliases_by_match=aliases,
        actor_labels_opened=False,round_events_used=False,
        independence_scope='New actor-label validation only. Rating data permanently consumed in earlier research; '
                           'limited map objective totals were inspected earlier. Cached source replay and public targets '
                           'are reused; no new actor labels or proposed owners inspected during reservation. Not a fresh Rating event.',
        selection_rule='All seven cached maps from this event; no selection by actor outcome or objective presence',
        protected_files_checked=len(protected))
    destination.write_text(json.dumps(reservation,indent=2)+'\n',encoding='utf-8')
    print('RESERVED',len(maps),'maps',sum(m['rounds'] for m in maps),'rounds, labels sealed',flush=True)


if __name__=='__main__':
    main()
