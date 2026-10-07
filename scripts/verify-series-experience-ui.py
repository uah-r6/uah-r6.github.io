"""Read-only series/trend/highlight browser checks against built or live exports."""
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
    series = [load(f'series/{sid}.json') for sid in ('170b708e12f1', '1a106d1b2f89', '40bf93b16f97')]
    profile = load('players/lgon/fall-2026.json')
    errors, checks = [], []
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=True)
        page = browser.new_page(viewport={'width': 1440, 'height': 960})
        page.on('pageerror', lambda e: errors.append(str(e)))
        for width in (1440, 1150, 768, 390):
            page.set_viewport_size({'width': width, 'height': 960})
            for doc in series:
                page.goto(url + '#/series/' + doc['id'], wait_until='networkidle')
                expect(page.locator('h1')).to_have_text('vs ' + doc['opponent'])
                expect(page.locator('.recorded-score')).to_contain_text(f"{doc['recorded_maps']['wins']}–{doc['recorded_maps']['losses']}")
                expect(page.locator('.series-map-summary a')).to_have_count(len(doc['maps']))
                expect(page.locator('.match-card')).to_have_count(len(doc['maps']))
                if width > 540:
                    expect(page.locator('tbody tr')).to_have_count(len(doc['players']))
                    for row, player in zip(page.locator('tbody tr').all(), doc['players']):
                        expect(row.locator('td').nth(1)).to_contain_text(f"{player['rating']:.2f}")
                        expect(row.locator('.rating-coverage')).to_contain_text(f"{player['rating_rounds']} / {player['rounds']} rounds rated")
                else:
                    expect(page.locator('.mobile-player')).to_have_count(len(doc['players']))
                    for card, player in zip(page.locator('.mobile-player').all(), doc['players']):
                        expect(card.locator('.mobile-rating strong')).to_have_text(f"{player['rating']:.2f}")
                        expect(card.locator('.rating-coverage')).to_contain_text(f"{player['rating_maps']} / {player['maps']} maps rated")
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1'), (width, doc['id'])
                page.screenshot(path=str(output / f"series-{doc['id']}-{width}.png"), full_page=True)
            page.goto(url + '#/players/lgon', wait_until='networkidle')
            expect(page.locator('.trend-point')).to_have_count(3)
            for i, (rating, opponent, coverage) in enumerate((('1.50', 'Placements', '1 / 3 maps rated'), ('1.43', 'University of Michigan', '1 / 2 maps rated'), ('1.42', 'UCF', '2 / 2 maps rated'))):
                point = page.locator('.trend-point').nth(i)
                point.hover()
                expect(page.locator('.exact-series-rating')).to_contain_text(rating)
                point.focus()
                expect(page.locator('.trend-detail')).to_contain_text(opponent)
                point.click()
                expect(page.locator('.trend-coverage')).to_contain_text(coverage)
                assert page.locator('.exact-series-rating').evaluate('e=>parseFloat(getComputedStyle(e).fontSize)') >= 24
                assert point.get_attribute('aria-describedby') == page.locator('.trend-detail').get_attribute('id')
            page.screenshot(path=str(output / f'trend-{width}.png'), full_page=True)
            page.locator('.trend-context a').click()
            expect(page.locator('h1')).to_have_text('vs UCF')
            page.locator('.series-map-summary a').first.click()
            expect(page.locator('h1')).to_contain_text('Nighthaven Labs')
            page.get_by_role('link', name='Back to series').click()
            expect(page.locator('h1')).to_have_text('vs UCF')
        checks.append('all three real series: exact five-player Ratings/coverage, map links and prominent hover/focus/click trend values at 1440/1150/768/390px')
        page.goto(url + '#/matches', wait_until='networkidle')
        expect(page.locator('.series-summary-link')).to_have_count(3)
        page.locator('.series-summary-link').first.click()
        expect(page.locator('h1')).to_have_text('vs UCF')
        checks.append('Matches → series → map → series and trend → series navigation')

        highlighted, total = 0, 0
        for width in (1440, 1150, 768, 390):
            page.set_viewport_size({'width': width, 'height': 960})
            for path in sorted((DATA / 'matches').glob('*.json')):
                doc = json.loads(path.read_text(encoding='utf-8'))
                page.goto(url + '#/matches/' + doc['id'], wait_until='networkidle')
                expect(page.locator('.curated-round')).to_have_count(len(doc['rounds']))
                for row, round_ in zip(page.locator('.curated-round').all(), doc['rounds']):
                    groups = round_['highlights']
                    expect(row.locator('.highlight-pill')).to_have_count(len(groups))
                    assert len(groups) <= 2
                    for pill, group in zip(row.locator('.highlight-pill').all(), groups):
                        assert len(group['labels']) <= 2
                        expect(pill).to_have_attribute('aria-label', f"{group['player_name']}: {', '.join(group['labels'])}")
                        expect(pill).to_have_attribute('href', '#/players/' + group['player_slug'])
                        box = pill.bounding_box()
                        assert box['x'] >= 0 and box['x'] + box['width'] <= width + 1, (width, doc['id'], round_['number'], box)
                    if width == 1440:
                        total += 1
                        highlighted += bool(groups)
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1'), (width, doc['id'])
                if doc['id'] in ('d64d5478cdb3', '076d2b6b02bc', 'b595ffaaec57'):
                    page.screenshot(path=str(output / f"breakdown-{doc['id']}-{width}.png"), full_page=True)
        assert (highlighted, total) == (31, 82)
        checks.append('all 82 actual logical rounds: 31 highlighted/51 empty; max two groups/two labels, no overflow, exact safe export labels')

        fixture = browser.new_page(viewport={'width': 1440, 'height': 960}, has_touch=True)
        fixture.on('pageerror', lambda e: errors.append(str(e)))
        unrated = deepcopy(series[-1])
        for player in unrated['players']:
            player.update(rating=None, rating_maps=0, rating_rounds=0, status='Alumni')
        fixture.route('**/data/series/' + unrated['id'] + '.json', lambda r: r.fulfill(json=unrated))
        fixture.goto(url + '#/series/' + unrated['id'], wait_until='networkidle')
        expect(fixture.locator('tbody tr')).to_have_count(5)
        expect(fixture.locator('.unrated-series')).to_be_visible()
        for row in fixture.locator('tbody tr').all():
            assert row.locator('td').nth(1).inner_text().startswith('—')
        assert '0.00' not in fixture.locator('tbody').inner_text()
        fixture.set_viewport_size({'width': 390, 'height': 900})
        expect(fixture.locator('.mobile-player')).to_have_count(5)
        expect(fixture.locator('.mobile-rating strong').first).to_have_text('—')
        checks.append('entirely unrated series and historical Alumni remain visible on desktop/mobile, never fake 0.00')
        fixture.unroute('**/data/series/' + unrated['id'] + '.json')
        for points in ([], profile['series_ratings'][:1]):
            fixture.route('**/data/players/lgon/fall-2026.json', lambda r, request, rows=points: r.fulfill(json={**profile, 'series_ratings': rows}))
            fixture.goto(url + '#/players/lgon', wait_until='networkidle')
            fixture.reload(wait_until='networkidle')
            expect(fixture.locator('.trend-point')).to_have_count(len(points))
            if not points:
                expect(fixture.get_by_text('No eligible Series Ratings yet.', exact=True)).to_be_visible()
            else:
                fixture.locator('.trend-point').first.tap()
                expect(fixture.locator('.exact-series-rating')).to_contain_text(f"{points[0]['rating']:.2f}")
                expect(fixture.locator('.trend-detail')).to_contain_text(points[0]['opponent'])
            fixture.unroute('**/data/players/lgon/fall-2026.json')
        career = load('players/lgon/career.json')
        future = {**profile['series_ratings'][0], 'id': 'white-series', 'series_id': 'white-series', 'date': '2027-02-01', 'season': 'spring-2027', 'season_name': 'Spring 2027', 'team_slug': 'white', 'team_name': 'UAH White', 'rating': 1.23}
        fixture.route('**/data/players/lgon/career.json', lambda r: r.fulfill(json={**career, 'series_ratings': career['series_ratings'] + [future]}))
        fixture.get_by_label('Statistics period').select_option('career')
        expect(fixture.locator('.trend-point')).to_have_count(4)
        fixture.locator('.trend-point').last.click()
        expect(fixture.locator('.trend-detail')).to_contain_text('UAH White')
        expect(fixture.locator('.exact-series-rating')).to_contain_text('1.23')
        fixture.get_by_label('Statistics period').select_option('fall-2026')
        expect(fixture.locator('.trend-point')).to_have_count(3)
        checks.append('single/empty trend and chronological career across teams with team context; season excludes future series')
        fixture.close()
        page.goto(url + '#/series/missing', wait_until='networkidle')
        expect(page.locator('h1')).to_have_text('Series not found')
        page.goto(url + '#/', wait_until='networkidle')
        expect(page.locator('footer time')).to_have_attribute('datetime', load('index.json')['generated_at'])
        page.goto(url + '#/submit', wait_until='domcontentloaded')
        expect(page.locator('h1')).to_have_text('Submit Replays')
        assert not errors, errors
        browser.close()
    report = {'status': 'PASS', 'url': url, 'checks': checks, 'javascript_errors': errors}
    (output / 'series-ui.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--url')
    ap.add_argument('--output', type=Path, default=ROOT / 'data/research/series-experience-20261007/browser')
    args = ap.parse_args()
    if args.url:
        verify(args.url, args.output)
    else:
        handler = functools.partial(SimpleHTTPRequestHandler, directory=str(ROOT / 'web/dist'))
        server = ThreadingHTTPServer(('127.0.0.1', 0), handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            verify(f'http://127.0.0.1:{server.server_port}/', args.output)
        finally:
            server.shutdown()
            server.server_close()
