"""Read-only White coverage/sub separation checks against built or live exports."""
import argparse
import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
from urllib.request import urlopen
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'web/public/data'


def load(name):return json.loads((DATA/name).read_text(encoding='utf-8'))


def verify(url,out):
    out.mkdir(parents=True,exist_ok=True)
    count=0
    for path in DATA.rglob('*.json'):
        name=path.relative_to(DATA).as_posix()
        with urlopen(url+'data/'+name+'?rating-evidence=20261008',timeout=30) as response:
            assert json.load(response)==load(name),f'Public JSON differs: {name}'
        count+=1
    white=load('teams/white/fall-2026.json');series=load('series/ada4becd7c74.json')
    assert load('matches/035ff71d4884.json')['rating_eligible']
    assert all(p['rating_maps']==2 and p['rating_rounds']==21 for p in series['players'])
    errors=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True)
        context=browser.new_context(viewport={'width':1440,'height':960},has_touch=True)
        page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
        for width in (1440,1100,768,390):
            page.set_viewport_size({'width':width,'height':960})
            for period in ('fall-2026','career'):
                for role in ('roster','subs'):
                    page.goto(url+'#/players?team=white'+('&players=subs' if role=='subs' else ''),wait_until='networkidle')
                    page.get_by_label('Statistics period').select_option(period)
                    expect(page.locator('.mobile-player' if width<=540 else 'tbody tr')).to_have_count(4 if role=='roster' else 1)
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
            # A new session defaults to the active season; restore it for profiles.
            page.get_by_label('Statistics period').select_option('fall-2026')
            for player in white['players']:
                profile=load(f'players/{player["slug"]}/fall-2026.json')
                assert profile['rating_rounds']==21 and profile['rating_maps']==2
                page.goto(url+'#/players/'+player['slug'],wait_until='networkidle')
                expect(page.locator('.trend-point')).to_have_count(1)
                point=page.locator('.trend-point')
                assert 'trend-point-partial' not in point.get_attribute('class')
                point.hover();point.focus();point.tap()
                expect(page.locator('.trend-detail')).to_contain_text('FSU Maroon')
                expect(page.locator('.exact-series-rating')).to_contain_text(f'{player["rating"]:.2f}')
                expect(page.locator('.trend-coverage')).to_contain_text('2 / 2 maps rated')
                expect(page.locator('.trend-coverage')).to_contain_text('21 / 21 rounds rated')
                expect(page.locator('.trend-partial-label')).to_have_count(0)
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
            page.screenshot(path=str(out/f'white-full-trend-{width}.png'),full_page=True)
            page.goto(url+'#/players/dinoted11',wait_until='networkidle')
            expect(page.locator('.trend-point')).to_have_count(0)
            page.get_by_role('link',name='View Sub Stats').click()
            expect(page.locator('.heading')).to_contain_text('SUBSTITUTE STATS')
            expect(page.locator('.trend-point')).to_have_count(0)
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
            page.goto(url+'#/series/ada4becd7c74',wait_until='networkidle')
            expect(page.locator('.sub-badge').filter(visible=True)).to_have_count(1)
            page.screenshot(path=str(out/f'white-series-{width}.png'),full_page=True)
            page.goto(url+'#/matches/035ff71d4884',wait_until='networkidle')
            expect(page.locator('.mobile-player' if width<=540 else 'tbody tr')).to_have_count(5)
            assert 'UNAVAILABLE' not in page.locator('main').inner_text()
        assert not errors,errors
        browser.close()
    report=dict(status='PASS',url=url,public_json_files=count,white_normal_players=4,white_sub_players=1,
        white_coverage='2/2 maps; 21/21 rounds',javascript_errors=errors)
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--url');parser.add_argument('--output',type=Path,
        default=ROOT/'data/research/rating-evidence-production-20261008/white-browser');args=parser.parse_args()
    if args.url:verify(args.url,args.output)
    else:
        class QuietHandler(SimpleHTTPRequestHandler):
            def log_message(self,*args):pass
        server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(QuietHandler,directory=str(ROOT/'web/dist')))
        threading.Thread(target=server.serve_forever,daemon=True).start()
        try:verify(f'http://127.0.0.1:{server.server_port}/',args.output)
        finally:server.shutdown();server.server_close()
