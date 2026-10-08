"""Complete-only Series Rating browser regression, with read-only public/fixture data."""
import argparse
from copy import deepcopy
import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import math
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
    lgon = load(f'players/lgon/{season}.json')
    series = [load('series/'+p.name) for p in sorted((DATA/'series').glob('*.json'))]
    profiles = [p['slug'] for p in index['players'] if load(f"players/{p['slug']}/{season}.json").get('series_ratings')]
    errors, mutations, checks = [], [], []
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=True)
        page = browser.new_page(viewport={'width':1440,'height':960}, has_touch=True)
        page.on('pageerror', lambda e:errors.append(str(e)))
        def readonly(route):
            if route.request.method not in ('GET','HEAD','OPTIONS'):
                mutations.append(route.request.url);route.abort()
            else:route.continue_()
        page.route('**/*', readonly)

        def layout():
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'), page.url

        def capture(label, width):
            layout()
            page.screenshot(path=str(output/f'{label}-{width}.png'), full_page=True)
            if page.locator('.rating-trend').count():
                page.locator('.rating-trend').screenshot(path=str(output/f'panel-{label}-{width}.png'))

        for width in (1440,1100,768,390):
            page.set_viewport_size({'width':width,'height':960})
            for slug in profiles:
                data = load(f'players/{slug}/{season}.json')
                page.goto(url+'#/players/'+slug, wait_until='networkidle')
                complete = [s for s in data['series_ratings'] if s['rating'] is not None]
                count=len(complete)
                expect(page.locator('.rating-trend svg')).to_have_count(int(count>=2))
                expect(page.locator('.trend-point')).to_have_count(count if count>=2 else 0)
                expect(page.locator('.trend-point-partial,.trend-partial-label')).to_have_count(0)
                expect(page.locator('.recent-rating button')).to_have_count(count if count>=2 else 0)
                if count==1:
                    expect(page.locator('.trend-pending')).to_contain_text('another fully rated series')
                    expect(page.locator('.exact-series-rating')).to_contain_text(f"{complete[0]['rating']:.2f}")
                else:
                    expect(page.locator('.trend-pending')).to_have_count(0)
                    for point in page.locator('.trend-point').all():
                        assert 'complete Series Rating' in point.get_attribute('aria-label')
                        point.hover();point.focus();point.click();point.tap();layout()
                    page.locator('.recent-rating button').last.click()
                expect(page.locator('.trend-heading .section-aside')).to_have_text(f"{count} of {len(data['series_ratings'])} series "+('has a complete Rating' if count==1 else 'have complete Ratings'))
                expect(page.locator('.trend-detail')).to_contain_text(complete[0]['opponent'])
                expect(page.locator('.profile-key-stats dd').first).to_have_text(f"{data['rating']:.2f}")
                assert page.locator('.rating-trend').bounding_box()['height']<(430 if count==1 else 750)
                capture('profile-'+slug,width)
            for doc in series:
                page.goto(url+'#/series/'+doc['id'],wait_until='networkidle')
                expect(page.locator('.map-summary-card')).to_have_count(len(doc['maps']))
                for player in doc['players']:
                    rating = f"{player['rating']:.2f}" if player['rating'] is not None else '\u2014'
                    if width>600:
                        row=page.locator('tbody tr').filter(has=page.get_by_role('link',name=player['name'],exact=False))
                        assert row.locator('td.rating').evaluate('e=>e.firstChild.textContent.trim()')==rating
                        expect(row.locator('td.rating')).to_have_attribute('title', f"Rating coverage: {player['rating_rounds']} of {player['rounds']} rounds across {player['rating_maps']} of {player['maps']} maps")
                        expect(row.locator('td').nth(3)).to_have_text(f"{player['kills']}-{player['deaths']} ({'+' if player['kd_diff']>=0 else ''}{player['kd_diff']})")
                    else:
                        row=page.locator('.mobile-player').filter(has=page.get_by_role('link',name=player['name'],exact=False))
                        expect(row.locator('.mobile-rating>strong')).to_have_text(rating)
                        expect(row.locator('dd').first).to_have_text(f"{math.floor(player['kost']*100+.5)}%")
                    expect(row.locator('.rating-coverage')).to_contain_text(f"{player['rating_maps']} / {player['maps']} maps rated")
                    expect(row.locator('.rating-coverage')).to_contain_text(f"{player['rating_rounds']} / {player['rounds']} rounds rated")
                    if player['appearance_role']=='sub':expect(row.locator('.sub-badge')).to_have_text('SUB')
                if not any(p['rating'] is not None for p in doc['players']):
                    expect(page.locator('.unrated-series')).to_contain_text('Recorded performance is still shown')
                page.get_by_role('button',name='About Rating',exact=True).first.focus()
                expect(page.get_by_role('dialog',name='Rating explained')).to_be_visible()
                page.keyboard.press('Escape')
                capture('series-'+doc['id'],width)
            # Career must retain every complete series.
            page.goto(url+'#/players/lgon',wait_until='networkidle')
            page.get_by_label('Statistics period').select_option('career')
            expect(page.locator('.rating-trend svg')).to_have_count(1)
            expect(page.locator('.trend-point')).to_have_count(3)
            expect(page.locator('.trend-detail')).to_contain_text('UCF')
            capture('career-lgon',width)
            page.get_by_label('Statistics period').select_option(season)
        checks.append('all nine normal profiles and four actual series at four widths: five Blue profiles have three complete points; four White profiles retain compact single-series summaries; exact coverage/raw stats, SUB badge and Rating help')

        # No eligible series, stale partial numerics, and true multi-team 2+ history.
        complete = lgon['series_ratings'][0]
        incomplete = {**lgon['series_ratings'][1], 'rating':1.4342647708955862,'rating_maps':1,'rating_rounds':12}
        future = {**complete,'id':'fixture-white','series_id':'fixture-white','date':'2027-02-01',
                  'team_slug':'white','team_name':'UAH White','season':'spring-2027','season_name':'Spring 2027',
                  'opponent':'University of the Northern Lakes Competitive Rainbow Six Varsity Program', 'rating':1.23}
        cases = [('zero', [{**incomplete,'rating':None}]), ('stale-partial', [incomplete]),
                 ('one', [incomplete,complete]), ('two', [future,incomplete,complete])]
        for width in (1440,1100,768,390):
            page.set_viewport_size({'width':width,'height':960})
            for label,rows in cases:
                fixture = deepcopy(lgon);fixture['series_ratings']=rows
                if label=='two':fixture['team_splits'].append({**fixture['team_splits'][0],'team_slug':'white','team_name':'UAH White'})
                pattern=f'**/data/players/lgon/{season}.json'
                page.route(pattern,lambda r,request,data=fixture:r.fulfill(json=data))
                page.goto(url+'#/players/lgon',wait_until='networkidle');page.reload(wait_until='networkidle')
                count={'zero':0,'stale-partial':0,'one':1,'two':2}[label]
                expect(page.locator('.rating-trend svg')).to_have_count(int(count>=2))
                expect(page.locator('.trend-point')).to_have_count(count if count>=2 else 0)
                expect(page.locator('.trend-point-partial,.trend-partial-label')).to_have_count(0)
                if count==0:
                    expect(page.locator('.exact-series-rating')).to_have_count(0)
                    expect(page.locator('.trend-pending')).to_have_text('Rating trend will appear after two fully rated series.')
                    assert page.locator('.rating-trend').bounding_box()['height']<290
                elif count==1:
                    expect(page.locator('.exact-series-rating')).to_contain_text('1.42')
                    expect(page.locator('.trend-detail')).to_contain_text('UCF')
                else:
                    expect(page.locator('.profile-head .team-logo img')).to_have_attribute('src','/brand/uah-esports-logo.png')
                    expect(page.locator('.recent-rating button')).to_have_count(2)
                    for i,point in enumerate(page.locator('.trend-point').all()):
                        expect(point).to_have_attribute('role','button')
                        assert 'complete Series Rating' in point.get_attribute('aria-label')
                        point.hover();point.focus();point.click();point.tap()
                        expect(page.locator('.trend-detail')).to_contain_text([complete,future][i]['opponent'])
                        layout()
                        if i==1:capture('fixture-long-opponent',width)
                    page.locator('.trend-point').first.focus();page.keyboard.press('ArrowRight')
                    expect(page.locator('.trend-point').last).to_be_focused()
                    page.keyboard.press('Enter');expect(page.locator('.trend-detail')).to_contain_text('UAH White')
                    page.locator('.recent-rating button').first.click()
                    expect(page.locator('.trend-detail')).to_contain_text('UCF')
                    expect(page.locator('.trend-coverage')).to_contain_text('20 / 20 rounds rated')
                    page.locator('.trend-context a').focus()
                capture('fixture-'+label,width)
                page.unroute(pattern)
        checks.append('zero/one/two complete states plus stale partial numerics; no SVG below two; only two complete controls; keyboard/hover/click, long opponent and multiple-team context at all widths')

        page.goto(url+'#/players/lgon',wait_until='networkidle')
        page.locator('.trend-context a').click();expect(page.locator('h1')).to_have_text('vs UCF')
        page.locator('.map-summary-card').first.click()
        expect(page.locator('.map-hero h1')).to_have_text('Nighthaven Labs')
        page.get_by_role('link',name='Back to series').click();expect(page.locator('h1')).to_have_text('vs UCF')
        page.goto(url+'#/methodology/rating',wait_until='networkidle')
        page.locator('summary').filter(has_text='Series Rating').click()
        expect(page.get_by_text('It is not estimated from the remaining maps.',exact=False)).to_be_visible()
        checks.append('latest complete Rating links to series/map/back; methodology explains complete-only evidence')
        assert not errors,errors
        assert not mutations,mutations
        browser.close()
    report=dict(status='PASS',url=url,widths=[1440,1100,768,390],profiles=len(profiles),series=len(series),checks=checks,javascript_errors=errors,mutations=mutations)
    (output/'complete-series-ui.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--url');ap.add_argument('--output',type=Path,default=ROOT/'data/research/series-completeness-20261008/browser');args=ap.parse_args()
    if args.url:verify(args.url,args.output)
    else:
        class Quiet(SimpleHTTPRequestHandler):
            def log_message(self,*_):pass
            def copyfile(self,source,output):
                try:super().copyfile(source,output)
                except ConnectionError:pass
        server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT/'web/dist')))
        threading.Thread(target=server.serve_forever,daemon=True).start()
        try:verify(f'http://127.0.0.1:{server.server_port}/',args.output)
        finally:server.shutdown()
