"""Built/live structured uploader and actual launcher admin, isolated inbox responses.

No request uploads to Cloudflare or imports into production SQLite. Real trusted
directory-drop regression is separately exercised by verify-replay-selection-ui.py.
"""
import argparse
import copy
import functools
import json
import tempfile
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from uuid import uuid4

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'data/research/logical-submissions-20261008/browser'


def widths(page, name):
    for width in (1440, 1100, 768, 390):
        page.set_viewport_size({'width': width, 'height': 1000})
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'), (name, width)
        page.screenshot(path=str(EVIDENCE / f'{name}-{width}.png'), full_page=True)


def verify(url, admin_url='http://127.0.0.1:8000/admin'):
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as temporary, sync_playwright() as p:
        parent = Path(temporary) / 'MatchReplay'
        for i, name in enumerate(['Folder-A', 'Folder-B', 'Folder-C', 'Unused']):
            path = parent / name; path.mkdir(parents=True)
            for j in (1, 2):
                file = path / f'{name}-R{j:02}.rec'
                file.write_bytes(b'dissect\0 synthetic fixture ' + bytes([i, j]))
                import os
                os.utime(file, (1791400000 + i * 3600 + j * 600,) * 2)
        browser = p.chromium.launch(channel='msedge', headless=True)
        page = browser.new_page(viewport={'width': 1440, 'height': 1000})
        errors, transfers = [], []
        page.on('pageerror', lambda error: errors.append(str(error)))
        state = dict(files=[], uploaded=set(), failure=True, full=False, expire=False, cancelled=False, bot=False, created=0)
        def reply(route, body, status=200):
            route.fulfill(status=status, json=body, headers={'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Headers': '*', 'Access-Control-Allow-Methods': 'GET,POST,PUT,OPTIONS'})
        def inbox(route):
            request = route.request
            if request.method == 'OPTIONS': return reply(route, {})
            if request.url.endswith('/config'):
                return reply(route, dict(enabled=True, available=True, turnstile_site_key='synthetic-widget' if state['bot'] else None,
                    teams=[dict(slug='blue', name='UAH Blue'), dict(slug='white', name='UAH White')], seasons=[dict(slug='fall-2026', name='Fall 2026')]))
            if request.url.endswith('/submissions'):
                if state['full']: return reply(route, {'error': 'Replay inbox is full.'}, 507)
                state['created'] += 1
                manifest = request.post_data_json
                assert manifest['schema_version'] == 2 and 'rehost' not in manifest and manifest['confirmed']
                assert [m['type'] for m in manifest['maps']] == ['normal', 'rehost']
                assert [f['name'] for f in manifest['folders']] == ['Folder-A', 'Folder-B', 'Folder-C']
                assert [p['folder_name'] for p in manifest['maps'][1]['segments']] == ['Folder-B', 'Folder-C']
                assert all(f['first_file_modified_at'] < f['last_file_modified_at'] for f in manifest['folders'])
                assert len(json.dumps(manifest)) < 128000 and temporary not in json.dumps(manifest)
                state['manifest'] = manifest
                state['files'] = [dict(id=str(i), folder=f['name'], name=file['name'], size=file['size'], logical_index=1 if f['name']=='Folder-A' else 2, segment_index=2 if f['name']=='Folder-C' else 1)
                                  for i, (f, file) in enumerate((f, file) for f in manifest['folders'] for file in f['files'])]
                return reply(route, dict(id='fixture', display_id='R6-FIXTURE', upload_token='fixture-only', files=state['files']), 201)
            if state['expire']: return reply(route, {'error': 'Upload session expired. Start a new submission.'}, 410)
            if '/files/' in request.url:
                fid = request.url.rsplit('/', 1)[-1]
                transfers.append(fid)
                if fid == '1' and state['failure']:
                    state['failure'] = False
                    return reply(route, {'error': 'Connection interrupted. Retry unfinished files.'}, 500)
                assert fid not in state['uploaded'], 'Retry must not transfer completed files'
                assert request.headers['authorization'] == 'Bearer fixture-only'
                state['uploaded'].add(fid)
                return reply(route, {'uploaded': True})
            if request.url.endswith('/complete'):
                assert len(state['uploaded']) == 6
                return reply(route, {'received': True, 'display_id': 'R6-FIXTURE'})
            if request.url.endswith('/cancel'):
                state['cancelled'] = True
                return reply(route, {'cancelled': True})
            return reply(route, {'files': [{**f, 'status': 'uploaded' if f['id'] in state['uploaded'] else 'waiting'} for f in state['files']]})
        page.route('**/submissions-config.json', lambda route: route.fulfill(json={'worker_url': 'https://fixture.invalid'}))
        page.route('https://fixture.invalid/**', inbox)
        def fill():
            page.get_by_role('combobox',name='UAH team', exact=True).select_option('blue')
            page.get_by_role('combobox',name='Season', exact=True).select_option('fall-2026')
            page.get_by_label('Opponent', exact=True).fill('TEST ONLY')
            page.get_by_label('Match date', exact=True).fill('2026-10-07')
            page.get_by_label('Your name / gamer tag').fill('TEST ONLY')
            page.locator('input[type=file]').set_input_files(str(parent))
            expect(page.locator('.candidate-folder')).to_have_count(4)
            count = page.get_by_role('combobox',name='How many maps are you submitting?',exact=True)
            count.select_option('2')
            page.get_by_role('combobox',name='Map 1 replay folder', exact=True).select_option('Folder-A')
            page.get_by_role('combobox',name='Map 2 type', exact=True).select_option('rehost')
            page.get_by_role('combobox',name='Map 2 / Part 1', exact=True).select_option('Folder-B')
            page.get_by_role('combobox',name='Map 2 / Part 2', exact=True).select_option('Folder-C')
        page.goto(url + '#/submit', wait_until='networkidle'); fill()
        assert page.get_by_role('radio').count() == 0
        expect(page.get_by_role('combobox',name='Map 1 replay folder',exact=True)).to_have_value('Folder-A')
        expect(page.get_by_role('combobox',name='Map 2 / Part 1', exact=True).locator('option[value="Folder-A"]')).to_have_attribute('disabled','')
        expect(page.locator('.candidate-folder').filter(has_text='Folder-A')).to_contain_text('Assigned to Map 1')
        page.get_by_role('combobox',name='How many maps are you submitting?',exact=True).select_option('5')
        expect(page.get_by_role('combobox',name='Map 1 replay folder', exact=True)).to_have_value('Folder-A')
        page.get_by_role('combobox',name='How many maps are you submitting?',exact=True).select_option('2')
        page.once('dialog',lambda dialog:dialog.dismiss())
        page.get_by_role('combobox',name='How many maps are you submitting?',exact=True).select_option('1')
        expect(page.get_by_role('combobox',name='How many maps are you submitting?',exact=True)).to_have_value('2')
        page.once('dialog',lambda dialog:dialog.dismiss())
        page.get_by_role('combobox',name='Map 2 type',exact=True).select_option('normal')
        expect(page.get_by_role('combobox',name='Map 2 / Part 2', exact=True)).to_have_value('Folder-C')
        page.once('dialog',lambda dialog:dialog.accept())
        page.get_by_role('combobox',name='Map 2 type',exact=True).select_option('normal')
        expect(page.get_by_role('combobox',name='Map 2 replay folder',exact=True)).to_have_value('Folder-B')
        expect(page.get_by_role('combobox',name='Map 1 replay folder',exact=True).locator('option[value="Folder-C"]')).not_to_have_attribute('disabled','')
        page.get_by_role('combobox',name='Map 2 type',exact=True).select_option('rehost')
        page.get_by_role('combobox',name='Map 2 / Part 2',exact=True).select_option('Folder-C')
        page.get_by_role('combobox',name='Map 2 type',exact=True).select_option('unsure')
        expect(page.get_by_text('An administrator must classify',exact=False)).to_be_visible()
        page.get_by_role('combobox',name='Map 2 type',exact=True).select_option('rehost')
        page.get_by_role('button', name='Move Map 2 Part 2 up', exact=True).focus(); page.keyboard.press('Enter')
        expect(page.get_by_role('combobox',name='Map 2 / Part 1', exact=True)).to_have_value('Folder-C')
        page.get_by_role('button', name='Move Map 2 Part 1 down', exact=True).click()
        page.get_by_role('button', name='+ Add rehost part to Map 2', exact=True).click()
        page.get_by_role('combobox',name='Map 2 / Part 3', exact=True).select_option('Unused')
        page.on('dialog', lambda dialog: dialog.accept())
        page.get_by_role('button', name='Remove Map 2 Part 3', exact=True).click()
        widths(page, 'live-selection' if url.startswith('https:') else 'selection')
        page.get_by_role('button', name='Review submission').click()
        expect(page.locator('.logical-map-review .logical-map-card')).to_have_count(2)
        expect(page.locator('.confirmation-facts')).to_contain_text('3 replay folders')
        expect(page.locator('.confirmation-facts')).to_contain_text('6 replay files')
        expect(page.get_by_role('button', name='Submit for Review', exact=True)).to_be_disabled()
        page.get_by_role('checkbox').check()
        state['full'] = True; page.get_by_role('button', name='Submit for Review', exact=True).click()
        expect(page.get_by_role('alert')).to_contain_text('full'); assert not transfers
        state['full'] = False; page.get_by_role('button', name='Submit for Review', exact=True).click()
        expect(page.get_by_role('alert')).to_contain_text('interrupted')
        assert state['uploaded'] == {'0'} and transfers == ['0', '1']
        expect(page.locator('.upload-progress')).to_contain_text('paused')
        widths(page, 'live-review' if url.startswith('https:') else 'review')
        page.get_by_role('button', name='Retry unfinished uploads').click()
        expect(page.get_by_role('heading', name='Submission received')).to_be_visible()
        assert transfers == ['0', '1', '1', '2', '3', '4', '5'] and state['created'] == 1
        # Cancelling and expiry keep discovery but never create a false receipt.
        page.reload(wait_until='networkidle'); fill(); state.update(uploaded=set(), failure=True)
        page.get_by_role('button', name='Review submission').click(); page.get_by_role('checkbox').check()
        page.get_by_role('button', name='Submit for Review', exact=True).click()
        expect(page.get_by_role('alert')).to_contain_text('interrupted')
        page.get_by_role('button', name='Cancel upload', exact=True).click()
        expect(page.get_by_role('combobox',name='Map 1 replay folder', exact=True)).to_have_value('Folder-A'); assert state['cancelled']
        page.get_by_role('button', name='Review submission').click(); page.get_by_role('checkbox').check(); state['expire']=True
        page.get_by_role('button', name='Submit for Review', exact=True).click()
        expect(page.get_by_role('alert')).to_contain_text('expired'); expect(page.get_by_role('combobox',name='Map 1 replay folder', exact=True)).to_have_value('Folder-A'); state['expire']=False
        # Real component Turnstile callbacks, synthetic provider only.
        state['bot']=True
        page.add_init_script("window.turnstile={render:(el,options)=>{window.fixtureBot=options;setTimeout(()=>options.callback('fixture-token'),0);return 'mock'},reset:()=>window.fixtureBot.callback('fixture-token'),remove:()=>{}}")
        page.route('https://challenges.cloudflare.com/**', lambda route: route.fulfill(body=''))
        page.reload(wait_until='networkidle'); fill()
        expect(page.get_by_role('button', name='Review submission')).to_be_enabled()
        page.evaluate("fixtureBot['expired-callback']()")
        expect(page.get_by_role('button', name='Review submission')).to_be_disabled()
        expect(page.get_by_role('alert')).to_contain_text('Verification expired')
        page.get_by_role('button', name='Retry verification', exact=True).click()
        expect(page.get_by_role('button', name='Review submission')).to_be_enabled()
        state['bot']=False
        report = {'url':url,'ordered_retry_transfers':transfers,'manifest':state['manifest'],'errors':errors,'widths':[1440,1100,768,390]}
        if admin_url: report['admin']=verify_admin(browser, admin_url, errors)
        assert not errors, errors
        (EVIDENCE / ('live-report.json' if url.startswith('https:') else 'report.json')).write_text(json.dumps(report,indent=2),encoding='utf8')
        browser.close()
        print('PASS: structured discovery/assignment/confirmation, timestamps, removal prompts, keyboard reorder, cap, retry, cancel, expiry, Turnstile and four widths; admin='+str(bool(admin_url)))


