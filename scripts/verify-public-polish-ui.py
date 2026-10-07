"""Optional built-site/live checks using Playwright and installed Microsoft Edge."""
import argparse
import json
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright, expect


def verify(url, output):
    output.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=True)
        page = browser.new_page(viewport={'width': 1366, 'height': 900})
        errors, failed = [], []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.on('response', lambda r: failed.append(r.url) if r.url.startswith(url) and r.status >= 400 else None)
        page.goto(url+'#/players', wait_until='networkidle')
        expect(page.get_by_role('heading', name='Player Stats', exact=True)).to_be_visible()
        expect(page.get_by_role('navigation', name='Main navigation').get_by_role('link', name='Player Stats')).to_be_visible()
        expect(page.locator('tbody tr')).to_have_count(5)
        headers = page.locator('th').all_text_contents()
        assert 'Rounds' not in headers and len(headers) == 10, headers
        assert 'Leaderboard' not in page.locator('body').inner_text()
        assert 'Kill counts use Ubisoft credit' not in page.locator('body').inner_text()
        rating = page.get_by_role('button', name='Rating', exact=True)
        rating.focus(); page.keyboard.press('Enter')
        expect(page.get_by_role('columnheader', name='Rating', exact=True)).to_have_attribute('aria-sort', 'ascending')
        page.keyboard.press('Enter')
        expect(page.get_by_role('columnheader', name='Rating', exact=True)).to_have_attribute('aria-sort', 'descending')
        page.goto(url+'#/methodology', wait_until='networkidle')
        expect(page.get_by_role('heading', name='Methodology', exact=True)).to_be_visible()
        nav = page.get_by_role('navigation', name='Methodology sections')
        expect(nav.get_by_role('link', name='Overview', exact=True)).to_have_attribute('aria-current', 'page')
        link = nav.get_by_role('link', name='Core Stats', exact=True)
        link.focus(); page.keyboard.press('Enter')
        expect(page.get_by_role('heading', name='Core Stats', exact=True)).to_be_visible()
        expect(nav.get_by_role('link',name='Core Stats',exact=True)).to_have_attribute('aria-current','page')
        summary = page.locator('.kost-grid summary').first
        summary.focus(); page.keyboard.press('Enter')
        expect(page.locator('.kost-grid details').first).to_have_attribute('open', '')
        expect(page.get_by_text('Teamkills do not qualify.', exact=False)).to_be_visible()
        page.keyboard.press('Enter')
        assert page.locator('.kost-grid details').first.get_attribute('open') is None
        nav.get_by_role('link', name='Rating', exact=True).click()
        expect(page.locator('.prediction-point')).to_have_count(110)
        expect(page.get_by_text('0.03036', exact=True)).to_be_visible()
        expect(page.get_by_text('81.82%', exact=True)).to_be_visible()
        point = page.locator('.prediction-point[tabindex="0"]')
        point.focus(); page.keyboard.press('ArrowRight')
        expect(page.locator('.prediction-point[data-point="1"]')).to_be_focused()
        expect(page.locator('.point-readout h4')).to_have_text('Faallz.DK')
        page.keyboard.press('Tab')
        assert page.locator('.rating-scatter').evaluate('(svg)=>!svg.contains(document.activeElement)')
        page.get_by_role('button', name='Next', exact=False).click()
        expect(page.locator('.prediction-point[data-point="2"]')).to_have_attribute('aria-pressed', 'true')
        page.locator('.prediction-point[data-point="0"]').hover(force=True)
        assert page.locator('.prediction-point.selected').count() == 1
        page.get_by_label('Explore an observation').select_option('5')
        expect(page.locator('.prediction-point[data-point="5"]')).to_have_attribute('aria-pressed', 'true')
        technical = page.locator('summary').filter(has=page.get_by_text('Technical details', exact=True))
        technical.click()
        expect(page.locator('.formula code')).to_be_visible()
        assert '0.073737' in page.locator('.formula code').inner_text()
        page.reload(wait_until='networkidle')
        expect(nav.get_by_role('link', name='Rating', exact=True)).to_have_attribute('aria-current', 'page')
        for width, height in [(1920,1080),(1366,900),(768,1024),(390,844)]:
            page.set_viewport_size({'width':width,'height':height})
            for route in ['', '/teams/blue', '/teams/white', '/teams/blue/stats', '/teams/blue/roster', '/players/lgon', '/matches', '/matches/d64d5478cdb3', '/methodology/rating', '/methodology/core-stats', '/methodology/objectives', '/methodology/advanced-stats']:
                page.goto(url+'#'+route, wait_until='networkidle')
                expect(page.locator('h1')).to_be_visible()
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'), (width, route)
                if route.startswith('/methodology/'):
                    label={'rating':'Rating','core-stats':'Core Stats','objectives':'Objectives','advanced-stats':'Advanced Stats'}[route.rsplit('/',1)[-1]]
                    expect(page.get_by_role('heading',name=label,exact=True)).to_be_visible()
                    expect(nav.get_by_role('link',name=label,exact=True)).to_have_attribute('aria-current','page')
                if route == '/methodology/rating':
                    expect(page.locator('.prediction-point')).to_have_count(110)
                    page.get_by_label('Explore an observation').select_option('109')
                    expect(page.locator('.prediction-point[data-point="109"]')).to_have_attribute('aria-pressed', 'true')
                    page.screenshot(path=str(output/f'rating-{width}.png'),full_page=True,animations='disabled')
                if route in ['/teams/blue/stats', '/teams/white', '/players/lgon', '/methodology/core-stats']:
                    page.screenshot(path=str(output/f'{route.strip("/").replace("/","-")}-{width}.png'),full_page=True,animations='disabled')
            page.emulate_media(reduced_motion='reduce')
            assert page.locator('.method-nav a').first.evaluate('(el)=>getComputedStyle(el).transitionDuration') == '0s'
            page.emulate_media(reduced_motion='no-preference')
        touch = browser.new_page(viewport={'width':390,'height':844},has_touch=True,is_mobile=True)
        touch.on('pageerror',lambda e:errors.append(str(e)))
        touch.goto(url+'#/methodology/rating',wait_until='networkidle')
        expect(touch.locator('.prediction-point')).to_have_count(110)
        points=touch.locator('.prediction-point')
        # The highest prediction is isolated, so this checks an actual point tap.
        index=points.evaluate_all('(points)=>points.reduce((best,p,i)=>Number(p.getAttribute("cy"))<Number(points[best].getAttribute("cy"))?i:best,0)')
        points.nth(index).tap()
        expect(points.nth(index)).to_have_attribute('aria-pressed','true')
        touch.get_by_role('navigation',name='Methodology sections').get_by_role('link',name='Advanced Stats').tap()
        expect(touch.get_by_role('heading',name='Advanced Stats',exact=True)).to_be_visible()
        touch.close()
        # Deliberately malformed browser-only response; no research/stat mutation.
        page.route('**/methodology/rating-v3-final.json', lambda r: r.fulfill(json={'points':[]}))
        page.goto(url+'#/methodology/rating',wait_until='networkidle')
        expect(page.get_by_role('status')).to_contain_text('interactive chart is unavailable')
        expect(page.get_by_text('0.03036',exact=True)).to_be_visible()
        assert page.locator('.prediction-point').count() == 0
        assert not errors, errors
        assert not failed, failed
        browser.close()
    report=dict(url=url,status='PASS',viewports=[1920,1366,768,390],points=110,
                checks=['public copy','columns','keyboard sorting','section URLs','keyboard accordions','scatter selection','technical equation','mobile selection and point tap','reduced motion','malformed-data fallback','public route overflow'],javascript_errors=errors,http_errors=failed)
    (output/'polish-ui.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--url')
    ap.add_argument('--output',type=Path,default=Path('data/research/public-polish-20261007/browser'))
    args=ap.parse_args()
    if args.url:
        verify(args.url,args.output)
    else:
        class Handler(SimpleHTTPRequestHandler):
            def __init__(self,*a,**kw): super().__init__(*a,directory=str(Path('web/dist').resolve()),**kw)
            def log_message(self,*_args): pass
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        threading.Thread(target=server.serve_forever,daemon=True).start()
        try: verify(f'http://127.0.0.1:{server.server_port}/',args.output)
        finally: server.shutdown();server.server_close()
