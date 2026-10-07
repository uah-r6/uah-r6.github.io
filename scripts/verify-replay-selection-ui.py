"""Folder selection browser tests. Cloud intake is mocked; no production upload/import.

--source optionally selects a real MatchReplay directory READ ONLY through Playwright's
file input automation. This is not proof of an OS picker or Explorer drag gesture.
"""
import argparse
import functools
import json
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

HARNESS = r"""() => {
  window.modernAccessCalls=0;
  const file=(name='Game-R01.rec')=>({kind:'file',name,getFile:async()=>new File(['dissect synthetic replay fixture'],name,{lastModified:1791400000000})});
  const directory=(name,children)=>({kind:'directory',name,values:async function*(){yield* children}});
  window.replayMatch=name=>directory(name,[file(),file('Game-R02.rec'),file('notes.txt')]);
  window.replayParent=()=>directory('MatchReplay',[window.replayMatch('Match-new'),window.replayMatch('Match-old')]);
  const legacy=h=>h.kind==='file'?{name:h.name,isFile:true,isDirectory:false,file:success=>h.getFile().then(success)}:
    {name:h.name,isFile:false,isDirectory:true,createReader:()=>{let done=false;return {readEntries:async success=>{
      if(done){success([]);return}done=true;const children=[];for await(const child of h.values())children.push(legacy(child));success(children)
    }}}};
  window.dropReplayRoots=(roots,method='modern')=>{
    const target=document.querySelector('.replay-dropzone');
    const transfer={types:['Files'],dropEffect:'copy',items:roots.map(root=>({kind:'file',webkitGetAsEntry:()=>legacy(root),
      ...(method==='legacy'?{}:{getAsFileSystemHandle:()=>{window.modernAccessCalls++;return method==='refused'?Promise.reject(new DOMException('Protected','NotAllowedError')):Promise.resolve(root)}})}))};
    for(const type of ['dragenter','dragover','drop']) {const event=new DragEvent(type,{bubbles:true,cancelable:true});Object.defineProperty(event,'dataTransfer',{value:transfer});target.dispatchEvent(event)}
  };
}"""


