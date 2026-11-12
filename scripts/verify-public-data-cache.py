"""Regression: fresh app must bypass a cached profile with the old schema."""
import functools
import http.server
import json
from pathlib import Path
import threading

from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
PROFILE = '/data/players/lgon/fall-2026.json'
fresh = json.loads((ROOT/'web/public'/PROFILE.lstrip('/')).read_text(encoding='utf-8'))
old = json.loads(json.dumps(fresh))
for side in old['sides'].values():
    side.pop('opening_kills', None)
    side.pop('opening_deaths', None)


class Handler(http.server.SimpleHTTPRequestHandler):
    current = False
    profile_reads = 0

    def log_message(self, *_):
        pass

    def do_GET(self):
        if self.path == '/cache-probe':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'<html><title>Cache regression</title></html>')
        elif self.path == PROFILE:
            Handler.profile_reads += 1
            body = json.dumps(fresh if Handler.current else old).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Cache-Control', 'public, max-age=3600')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            super().do_GET()


def main():
    handler = functools.partial(Handler, directory=str(ROOT/'web/dist'))
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    origin = f'http://127.0.0.1:{server.server_port}'
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(channel='msedge', headless=True)
            page = browser.new_page()
            page.goto(origin+'/cache-probe')
            cached = page.evaluate('(path)=>fetch(path).then(r=>r.json())', PROFILE)
            assert 'opening_kills' not in cached['sides']['Attack']
            Handler.current = True
            cached = page.evaluate('(path)=>fetch(path).then(r=>r.json())', PROFILE)
            assert 'opening_kills' not in cached['sides']['Attack']
            assert Handler.profile_reads == 1, 'Control did not reproduce browser caching'
            page.goto(origin+'/#/players/lgon', wait_until='networkidle')
            panel = page.locator('section[aria-label="Entry breakdown"]')
            expect(panel.locator('tbody tr')).to_have_count(2)
            expect(panel).not_to_contain_text('Breakdown unavailable')
            assert Handler.profile_reads == 2, 'Profile did not bypass stale browser cache'
            for index, side in enumerate(('Attack', 'Defense')):
                s = fresh['sides'][side]
                expect(panel.locator('tbody tr').nth(index)).to_contain_text(
                    f"{s['opening_kills']}\u2013{s['opening_deaths']}")
            browser.close()
        print('PASS: cached old profile reproduced; new app bypassed cache and rendered both Entry sides.')
    finally:
        server.shutdown()
        server.server_close()


if __name__ == '__main__':
    main()
