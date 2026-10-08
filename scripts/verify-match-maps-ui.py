"""Read-only match discovery/map analytics browser checks, local or live."""
import argparse
from copy import deepcopy
import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading

from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'web/public/data'


def load(name):
    return json.loads((DATA / name).read_text(encoding='utf-8'))


def verify(url, output):
    output.mkdir(parents=True, exist_ok=True)
    index = load('index.json'); season = index['active_season']
    errors, mutations, checks, requests = [], [], [], []
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=True)
        page = browser.new_page(viewport={'width': 1440, 'height': 960})
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.on('request', lambda r: requests.append(r.url))
        def readonly(route):
            if route.request.method not in ('GET', 'HEAD', 'OPTIONS'):
                mutations.append(route.request.url); route.abort()
            else:
                route.continue_()
        page.route('**/*', readonly)
        def go(route):
            page.goto(url + '#/' + route, wait_until='networkidle')
        def layout(label, width):
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'), (page.url, width)
            expect(page.locator('h1')).to_have_count(1)
            page.screenshot(path=str(output / f'{label}-{width}.png'), full_page=True)
        def series_count(n):
            expect(page.locator('.series-card')).to_have_count(n)
        for width in (1440, 1100, 768, 390):
            page.set_viewport_size({'width': width, 'height': 960})
            go('matches')
            expect(page.get_by_label('Match team')).to_have_value('')
            series_count(4)
            page.get_by_label('Match team').select_option('blue'); series_count(3)
            assert 'team=blue' in page.url and 'season=' in page.url
            page.get_by_label('Opponent', exact=True).fill('uCf'); series_count(1)
            expect(page.locator('.series-maps>a')).to_have_count(2)
            layout('matches-blue-ucf', width)
            page.reload(wait_until='networkidle'); series_count(1)
            expect(page.get_by_label('Opponent', exact=True)).to_have_value('uCf')
            page.get_by_label('Match sort').select_option('oldest'); series_count(1)
            page.go_back(wait_until='networkidle')
            expect(page.get_by_label('Match sort')).to_have_value('newest')
            page.go_forward(wait_until='networkidle')
            expect(page.get_by_label('Match sort')).to_have_value('oldest')
            page.get_by_label('Opponent', exact=True).fill('Georgia Tech'); series_count(0)
            expect(page.locator('.empty')).to_contain_text('Georgia Tech')
            expect(page.locator('.empty')).to_contain_text('UAH Blue')
            page.locator('.empty').get_by_role('button', name='Clear filters').click(); series_count(4)
            expect(page.get_by_label('Match team')).to_have_value('')
            page.get_by_label('Opponent', exact=True).fill('mich'); series_count(1)
            expect(page.locator('.series-card')).to_contain_text('University of Michigan')
            go('matches?team=invalid&sort=invalid&season=invalid'); series_count(4)
            expect(page.get_by_label('Match team')).to_have_value('')
            expect(page.get_by_label('Match sort')).to_have_value('newest')
            go('teams/white/matches?team=blue&opponent=FSU&season=career')
            expect(page.get_by_label('Match team')).to_have_count(0); series_count(1)
            expect(page.locator('.series-card')).to_contain_text('UAH White')
            expect(page.get_by_label('Statistics period')).to_have_value('career')
            layout('white-team-matches', width)
            page.get_by_role('navigation', name='Team navigation').get_by_role('link', name='Maps', exact=True).click()
            expect(page.locator('.map-analytics-card')).to_have_count(26)
            assert 'season=career' in page.url
            expect(page.get_by_role('navigation', name='Team navigation').get_by_role('link', name='Maps', exact=True)).to_have_attribute('aria-current', 'page')
            page.get_by_label('Statistics period').select_option(season)
            for team in ('blue', 'white'):
                page.get_by_label('Public team').select_option(team)
                expect(page.locator('.map-analytics-card')).to_have_count(26)
                data = load(f'teams/{team}/maps/{season}.json')
                assert page.locator('.map-analytics-card>h3').all_text_contents() == [m['name'] for m in data['maps']]
                for m in data['maps']:
                    card = page.locator('.map-analytics-card').filter(has=page.get_by_role('link', name=m['name'], exact=True))
                    if not m['maps_played']:
                        expect(card).to_contain_text('No recorded maps yet.')
                        expect(card.locator('.map-round-stat,.map-record')).to_have_count(0)
                    else:
                        expect(card.locator('.map-record')).to_contain_text(f"{m['map_wins']}–{m['map_losses']}")
                layout(f'{team}-maps', width)
            requests.clear()
            go(f'teams/blue/maps/nighthaven-labs?season={season}')
            expect(page.locator('.map-detail-hero h2')).to_have_text('Nighthaven Labs')
            expect(page.locator('.map-round-stat strong')).to_have_text(['77.8%', '100%', '66.7%'])
            expect(page.locator('.map-round-stat small')).to_have_text(['7–2 · 9 rounds', '3–0 · 3 rounds', '4–2 · 6 rounds'])
            expect(page.locator('.map-sites').nth(0)).to_contain_text('2F Command Center / 2F Servers')
            expect(page.locator('.map-history a')).to_have_count(1)
            assert not [r for r in requests if '/data/matches/' in r], requests
            layout('blue-nighthaven-detail', width)
            page.get_by_label('Public team').select_option('white')
            expect(page.locator('.map-round-stat small')).to_have_text(['6–8 · 14 rounds', '3–4 · 7 rounds', '3–4 · 7 rounds'])
            layout('white-nighthaven-detail', width)
            page.get_by_label('Statistics period').select_option('career')
            page.reload(wait_until='networkidle')
            expect(page.get_by_label('Statistics period')).to_have_value('career')
            expect(page.locator('.map-round-stat small').nth(0)).to_have_text('6–8 · 14 rounds')
            page.locator('.map-history a').click()
            expect(page.locator('.map-hero')).to_contain_text('FSU')
            go('teams/blue/maps/clubhouse?season='+season)
            expect(page.locator('.map-detail-hero')).to_contain_text('No recorded maps yet.')
            expect(page.locator('.map-round-stat,.map-sites,.map-history')).to_have_count(0)
            layout('unplayed-detail', width)
            go('teams/blue/maps/invalid-map')
            expect(page.locator('.empty')).to_contain_text('Map not found')
            checks.append(f'{width}px: filters, history, scope, period, catalog, details, samples, links and layout')
        # Fixture-only future team, empty season, unknown site, and independent side records.
        fixture_index = deepcopy(index)
        future = {**index['teams'][0], 'id': 99, 'slug': 'future', 'name': 'Future Team', 'aliases': [], 'maps': 0, 'rounds': 0, 'roster_count': 0}
        fixture_index['teams'].append(future)
        fixture_index['seasons'].append({'slug': 'empty', 'name': 'Empty season'})
        def fixtures(route):
            path = route.request.url.split('/data/', 1)[-1].split('?', 1)[0]
            if path == 'index.json':
                route.fulfill(json=fixture_index)
            elif path == 'teams/future/empty.json':
                route.fulfill(json={'team': future, 'slug': 'empty', 'name': 'Empty season', 'maps': 0, 'wins': 0, 'rounds': 0, 'players': [], 'matches': []})
            elif path == 'teams/future/maps/empty.json':
                data = deepcopy(load(f'teams/white/maps/{season}.json'))
                data.update(team_slug='future', period='empty', period_name='Empty season')
                for m in data['maps']:
                    m.update(maps_played=0, map_wins=0, map_losses=0, rounds=0, wins=0, losses=0, matches=[])
                    m.update(attack={'rounds':0,'wins':0,'losses':0}, defense={'rounds':0,'wins':0,'losses':0}, unknown_side={'rounds':0,'wins':0,'losses':0}, sites={'Attack':[],'Defense':[],'Unknown':[]})
                route.fulfill(json=data)
            elif path == f'teams/blue/maps/{season}.json':
                data = deepcopy(load(path))
                m = next(m for m in data['maps'] if m['slug'] == 'nighthaven-labs')
                m['sites']['Defense'] = [dict(site='',unknown=True,rounds=2,wins=2,losses=0),dict(site='Known singleton',unknown=False,rounds=1,wins=1,losses=0)]
                route.fulfill(json=data)
            else:
                route.continue_()
        page.route('**/data/**', fixtures)
        go('matches')
        page.reload(wait_until='networkidle')
        expect(page.get_by_label('Match team').get_by_role('option',name='Future Team')).to_have_count(1)
        go('teams/future/maps?season=empty')
        expect(page.locator('.map-analytics-card.unplayed')).to_have_count(26)
        expect(page.locator('.map-round-stat')).to_have_count(0)
        layout('future-empty-fixture', 390)
        go('teams/blue/maps?season='+season)
        card=page.locator('.map-analytics-card').filter(has=page.get_by_role('link',name='Nighthaven Labs',exact=True))
        expect(card.locator('.map-site-summary').nth(0)).to_contain_text('Limited sample')
        go('teams/blue/maps/nighthaven-labs?season='+season)
        expect(page.locator('.map-sites').nth(0)).to_contain_text('Unknown site')
        layout('unknown-site-fixture', 390)
        page.unroute('**/data/**', fixtures)
        assert not errors, errors
        assert not mutations, mutations
        browser.close()
    result = dict(status='PASS', url=url, widths=[1440,1100,768,390], checks=checks,
                  fixtures=['future team','empty season','unknown site excluded from best ranking'], javascript_errors=errors, mutations=mutations)
    (output / 'match-maps-ui.json').write_text(json.dumps(result, indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--url'); parser.add_argument('--output',type=Path,default=ROOT/'data/research/match-map-analytics-20261008/browser')
    args=parser.parse_args()
    if args.url:
        verify(args.url,args.output)
    else:
        class Quiet(SimpleHTTPRequestHandler):
            def log_message(self,*_): pass
            def copyfile(self,source,output):
                try: super().copyfile(source,output)
                except ConnectionError: pass
        server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT/'web/dist')))
        threading.Thread(target=server.serve_forever,daemon=True).start()
        try: verify(f'http://127.0.0.1:{server.server_port}/',args.output)
        finally: server.shutdown()
