"""Read-only branding regression against a build or deployed Pages and real admin.

Future teams and failed assets use browser fixtures; no production records change.
"""
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


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def verify(url, output, admin):
    output.mkdir(parents=True, exist_ok=True)
    index = load(DATA / 'index.json')
    season = index['active_season']
    assert {t['slug'] for t in index['teams']} == {'blue', 'white'}
    series = [load(p) for p in sorted((DATA / 'series').glob('*.json'))]
    maps = [load(p) for p in sorted((DATA / 'matches').glob('*.json'))]
    errors, checks, alpha = [], [], {}
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=True)
        page = browser.new_page(viewport={'width':1440, 'height':960})
        page.on('pageerror', lambda e: errors.append(str(e)))

        def go(route):
            page.goto(url + '#/' + route, wait_until='networkidle')

        def logo(slug, scope='.team-logo'):
            node = page.locator(scope).filter(has=page.locator(f'img[src$="/teams/{slug}.png"]'))
            expect(node).to_have_count(1)
            expect(node.locator('img')).to_have_attribute('alt', '')
            assert node.locator('img').evaluate('e=>e.complete&&e.naturalWidth===1080&&e.naturalHeight===1080')
            assert node.locator('img').evaluate('e=>getComputedStyle(e).objectFit') == 'contain'
            return node

        def layout():
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'), page.url
            for node in page.locator('.team-heading-identity,.team-card-identity').all():
                img = node.locator('.team-logo').first.bounding_box()
                text = node.locator(':scope > div,:scope > h2').last.bounding_box()
                if img and text:
                    assert img['x'] + img['width'] <= text['x'] + 1, (page.url, img, text)

        go('')
        for slug in ('blue', 'white'): logo(slug)
        assert page.locator('.brand img').get_attribute('src').endswith('brand/uah-esports-logo.png')
        assert page.locator('.team-card').count() == 2
        for slug in ('blue', 'white', 'grey', 'black'):
            alpha[slug] = page.evaluate('''async slug=>{
                const im=new Image();im.src=new URL('brand/teams/'+slug+'.png',location.href.split('#')[0]).href;await im.decode();
                const c=document.createElement('canvas');c.width=im.naturalWidth;c.height=im.naturalHeight;
                const ctx=c.getContext('2d');ctx.drawImage(im,0,0);const pixels=ctx.getImageData(0,0,c.width,c.height).data;
                let min=255,max=0,transparent=0;for(let i=3;i<pixels.length;i+=4){min=Math.min(min,pixels[i]);max=Math.max(max,pixels[i]);if(pixels[i]===0)transparent++}
                return {width:c.width,height:c.height,min_alpha:min,max_alpha:max,transparent_pixels:transparent};
            }''', slug)
            assert alpha[slug]['min_alpha'] == 0 and alpha[slug]['max_alpha'] == 255
        checks.append('four original PNGs decode at 1080x1080 with transparent pixels; program branding and only two team cards preserved')

        routes = []
        for slug in ('blue', 'white'):
            routes += [(f'teams/{slug}', slug), (f'teams/{slug}/roster', slug), (f'teams/{slug}/stats', slug), (f'players?team={slug}', slug)]
        routes += [(f'series/{s["id"]}', s['team_slug']) for s in series]
        routes += [(f'matches/{m["id"]}', m['team_slug']) for m in maps]
        for width in (1440, 1100, 768, 390):
            page.set_viewport_size({'width':width, 'height':960})
            for route, slug in routes:
                go(route); logo(slug); layout()
                assert page.locator('.team-logo').count() == 1, route
                page.screenshot(path=str(output / f'{route.replace("/", "-").replace("?", "-")}-{width}.png'), full_page=True)
        checks.append(f'{len(routes)} actual team/roster/stats/series/map contexts at all four widths: owning logo, no repetition, overlap or horizontal overflow')

        page.set_viewport_size({'width':1440, 'height':960})
        go('players?team=blue')
        page.get_by_role('button', name='Rating', exact=True).click()
        state = page.locator('th[data-stat=rating]').get_attribute('aria-sort')
        page.get_by_label('Statistics period').select_option('career')
        for slug in ('white', 'blue'):
            page.get_by_label('Team', exact=True).select_option(slug)
            expect(page).to_have_url(url + '#/players?team=' + slug)
            logo(slug)
            expect(page.get_by_label('Statistics period')).to_have_value('career')
            expect(page.locator('th[data-stat=rating]')).to_have_attribute('aria-sort', state)
        checks.append('native team selector preserves URL, Career and sorting and updates logo')

        for width in (1440, 1100, 768, 390):
            page.set_viewport_size({'width':width, 'height':960})
            for slug in ('blue', 'white'):
                go(f'embed/{slug}/player-stats'); logo(slug)
                assert page.locator('.embed-team-identity').bounding_box()['height'] <= 38
                assert page.locator('.brand').count() == 0
                layout()
                for link in page.locator('.player-link').all():
                    expect(link).to_have_attribute('target', '_blank')
                page.screenshot(path=str(output / f'embed-{slug}-{width}.png'), full_page=True)
        checks.append('both unchanged embed routes keep team-specific stats, compact 32px identity and player profile links at four widths')

        future = deepcopy(index)
        base = load(DATA / f'teams/blue/{season}.json')
        def team_fixture(team):
            return lambda r: r.fulfill(json={**base, 'team':team, 'roster':[], 'players':[], 'maps':0, 'rounds':0})
        for i, slug in enumerate(('grey', 'black', 'gold'), 3):
            team = {**index['teams'][0], 'id':i, 'slug':slug, 'name':'UAH ' + slug.title(), 'maps':0, 'rounds':0, 'roster_count':0}
            future['teams'].append(team)
            page.route(f'**/data/teams/{slug}/*.json', team_fixture(team))
        page.route('**/data/index.json', lambda r: r.fulfill(json=future))
        page.reload(wait_until='networkidle')
        for slug in ('grey', 'black', 'gold'):
            go(f'players?team={slug}')
            page.reload(wait_until='networkidle')
            suffix = f'teams/{slug}.png' if slug != 'gold' else 'uah-esports-logo.png'
            expect(page.locator('.team-logo img')).to_have_attribute('src', '/' + 'brand/' + suffix)
            layout()
        page.unroute('**/data/index.json')
        page.reload(wait_until='networkidle')
        checks.append('Grey/Black fixtures automatically resolve; unknown Gold uses program fallback with zero database writes')

        attempts = []
        def missing(r):
            attempts.append(r.request.url)
            r.fulfill(status=404, body='fixture missing image')
        page.route('**/brand/teams/blue.png', missing)
        go('players?team=blue')
        page.reload(wait_until='networkidle')
        expect(page.locator('.team-logo img')).to_have_attribute('src', '/brand/uah-esports-logo.png')
        page.route('**/brand/uah-esports-logo.png', missing)
        go('teams/blue')
        page.reload(wait_until='networkidle')
        expect(page.locator('.team-logo-fallback')).to_have_text('UAH')
        expect(page.locator('.team-logo img')).to_have_count(0)
        settled = len(attempts)
        page.wait_for_timeout(250)
        assert len(attempts) == settled and settled <= 10, attempts
        page.unroute('**/brand/teams/blue.png'); page.unroute('**/brand/uah-esports-logo.png')
        checks.append('real component handles missing team and program assets without a broken team image or retry loop')

        # Contrast gallery uses the real unchanged assets and CSS on four panels.
        go('')
        page.set_viewport_size({'width':1100, 'height':960})
        page.evaluate('''()=>{const g=document.createElement('section');g.style.cssText='position:fixed;inset:0;z-index:9999;background:#0d1420;display:grid;grid-template-columns:repeat(4,1fr);gap:20px;padding:30px';
          for(const bg of ['#0d1420','#0058A4','#E6EDF5','#ffffff']){const p=document.createElement('div');p.style.cssText='background:'+bg+';padding:20px;display:flex;flex-direction:column;gap:16px';
            for(const slug of ['blue','white','grey','black']){const s=document.createElement('span');s.className='team-logo team-logo-lg';const i=new Image();i.src='brand/teams/'+slug+'.png';i.alt=slug;s.append(i);p.append(s)}g.append(p)}document.body.append(g)}''')
        page.wait_for_timeout(250)
        page.screenshot(path=str(output / 'all-variants-contrast.png'))

        if admin:
            ap = browser.new_page(viewport={'width':1440, 'height':960})
            ap.on('pageerror', lambda e: errors.append(str(e)))
            mutations = []
            def readonly(r):
                if r.request.method not in ('GET', 'HEAD', 'OPTIONS'):
                    mutations.append(r.request.url); r.abort()
                else: r.continue_()
            ap.route('**/api/admin/**', readonly)
            ap.goto(admin, wait_until='networkidle')
            for width in (1440, 1100, 768, 390):
                ap.set_viewport_size({'width':width, 'height':960})
                for slug, team_id in (('blue','1'), ('white','2')):
                    ap.get_by_label('Active admin team').select_option(team_id)
                    expect(ap.locator('.admin-context .team-logo img')).to_have_attribute('src', '/brand/teams/' + slug + '.png')
                    assert ap.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                    ap.screenshot(path=str(output / f'admin-{slug}-{width}.png'), full_page=True)
            ap.get_by_role('button', name='Teams', exact=False).first.click()
            expect(ap.locator('.team-editor')).to_have_count(3)
            form = ap.locator('.team-editor').filter(has=ap.get_by_role('heading', name='Create a team', exact=True))
            for slug in ('grey', 'black', 'future'):
                form.get_by_label('Public URL slug').fill(slug)
                suffix = 'teams/' + slug + '.png' if slug != 'future' else 'uah-esports-logo.png'
                expect(form.locator('.team-logo img')).to_have_attribute('src', '/brand/' + suffix)
            assert not mutations, mutations
            checks.append('actual launcher admin: Blue/White context at four widths and unsaved future-team editor previews; no mutation requests')
            ap.close()
        assert not errors, errors
        browser.close()
    report = {'status':'PASS', 'url':url, 'admin':admin, 'checks':checks, 'images':alpha, 'javascript_errors':errors}
    (output / 'team-logos-ui.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--url')
    ap.add_argument('--admin', default='http://127.0.0.1:8000/admin')
    ap.add_argument('--output', type=Path, default=ROOT / 'data/research/team-logos-20261008/browser')
    args = ap.parse_args()
    if args.url:
        verify(args.url, args.output, args.admin)
    else:
        class QuietHandler(SimpleHTTPRequestHandler):
            def log_message(self, *_): pass
            def copyfile(self, source, outputfile):
                try: super().copyfile(source, outputfile)
                except ConnectionError: pass  # Navigations can cancel an in-flight fixture response.
        server = ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(QuietHandler, directory=str(ROOT / 'web/dist')))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try: verify(f'http://127.0.0.1:{server.server_port}/', args.output, args.admin)
        finally: server.shutdown()
