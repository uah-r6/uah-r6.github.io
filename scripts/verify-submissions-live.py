"""Opt-in live upload/reject check. Never imports into production SQLite.

Uploads a private copy of Fortress through the deployed form, previews locally,
rejects it, then removes only this test's cloud objects/metadata and staging.
"""
import argparse
import hashlib
import json
import shutil
import sys
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright, expect
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from r6stats.submissions import Client

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'data/research/submissions-20261007'


def local(path, method='GET', payload=None):
    base = 'http://127.0.0.1:8000/api/admin'
    headers = {'Content-Type': 'application/json'}
    if method != 'GET':
        with urllib.request.urlopen(base + '/session') as r: token = json.load(r)['token']
        headers['X-R6-Admin-Token'] = token
    request = urllib.request.Request(base + path, headers=headers, method=method,
                                     data=json.dumps(payload).encode() if payload is not None else None)
    with urllib.request.urlopen(request, timeout=180) as response: return json.load(response)


def review(browser, sid, display, report, errors):
    admin = browser.new_page(viewport={'width': 1366, 'height': 1000})
    admin.on('pageerror', lambda e: errors.append(str(e)))
    admin.on('dialog', lambda dialog: dialog.accept())
    admin.goto('http://127.0.0.1:8000/admin', wait_until='networkidle')
    admin.get_by_role('button', name='Submissions', exact=False).first.click()
    row = admin.locator('.activity-row').filter(has_text=display)
    row.get_by_role('button', name='Review', exact=True).click()
    expect(admin.get_by_text('Submitted as:', exact=True)).to_be_visible()
    admin.get_by_role('combobox', name='Importing as team').select_option('1')
    admin.get_by_role('button', name='Download, verify & inspect locally').click()
    expect(admin.get_by_text('5 roster matches', exact=False)).to_be_visible(timeout=180000)
    expect(admin.get_by_text('duplicate already imported', exact=False)).to_be_visible()
    report['inspection'] = local('/submissions/' + sid + '/inspect', 'POST', {'team_id': 1, 'season_slug': 'fall-2026'})
    f = report['inspection']['folders'][0]
    assert f['map'] == 'Fortress' and f['rounds'] == 10 and f['score'] == [7, 3]
    assert f['tracked_count'] == 5 and f['eligible'] and f['duplicate']
    admin.locator('.activity-row input[type=checkbox]').check()
    admin.get_by_role('button', name='Open existing import review').click()
    expect(admin.get_by_role('heading', name='Import an NECC map')).to_be_visible()
    # Preview only; the existing duplicate guard must still block import.
    admin.get_by_role('button', name='Preview path', exact=False).click()
    expect(admin.get_by_text('This replay has already been imported.', exact=True)).to_be_visible(timeout=180000)
    report['normal_handoff_duplicate_guard'] = True
    admin.get_by_role('button', name='Submissions', exact=False).first.click()
    admin.locator('.activity-row').filter(has_text=display).get_by_role('button', name='Review', exact=True).click()
    admin.get_by_label('Rejection reason').fill('Duplicate · production submission E2E test; never imported')
    admin.get_by_role('button', name='Reject remaining folders').click()
    expect(admin.get_by_role('heading', name=display + ' · rejected')).to_be_visible(timeout=15000)
    report['rejected_through_ui'] = True