def verify(url, channel, evidence, source=None):
    evidence.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel=channel, headless=True)
        page = browser.new_page(viewport={'width': 1366, 'height': 900})
        errors, transfers = [], []
        page.on('pageerror', lambda error: errors.append(str(error)))

        def inbox(route):
            if route.request.url.endswith('/config'):
                route.fulfill(json={'enabled': True, 'available': True, 'turnstile_site_key': None,
                    'teams': [{'slug': 'blue', 'name': 'UAH Blue'}, {'slug': 'white', 'name': 'UAH White'}],
                    'seasons': [{'slug': 'fall-2026', 'name': 'Fall 2026'}]})
            else:
                transfers.append(route.request.url)
                route.fulfill(status=500, json={'error': 'No upload allowed in folder selection tests.'})

        page.route('**/submissions-config.json', lambda route: route.fulfill(json={'worker_url': 'https://fixture.invalid'}))
        page.route('https://fixture.invalid/**', inbox)
        page.goto(url + '#/submit', wait_until='networkidle')
        page.evaluate(HARNESS)
        expect(page.get_by_role('heading', name='Add your replays')).to_be_visible()
        zone = page.get_by_role('button', name='Add replay folders: drag here or choose a folder')
        zone.focus(); expect(zone).to_be_focused()
        with page.expect_file_chooser(): zone.press('Enter')

        def clear():
            if page.get_by_role('button', name='Clear folders').count():
                page.get_by_role('button', name='Clear folders').click()

        def count(n):
            expect(page.locator('.replay-folder-list label')).to_have_count(n)
            expect(page.locator('.replay-picker')).to_have_attribute('aria-busy', 'false')

        # Whole tree; selection retained after repeated child and parent additions.
        page.evaluate("dropReplayRoots([replayParent()])")
        count(2)
        page.locator('.replay-folder-list input').first.check()
        page.evaluate("dropReplayRoots([replayMatch('Match-new')])")
        count(2)
        expect(page.locator('.replay-scan-status')).to_contain_text('kept just once')
        expect(page.locator('.replay-folder-list input').first).to_be_checked()
        clear()
        page.evaluate("dropReplayRoots([replayMatch('Single')])")
        count(1)
        clear()
        page.evaluate("dropReplayRoots([replayMatch('Map1'),replayMatch('Map2')],'legacy')")
        count(2)
        clear()
        page.evaluate("dropReplayRoots([replayMatch('Entry-fallback')],'refused')")
        count(1)
        assert page.evaluate('modernAccessCalls') == 0, 'Read-only drops must not trigger protected directory handle requests'
        clear()

        # Unrelated directory and loose-file guidance, with no alarming global error.
        page.evaluate("dropReplayRoots([{kind:'directory',name:'Other',values:async function*(){yield {kind:'file',name:'notes.txt'}}}])")
        expect(page.locator('.replay-scan-status')).to_have_text('No Rainbow Six replay files were found in that folder.')
        page.evaluate("dropReplayRoots([{kind:'file',name:'Loose-R01.rec'}])")
        expect(page.locator('.replay-scan-status')).to_contain_text('rather than individual files')
        expect(page.get_by_role('alert')).to_have_count(0)

        # Native success, cancellation, protected failure, keyboard help and tabs.
        page.evaluate("() => { window.showDirectoryPicker=async()=>replayParent() }")
        page.get_by_role('button', name='Choose MatchReplay Folder', exact=True).click()
        count(2)
        page.evaluate("() => { window.showDirectoryPicker=async()=>{throw new DOMException('Cancelled','AbortError')} }")
        page.get_by_role('button', name='Choose MatchReplay Folder', exact=True).click()
        expect(page.locator('.replay-scan-status')).to_contain_text('No folder added.')
        count(2); expect(page.get_by_role('alert')).to_have_count(0)
        page.evaluate("() => { window.showDirectoryPicker=async()=>{throw new DOMException('Contains system files','SecurityError')} }")
        page.get_by_role('button', name='Choose MatchReplay Folder', exact=True).click()
        expect(page.locator('.replay-scan-status')).to_contain_text('blocked direct access')
        page.get_by_role('button', name='Show me how', exact=True).click()
        expect(page.get_by_role('tab', name='Steam', exact=True)).to_have_attribute('aria-selected', 'true')
        steam = page.get_by_role('tabpanel', name='Steam', exact=True)
        assert steam.locator('li').all_text_contents() == ['Open Steam.', 'Click Library.', 'Find Rainbow Six Siege.', 'Right-click Rainbow Six Siege.', 'Click Manage.', 'Click Browse local files.']
        page.get_by_role('tab', name='Steam', exact=True).focus()
        page.keyboard.press('ArrowRight')
        expect(page.get_by_role('tab', name='Ubisoft Connect', exact=True)).to_be_focused()
        ubi = page.get_by_role('tabpanel', name='Ubisoft Connect', exact=True)
        expect(ubi).to_contain_text('Manage, then Properties')
        expect(ubi).to_contain_text('Installation directory')
        expect(ubi).to_contain_text('paste that location, and press Enter')
        assert 'Open folder' not in ubi.inner_text()
        expect(ubi.get_by_role('link')).to_have_attribute('href', 'https://www.ubisoft.com/en-gb/help/connectivity-and-performance/article/finding-the-installation-location-for-your-ubisoft-game/000063991')

        # Native picker absent: both the main action and secondary browse invoke input.
        page.evaluate("window.showDirectoryPicker=undefined")
        with page.expect_file_chooser() as choice:
            page.get_by_role('button', name='Choose MatchReplay Folder', exact=True).click()
        assert choice.value.is_multiple()
        with page.expect_file_chooser():
            page.get_by_role('button', name='Browse for replay folder', exact=True).click()

        for width in (1920, 1366, 768, 390):
            page.set_viewport_size({'width': width, 'height': 1000})
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'), width
            page.locator('.replay-picker').screenshot(path=str(evidence / f'{channel}-selection-{width}.png'))
        # Filled confirmation retains multi-map/rehost semantics.
        page.get_by_role('combobox', name='UAH team', exact=True).select_option('blue')
        page.get_by_role('combobox', name='Season', exact=True).select_option('fall-2026')
        page.get_by_label('Opponent', exact=True).fill('TEST ONLY')
        page.get_by_label('Match date', exact=True).fill('2026-10-07')
        page.get_by_label('Your name / gamer tag').fill('TEST ONLY')
        for name in ('Yes', 'No', 'Not sure'):
            page.get_by_role('radio', name=name, exact=True).check()
        for checkbox in page.locator('.replay-folder-list input').all(): checkbox.check()
        page.get_by_role('button', name='Review submission').click()
        expect(page.locator('.confirmation-facts')).to_contain_text('2 replay folders')
        expect(page.locator('.confirmation-facts')).to_contain_text('Not sure')
        for width in (1920, 1366, 768, 390):
            page.set_viewport_size({'width': width, 'height': 900})
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'), width
        page.locator('.confirmation').screenshot(path=str(evidence / f'{channel}-confirmation.png'))

        real = None
        if source:
            page.reload(wait_until='networkidle')
            page.evaluate("document.querySelector('input[type=file]').addEventListener('change',e=>{window.realFiles=Array.from(e.target.files)}, {capture:true,once:true})")
            page.locator('input[type=file]').set_input_files(str(source))
            expected = len({str(f.parent) for f in source.rglob('*.rec')})
            count(expected)
            real = {'folders': expected, 'files': page.evaluate('realFiles.filter(f=>/\\.rec$/i.test(f.name)).length'), 'source': str(source)}
            assert real['files'] == len(list(source.rglob('*.rec')))
            expect(page.locator('.replay-folder-list input:checked')).to_have_count(0)
            page.locator('.replay-picker').screenshot(path=str(evidence / f'{channel}-real-protected-input.png'))
            # CDP sends a trusted browser drop with the REAL directory path. Its
            # directory entries/read calls are Chromium's implementations, not
            # the JavaScript fixtures above. This still is not an Explorer gesture.
            clear()
            page.evaluate("""() => {
              window.nativeHandleCalls=0;window.nativeEntryCalls=0;
              const modern=DataTransferItem.prototype.getAsFileSystemHandle;
              if(modern)DataTransferItem.prototype.getAsFileSystemHandle=function(){window.nativeHandleCalls++;return modern.call(this)};
              const readOnly=DataTransferItem.prototype.webkitGetAsEntry;
              DataTransferItem.prototype.webkitGetAsEntry=function(){window.nativeEntryCalls++;return readOnly.call(this)};
            }""")
            zone.scroll_into_view_if_needed()
            bounds = zone.bounding_box()
            cdp = page.context.new_cdp_session(page)
            data = {'items': [], 'files': [str(source.resolve())], 'dragOperationsMask': 1}
            for event in ('dragEnter', 'dragOver', 'drop'):
                cdp.send('Input.dispatchDragEvent', {'type': event, 'x': bounds['x'] + bounds['width'] / 2, 'y': bounds['y'] + bounds['height'] / 2, 'data': data})
            count(expected)
            assert page.evaluate('nativeHandleCalls') == 0
            assert page.evaluate('nativeEntryCalls') > 0
            real['trusted_browser_drop_verified'] = True
            real['modern_handle_requests'] = page.evaluate('nativeHandleCalls')
            page.locator('.replay-picker').screenshot(path=str(evidence / f'{channel}-real-protected-browser-drop.png'))
            cdp.detach()

        assert not transfers, transfers
        assert not errors, errors
        report = {'browser': channel, 'version': browser.version, 'url': url, 'real_read_only_input': real, 'errors': errors, 'cloud_transfers': transfers, 'os_drag_verified': False}
        (evidence / f'{channel}-report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        browser.close()
        print(f'PASS {channel}: folder drop/native/fallback, duplicates, help, keyboard, cancellation, protected guidance, responsive selection and confirmation; real={real}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--url')
    parser.add_argument('--source', type=Path)
    parser.add_argument('--evidence', type=Path, default=Path('data/research/replay-selection-20261007/browser'))
    args = parser.parse_args()
    server = None
    if not args.url:
        handler = functools.partial(SimpleHTTPRequestHandler, directory=str(Path(__file__).resolve().parents[1] / 'web/dist'))
        server = ThreadingHTTPServer(('127.0.0.1', 0), handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        args.url = f'http://127.0.0.1:{server.server_port}/'
    try:
        for channel in ('chrome', 'msedge'): verify(args.url, channel, args.evidence, args.source)
    finally:
        if server: server.shutdown()
