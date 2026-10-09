"""Pool editor real API/SQLite tests run in an isolated fixture, never production writes."""
import argparse
import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import shutil
import socket
import sys
import threading
import time
from uuid import uuid4

import uvicorn
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from r6stats.admin.server import create_app
from r6stats.db import repository as repo,map_pool
from r6stats.map_analytics import project_pool
from r6stats.export import export

OUT=ROOT/'data/research/competitive-map-pool-20261008'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def admin_fixture(output):
    root=OUT/'browser-fixture'/('run-'+uuid4().hex)
    (root/'config').mkdir(parents=True)
    settings={'team':{'name':'Fixture','short_name':'Fixture','accent':'#0058A4'},
              'stats':{'rating_version':'collegiate_v1','trade_window_seconds':8},
              'replays':{'path':''},'publishing':{'enabled':False,'branch':'main'}}
    (root/'config/settings.json').write_text(json.dumps(settings),encoding='utf-8')
    with repo.connect(root/'data/r6stats.sqlite') as db:
        repo.season_create(db,'Fall 2026');repo.season_create(db,'Spring 2027')
        map_pool.save(db,'fall-2026',['bank','border']);map_pool.save(db,'spring-2027',['chalet'])
        export(db,settings,root/'web/public/data')
    shutil.copytree(ROOT/'web/admin-dist',root/'web/admin-dist',dirs_exist_ok=True)
    shutil.copytree(ROOT/'web/public/brand',root/'web/public/brand',dirs_exist_ok=True)
    with socket.socket() as listener:
        listener.bind(('127.0.0.1',0));port=listener.getsockname()[1]
    server=uvicorn.Server(uvicorn.Config(create_app(root),host='127.0.0.1',port=port,log_level='error'))
    thread=threading.Thread(target=server.run,daemon=True);thread.start()
    deadline=time.monotonic()+15
    while not server.started:
        assert time.monotonic()<deadline, 'Fixture server failed to start'
        time.sleep(.05)
    url=f'http://127.0.0.1:{port}/admin'
    errors=[]
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(channel='msedge',headless=True)
            page=browser.new_page(viewport={'width':1440,'height':960})
            page.on('pageerror',lambda e:errors.append(str(e)))
            for width in (1440,1100,768,390):
                with repo.connect(root/'data/r6stats.sqlite') as db:
                    map_pool.save(db,'fall-2026',['bank','border']);map_pool.save(db,'spring-2027',['chalet'])
                page.set_viewport_size({'width':width,'height':960})
                page.goto(url,wait_until='networkidle')
                page.get_by_role('button',name='Seasons',exact=True).click()
                editor=page.locator('.competitive-map-pool')
                expect(editor.get_by_role('checkbox')).to_have_count(26)
                expect(editor.get_by_role('checkbox',name='Bank',exact=True)).to_be_checked()
                expect(editor.get_by_role('checkbox',name='Border',exact=True)).to_be_checked()
                expect(editor.locator('.pool-save-state')).to_have_text('2 selected · Saved configuration')
                expect(editor.get_by_role('button',name='Save Map Pool',exact=True)).to_be_disabled()
                editor.get_by_label('Map pool season').select_option('spring-2027')
                expect(editor.get_by_role('checkbox',name='Chalet',exact=True)).to_be_checked()
                expect(editor.get_by_role('checkbox',name='Bank',exact=True)).not_to_be_checked()
                editor.get_by_label('Map pool season').select_option('fall-2026')
                expect(editor.get_by_role('checkbox',name='Bank',exact=True)).to_be_checked()
                editor.get_by_role('checkbox',name='Bank',exact=True).uncheck()
                expect(editor.locator('.pool-save-state')).to_contain_text('1 selected · Unsaved changes')
                with repo.connect(root/'data/r6stats.sqlite') as db:assert len(map_pool.load(db,'fall-2026')['maps'])==2
                page.once('dialog',lambda d:d.dismiss())
                editor.get_by_label('Map pool season').select_option('spring-2027')
                expect(editor.get_by_label('Map pool season')).to_have_value('fall-2026')
                page.once('dialog',lambda d:d.dismiss())
                page.get_by_role('button',name='Dashboard',exact=True).click()
                expect(editor).to_be_visible()
                editor.get_by_role('button',name='Save Map Pool',exact=True).click()
                expect(editor.locator('.pool-save-state')).to_have_text('1 selected · Saved configuration')
                with repo.connect(root/'data/r6stats.sqlite') as db:
                    assert [m['slug'] for m in map_pool.load(db,'fall-2026')['maps']]==['border']
                    assert [m['slug'] for m in map_pool.load(db,'spring-2027')['maps']]==['chalet']
                assert read(root/'web/public/data/teams/blue/maps/fall-2026.json')['maps'][0]['slug']=='border'
                page.reload(wait_until='networkidle');page.get_by_role('button',name='Seasons',exact=True).click()
                expect(editor.get_by_role('checkbox',name='Border',exact=True)).to_be_checked()
                expect(editor.get_by_role('checkbox',name='Bank',exact=True)).not_to_be_checked()
                editor.get_by_role('checkbox',name='Border',exact=True).uncheck()
                expect(editor.locator('.pool-empty-warning')).to_be_visible()
                page.once('dialog',lambda d:d.dismiss())
                editor.get_by_role('button',name='Save Map Pool',exact=True).click()
                expect(editor.locator('.pool-save-state')).to_contain_text('Unsaved changes')
                with repo.connect(root/'data/r6stats.sqlite') as db:assert len(map_pool.load(db,'fall-2026')['maps'])==1
                page.once('dialog',lambda d:d.accept())
                editor.get_by_role('button',name='Save Map Pool',exact=True).click()
                expect(editor.locator('.pool-save-state')).to_have_text('0 selected · Saved configuration')
                with repo.connect(root/'data/r6stats.sqlite') as db:assert map_pool.load(db,'fall-2026')['maps']==[]
                # Restore fixture selection for a readable screenshot, using the UI.
                editor.get_by_role('checkbox',name='Bank',exact=True).check()
                editor.get_by_role('checkbox',name='Border',exact=True).check()
                editor.get_by_role('button',name='Save Map Pool',exact=True).click()
                expect(editor.locator('.pool-save-state')).to_have_text('2 selected · Saved configuration')
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                page.screenshot(path=str(output/f'admin-fixture-{width}.png'),full_page=True)
            assert not errors,errors
            browser.close()
    finally:
        server.should_exit=True;thread.join(timeout=10)
    return dict(status='PASS',url=url,widths=[1440,1100,768,390],writes='isolated fixture SQLite only',javascript_errors=errors)


