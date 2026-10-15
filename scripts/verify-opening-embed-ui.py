"""Browser QA of real exports and read-only zero-sample fixtures, local or live."""
import argparse
import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading

from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT/'web/public/data'
OUT = ROOT/'data/research/opening-embed-20261015'
METRICS = [('opening_kills', 'eligible_rounds'), ('opening_kill_wins', 'opening_kills'),
           ('opening_death_wins', 'opening_deaths')]


def read(name):
    return json.loads((DATA/name).read_text(encoding='utf-8'))


def percentage(n, d):
    return f'{100*n/d:.1f}%' if d else '—'


def verify(url, output):
    output.mkdir(parents=True, exist_ok=True)
    index = read('index.json'); season = index['active_season']
    blue = read(f'teams/blue/{season}.json')
    white = read(f'teams/white/{season}.json')
    series = read(f'series/{blue["matches"][0]["series_id"]}.json')
    map_ = read(f'matches/{blue["matches"][0]["id"]}.json')
    analytics = read(f'teams/blue/maps/{season}.json')
    repeated = next(m for m in analytics['maps']+analytics['historical_maps'] if m['maps_played'] > 1 and m['slug'] == 'border')
    checks, errors, mutations = [], [], []
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=True)
        page = browser.new_page(viewport={'width':1440,'height':960})
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.on('request', lambda r: mutations.append(r.url) if r.method not in ('GET','HEAD','OPTIONS') and '/api/' in r.url else None)

        def go(route):
            page.goto(url+'#/'+route, wait_until='networkidle')

        def layout():
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'), page.url

        def opening_counts(stats):
            cards = page.locator('.opening-card')
            expect(cards).to_have_count(3)
            for i, (n, d) in enumerate(METRICS):
                card = cards.nth(i); overall = stats['overall']
                expect(card.locator('.opening-headline strong')).to_have_text(percentage(overall[n], overall[d]))
                expect(card.locator('.opening-headline>span')).to_have_text(f'{overall[n]} / {overall[d]} rounds')
                for j, side in enumerate(('attack','defense')):
                    count = stats[side]
                    expect(card.locator('dd b').nth(j)).to_have_text(percentage(count[n], count[d]))
                    expect(card.locator('dd span').nth(j)).to_have_text(f'{count[n]} / {count[d]}')

        cases = [(f'teams/blue', blue), (f'teams/white', white),
                 (f'series/{series["id"]}', series), (f'matches/{map_["id"]}', map_),
                 (f'teams/blue/maps/{repeated["slug"]}?season={season}', repeated)]
        for width in (1440,1100,768,390):
            page.set_viewport_size({'width':width,'height':960})
            for route, data in cases:
                go(route); opening_counts(data['opening_engagements']); layout()
                page.screenshot(path=str(output/f'{route.split("?")[0].replace("/","-")}-{width}.png'), full_page=True)
            checks.append(f'{width}px: Blue/White season, series, individual map and repeated Border aggregate with exact overall/ATK/DEF raw samples')
        go('teams/blue')
        page.get_by_label('Statistics period').select_option('career')
        opening_counts(read('teams/blue/career.json')['opening_engagements'])
        page.get_by_label('Public team').select_option('white')
        opening_counts(read('teams/white/career.json')['opening_engagements'])
        page.get_by_label('Statistics period').select_option(season)
        page.get_by_role('button',name='About Opening Kill %',exact=True).focus()
        expect(page.get_by_role('dialog',name='Opening Kill % explained')).to_be_visible()
        page.keyboard.press('Escape')
        expect(page.get_by_role('dialog',name='Opening Kill % explained')).to_have_count(0)
        checks.append('Career scope, team switching and keyboard opening definitions')

        empty = json.loads(json.dumps(white))
        for scope in empty['opening_engagements'].values():
            for key in scope: scope[key] = None if key.endswith('_pct') else 0
        page.route(f'**/data/teams/white/{season}.json',lambda r:r.fulfill(json=empty))
        go('teams/white'); page.reload(wait_until='networkidle'); opening_counts(empty['opening_engagements'])
        assert 'NaN' not in page.locator('.opening-engagements').inner_text()
        page.unroute(f'**/data/teams/white/{season}.json')
        checks.append('zero-sample percentages display dashes and 0 / 0, never fake 0% or NaN')

        for width in (1200,1000,800,600,390):
            page.set_viewport_size({'width':width,'height':900})
            for team in ('blue','white'):
                data = blue if team == 'blue' else white
                go(f'embed/{team}/player-stats')
                expect(page.get_by_role('table',name='Player Stats',exact=True)).to_be_visible()
                expect(page.locator('.app,.topbar,footer,.embed-team-identity,.public-hero')).to_have_count(0)
                assert page.evaluate('getComputedStyle(document.body).backgroundColor') == 'rgb(243, 243, 243)'
                assert page.locator('td').first.evaluate('e=>getComputedStyle(e).color') == 'rgb(32, 32, 32)'
                assert page.locator('td').first.evaluate('e=>getComputedStyle(e).fontFamily').startswith('Arial')
                assert page.locator('.table-wrap').evaluate('e=>getComputedStyle(e).borderTopWidth') == '0px'
                assert page.locator('thead th:visible').count() == 10  # All existing columns retained at every width.
                expect(page.locator('thead th[scope=col]')).to_have_count(10)
                expect(page.get_by_role('region',name='Player Stats table')).to_have_attribute('tabindex','0')
                roster = [p for p in data['players'] if p.get('status') != 'Alumni']
                rows = page.locator('tbody tr')
                expect(rows).to_have_count(len(roster))
                for player in roster:
                    row = rows.filter(has=page.get_by_role('link',name=player['name'],exact=False))
                    expect(row.locator('td.rating')).to_have_text(f'{player["rating"]:.2f}' if player['rating'] is not None else '—')
                    expect(row.get_by_role('link')).to_have_attribute('target','_blank')
                before = rows.first.inner_text()
                page.get_by_role('button',name='Rating',exact=True).focus(); page.keyboard.press('Enter')
                expect(page.locator('th[data-stat=rating]')).to_have_attribute('aria-sort','ascending')
                if len(roster)>1: assert rows.first.inner_text() != before
                page.get_by_role('button',name='About KOST',exact=True).focus()
                popup = page.get_by_role('dialog',name='KOST explained')
                expect(popup).to_be_visible()
                assert popup.evaluate('e=>getComputedStyle(e).backgroundColor') == 'rgb(250, 250, 250)'
                page.keyboard.press('Escape')
                assert page.locator('.embed-page').bounding_box()['height'] < 450
                wrap = page.locator('.table-wrap')
                if width >= 800:
                    assert wrap.evaluate('e=>e.scrollWidth<=e.clientWidth+1'), (width, wrap.bounding_box())
                else:
                    assert wrap.evaluate('e=>getComputedStyle(e).overflowX') == 'auto'
                    wrap.evaluate('e=>e.scrollLeft=e.scrollWidth')
                    assert wrap.evaluate('e=>e.scrollLeft>0')
                layout()
                page.screenshot(path=str(output/f'embed-{team}-{width}.png'), full_page=True)
            checks.append(f'{width}px embeds: exact player Ratings/rows, all columns, keyboard sorting/help, light background, no chrome or height filler; contained scroll only below 800px')
        go(f'embed/blue/player-stats?season={season}')
        expect(page.get_by_role('region',name='Player Stats table')).to_be_visible()
        go('players?team=blue')
        expect(page.get_by_role('navigation',name='Main navigation')).to_be_visible()
        assert page.evaluate('document.documentElement.classList.contains("embed-document")') is False
        assert page.evaluate('getComputedStyle(document.body).backgroundColor') != 'rgb(243, 243, 243)'
        checks.append('explicit embed season URL and return to standalone dark chrome; no parent DOM access')
        assert not errors, errors
        assert not mutations, mutations
        browser.close()
    report = dict(status='PASS',url=url,checks=checks,javascript_errors=errors,api_mutations=mutations)
    (output/'opening-embed-ui.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--url')
    parser.add_argument('--output',type=Path,default=OUT/'browser')
    args = parser.parse_args()
    if args.url:
        verify(args.url,args.output)
    else:
        class Quiet(SimpleHTTPRequestHandler):
            def log_message(self,*_): pass
            def copyfile(self,source,output):
                try: super().copyfile(source,output)
                except ConnectionError: pass
        server = ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT/'web/dist')))
        threading.Thread(target=server.serve_forever,daemon=True).start()
        try: verify(f'http://127.0.0.1:{server.server_port}/',args.output)
        finally: server.shutdown()
