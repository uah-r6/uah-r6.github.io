"""Prepare unused SI series metadata; never inspect public round actor labels."""
from collections import Counter
import json
import subprocess

from objective_production_check import candidate_raw
from objective_transition_probe import ROOT


def main():
    cache = ROOT/'data/research/diagnostics/si-final-acquisition'
    path = ROOT/'data/research/targets/siegegg-match-3173-api.json'
    if not path.exists():
        partial = path.with_suffix('.json.partial')
        subprocess.run(['curl.exe','--fail','--location','--retry','3','--output',str(partial),
                        'https://siege.gg/api/stats/matches/3173'],check=True)
        partial.replace(path)
    public = json.loads(path.read_text())
    safe = dict(match_id=3173,game_schema=sorted(public['games'][0]),
                games=[{k:g[k] for k in ('id','map','map_name','team_1_score','team_2_score','team1_score','team2_score','scores') if k in g}
                       for g in public['games']],
                players=[{k:p[k] for k in ('id','ign','stylized_name') if k in p} for p in public['players']])
    (cache/'public-metadata-only.json').write_text(json.dumps(safe,indent=2))
    print('Public metadata only:',json.dumps(safe),flush=True)
    extraction = ROOT/'data/research/extracted/actor-si-final-2026-02-15'
    folders = sorted({p.parent for p in extraction.rglob('*.rec')})
    reports = []
    for folder in folders:
        raw = candidate_raw(folder)
        records = []
        files = sorted(folder.glob('*.rec'))
        if len(files)!=len(raw['rounds']):
            raise ValueError('Physical file/parser row alignment changed')
        for rec,row in zip(files,raw['rounds']):
            header = row.get('header',row)
            teams = header['teams']
            deltas = [t['score']-t['startingScore'] for t in teams]
            completed = sorted(deltas)==[0,1]
            # Neither round actor labels nor candidate actor outcomes accessed.
            records.append(dict(filename=rec.name,completed=completed,start=[t['startingScore'] for t in teams],
                                end=[t['score'] for t in teams],map=header.get('map'),build=header['codeVersion'],
                                players=[dict(username=p['username'],numeric_uid=p['id'],team=p['teamIndex']) for p in header['players']]))
        result = dict(folder=folder.name,relative_folder=str(folder.relative_to(extraction)),
                      completed_rounds=sum(r['completed'] for r in records),rounds=records)
        (cache/(folder.name+'-metadata.json')).write_text(json.dumps(result,indent=2))
        reports.append(result)
        print(folder.name,'completed',result['completed_rounds'],'physical',len(records),
              'builds',dict(Counter(r['build'] for r in records)),'maps',str(records[0]['map']),
              'roster',[p['username'] for p in records[0]['players']],flush=True)
    (cache/'replay-metadata-only.json').write_text(json.dumps(reports,indent=2))


if __name__=='__main__':
    main()
