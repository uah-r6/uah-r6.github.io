"""Read-only local/live presentation checks. Fixtures never call the submission API."""
import argparse
import json
import threading
import functools
from pathlib import Path
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'web/public/data'


def verify(url, output):
    output.mkdir(parents=True, exist_ok=True)
    index = json.loads((DATA / 'index.json').read_text(encoding='utf-8'))
    season = json.loads((DATA / 'teams/blue/fall-2026.json').read_text(encoding='utf-8'))
    profile = json.loads((DATA / 'players/lgon/fall-2026.json').read_text(encoding='utf-8'))
    errors = []
    checks = []
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=True)
        page = browser.new_page(viewport={'width': 1440, 'height': 960})
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.goto(url+'#/teams/blue/stats', wait_until='networkidle')
        expect(page.locator('tbody tr')).to_have_count(5)
        expect(page.locator('.team-header')).to_contain_text('82')
        expect(page.locator('.team-header')).to_contain_text('6–1')
        for row, player in zip(page.locator('tbody tr').all(), season['players']):
            expect(row.locator('td').nth(1)).to_have_text(f"{player['rating']:.2f}" if player['rating'] is not None else '—')
        assert 'Rounds' not in page.locator('thead').inner_text()
        page.get_by_role('button', name='Rating', exact=True).click()
        expect(page.locator('th[data-stat=rating]')).to_have_attribute('aria-sort', 'ascending')
        page.get_by_role('button', name='About KOST', exact=True).focus()
        expect(page.get_by_role('dialog', name='KOST explained')).to_be_visible()
        expect(page.get_by_role('dialog').get_by_role('link')).to_have_attribute('href', '#/methodology/core-stats')
        page.keyboard.press('Enter')
        expect(page.get_by_role('dialog').get_by_role('link')).to_be_focused()
        page.keyboard.press('Escape'); expect(page.get_by_role('dialog')).to_have_count(0)
        page.get_by_role('button', name='About Entry', exact=True).click()
        expect(page.get_by_role('dialog')).to_be_visible()
        page.locator('h1').click(); expect(page.get_by_role('dialog')).to_have_count(0)
        checks.append('exact trusted stats; independent sorting/help focus, click, Escape and outside dismissal')
        page.set_viewport_size({'width': 390, 'height': 900})
        expect(page.locator('.stats-desktop')).to_be_hidden()
        expect(page.locator('.mobile-player')).to_have_count(5)
        for card in page.locator('.mobile-player').all():
            assert all(x in card.inner_text() for x in ['Rating', 'K-D', 'KOST', 'Entry', 'KPR'])
        page.locator('.mobile-player .player-link').filter(has_text='Lgon').click()
        expect(page.locator('h1')).to_have_text('Lgon')
        expect(page.locator('.trend-point')).to_have_count(3)
        labels = page.locator('.trend-point').evaluate_all('(els)=>els.map(e=>e.getAttribute("aria-label"))')
        assert ['Placements','University of Michigan','UCF'] == [m for m in ['Placements','University of Michigan','UCF'] if any(m in label for label in labels)]
        page.locator('.trend-point').first.focus()
        expect(page.locator('.trend-detail')).to_contain_text('Placements')
        expect(page.locator('.trend-detail')).to_contain_text('1.50')
        page.keyboard.press('ArrowRight'); expect(page.locator('.trend-detail')).to_contain_text('1.43')
        page.locator('.trend-point').last.click(); expect(page.locator('.trend-detail')).to_contain_text('UCF'); expect(page.locator('.exact-series-rating')).to_contain_text('1.42')
        page.get_by_label('Statistics period').select_option('career')
        expect(page.locator('.trend-point')).to_have_count(3)
        checks.append('mobile cards, normal profile link, exact Rating history, keyboard/tap context, career scope')
        page.goto(url+'#/matches', wait_until='networkidle')
        expect(page.locator('.series-card')).to_have_count(3)
        expect(page.locator('.series-maps a')).to_have_count(7)
        assert 'Recorded maps' in page.locator('.series-card').first.inner_text()
        assert '2–0' in page.locator('.recorded-score').first.inner_text()
        page.locator('.series-maps a').first.click()
        expect(page.locator('h1')).to_contain_text('Nighthaven Labs')
        checks.append('recorded series counts, map scores/results and working links')
        # Embeds ignore saved Career and stay compact at all iframe widths.
        page.evaluate("localStorage.setItem('necc-season','career')")
        for width, expected in [(1000,10),(800,7),(600,5),(390,5)]:
            page.set_viewport_size({'width':width,'height':600})
            page.goto(url+'#/embed/blue/player-stats', wait_until='networkidle')
            expect(page.locator('tbody tr')).to_have_count(5)
            assert page.locator('header,footer,nav,h1,.season-select').count()==0
            assert page.locator('thead th:visible').count()==expected
            assert page.locator('th[data-stat=rating]').is_visible()
            assert page.title()=='UAH Blue Player Stats | UAH R6'
            dims=page.evaluate('({width:document.documentElement.scrollWidth, height:document.body.scrollHeight, view:innerWidth})')
            assert dims['width']<=dims['view']+1,dims
            assert dims['height']<380,dims
            page.locator('.table-wrap').focus()
            page.get_by_role('button',name='About Rating',exact=True).focus()
            expect(page.get_by_role('dialog')).to_be_visible()
            bounds=page.get_by_role('dialog').bounding_box()
            assert bounds['x']>=0 and bounds['x']+bounds['width']<=width,bounds
            page.keyboard.press('Enter')
            expect(page.get_by_role('dialog').get_by_role('link')).to_be_focused()
            page.keyboard.press('Escape')
            page.screenshot(path=str(output/f'embed-blue-{width}.png'),full_page=True)
        page.goto(url+'#/embed/white/player-stats',wait_until='networkidle')
        expect(page.locator('tbody tr')).to_have_count(0)
        expect(page.get_by_text('No player statistics available yet.',exact=True)).to_be_visible()
        page.goto(url+'#/embed/blue/player-stats?season=fall-2026',wait_until='networkidle')
        expect(page.locator('tbody tr')).to_have_count(5)
        page.goto(url+'#/embed/missing/player-stats',wait_until='networkidle')
        expect(page.locator('h1')).to_have_text('Page not found')
        page.goto(url+'#/embed/blue/player-stats?season=missing',wait_until='networkidle')
        expect(page.locator('h1')).to_have_text('Page not found')
        checks.append('unlisted chrome-free compact embeds: 1000/800/600/390px, White, invalid team/season')
        restricted=browser.new_page()
        restricted.on('pageerror',lambda e:errors.append(str(e)))
        restricted.add_init_script("Object.defineProperty(window,'localStorage',{get(){throw new DOMException('Storage unavailable','SecurityError')}})")
        restricted.goto(url+'#/embed/blue/player-stats',wait_until='networkidle')
        expect(restricted.locator('tbody tr')).to_have_count(5)
        restricted.close()
        checks.append('embed renders when browser storage is inaccessible; no saved-period access')
        # New generic team and active season rollover, historical override, and Alumni.
        fixture=browser.new_page(viewport={'width':1000,'height':700})
        fixture.on('pageerror',lambda e:errors.append(str(e)))
        future=json.loads(json.dumps(index));future['active_season']='spring-2027'
        future['seasons'].append({'slug':'spring-2027','name':'Spring 2027'})
        future['teams'].append({**future['teams'][0],'slug':'yellow','name':'UAH Yellow','primary_color':'#FDDA24'})
        fixture.route('**/data/index.json',lambda r:r.fulfill(json=future))
        spring={**season,'slug':'spring-2027','name':'Spring 2027','players':[{**season['players'][0],'name':'Spring active'},{**season['players'][1],'name':'Former member','status':'Alumni'}]}
        fixture.route('**/data/teams/*/spring-2027.json',lambda r:r.fulfill(json={**spring,'team':{**spring['team'],'slug':r.request.url.split('/teams/')[1].split('/')[0]}}))
        fixture.route('**/data/teams/yellow/fall-2026.json',lambda r:r.fulfill(json={**season,'team':{**season['team'],'slug':'yellow'}}))
        fixture.goto(url+'#/embed/yellow/player-stats',wait_until='networkidle')
        expect(fixture.locator('tbody tr')).to_have_count(1)
        expect(fixture.locator('tbody')).to_contain_text('Spring active')
        assert fixture.locator('.embed-page').evaluate("e=>e.style.getPropertyValue('--team-primary')")=='#FDDA24'
        fixture.goto(url+'#/embed/yellow/player-stats?season=fall-2026',wait_until='networkidle')
        expect(fixture.locator('tbody tr')).to_have_count(5)
        # Normal filter retains Alumni; map-level historical participant rules are unchanged.
        fixture.goto(url+'#/teams/yellow/stats',wait_until='networkidle')
        expect(fixture.locator('tbody tr')).to_have_count(1)
        fixture.get_by_label('Include Alumni',exact=True).check()
        expect(fixture.locator('tbody tr')).to_have_count(2)
        checks.append('generic team, active-season rollover, explicit historical season and Alumni rules')
        fixture.get_by_label('Statistics period').select_option('fall-2026')
        for rows,label in [([profile['series_ratings'][0]],None),([],'No eligible Series Ratings yet.')]:
            fixture.route('**/data/players/lgon/fall-2026.json',lambda r,request,rows=rows:r.fulfill(json={**profile,'series_ratings':rows}))
            fixture.goto(url+'#/players/lgon',wait_until='networkidle');fixture.reload(wait_until='networkidle')
            expect(fixture.locator('.trend-point')).to_have_count(len(rows))
            if label:expect(fixture.get_by_text(label,exact=True)).to_be_visible()
            fixture.unroute('**/data/players/lgon/fall-2026.json')
        checks.append('single-point and empty Rating chart states')
        fixture.close()
        # Real cross-origin framing: harness origin differs from built/live site origin.
        class Harness(SimpleHTTPRequestHandler):
            def do_GET(self):
                body=f'<html><body style="margin:0"><iframe title="UAH stats" src="{url}#/embed/blue/player-stats" width="800" height="360" style="border:0"></iframe></body></html>'.encode()
                self.send_response(200);self.send_header('Content-Type','text/html');self.end_headers();self.wfile.write(body)
            def log_message(self,*_):pass
        server=ThreadingHTTPServer(('127.0.0.1',0),Harness)
        threading.Thread(target=server.serve_forever,daemon=True).start()
        try:
            page.set_viewport_size({'width':1000,'height':600})
            page.goto(f'http://127.0.0.1:{server.server_port}/',wait_until='networkidle')
            frame=page.frame_locator('iframe')
            expect(frame.locator('tbody tr')).to_have_count(5)
            assert frame.locator('header,footer,nav,h1').count()==0
            page.screenshot(path=str(output/'cross-origin-iframe.png'))
        finally:server.shutdown();server.server_close()
        checks.append('actual cross-origin iframe rendered trusted table without chrome')
        routes=['','teams/blue','teams/white','teams/blue/roster','teams/white/roster','teams/blue/stats','players','players/lgon','matches','matches/9db26f1b6ca7','series/40bf93b16f97','series/1a106d1b2f89','series/170b708e12f1','methodology/rating','submit','does-not-exist']
        for width in [1440,1150,768,390]:
            page.set_viewport_size({'width':width,'height':960})
            for route in routes:
                page.goto(url+'#/'+route,wait_until='domcontentloaded' if route=='submit' else 'networkidle')
                expect(page.locator('h1').first).to_be_visible()
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1'),(width,route)
                page.screenshot(path=str(output/f'{width}-{route.replace("/","_") or "home"}.png'),full_page=True)
                assert page.title().endswith('UAH R6'),page.title()
        assert page.locator('meta[property="og:image"]').get_attribute('content').endswith('uah-esports-logo.png')
        assert not errors,errors
        browser.close()
        checks.append('whole-site visual/overflow/title audit: 1440/1150/768/390px; favicon/social metadata')
    report={'status':'PASS','url':url,'checks':checks,'javascript_errors':errors}
    (output/'presentation-ui.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--url');ap.add_argument('--output',type=Path,default=ROOT/'data/research/public-presentation-20261007/browser');args=ap.parse_args()
    if args.url:verify(args.url,args.output)
    else:
        handler=functools.partial(SimpleHTTPRequestHandler,directory=str(ROOT/'web/dist'))
        server=ThreadingHTTPServer(('127.0.0.1',0),handler);threading.Thread(target=server.serve_forever,daemon=True).start()
        try:verify(f'http://127.0.0.1:{server.server_port}/',args.output)
        finally:server.shutdown();server.server_close()
