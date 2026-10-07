"""Untouched APAC North Stage1 qualification; schedules/metadata only, no Ratings."""
import argparse
import html
import json
import re
import time

from v3_cnl_metadata import DATA,fetch


def nextdata(text):
    return json.loads(re.search(r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>',text,re.S).group(1))['props']['pageProps']['pageData']


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--competition',type=int);ap.add_argument('--pages',type=int,default=2);args=ap.parse_args()
    path=DATA/'competition-505-15000-native-final-discovery.html'
    official=nextdata(fetch('https://www.ubisoft.com/en-us/esports/rainbow-six/siege/competition/505/15000',path))
    print('OFFICIAL',json.dumps(official['competition'],ensure_ascii=True),'params',official['params'],flush=True)
    matches=sorted([m for step in official['phaseDetails']['steps'] for m in step['matches']],key=lambda m:(m['date'],m['id']))
    print('SCHEDULE',len(matches),'linked',sum(bool(m.get('replayLink')) for m in matches),flush=True)
    comp=f'competitions={args.competition}&' if args.competition is not None else ''
    links=set()
    for page in range(1,args.pages+1):
        text=fetch(f'https://siege.gg/matches?{comp}tab=results&page={page}',DATA/f'apac1-schedule-{args.competition}-{page}.html')
        options=[(m[0],html.unescape(re.sub('<[^>]+>',' ',m[1])).strip()) for m in re.findall(r'<option[^>]*value="(\d+)"[^>]*>(.*?)</option>',text,re.S)]
        print('COMPETITION OPTIONS',json.dumps([x for x in options if '2026' in x[1] and ('Asia' in x[1] or 'APAC' in x[1] or 'Pacific' in x[1])]),flush=True)
        flattened=json.loads(re.search(r'<script[^>]*id="__NUXT_DATA__"[^>]*>(.*?)</script>',text,re.S).group(1))
        sought={i for i,v in enumerate(flattened) if v=='APAC N 2026 Stage 1'}
        for value in flattened:
            if isinstance(value,dict) and any(type(v) is int and v in sought for v in value.values()):
                print('APAC1 FILTER',json.dumps({k:flattened[v] for k,v in value.items() if type(v) is int and v in sought},ensure_ascii=True),flush=True)
        for value in flattened:
            if isinstance(value,dict) and 'id' in value and 'abbreviation' in value:
                abbreviation=flattened[value['abbreviation']]
                if isinstance(abbreviation,str) and '2026' in abbreviation and 'APAC' in abbreviation:
                    print('NUXT COMPETITION',flattened[value['id']],abbreviation,flush=True)
        found=set(re.findall(r'href="(?:https://siege.gg)?(/matches/\d+-[^"?#]+)',text))
        print('SCHEDULE LINKS',len(found),sorted(found)[:2],flush=True);links|=found
    if args.competition is None:return
    for link in sorted(links):
        mid=int(link.split('/')[2].split('-')[0]);path=DATA/f'apac1-metadata-{mid}.json'
        if not path.exists():time.sleep(2)
        meta=json.loads(fetch(f'https://siege.gg/api/stats/matches/{mid}',path))
        if meta['competition_id']!=args.competition:continue
        if any(p.get('stats') is not None for p in meta['players']):raise ValueError('Metadata unexpectedly contains stats; do not project Ratings')
        print('METADATA',mid,meta['date'],[r['name'] for r in meta['rosters']],[(g['id'],g['map']['name'],g['win_score'],g['loss_score']) for g in meta['games']],flush=True)


if __name__=='__main__':main()
