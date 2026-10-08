"""Read-only built/live roster checks, including exact published JSON."""
import argparse
import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'web/public/data'


def verify(url, output):
    output.mkdir(parents=True,exist_ok=True)
    documents={p.relative_to(DATA).as_posix():json.loads(p.read_text(encoding='utf-8')) for p in DATA.rglob('*.json')}
    errors=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True)
        context=browser.new_context(timezone_id='America/Chicago',viewport={'width':1440,'height':960})
        page=context.new_page()
        page.on('pageerror',lambda e:errors.append(str(e)))
        for name,expected in documents.items():
            response=page.request.get(url+'data/'+name,params={'roster_check':documents['index.json']['generated_at']})
            assert response.ok,(name,response.status)
            assert response.json()==expected,('Published JSON differs',name)
        for width in (1440,1100,768,390):
            page.set_viewport_size({'width':width,'height':960})
            page.goto(url+'#/teams/white/roster',wait_until='networkidle')
            expect(page.locator('.roster-cards>a')).to_have_count(5)
            expect(page.locator('.roster-cards')).to_contain_text('Nachofries_08')
            expect(page.locator('.roster-cards')).not_to_contain_text('Nanor555')
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),('roster',width)
            page.screenshot(path=str(output/f'white-roster-{width}.png'),full_page=True)
            page.goto(url+'#/players?team=white',wait_until='networkidle')
            for period in ('fall-2026','career'):
                page.get_by_label('Statistics period').select_option(period)
                expect(page.locator('.team-empty')).to_contain_text('No player statistics yet')
                expect(page.locator('.empty-roster>a')).to_have_count(5)
                expect(page.locator('.empty-roster')).to_contain_text('Nachofries_08')
                expect(page.locator('.empty-roster')).not_to_contain_text('Nanor555')
                expect(page.locator('tbody tr')).to_have_count(0)
                expect(page.locator('.mobile-player')).to_have_count(0)
            page.screenshot(path=str(output/f'white-stats-{width}.png'),full_page=True)
            page.goto(url+'#/players/nachofries-08',wait_until='networkidle')
            expect(page.locator('.profile-head')).to_contain_text('0 regular roster rounds across 0 maps')
            expect(page.locator('.profile-cards>div').first).to_contain_text('—')
            expect(page.locator('.membership')).to_contain_text('UAH White')
            expect(page.locator('.match-card')).to_have_count(0)
            expect(page.locator('.trend-point')).to_have_count(0)
            expect(page.locator('.operator')).to_have_count(0)
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),('empty profile',width)
            page.screenshot(path=str(output/f'nacho-empty-profile-{width}.png'),full_page=True)
            page.goto(url+'#/players/nanor555',wait_until='networkidle')
            expect(page.locator('h1')).to_have_text('Nanor555')
            expect(page.locator('.membership')).to_have_count(0)
            expect(page.locator('.profile-head')).to_contain_text('0 regular roster rounds across 0 maps')
            page.goto(url+'#/players?team=blue',wait_until='networkidle')
            page.get_by_label('Statistics period').select_option('fall-2026')
            expect(page.locator('.mobile-player' if width<=540 else 'tbody tr')).to_have_count(5)
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),('Blue stats',width)
            page.goto(url+'#/players?team=white&players=subs',wait_until='networkidle')
            expect(page.locator('.team-empty')).to_be_visible()
            expect(page.locator('tbody tr')).to_have_count(0)
            expect(page.locator('.empty-roster')).to_have_count(0)
        assert not errors,errors
        browser.close()
    report=dict(status='PASS',url=url,exact_public_json=len(documents),white_regular_players=5,
        nacho_unique_global_identity=True,nanor_identity_retained=True,empty_profiles_no_fabricated_statistics=True,
        javascript_errors=errors,viewports=[1440,1100,768,390])
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--url');parser.add_argument('--output',type=Path,
        default=ROOT/'data/research/roster-deletion-20261007/public-browser');args=parser.parse_args()
    if args.url:verify(args.url,args.output)
    else:
        class Handler(SimpleHTTPRequestHandler):
            def log_message(self,*args):pass
        server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(ROOT/'web/dist')))
        threading.Thread(target=server.serve_forever,daemon=True).start()
        try:verify(f'http://127.0.0.1:{server.server_port}/',args.output)
        finally:server.shutdown();server.server_close()
