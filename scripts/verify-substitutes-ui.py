"""Read-only production and intercepted substitute-fixture browser verification."""
import argparse
from copy import deepcopy
import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading

from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    return json.loads((ROOT/'web/public/data'/name).read_text(encoding='utf8'))


def verify(url, output):
    output.mkdir(parents=True, exist_ok=True)
    checks, errors = [], []
    index = load('index.json')
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=True)
        context = browser.new_context(viewport={'width':1440,'height':960})
        page = context.new_page()
        page.on('pageerror', lambda e:errors.append(str(e)))
        page.add_init_script("localStorage.setItem('necc-season','career')")
        page.goto(url+'#/players', wait_until='networkidle')
        expect(page.get_by_label('Statistics period')).to_have_value(index['active_season'])
        expect(page.get_by_label('Team', exact=True)).to_have_value('blue')
        expect(page.get_by_role('button', name='Roster', exact=True)).to_have_attribute('aria-pressed','true')
        for width in (1440,1100,768,390):
            page.set_viewport_size({'width':width,'height':960})
            for team in ('blue','white'):
                for role in ('roster','subs'):
                    page.goto(url+f'#/players?team={team}'+('&players=subs' if role=='subs' else ''),wait_until='networkidle')
                    expect(page.get_by_role('button',name='Subs' if role=='subs' else 'Roster',exact=True)).to_have_attribute('aria-pressed','true')
                    data=load(f'teams/{team}/{index["active_season"]}.json')
                    count=len(data['players' if role=='roster' else 'sub_players'])
                    expect(page.locator('.mobile-player' if width<=540 else 'tbody tr')).to_have_count(count)
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),(width,team,role)
                    page.screenshot(path=str(output/f'{team}-{role}-{width}.png'),full_page=True)
            page.goto(url+'#/players/lgon',wait_until='networkidle')
            expect(page.locator('.trend-point')).to_have_count(3)
            expect(page.get_by_role('link',name='View Sub Stats')).to_have_count(0)
        page.goto(url+'#/players?team=blue',wait_until='networkidle')
        page.get_by_label('Statistics period').select_option('career')
        page.get_by_role('button',name='Subs',exact=True).click()
        page.get_by_label('Team',exact=True).select_option('white')
        expect(page).to_have_url(url+'#/players?team=white&players=subs')
        expect(page.get_by_label('Statistics period')).to_have_value('career')
        page.reload(wait_until='networkidle')
        expect(page.get_by_label('Statistics period')).to_have_value('career')
        page.get_by_role('button',name='Roster',exact=True).click()
        expect(page).to_have_url(url+'#/players?team=white')
        page.go_back(wait_until='networkidle')
        expect(page.get_by_role('button',name='Subs',exact=True)).to_have_attribute('aria-pressed','true')
        fresh=browser.new_page()
        fresh.add_init_script("localStorage.setItem('necc-season','career');sessionStorage.setItem('necc-period-session',JSON.stringify({period:'career',at:Date.now()-86400000}))")
        fresh.goto(url+'#/players',wait_until='networkidle')
        expect(fresh.get_by_label('Statistics period')).to_have_value(index['active_season'])
        fresh.close()
        checks.append('real Blue/White Roster/Subs, 1440/1100/768/390, default active season despite old saved Career, session refresh/history and expired session')

        # Synthetic public responses use the real frontend without writing any
        # production JSON, database rows or cloud submissions.
        fixture=context.new_page();fixture.on('pageerror',lambda e:errors.append(str(e)))
        profile=load('players/lgon/fall-2026.json')
        sub={**deepcopy(profile),'slug':'sub-only','name':'Fixture Substitute','appearance_role':'sub',
             'team_slug':'white','team_name':'UAH White','season':'fall-2026','matches':[dict(profile['matches'][0],team_slug='white',team_name='UAH White')]}
        normal={**deepcopy(sub),'rounds':0,'maps':0,'rating':None,'matches':[],'series_ratings':[],
                'memberships':[],'team_splits':[],
                'sub_teams':[{'team_slug':'white','team_name':'UAH White','maps':1,'rounds':10,'rating':sub['rating']},
                             {'team_slug':'blue','team_name':'UAH Blue','maps':2,'rounds':20,'rating':sub['rating']} ]}
        fixture.route('**/data/players/sub-only/*.json', lambda r:r.fulfill(json={**normal,'season':Path(r.request.url).stem}))
        fixture.route('**/data/players/sub-only/subs/*/*.json',lambda r:r.fulfill(json={**sub,'team_slug':r.request.url.split('/')[-2], 'season':Path(r.request.url).stem}))
        white=load('teams/white/fall-2026.json')
        fixture.route('**/data/teams/white/*.json',lambda r:r.fulfill(json={**white,'slug':Path(r.request.url).stem,'maps':1,'matches':sub['matches'],'sub_players':[sub]}))
        series=load('series/40bf93b16f97.json');series['players'].append(sub)
        fixture.route('**/data/series/40bf93b16f97.json',lambda r:r.fulfill(json=series))
        for width in (1440,1100,768,390):
            fixture.set_viewport_size({'width':width,'height':960})
            fixture.goto(url+'#/players?team=white&players=subs',wait_until='networkidle')
            expect(fixture.locator('.mobile-player' if width<=540 else 'tbody tr')).to_have_count(1)
            expect(fixture.locator('.sub-badge').filter(visible=True)).to_have_count(1)
            fixture.goto(url+'#/players/sub-only',wait_until='networkidle')
            expect(fixture.locator('.trend-point')).to_have_count(0)
            fixture.get_by_role('link',name='View Sub Stats').click()
            expect(fixture.locator('.heading')).to_contain_text('SUBSTITUTE STATS')
            expect(fixture.get_by_label('Substitute team')).to_have_value('white')
            fixture.get_by_label('Substitute team').select_option('blue')
            expect(fixture.get_by_label('Substitute team')).to_have_value('blue')
            expect(fixture.locator('.trend-point')).to_have_count(0)
            assert fixture.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),('sub-profile',width)
            fixture.screenshot(path=str(output/f'sub-profile-{width}.png'),full_page=True)
            fixture.goto(url+'#/series/40bf93b16f97',wait_until='networkidle')
            expect(fixture.locator('.sub-badge').filter(visible=True)).to_have_count(1)
        fixture.unroute('**/data/teams/white/*.json')
        fixture.route('**/data/teams/white/*.json',lambda r:r.fulfill(json={**white,'slug':Path(r.request.url).stem,'roster':[{'slug':'unused','name':'Unused Eligible Player','status':'Active'}]}))
        fixture.goto(url+'#/players?team=white&players=subs',wait_until='networkidle')
        expect(fixture.locator('main')).not_to_contain_text('Unused Eligible Player')
        checks.append('intercepted sub-only profile, per-team Subs totals/selector and Series SUB badge at all four widths; no production fixture data')
        for team in ('blue','white'):
            page.goto(url+f'#/embed/{team}/player-stats',wait_until='networkidle')
            expect(page.locator('tbody tr')).to_have_count(len(load(f'teams/{team}/{index["active_season"]}.json')['players']))
            expect(page.locator('.appearance-switch')).to_have_count(0)
        page.goto(url+'#/submit',wait_until='networkidle')
        expect(page.locator('h1')).to_contain_text('Submit')
        checks.append('Blue/White read-only embeds and public Submit Replays shell preserved')
        assert not errors,errors
        browser.close()
    report={'status':'PASS','url':url,'checks':checks,'javascript_errors':errors}
    (output/'substitutes-ui.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--url');ap.add_argument('--output',type=Path,default=ROOT/'data/research/substitutes-20261007/browser');args=ap.parse_args()
    if args.url:verify(args.url,args.output)
    else:
        handler=functools.partial(SimpleHTTPRequestHandler,directory=str(ROOT/'web/dist'))
        server=ThreadingHTTPServer(('127.0.0.1',0),handler);threading.Thread(target=server.serve_forever,daemon=True).start()
        try:verify(f'http://127.0.0.1:{server.server_port}/',args.output)
        finally:server.shutdown();server.server_close()
