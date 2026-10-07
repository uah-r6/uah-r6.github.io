"""Read-only team leaderboard checks. Synthetic team moves never change data."""
import argparse
from copy import deepcopy
import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading

from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'web/public/data'


def load(name):
    return json.loads((DATA/name).read_text(encoding='utf-8'))


def verify(url,output):
    output.mkdir(parents=True,exist_ok=True)
    index=load('index.json');blue=load('teams/blue/fall-2026.json')
    errors,checks,requests=[],[],[]
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True)
        page=browser.new_page(viewport={'width':1440,'height':960})
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.on('request',lambda r:requests.append(r.url))
        page.goto(url+'#/players',wait_until='networkidle')
        expect(page).to_have_url(url+'#/players?team=blue')
        expect(page.get_by_label('Team',exact=True)).to_have_value('blue')
        expect(page.locator('tbody tr')).to_have_count(5)
        expect(page.locator('.heading')).to_contain_text('UAH BLUE / FALL 2026')
        assert page.title()=='UAH Blue · Player Stats | UAH R6'
        assert page.locator('.main-player-stats').evaluate("e=>e.style.getPropertyValue('--team-primary')")=='#0058A4'
        expect(page.get_by_role('navigation',name='Main navigation').get_by_role('link',name='Player Stats')).to_have_attribute('href','#/players?team=blue')
        for row,player in zip(page.locator('tbody tr').all(),blue['players']):
            expect(row.locator('td').nth(1)).to_have_text(f"{player['rating']:.2f}")
        page.get_by_role('button',name='Rating',exact=True).click()
        page.get_by_label('Team',exact=True).select_option('white')
        expect(page).to_have_url(url+'#/players?team=white')
        expect(page.get_by_text('No player statistics yet',exact=True)).to_be_visible()
        expect(page.locator('.heading')).to_contain_text('UAH WHITE / FALL 2026')
        expect(page.locator('.team-empty')).to_contain_text('approved UAH White match replays')
        expect(page.locator('tbody tr')).to_have_count(0)
        expect(page.locator('.mobile-player')).to_have_count(0)
        assert 'Lgon' not in page.locator('main').inner_text()
        assert page.title()=='UAH White · Player Stats | UAH R6'
        assert page.locator('.main-player-stats').evaluate("e=>e.style.getPropertyValue('--team-primary')")=='#E6EDF5'
        page.reload(wait_until='networkidle')
        expect(page.get_by_label('Team',exact=True)).to_have_value('white')
        page.get_by_label('Team',exact=True).select_option('blue')
        expect(page.locator('tbody tr')).to_have_count(5)
        page.go_back(wait_until='networkidle')
        expect(page.get_by_label('Team',exact=True)).to_have_value('white')
        page.go_forward(wait_until='networkidle')
        expect(page.get_by_label('Team',exact=True)).to_have_value('blue')
        page.get_by_role('button',name='Rating',exact=True).click()
        state=page.locator('th[data-stat=rating]').get_attribute('aria-sort')
        page.get_by_label('Team',exact=True).select_option('white')
        expect(page.locator('.team-empty')).to_be_visible()
        page.get_by_label('Team',exact=True).select_option('blue')
        expect(page.locator('tbody tr')).to_have_count(5)
        expect(page.locator('th[data-stat=rating]')).to_have_attribute('aria-sort',state)
        page.get_by_label('Statistics period').select_option('career')
        page.get_by_label('Team',exact=True).select_option('white')
        expect(page.get_by_label('Statistics period')).to_have_value('career')
        expect(page.locator('.heading')).to_contain_text('UAH WHITE / CAREER')
        expect(page.locator('tbody tr')).to_have_count(0)
        page.get_by_label('Team',exact=True).select_option('blue')
        expect(page.locator('tbody tr')).to_have_count(5)
        expect(page.get_by_label('Statistics period')).to_have_value('career')
        assert any('/data/teams/blue/career.json' in r for r in requests)
        assert any('/data/teams/white/career.json' in r for r in requests)
        assert not any('/data/seasons/' in r for r in requests),requests
        checks.append('actual Blue/White, exact exported Ratings, URL normalization, headings/themes/titles, refresh/back/forward, preserved sorting and Career with no program data fetch')

        for width in (1440,1150,768,390):
            page.set_viewport_size({'width':width,'height':960})
            page.get_by_label('Statistics period').select_option('fall-2026')
            for slug in ('blue','white'):
                page.goto(url+'#/players?team='+slug,wait_until='networkidle')
                expect(page.get_by_label('Team',exact=True)).to_have_value(slug)
                if slug=='blue':
                    expect(page.locator('.mobile-player' if width<=540 else 'tbody tr')).to_have_count(5)
                    page.get_by_role('button',name='About KOST',exact=True).filter(visible=True).first.click()
                    expect(page.get_by_role('dialog',name='KOST explained')).to_be_visible()
                    page.keyboard.press('Escape')
                else:
                    expect(page.locator('tbody tr,.mobile-player')).to_have_count(0)
                    expect(page.get_by_role('link',name='Submit match replays')).to_be_visible()
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),(width,slug)
                page.screenshot(path=str(output/f'{slug}-{width}.png'),full_page=True)
        page.get_by_label('Team',exact=True).focus()
        page.keyboard.press('Home');page.keyboard.press('Enter')
        expect(page.get_by_label('Team',exact=True)).to_have_value('blue')
        page.goto(url+'#/players?team=not-a-team',wait_until='networkidle')
        expect(page).to_have_url(url+'#/players?team=blue')
        page.locator('.mobile-player .player-link').filter(has_text='Lgon').click()
        expect(page.locator('h1')).to_have_text('Lgon')
        page.get_by_label('Statistics period').select_option('career')
        expect(page.get_by_text('Global career',exact=False)).to_be_visible()
        expect(page.locator('.trend-point')).to_have_count(3)
        checks.append('desktop/tablet/phone exact team cards, accessible help, White empty state, invalid fallback and global player Career links')

        fixture=browser.new_page(viewport={'width':1440,'height':900})
        fixture.on('pageerror',lambda e:errors.append(str(e)))
        future=deepcopy(index)
        yellow={**index['teams'][0],'id':3,'slug':'yellow','name':'UAH Yellow','primary_color':'#FDDA24','aliases':['gold']}
        future['teams'].append(yellow)
        future['teams'][1]['aliases']=['silver']
        fixture.route('**/data/index.json',lambda r:r.fulfill(json=future))
        owned={**blue,'team':yellow,'players':[{**blue['players'][0],'slug':'yellow-player','name':'Yellow player'}]}
        fixture.route('**/data/teams/yellow/*.json',lambda r:r.fulfill(json={**owned,'slug':r.request.url.split('/')[-1][:-5]}))
        fixture.goto(url+'#/players?team=gold',wait_until='networkidle')
        expect(fixture).to_have_url(url+'#/players?team=yellow')
        expect(fixture.locator('tbody tr')).to_have_count(1)
        expect(fixture.locator('tbody')).to_contain_text('Yellow player')
        assert fixture.title()=='UAH Yellow · Player Stats | UAH R6'
        assert fixture.locator('.main-player-stats').evaluate("e=>e.style.getPropertyValue('--team-primary')")=='#FDDA24'
        expect(fixture.get_by_label('Team',exact=True).locator('option')).to_have_count(3)
        fixture.goto(url+'#/players?team=silver',wait_until='networkidle')
        expect(fixture).to_have_url(url+'#/players?team=white')
        expect(fixture.locator('tbody tr')).to_have_count(0)

        # Same identity on two teams has distinct map-owned stats. Current roster
        # membership is deliberately irrelevant to this client-side selection.
        white={**blue,'team':future['teams'][1],'maps':1,'rounds':4,'players':[{**blue['players'][0],'slug':'lgon','name':'Lgon','rounds':4,'maps':1,'kills':3,'deaths':2,'kd_diff':1,'rating':.8}]}
        fixture.route('**/data/teams/white/*.json',lambda r:r.fulfill(json={**white,'slug':r.request.url.split('/')[-1][:-5]}))
        fixture.get_by_label('Statistics period').select_option('career')
        expect(fixture.locator('tbody tr')).to_have_count(1)
        expect(fixture.locator('tbody')).to_contain_text('3-2 (+1)')
        fixture.get_by_label('Team',exact=True).select_option('blue')
        expect(fixture.locator('tbody tr')).to_have_count(5)
        assert '3-2 (+1)' not in fixture.locator('tbody').inner_text()
        fixture.get_by_label('Team',exact=True).select_option('white')
        expect(fixture.locator('tbody tr')).to_have_count(1)
        fixture.locator('.stats-desktop .player-link').click()
        expect(fixture.locator('h1')).to_have_text('Lgon')
        expect(fixture.get_by_text('82 rounds across 7 maps',exact=True)).to_be_visible()
        checks.append('future team and aliases canonicalize; synthetic same-player transfer proves team-only Career while global profile keeps full Career')

        # Hold the White response after Blue was rendered: stale Blue players
        # must disappear immediately, before White JSON becomes available.
        fixture.unroute('**/data/teams/white/*.json')
        pending=[]
        fixture.route('**/data/teams/white/*.json',lambda r:pending.append(r))
        fixture.goto(url+'#/players?team=blue',wait_until='networkidle')
        expect(fixture.locator('tbody tr')).to_have_count(5)
        fixture.get_by_label('Team',exact=True).select_option('white')
        expect(fixture.locator('tbody tr,.mobile-player')).to_have_count(0)
        expect(fixture.locator('.heading')).to_contain_text('UAH WHITE')
        fixture.wait_for_timeout(100)
        assert pending
        for r in pending:r.fulfill(json={**white,'slug':'career'})
        expect(fixture.locator('tbody tr')).to_have_count(1)
        checks.append('held network response cannot show old-team players under the new team heading')
        fixture.close()
        fallback=browser.new_page()
        no_blue={**index,'teams':index['teams'][1:]}
        fallback.route('**/data/index.json',lambda r:r.fulfill(json=no_blue))
        fallback.goto(url+'#/players',wait_until='networkidle')
        expect(fallback).to_have_url(url+'#/players?team=white')
        fallback.unroute('**/data/index.json')
        fallback.route('**/data/index.json',lambda r:r.fulfill(json={**index,'teams':[]}))
        fallback.reload(wait_until='networkidle')
        expect(fallback.get_by_text('No active teams are available yet.',exact=True)).to_be_visible()
        fallback.close()
        assert not errors,errors
        browser.close()
    report={'status':'PASS','url':url,'checks':checks,'javascript_errors':errors}
    (output/'scope-ui.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--url');ap.add_argument('--output',type=Path,default=ROOT/'data/research/player-stats-scoping-20261007/browser');args=ap.parse_args()
    if args.url:verify(args.url,args.output)
    else:
        handler=functools.partial(SimpleHTTPRequestHandler,directory=str(ROOT/'web/dist'))
        server=ThreadingHTTPServer(('127.0.0.1',0),handler);threading.Thread(target=server.serve_forever,daemon=True).start()
        try:verify(f'http://127.0.0.1:{server.server_port}/',args.output)
        finally:server.shutdown();server.server_close()
