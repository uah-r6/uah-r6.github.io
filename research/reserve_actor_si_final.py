"""Reserve all four SI-final maps using metadata and completed score transitions."""
import hashlib
import json

from objective_transition_probe import ROOT


def main():
    base = ROOT/'data/research/diagnostics/si-final-acquisition'
    metadata = json.loads((base/'replay-metadata-only.json').read_text())
    public = json.loads((base/'public-metadata-only.json').read_text())
    prior = json.loads((ROOT/'research/sources.json').read_text())['matches']
    known = {name.casefold():pid for s in prior for name,pid in s.get('players',{}).items()}
    canonical = {}
    for p in public['players']:
        for key in ('ign','stylized_name'):
            if p.get(key):
                canonical[p[key].casefold()]=p['id']
    aliases = {}
    replay_names = {p['username'] for m in metadata for r in m['rounds'] for p in r['players']}
    for name in sorted(replay_names):
        pid = canonical.get(name.casefold()) or known.get(name.casefold())
        if pid not in {p['id'] for p in public['players']}:
            raise ValueError('Unverified replay/player alias: '+name)
        aliases[name]=pid
    teams = [set(n.casefold() for n in ('soulz1','handyy','vitaking','cyberzera','kds')),
             set(n.casefold() for n in ('Adrian','Mowwwgli','Savage','Jume','noa'))]
    specs = [(1,5930,'Consulate',[7,4]),(2,5931,'Bank',[7,2]),(3,5932,'Fortress',[9,11]),(4,5933,'Border',[10,8])]
    maps = []
    excluded = []
    extraction = ROOT/'data/research/extracted/actor-si-final-2026-02-15'
    for number,gid,label,final in specs:
        segments = [m for m in metadata if f'GAME {number} - ' in m['relative_folder']]
        segments.sort(key=lambda s:s['folder'])
        last = [0,0]
        files = []
        physical = []
        for segment in segments:
            included = []
            for row in segment['rounds']:
                if not row['completed']:
                    excluded.append(dict(folder=segment['folder'],filename=row['filename'],reason='no_unique_physical_score_increment'))
                    continue
                permutation = []
                for index in (0,1):
                    names = {p['username'].casefold() for p in row['players'] if p['team']==index}
                    if names not in teams:
                        raise ValueError('Mixed or incomplete team roster')
                    permutation.append(teams.index(names))
                start,end = [None,None],[None,None]
                for i,target in enumerate(permutation):
                    start[target],end[target]=row['start'][i],row['end'][i]
                if start!=last:
                    raise ValueError('Rehost score chronology differs: '+str((label,start,last)))
                last=end
                included.append(row['filename'])
                rec = next(extraction.rglob(row['filename']))
                files.append(dict(folder=segment['folder'],filename=row['filename'],sha256=hashlib.sha256(rec.read_bytes()).hexdigest()))
            physical.append(dict(folder=segment['folder'],included_round_files=included))
        if last!=final or len(files)!=sum(final):
            raise ValueError('Logical map score/round count does not match official metadata')
        maps.append(dict(match_id=3173,game_id=gid,event='Six Invitational 2026',map=label,
                         rounds=len(files),expected_faze_secret_score=final,
                         logical_folder=f'actor-si-final-{gid}',physical_segments=physical,
                         exact_replay_sha256=files))
    reserve = dict(status='reserved_actor_labels_unread',purpose='further unchanged cd28f76 actor diagnostic validation',
                   candidate_freeze_commit='cd28f76c7f22b6dc76af0a8afdbebb984e5232a1',
                   source=dict(official_page='https://www.ubisoft.com/en-us/esports/rainbow-six/siege/match/7740',
                               public_match_page='https://siege.gg/matches/3173-invitational-intl-faze-clan-vs-team-secret',
                               provenance_cache='data/research/diagnostics/si-final-acquisition/provenance.json'),
                   player_aliases=aliases,
                   alias_evidence='Exact public ign/stylized names, plus pre-existing sources.json cyberzera=104 from match3554; no fuzzy or leftover-player inference',
                   maps=maps,excluded_incomplete_rounds=excluded,
                   actor_labels_opened=False,public_round_events_used=False)
    path = ROOT/'research/objective-si-final-reserve.json'
    if path.exists():
        raise ValueError('Do not overwrite an existing predeclared reserve')
    path.write_text(json.dumps(reserve,indent=2)+'\n',encoding='utf-8')
    print('reserved',len(maps),'maps',sum(m['rounds'] for m in maps),'completed rounds; excluded',excluded)


if __name__=='__main__':
    main()
