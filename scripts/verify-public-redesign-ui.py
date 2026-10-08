"""Read-only public redesign regression; future teams/transfers use browser fixtures."""
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


def verify(url, output, admin):
    output.mkdir(parents=True, exist_ok=True)
    index = load('index.json'); season = index['active_season']
    program = load(f'seasons/{season}.json')
    series = [load(str(p.relative_to(DATA))) for p in sorted((DATA / 'series').glob('*.json'))]
    maps = [load(str(p.relative_to(DATA))) for p in sorted((DATA / 'matches').glob('*.json'))]
    errors, checks, mutations = [], [], []
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=True)
        page = browser.new_page(viewport={'width':1440, 'height':960})
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.on('request', lambda r: mutations.append(r.url) if r.method not in ('GET', 'HEAD', 'OPTIONS') and '/api/' in r.url else None)

        def go(route):
            page.goto(url + '#/' + route, wait_until='networkidle')

        def layout():
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'), page.url
            for node in page.locator('.hero-identity,.team-card-identity,.series-card-identity').all():
                image = node.locator('.team-logo').bounding_box()
                text = node.locator(':scope > div').bounding_box()
                if image and text and abs(image['y']-text['y']) < image['height']:
                    assert image['x'] + image['width'] <= text['x'] + 1, (page.url, image, text)
            for im in page.locator('.team-logo img').all():
                assert im.evaluate('e=>e.complete&&e.naturalWidth===1080&&getComputedStyle(e).objectFit==="contain"')

        def exact_players(data):
            if page.viewport_size['width'] <= 600:
                for item in data['players']:
                    card = page.locator('.mobile-player').filter(has=page.get_by_role('link', name=item['name'], exact=False))
                    expect(card.locator('.mobile-rating>strong')).to_have_text(f'{item["rating"]:.2f}' if item['rating'] is not None else '—')
            else:
                for item in data['players']:
                    row = page.locator('tbody tr').filter(has=page.get_by_role('link', name=item['name'], exact=False))
                    assert row.locator('td.rating').evaluate('e=>e.firstChild.textContent.trim()') == (f'{item["rating"]:.2f}' if item['rating'] is not None else '—')
                    if 'rating_rounds' in item and 'maps' in item:
                        expect(row.locator('td.rating')).to_have_attribute('title',f'Rating coverage: {item["rating_rounds"]} of {item["rounds"]} rounds across {item["rating_maps"]} of {item["maps"]} maps')

        routes = ['']
        routes += [f'teams/{slug}{suffix}' for slug in ('blue','white') for suffix in ('','/roster','/stats','/matches')]
        routes += ['players?team=blue','players?team=white','players/lgon','players/flex-uah','players/dinoted11?stats=subs&team=white']
        routes += [f'series/{s["id"]}' for s in series] + [f'matches/{m["id"]}' for m in maps]
        routes += ['matches','methodology','methodology/rating','submit','embed/blue/player-stats','embed/white/player-stats']
        for width in (1440,1100,768,390):
            page.set_viewport_size({'width':width,'height':960})
            for route in routes:
                go(route); layout()
                if not route.startswith('embed/'):
                    expect(page.locator('h1')).to_have_count(1)
                if route == '':
                    expect(page.locator('.team-grid .team-card')).to_have_count(2)
                    expect(page.locator('.program-summary dd').nth(1)).to_have_text(str(program['maps']))
                    expect(page.locator('.program-summary dd').nth(2)).to_have_text(str(len(series)))
                    for team in index['teams']:
                        card = page.locator('.team-card').filter(has_text=team['name'])
                        expect(card.locator('.team-logo img')).to_have_attribute('src','/brand/teams/'+team['slug']+'.png')
                elif route.startswith('teams/'):
                    slug = route.split('/')[1]; data = load(f'teams/{slug}/{season}.json')
                    expect(page.locator('.team-header h1')).to_have_text(data['team']['name'])
                    expect(page.locator('.team-header .team-logo img')).to_have_attribute('src','/brand/teams/'+slug+'.png')
                    expect(page.locator('.hero-facts dd').nth(0)).to_have_text(f'{data["wins"]}–{data["maps"]-data["wins"]}')
                    suffix = route.split('/')[-1]
                    active = {'blue':'Overview','white':'Overview','roster':'Roster','stats':'Player Stats','matches':'Matches'}[suffix]
                    expect(page.get_by_role('navigation',name='Team navigation').get_by_role('link',name=active,exact=True)).to_have_attribute('aria-current','page')
                    if suffix in ('blue','white'):
                        expected = [f'{data["wins"]}–{data["maps"]-data["wins"]}',str(data['maps']),str(data['rounds_won']),f'{round(data["rounds_won"]/data["rounds"]*100)}%']
                        assert page.locator('.season-numbers strong').all_text_contents() == expected
                    if suffix in ('stats','blue','white'): exact_players(data)
                elif route.startswith('series/'):
                    data = next(s for s in series if s['id']==route.split('/')[1])
                    expect(page.locator('.series-hero h1')).to_have_text('vs '+data['opponent'])
                    expect(page.locator('.series-hero .score-display')).to_have_attribute('data-score',f'{data["recorded_maps"]["wins"]}-{data["recorded_maps"]["losses"]}')
                    expect(page.locator('.map-summary-card')).to_have_count(len(data['maps']))
                    for m in data['maps']:
                        card = page.locator(f'.map-summary-card[href="#/matches/{m["id"]}"]')
                        expect(card.locator('h2')).to_have_text(m['map'])
                        assert card.locator('dd').all_text_contents()==[str(m['our_score']),str(m['their_score'])]
                        expect(card.locator('.badge')).to_have_text(m['result'])
                    exact_players(data)
                elif route.startswith('matches/'):
                    data = next(m for m in maps if m['id']==route.split('/')[1])
                    expect(page.locator('.map-hero h1')).to_have_text(data['map'])
                    expect(page.locator('.map-hero')).to_contain_text(data['team_name'])
                    expect(page.locator('.map-hero')).to_contain_text('vs '+data['opponent'])
                    expect(page.locator('.map-hero .score-display')).to_have_attribute('data-score',f'{data["our_score"]}-{data["their_score"]}')
                    exact_players(data)
                elif route in ('players/lgon','players/flex-uah'):
                    data = load(route+'/'+season+'.json')
                    expect(page.locator('.profile-head h1')).to_have_text(data['name'])
                    assert page.locator('.profile-key-stats dd').all_text_contents() == [f'{data["rating"]:.2f}',f'{data["kills"]}–{data["deaths"]}',f'{round(data["kost"]*100)}%',f'{data["opening_kills"]}–{data["opening_deaths"]}']
                    expect(page.locator('.profile-head .team-logo img')).to_have_attribute('src','/brand/teams/'+data['team_splits'][0]['team_slug']+'.png')
                elif route.startswith('embed/'):
                    assert page.locator('.embed-team-identity').bounding_box()['height'] <= 38
                    assert page.locator('.public-hero,.topbar').count()==0
                page.screenshot(path=str(output / f'{route.replace("/","-").replace("?","-") or "home"}-{width}.png'), full_page=True)
                page.screenshot(path=str(output / f'viewport-{route.replace("/","-").replace("?","-") or "home"}-{width}.png'))
        checks.append(f'{len(routes)} actual routes at four widths: exact records/map scores/Ratings, ownership, nav states, headings, compact embeds and no page overflow')

        page.set_viewport_size({'width':1440,'height':960})
        go('teams/blue/stats?players=subs')
        page.get_by_label('Public team').select_option('white')
        expect(page).to_have_url(url+'#/teams/white/stats?players=subs')
        expect(page.get_by_role('button',name='Subs',exact=True)).to_have_attribute('aria-pressed','true')
        page.get_by_role('button',name='Roster',exact=True).click()
        expect(page).to_have_url(url+'#/teams/white/stats')
        go('players?team=blue')
        page.get_by_role('button',name='Rating',exact=True).click()
        sort = page.locator('th[data-stat=rating]').get_attribute('aria-sort')
        page.get_by_label('Statistics period').select_option('career')
        page.get_by_label('Team',exact=True).select_option('white')
        expect(page.get_by_label('Statistics period')).to_have_value('career')
        expect(page.locator('th[data-stat=rating]')).to_have_attribute('aria-sort',sort)
        page.get_by_role('button',name='About KOST',exact=True).focus()
        expect(page.get_by_role('dialog',name='KOST explained')).to_be_visible()
        page.keyboard.press('Escape')
        go('players/lgon')
        history=load('players/lgon/'+season+'.json')['series_ratings']
        complete=[s for s in history if s['rating'] is not None]
        expect(page.locator('.rating-trend svg')).to_have_count(int(len(complete)>=2))
        expect(page.locator('.trend-point')).to_have_count(len(complete) if len(complete)>=2 else 0)
        expect(page.locator('.trend-detail')).to_contain_text('UCF')
        checks.append('team switch retains section/Sub query; main selector preserves Career/sort; keyboard stat help and complete-only compact Series Rating summary retained')

        fixture = browser.new_page(viewport={'width':390,'height':960})
        fixture.on('pageerror',lambda e: errors.append(str(e)))
        future=deepcopy(index);base=load(f'teams/blue/{season}.json')
        for i,(slug,color) in enumerate((('grey','#63666A'),('black','#2C2A29'),('gold','#FDDA24')),3):
            team={**index['teams'][0],'id':i,'slug':slug,'name':'UAH '+slug.title(),'primary_color':color,'maps':0,'rounds':0,'roster_count':0}
            future['teams'].append(team)
            def handler(team):
                return lambda r:r.fulfill(json={**base,'team':team,'maps':0,'rounds':0,'wins':0,'rounds_won':0,'players':[],'matches':[],'roster':[]})
            fixture.route(f'**/data/teams/{slug}/*.json',handler(team))
        fixture.route('**/data/index.json',lambda r:r.fulfill(json=future))
        fixture.goto(url+'#/',wait_until='networkidle')
        expect(fixture.locator('.team-grid .team-card')).to_have_count(5)
        for slug in ('grey','black','gold'):
            card=fixture.locator(f'.team-card[href="#/teams/{slug}"]')
            expect(card.locator('.team-card-empty')).to_contain_text('No matches recorded')
            expect(card.locator('.team-card-record')).to_have_count(0)
        for slug in ('grey','black','gold'):
            fixture.goto(url+'#/teams/'+slug,wait_until='networkidle')
            suffix='teams/'+slug+'.png' if slug!='gold' else 'uah-esports-logo.png'
            expect(fixture.locator('.team-header .team-logo img')).to_have_attribute('src','/brand/'+suffix)
            expect(fixture.locator('.hero-facts dd').first).to_have_text('—')
            assert fixture.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
            fixture.screenshot(path=str(output / f'empty-{slug}-390.png'),full_page=True)
        fixture.close()

        fixture=browser.new_page(viewport={'width':1440,'height':960})
        fixture.on('pageerror',lambda e: errors.append(str(e)))
        data=load('players/lgon/career.json')
        data['team_splits'].append({**data['team_splits'][0],'team_slug':'white','team_name':'UAH White'})
        fixture.add_init_script("sessionStorage.setItem('necc-period-session',JSON.stringify({period:'career',at:Date.now()}))")
        fixture.route('**/data/players/lgon/career.json',lambda r:r.fulfill(json=data))
        fixture.goto(url+'#/players/lgon',wait_until='networkidle')
        expect(fixture.locator('.profile-head .team-logo img')).to_have_attribute('src','/brand/uah-esports-logo.png')
        expect(fixture.locator('.profile-team-chips a')).to_have_count(2)
        expect(fixture.locator('.profile-head')).to_contain_text('Global career')
        expect(fixture.locator('.profile-key-stats dd').first).to_have_text(f'{data["rating"]:.2f}')
        fixture.screenshot(path=str(output/'multi-team-career.png'),full_page=True)
        fixture.close()
        checks.append('Grey/Black/unknown empty-team fixtures retain contrast/fallback without fake records; multi-team Career uses program mark and contribution chips without changing Rating')

        page.get_by_label('Statistics period').select_option(season)
        page.route('**/brand/teams/blue.png',lambda r:r.fulfill(status=404,body='missing image fixture'))
        go('teams/blue'); page.reload(wait_until='networkidle')
        expect(page.locator('.team-header .team-logo img')).to_have_attribute('src','/brand/uah-esports-logo.png')
        page.unroute('**/brand/teams/blue.png')
        page.emulate_media(reduced_motion='reduce')
        go('')
        assert page.locator('.team-card').first.evaluate('e=>getComputedStyle(e).transitionDuration')=='0s'
        checks.append('missing team image falls back safely; reduced motion disables card transitions')

        if admin:
            ap=browser.new_page(viewport={'width':390,'height':960})
            ap.on('pageerror',lambda e:errors.append(str(e)))
            def readonly(r):
                if r.request.method not in ('GET','HEAD','OPTIONS'):mutations.append(r.request.url);r.abort()
                else:r.continue_()
            ap.route('**/api/admin/**',readonly)
            ap.goto(admin,wait_until='networkidle')
            for width in (1440,1100,768,390):
                ap.set_viewport_size({'width':width,'height':960})
                for slug,tid in (('blue','1'),('white','2')):
                    ap.get_by_label('Active admin team').select_option(tid)
                    expect(ap.locator('.admin-context .team-logo img')).to_have_attribute('src','/brand/teams/'+slug+'.png')
                    assert ap.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                    ap.screenshot(path=str(output/f'admin-{slug}-{width}.png'),full_page=True)
            ap.close();checks.append('actual launcher admin remains responsive for both teams with no API mutations')
        assert not mutations,mutations
        assert not errors,errors
        browser.close()
    report=dict(status='PASS',url=url,routes=len(routes),widths=[1440,1100,768,390],checks=checks,javascript_errors=errors,api_mutations=mutations)
    (output/'public-redesign-ui.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--url');ap.add_argument('--admin',default='http://127.0.0.1:8000/admin');ap.add_argument('--output',type=Path,default=ROOT/'data/research/public-redesign-20261008/browser');args=ap.parse_args()
    if args.url:verify(args.url,args.output,args.admin)
    else:
        class Quiet(SimpleHTTPRequestHandler):
            def log_message(self,*_):pass
            def copyfile(self,source,output):
                try:super().copyfile(source,output)
                except ConnectionError:pass
        server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT/'web/dist')))
        threading.Thread(target=server.serve_forever,daemon=True).start()
        try:verify(f'http://127.0.0.1:{server.server_port}/',args.output,args.admin)
        finally:server.shutdown()
