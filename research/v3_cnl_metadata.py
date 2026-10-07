"""CNL Stage 1 schedule projection only; never request player-stat targets."""
import json
from pathlib import Path
import re
import urllib.request
import time

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/research/diagnostics/v3-event-metadata'


def fetch(url,path):
    if not path.exists():
        path.parent.mkdir(parents=True,exist_ok=True)
        request=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
        with urllib.request.urlopen(request,timeout=60) as response:path.write_bytes(response.read())
    return path.read_text(encoding='utf-8')


def official():
    text=(DATA/'competition-517-15026-sequential-discovery.html').read_text(encoding='utf-8')
    data=json.loads(re.search(r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>',text,re.S).group(1))['props']['pageProps']['pageData']
    return data,sorted([m for s in data['phaseDetails']['steps'] for m in s['matches']],key=lambda m:(m['date'],m['id']))


if __name__=='__main__':
    d,ms=official()
    print('OFFICIAL',d['competition'],len(ms),'linked',sum(bool(m.get('replayLink')) for m in ms))
    for m in ms:
        if m.get('replayLink'):print(m['id'],m['date'],[(t['id'],t.get('name')) for t in m['teams']],Path(m['replayLink']).name,[[t['score'] for t in g['teams']] for g in m['games']])
    links=set()
    for p in DATA.glob('siegegg-cnl1-*.html'):
        links.update(re.findall(r'href="(?:https://siege.gg)?(/matches/\d+-cnl-[^"?#]+)',p.read_text(encoding='utf-8')))
    for link in sorted(links):
        mid=int(link.split('/')[2].split('-')[0]);p=DATA/f'cnl1-metadata-{mid}.json'
        if mid>=4000:continue # Playoffs are outside the fixed linked group-stage snapshot.
        if not p.exists():time.sleep(3)
        try:meta=json.loads(fetch(f'https://siege.gg/api/stats/matches/{mid}',p))
        except Exception as e:print('METADATA BLOCKER',mid,str(e));continue
        if meta['competition_id']!=105:continue
        print('SGG',mid,meta['date'],[r['name'] for r in meta['rosters']],[(g['id'],g['map']['name'],g['win_score'],g['loss_score']) for g in meta['games']])