def public_verify(url,output,admin):
    errors,mutations=[],[]
    source=ROOT/'web/public/data'
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True)
        page=browser.new_page(viewport={'width':1440,'height':960})
        page.on('pageerror',lambda e:errors.append(str(e)))
        def readonly(route):
            if route.request.method not in ('GET','HEAD','OPTIONS'):
                mutations.append(route.request.url);route.abort()
            else:route.continue_()
        page.route('**/*',readonly)
        def go(route):page.goto(url+'#/'+route,wait_until='networkidle')
        def capture(label,width):
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),page.url
            page.screenshot(path=str(output/f'{label}-{width}.png'),full_page=True)
        for width in (1440,1100,768,390):
            page.set_viewport_size({'width':width,'height':960})
            go('matches?team=blue&opponent=UCF&sort=team')
            expect(page.locator('.series-card')).to_have_count(1)
            expect(page.get_by_label('Match sort')).to_have_value('newest')
            expect(page.get_by_label('Match sort').get_by_role('option')).to_have_count(3)
            assert 'sort=team' not in page.url
            expect(page.locator('.series-maps>a')).to_have_count(2)
            capture('global-matches',width)
            go('matches?team=white')
            expect(page.get_by_label('Match team')).to_have_value('white')
            expect(page.locator('.series-card')).to_have_count(1)
            go('teams/blue/matches?sort=team')
            expect(page.get_by_label('Match team')).to_have_count(0)
            expect(page.get_by_label('Match sort').get_by_role('option')).to_have_count(3)
            expect(page.get_by_label('Match sort')).to_have_value('newest')
            capture('team-matches',width)
            for team in ('blue','white'):
                for period in ('fall-2026','career'):
                    go(f'teams/{team}/maps?season={period}')
                    data=read(source/f'teams/{team}/maps/{period}.json')
                    expect(page.locator('.map-analytics-card')).to_have_count(len(data['maps']))
                    assert page.locator('.map-analytics-card>h3').all_text_contents()==[m['name'] for m in data['maps']]
                    capture(f'{team}-{period}-maps',width)
            # API/config-driven narrow pool fixture with original numerical data.
            def narrow(route):
                path=route.request.url.split('/data/',1)[-1].split('?',1)[0]
                raw=read(source/path)
                combined=raw['maps']+raw['historical_maps']
                pool={'season':'fall-2026','season_name':'Fall 2026','configured':True,
                      'maps':[{'slug':'bank','name':'Bank'},{'slug':'border','name':'Border'},{'slug':'nighthaven-labs','name':'Nighthaven Labs'}]}
                route.fulfill(json=project_pool({**raw,'maps':combined},pool))
            page.route('**/data/teams/*/maps/*.json',narrow)
            for team in ('blue','white'):
                go(f'teams/{team}/maps?season=career');page.reload(wait_until='networkidle')
                expect(page.locator('.map-analytics-card')).to_have_count(3)
                assert page.locator('.map-analytics-card>h3').all_text_contents()==['Bank','Border','Nighthaven Labs']
                card=page.locator('.map-analytics-card').filter(has=page.get_by_role('link',name='Bank',exact=True))
                expect(card).to_contain_text('No recorded maps yet.')
                expect(card.locator('.map-round-stat')).to_have_count(0)
                capture(f'{team}-narrow-pool',width)
            go('teams/blue/maps/fortress?season=career')
            expect(page.locator('.map-detail-hero h2')).to_have_text('Fortress')
            expect(page.locator('.team-map-detail')).to_contain_text('Not in the selected competitive map pool')
            expect(page.locator('.map-round-stat small').nth(0)).to_have_text('7–3 · 10 rounds')
            capture('out-of-pool-historical-detail',width)
            page.locator('.map-history a').click()
            expect(page.locator('.map-hero h1')).to_have_text('Fortress')
            page.unroute('**/data/teams/*/maps/*.json',narrow)
            # Read-only actual launcher UI. No saves to the production pool.
            page.goto(admin,wait_until='networkidle')
            page.get_by_role('button',name='Seasons',exact=True).click()
            expect(page.locator('.competitive-map-pool').get_by_role('checkbox')).to_have_count(26)
            expect(page.locator('.pool-save-state')).to_have_text('26 selected · Saved configuration')
            expect(page.locator('.pool-migration-note')).to_be_visible()
            capture('actual-launcher-admin',width)
        assert not errors,errors
        assert not mutations,mutations
        browser.close()
    return dict(status='PASS',url=url,widths=[1440,1100,768,390],javascript_errors=errors,production_mutations=mutations)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--url');ap.add_argument('--output',type=Path,default=OUT/'browser');ap.add_argument('--admin',default='http://127.0.0.1:8000/admin');ap.add_argument('--fixture',action='store_true');args=ap.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    if args.fixture:
        report=admin_fixture(args.output)
    elif args.url:
        report=public_verify(args.url,args.output,args.admin)
    else:
        class Quiet(SimpleHTTPRequestHandler):
            def log_message(self,*_):pass
            def copyfile(self,source,output):
                try:super().copyfile(source,output)
                except ConnectionError:pass
        server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT/'web/dist')))
        threading.Thread(target=server.serve_forever,daemon=True).start()
        try:report=public_verify(f'http://127.0.0.1:{server.server_port}/',args.output,args.admin)
        finally:server.shutdown()
    (args.output/('fixture-ui.json' if args.fixture else 'competitive-pool-ui.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