def verify_admin(browser, url, errors):
    page=browser.new_page(viewport={'width':1440,'height':1000})
    page.on('pageerror',lambda error:errors.append(str(error)))
    page.on('dialog',lambda dialog:dialog.accept())
    sid=str(uuid4()); mids=[str(uuid4()),str(uuid4())]; fids=[str(uuid4()) for _ in range(3)]
    folders=[dict(id=fid,name=name,disposition=None,first_file_modified_at='2026-10-07T19:00:00.000Z',last_file_modified_at='2026-10-07T19:20:00.000Z') for fid,name in zip(fids,['Folder-A','Folder-B','Folder-C'])]
    maps=[dict(id=mids[0],index=1,type='normal',segments=[dict(index=1,folder_id=fids[0])]),dict(id=mids[1],index=2,type='rehost',segments=[dict(index=1,folder_id=fids[1]),dict(index=2,folder_id=fids[2])])]
    submission=dict(id=sid,display_id='R6-UI-FIXTURE',schema_version=2,maps=maps,reviewed_maps=copy.deepcopy(maps),folders=folders,files=[dict(folder_id=fid,declared_size=32) for fid in fids],status='reviewing',team_slug='white',team_name='UAH White',season_slug='fall-2026',season_name='Fall 2026',opponent='Submitted opponent',match_date='2026-10-07',submitter='TEST ONLY',discord='',notes='',rehost='unsure',actual_bytes=96,objects_deleted_at=None,local_receipts=[])
    calls=[]
    def route_inbox(route):
        request=route.request; suffix=request.url.split('/api/admin/submissions',1)[1].split('?',1)[0]
        calls.append([suffix,request.method])
        if suffix=='/storage': return route.fulfill(json=dict(configured=True,enabled=True,stored_bytes=96,reserved_bytes=0,cap_bytes=9663676416,pending_bytes=96,terminal_bytes=0,pending_count=1,percent=0,last_reconciled=None))
        if suffix=='': return route.fulfill(json=[submission])
        if suffix=='/'+sid:return route.fulfill(json=submission)
        if suffix.endswith('/stage'):return route.fulfill(json=dict(folders=folders))
        if suffix.endswith('/inspect'):
            assert request.post_data_json['team_id']==1
            inspected=[dict(**f,path='C:\\fixture-private\\'+f['id'],files=1,bytes=32,map='Border',rounds=2,match_type='Custom Game',tracked_count=5,eligible=True,rehost_eligible=True,duplicate=False) for f in folders]
            return route.fulfill(json=dict(folders=inspected,reviewed_maps=submission['reviewed_maps']))
        if suffix.endswith('/structure'):
            assert submission['maps']==maps
            submission['reviewed_maps']=request.post_data_json['maps']
            return route.fulfill(json=dict(reviewed_maps=submission['reviewed_maps']))
        raise AssertionError('Unexpected inbox mutation '+suffix)
    page.route('**/api/admin/submissions**',route_inbox)
    page.goto(url,wait_until='networkidle')
    page.get_by_role('button',name='Submissions',exact=False).first.click()
    page.locator('.activity-row').filter(has_text='R6-UI-FIXTURE').get_by_role('button',name='Review',exact=True).click()
    expect(page.locator('.submission-map-card')).to_have_count(2)
    page.get_by_role('combobox',name='Importing as team',exact=True).select_option('1')
    page.get_by_role('button',name='Download, verify & inspect locally').click()
    expect(page.locator('.submission-map-card').first.get_by_role('button',name='Open Normal Import')).to_be_enabled()
    expect(page.get_by_role('combobox',name='Importing as team',exact=True)).to_have_value('1')
    expect(page.locator('.submission-map-card').nth(1).get_by_role('button',name='Open Rehost Builder')).to_be_enabled()
    page.get_by_role('button',name='Move reviewed Map 2 Part 2 up',exact=True).click()
    expect(page.get_by_role('button',name='Open Rehost Builder')).to_be_disabled()
    page.get_by_role('button',name='Save reviewed map structure').click()
    expect(page.get_by_role('status').filter(has_text='Original submitted')).to_be_visible()
    assert submission['maps'][1]['segments'][0]['folder_id']==fids[1]
    assert submission['reviewed_maps'][1]['segments'][0]['folder_id']==fids[2]
    widths(page,'live-admin-grouping')
    page.get_by_role('button',name='Open Normal Import').click()
    expect(page.get_by_label('Or paste a complete match folder / ZIP path')).to_have_value('C:\\fixture-private\\'+fids[0])
    # Simulate confirmed first-map receipt; second handoff must reuse its scope.
    submission['series_context']=dict(series_id='fixture-series',team_slug='blue',season_slug='fall-2026',opponent='Corrected opponent',match_date='2026-10-06')
    submission['folders'][0]['disposition']='imported'
    submission['local_receipts']=[dict(folder_ids=[fids[0]],synced=True)]
    page.get_by_role('button',name='Submissions',exact=False).first.click()
    page.locator('.activity-row').filter(has_text='R6-UI-FIXTURE').get_by_role('button',name='Review',exact=True).click()
    expect(page.get_by_role('combobox',name='Importing as team',exact=True)).to_have_value('1')
    page.get_by_role('button',name='Download, verify & inspect locally').click()
    page.get_by_role('button',name='Open Rehost Builder').click()
    expect(page.get_by_text('same confirmed series',exact=False)).to_be_visible()
    inputs=page.locator('.rehost-segment input')
    # Match labels directly when implementation layout uses different wrappers.
    paths=page.locator('input').evaluate_all('(els)=>els.map(el=>el.value).filter(value=>value.startsWith("C:\\\\fixture-private"))')
    assert paths==['C:\\fixture-private\\'+fids[2],'C:\\fixture-private\\'+fids[1]],paths
    widths(page,'live-admin-rehost-handoff')
    assert not any('import' in suffix for suffix,method in calls)
    page.close()
    return dict(calls=calls,normal_handoff=True,ordered_rehost_handoff=True,shared_series=True,production_imports=0)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--url');parser.add_argument('--admin-url',default='http://127.0.0.1:8000/admin');args=parser.parse_args()
    server=None
    if not args.url:
        handler=functools.partial(SimpleHTTPRequestHandler,directory=str(ROOT/'web/dist'))
        server=ThreadingHTTPServer(('127.0.0.1',0),handler);threading.Thread(target=server.serve_forever,daemon=True).start()
        args.url=f'http://127.0.0.1:{server.server_port}/'
    try:verify(args.url,args.admin_url)
    finally:
        if server:server.shutdown()