def verify(headful=False):
    source = ROOT / 'data/replay-archive/fall-2026/d64d5478cdb3'
    target = EVIDENCE / 'e2e-source/MatchReplay/Match-2026-09-23_20-58-42-28736'
    target.mkdir(parents=True, exist_ok=True)
    for replay in source.glob('*.rec'): shutil.copy2(replay, target / replay.name)
    assert len(list(target.glob('*.rec'))) == 10
    seal = json.loads((EVIDENCE / 'before.json').read_text(encoding='utf-8'))['hashes']
    report, session = {'release': '244fe4d', 'uploaded_files': 10}, {}
    cloud = Client(ROOT)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=not headful)
        page = browser.new_page(viewport={'width': 1366, 'height': 1000})
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))

        def response(r):
            if r.url.endswith('/v1/submissions') and r.request.method == 'POST' and r.status == 201:
                session.update(r.json())  # Ephemeral scoped upload capability; never logged/saved.
        page.on('response', response)
        try:
            page.goto('https://uah-r6.github.io/#/submit', wait_until='domcontentloaded')
            expect(page.get_by_role('heading', name='Submit Replays', exact=True)).to_be_visible()
            page.get_by_role('combobox', name='UAH team', exact=True).select_option('white')
            page.get_by_role('combobox', name='Season', exact=True).select_option('fall-2026')
            page.get_by_label('Opponent', exact=True).fill('TEST ONLY · submission verification')
            page.get_by_label('Match date', exact=True).fill('2026-10-07')
            page.get_by_label('Your name / gamer tag').fill('TEST ONLY · DO NOT IMPORT')
            page.get_by_role('radio', name='Not sure', exact=True).check()
            page.locator('input[type=file]').set_input_files(str(target.parent))
            page.locator('.replay-folder-list input').check()
            review = page.get_by_role('button', name='Review submission')
            expect(review).to_be_enabled(timeout=600000 if headful else 60000)
            report['real_turnstile'] = True
            review.click()
            expect(page.get_by_role('heading', name='UAH White', exact=True)).to_be_visible()
            page.get_by_role('checkbox').check()
            page.get_by_role('button', name='Submit for Review', exact=True).click()
            expect(page.get_by_role('heading', name='Submission received')).to_be_visible(timeout=180000)
            report['display_id'] = session['display_id']
            report['submission_id'] = session['id']
            for width in (1920, 1366, 768, 390):
                page.set_viewport_size({'width': width, 'height': 1000})
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'), width
            sid = session['id']
            listing = local('/submissions')
            assert any(s['id'] == sid and s['status'] == 'pending' for s in listing)
            report['storage_after_upload'] = local('/submissions/storage')
            review(browser, sid, session['display_id'], report, errors)
            report['javascript_errors'] = errors
            assert not errors, errors
        finally:
            browser.close()
            if session:
                sid = session['id']
                detail = cloud.call('/submissions/' + sid)
                if detail['status'] in ('pending', 'reviewing'):
                    cloud.call('/submissions/' + sid + '/reject', 'POST', {'reason': 'Live E2E cleanup; never imported'})
                elif detail['status'] == 'uploading':
                    req = urllib.request.Request(cloud.url + '/v1/uploads/' + sid + '/cancel', data=b'{}', method='POST', headers={'Origin': 'https://uah-r6.github.io', 'Authorization': 'Bearer ' + session['upload_token'], 'Content-Type': 'application/json'})
                    with urllib.request.urlopen(req): pass
                cloud.call('/submissions/' + sid + '/purge', 'POST', {'confirm_display_id': session['display_id'], 'delete_metadata': True})
                # Checked absolute private target; never remove raw archive/source.
                staging = (ROOT / 'data/submission-staging' / sid).resolve()
                assert staging.is_relative_to((ROOT / 'data/submission-staging').resolve())
                if staging.exists(): shutil.rmtree(staging)
            result = cloud.call('/reconcile', 'POST', {})
            while not result['complete']: result = cloud.call('/reconcile', 'POST', {})
            report['storage_after_cleanup'] = result
            assert result['stored_bytes'] == 0 and result['reserved_bytes'] == 0 and result['pending_count'] == 0
            report['protected_hashes_unchanged'] = all(hashlib.sha256((ROOT / k).read_bytes()).hexdigest() == value for k, value in seal.items())
            assert report['protected_hashes_unchanged']
            (EVIDENCE / 'live-e2e.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print('PASS: live Turnstile upload, launcher inbox, verified real preview, corrected context, duplicate guard, rejection and cleanup; no imports.')


def review_receipt(display):
    cloud = Client(ROOT)
    matches = [s for s in local('/submissions') if s['display_id'] == display]
    assert len(matches) == 1, 'Test receipt not found in pending submissions.'
    item = matches[0]
    assert 'TEST' in item['opponent'].upper() and 'DO NOT IMPORT' in item['submitter'].upper()
    sid = item['id']
    seal = json.loads((EVIDENCE / 'before.json').read_text(encoding='utf-8'))['hashes']
    report = {'display_id': display, 'submission_id': sid, 'normal_browser_public_upload': True,
              'storage_after_upload': local('/submissions/storage')}
    errors = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(channel='msedge', headless=True)
            try:
                review(browser, sid, display, report, errors)
                assert not errors, errors
            finally: browser.close()
    finally:
        current = cloud.call('/submissions/' + sid)
        if current['status'] in ('pending', 'reviewing'):
            cloud.call('/submissions/' + sid + '/reject', 'POST', {'reason': 'Live E2E cleanup; never imported'})
        cloud.call('/submissions/' + sid + '/purge', 'POST', {'confirm_display_id': display, 'delete_metadata': True})
        staging = (ROOT / 'data/submission-staging' / sid).resolve()
        assert staging.is_relative_to((ROOT / 'data/submission-staging').resolve())
        if staging.exists(): shutil.rmtree(staging)
        result = cloud.call('/reconcile', 'POST', {})
        while not result['complete']: result = cloud.call('/reconcile', 'POST', {})
        report['storage_after_cleanup'] = result
        assert result['stored_bytes'] == 0 and result['reserved_bytes'] == 0 and result['pending_count'] == 0
        report['protected_hashes_unchanged'] = all(hashlib.sha256((ROOT / k).read_bytes()).hexdigest() == value for k, value in seal.items())
        assert report['protected_hashes_unchanged']
        report['javascript_errors'] = errors
        (EVIDENCE / 'live-e2e.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print('PASS: normal-browser live upload, launcher review, real verified preview, corrected context, duplicate guard, UI rejection and cloud cleanup. No imports.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--headful', action='store_true', help='Visible interactive browser for the real Turnstile challenge.')
    parser.add_argument('--review-receipt', help='Review and clean the explicit TEST ONLY receipt uploaded in a normal browser.')
    args = parser.parse_args()
    if args.review_receipt: review_receipt(args.review_receipt)
    else: verify(args.headful)
