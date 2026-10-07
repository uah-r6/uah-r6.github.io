"""Real Edge checks for built/static public pages, or a deployed site.

Requires the optional Playwright package and Microsoft Edge. No database writes.
"""
import argparse
import json
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from playwright.sync_api import sync_playwright, expect


def verify(url, output):
    output.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel='msedge', headless=True)
        context = browser.new_context(viewport={'width': 1440, 'height': 1000})
        page = context.new_page()
        errors, failed = [], []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('response', lambda response: failed.append(response.url) if response.status >= 400 and response.url.startswith(url) else None)
        page.goto(url, wait_until='networkidle')
        expect(page.get_by_role('heading', name='UAH Rainbow Six Siege', exact=True)).to_be_visible()
        expect(page.get_by_role('heading', name='UAH Blue', exact=True)).to_be_visible()
        expect(page.get_by_text('No matches recorded yet', exact=True)).to_be_visible()
        assert page.locator('.brand img').evaluate('(img)=>img.complete && img.naturalWidth===1080')
        page.locator('.team-card').filter(has=page.get_by_role('heading', name='UAH Blue', exact=True)).click()
        expect(page.get_by_role('heading', name='UAH Blue · Fall 2026', exact=True)).to_be_visible()
        assert page.locator('tbody tr').count() == 5
        page.get_by_label('Statistics period').select_option('career')
        expect(page.get_by_role('heading', name='UAH Blue · Career', exact=True)).to_be_visible()
        page.get_by_label('Public team').select_option('white')
        expect(page.get_by_role('heading', name='UAH White · Career', exact=True)).to_be_visible()
        assert page.locator('tbody tr').count() == 0
        page.get_by_label('Public team').select_option('blue')
        page.get_by_label('Statistics period').select_option('fall-2026')
        page.get_by_role('link', name='Roster', exact=True).click()
        expect(page.locator('.roster-cards .panel')).to_have_count(5)
        page.get_by_role('link', name='Statistics', exact=True).click()
        expect(page.locator('tbody tr')).to_have_count(5)
        # Alumni fixtures affect this browser's responses only, never production status.
        def alumni(route):
            response = route.fetch()
            data = response.json()
            data['players'][0]['status'] = 'Alumni'
            route.fulfill(response=response, json=data)
        page.route('**/data/teams/blue/fall-2026.json', alumni)
        page.reload(wait_until='networkidle')
        expect(page.locator('tbody tr')).to_have_count(4)
        page.get_by_label('Include Alumni', exact=True).check()
        expect(page.locator('tbody tr')).to_have_count(5)
        page.unroute('**/data/teams/blue/fall-2026.json', alumni)
        page.goto(url+'#/players/lgon', wait_until='networkidle')
        expect(page.get_by_role('heading', name='Lgon', exact=True)).to_be_visible()
        expect(page.get_by_text('Rating coverage: 42 of 82 rounds across 4 of 7 maps.', exact=False)).to_be_visible()
        page.get_by_label('Statistics period').select_option('career')
        expect(page.get_by_text('Active · Global career', exact=True)).to_be_visible()
        def alumni_profile(route):
            response=route.fetch()
            data=response.json()
            data['status']='Alumni'
            route.fulfill(response=response,json=data)
        page.route('**/data/players/lgon/career.json',alumni_profile)
        page.reload(wait_until='networkidle')
        expect(page.get_by_text('Alumni · Global career',exact=True)).to_be_visible()
        expect(page.get_by_text('82 rounds across 7 maps',exact=True)).to_be_visible()
        page.unroute('**/data/players/lgon/career.json',alumni_profile)
        for route, heading in [('/matches/d64d5478cdb3', '7 : 3'), ('/methodology', 'METHODOLOGY'), ('/players', 'Program players'), ('/matches', 'MATCHES')]:
            page.goto(url+'#'+route, wait_until='networkidle')
            expect(page.get_by_role('heading', name=heading, exact=True)).to_be_visible()
        for width, height in [(1920,1080),(1366,768),(768,1024),(390,844)]:
            page.set_viewport_size({'width':width,'height':height})
            for route in ['/', '/teams/blue', '/teams/white', '/players/lgon', '/matches/d64d5478cdb3']:
                page.goto(url+'#'+route, wait_until='networkidle')
                expect(page.locator('main h1')).to_be_visible()
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1'), (width,route)
            page.goto(url, wait_until='networkidle')
            page.screenshot(path=str(output/f'program-{width}.png'), full_page=True)
        assert not errors, errors
        assert not failed, failed
        browser.close()
    report = {'url':url,'status':'PASS','viewports':[1920,1366,768,390], 'javascript_errors':errors,
              'same_origin_http_errors':failed,'alumni_fixture':'browser response only; 4 default/5 included',
              'checks':['root','teams','roster','stats','team selector','season/career','player','map','old routes','logo','responsive overflow']}
    (output/'public-ui.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url')
    parser.add_argument('--data', type=Path, default=Path('web/public/data'))
    parser.add_argument('--output', type=Path, default=Path('data/research/team-architecture-20261007/browser'))
    args = parser.parse_args()
    if args.url:
        verify(args.url, args.output)
    else:
        class Handler(SimpleHTTPRequestHandler):
            def __init__(self, *a, **kw):
                super().__init__(*a, directory=str(Path('web/dist').resolve()), **kw)

            def translate_path(self, path):
                name = unquote(urlparse(path).path)
                if name.startswith('/data/'):
                    target = (args.data.resolve()/name.removeprefix('/data/')).resolve()
                    if target.is_relative_to(args.data.resolve()):
                        return str(target)
                return super().translate_path(path)

            def log_message(self, *_args):
                pass
        server = ThreadingHTTPServer(('127.0.0.1',0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            verify(f'http://127.0.0.1:{server.server_port}/', args.output)
        finally:
            server.shutdown()
            server.server_close()
