"""Browser checks against built UI, with synthetic inbox responses (no imports)."""
import argparse
import functools
import json
import tempfile
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright, expect


def verify(url):
    with tempfile.TemporaryDirectory() as directory, sync_playwright() as p:
        folder = Path(directory) / 'MatchReplay' / 'Match-2026-10-07_12-00-00'
        folder.mkdir(parents=True)
        for i in (1, 2):
            (folder / f'Test-R{i:02}.rec').write_bytes(b'dissect\0 synthetic fixture ' + bytes([i]))
        other = folder.parent / 'Match-unselected'
        other.mkdir()
        (other / 'Other-R01.rec').write_bytes(b'dissect\0 must not upload this replay')
        browser = p.chromium.launch(channel='msedge', headless=True)
        page = browser.new_page(viewport={'width': 1366, 'height': 900})
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        state = {'files': [], 'uploaded': set(), 'failure': True, 'full': False, 'cancelled': False, 'bot': False}

        def reply(route, payload, status=200):
            route.fulfill(status=status, json=payload, headers={'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Headers': '*', 'Access-Control-Allow-Methods': 'GET,POST,PUT,OPTIONS'})

        def inbox(route):
            request = route.request
            if request.method == 'OPTIONS': return reply(route, {})
            if request.url.endswith('/config'):
                return reply(route, {'enabled': True, 'available': True, 'turnstile_site_key': 'synthetic-widget' if state['bot'] else None,
                                     'teams': [{'slug': 'blue', 'name': 'UAH Blue'}, {'slug': 'white', 'name': 'UAH White'}],
                                     'seasons': [{'slug': 'fall-2026', 'name': 'Fall 2026'}]})
            if request.url.endswith('/submissions'):
                if state['full']: return reply(route, {'error': 'Replay inbox is full.'}, 507)
                manifest = request.post_data_json
                assert manifest['confirmed'] is True and manifest['rehost'] == 'unsure'
                assert len(manifest['folders']) == 1 and len(manifest['folders'][0]['files']) == 2
                assert manifest['folders'][0]['name'] == folder.name
                state['files'] = [{'id': str(i), 'folder': f['name'], 'name': replay['name'], 'size': replay['size']}
                                  for f in manifest['folders'] for i, replay in enumerate(f['files'])]
                return reply(route, {'id': 'fixture', 'display_id': 'R6-FIXTURE', 'upload_token': 'scoped-upload-only', 'files': state['files'], 'expires_at': 9999999999}, 201)
            if '/files/' in request.url:
                if state['failure']:
                    state['failure'] = False
                    return reply(route, {'error': 'Connection interrupted. Retry this file.'}, 500)
                assert request.headers['authorization'] == 'Bearer scoped-upload-only'
                state['uploaded'].add(request.url.rsplit('/', 1)[-1])
                return reply(route, {'uploaded': True})
            if request.url.endswith('/complete'):
                assert len(state['uploaded']) == 2
                return reply(route, {'received': True, 'display_id': 'R6-FIXTURE'})
            if request.url.endswith('/cancel'):
                state['cancelled'] = True
                return reply(route, {'cancelled': True})
            return reply(route, {'files': [{**f, 'status': 'uploaded' if f['id'] in state['uploaded'] else 'waiting'} for f in state['files']]})

        page.route('**/submissions-config.json', lambda route: route.fulfill(json={'worker_url': 'https://fixture.invalid'}))
        page.route('https://fixture.invalid/**', inbox)
        page.goto(url + '#/submit', wait_until='networkidle')
        expect(page.get_by_role('heading', name='Submit Replays', exact=True)).to_be_visible()
        expect(page.get_by_role('combobox', name='UAH team', exact=True)).to_have_value('')
        expect(page.get_by_role('combobox', name='Season', exact=True)).to_have_value('')
        assert page.get_by_label('Statistics period').count() == 0
        page.get_by_role('combobox', name='UAH team', exact=True).select_option('blue')
        page.get_by_role('combobox', name='Season', exact=True).select_option('fall-2026')
        page.get_by_label('Opponent', exact=True).fill('TEST opponent')
        page.get_by_label('Match date', exact=True).fill('2026-10-07')
        page.get_by_label('Your name / gamer tag').fill('TEST fixture')
        page.get_by_role('radio', name='Not sure', exact=True).check()
        page.locator('summary').filter(has_text='Show me where to find my replays').click()
        expect(page.get_by_text('Browse local files', exact=False)).to_be_visible()
        page.evaluate("document.querySelector('input[type=file]').addEventListener('change',e=>{window.fixtureFiles=Array.from(e.target.files)}, {capture:true,once:true})")
        page.locator('input[type=file]').set_input_files(str(folder.parent))
        expect(page.get_by_text('2 replay folders found', exact=True)).to_be_visible()
        page.get_by_role('button', name='Clear folders').click()
        # Feed actual browser File objects through the drop path, then prove the
        # unselected folder is excluded from the unchanged upload manifest.
        page.evaluate("""() => {
          const names=[...new Set(window.fixtureFiles.map(f=>f.webkitRelativePath.split('/').at(-2)))];
          const roots=names.map(name=>({kind:'directory',name,values:async function*(){
            for(const file of window.fixtureFiles.filter(f=>f.webkitRelativePath.split('/').at(-2)===name))
              yield {kind:'file',name:file.name,getFile:async()=>file}
          }}));
          const event=new DragEvent('drop',{bubbles:true,cancelable:true});
          Object.defineProperty(event,'dataTransfer',{value:{items:roots.map(handle=>({kind:'file',getAsFileSystemHandle:async()=>handle}))}});
          document.querySelector('.replay-dropzone').dispatchEvent(event);
        }""")
        expect(page.get_by_text('2 replay folders found', exact=True)).to_be_visible()
        page.locator('.replay-folder-list label').filter(has_text=folder.name).locator('input').check()
        page.get_by_role('button', name='Review submission').click()
        expect(page.get_by_role('heading', name='UAH Blue', exact=True)).to_be_visible()
        expect(page.get_by_text('Fall 2026', exact=True)).to_be_visible()
        expect(page.get_by_role('button', name='Submit for Review', exact=True)).to_be_disabled()
        page.get_by_role('checkbox').check()
        state['full'] = True
        page.get_by_role('button', name='Submit for Review', exact=True).click()
        expect(page.get_by_role('alert')).to_contain_text('full')
        assert not state['uploaded']
        state['full'] = False
        page.get_by_role('button', name='Submit for Review', exact=True).click()
        expect(page.get_by_role('alert')).to_contain_text('interrupted')
        assert page.get_by_role('heading', name='Submission received').count() == 0
        evidence = Path(__file__).resolve().parents[1] / 'data/research/replay-selection-20261007' / ('live-upload-ui' if url.startswith('https:') else 'upload-ui')
        evidence.mkdir(parents=True, exist_ok=True)
        for width in (1920, 1366, 768, 390):
            page.set_viewport_size({'width': width, 'height': 900})
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'), width
        page.locator('.confirmation').screenshot(path=str(evidence / 'paused-progress-mobile.png'))
        page.get_by_role('button', name='Retry unfinished uploads').click()
        expect(page.get_by_role('heading', name='Submission received')).to_be_visible(timeout=15000)
        expect(page.get_by_text('R6-FIXTURE', exact=True)).to_be_visible()
        for width in (1920, 1366, 768, 390):
            page.set_viewport_size({'width': width, 'height': 900})
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'), width
        # Exercise modern directory handles, not just input.webkitdirectory.
        page.reload(wait_until='networkidle')
        page.evaluate("""() => { const bytes=new TextEncoder().encode('dissect synthetic modern replay');
          const replay={kind:'file',name:'Modern-R01.rec',getFile:async()=>new File([bytes],'Modern-R01.rec',{lastModified:100})};
          const match={kind:'directory',name:'Match-modern',values:async function*(){yield replay}};
          window.showDirectoryPicker=async()=>({kind:'directory',name:'MatchReplay',values:async function*(){yield match}}); }""")
        page.get_by_role('button', name='Choose MatchReplay Folder', exact=True).click()
        expect(page.get_by_text('Match-modern', exact=True)).to_be_visible()
        state['bot'] = True
        page.add_init_script("window.turnstile={render:(el,options)=>{window.syntheticBot=options;setTimeout(()=>options['error-callback']('600010'),0);return 'mock-id'},reset:()=>window.syntheticBot.callback('mock-token'),remove:()=>{}}")
        page.reload(wait_until='networkidle')
        expect(page.get_by_role('alert')).to_contain_text('Browser verification failed')
        page.get_by_role('button', name='Retry verification', exact=True).click()
        expect(page.get_by_role('alert')).to_have_count(0)
        assert not errors, errors
        browser.close()
        print('PASS: directory/fallback, context, confirmation, cap, retry, receipt, responsive layout and modern picker.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--url')
    args = parser.parse_args()
    if args.url:
        verify(args.url)
    else:
        handler = functools.partial(SimpleHTTPRequestHandler, directory=str(Path(__file__).resolve().parents[1] / 'web/dist'))
        server = ThreadingHTTPServer(('127.0.0.1', 0), handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try: verify(f'http://127.0.0.1:{server.server_port}/')
        finally: server.shutdown()
