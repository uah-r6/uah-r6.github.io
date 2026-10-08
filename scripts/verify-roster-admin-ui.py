"""Opt-in browser verification against the real CMD-launched local admin.

Creates exactly one unused temporary identity, exercises its UI, and deletes it
in a finally block. Never imports a replay or changes an existing membership.
"""
import argparse
import json
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'data/research/roster-deletion-20261007/admin-browser'
BASE = 'http://127.0.0.1:8000'
USERNAME = 'RosterDeleteTest_20261007'
ALIAS = 'RosterDeleteAlias_20261007'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--allow-temporary-player', action='store_true', required=True)
    parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=True)
        context = browser.new_context(viewport={'width':1440,'height':960}, timezone_id='America/Chicago')
        page = context.new_page()
        errors, actions, dialogs = [], [], []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.on('dialog', lambda d: (dialogs.append(d.message), d.accept()))
        page.on('response', lambda r: actions.append({'url':r.url,'status':r.status,'method':r.request.method})
                if r.request.method not in ('GET','HEAD') else None)
        page.goto(BASE+'/admin', wait_until='networkidle')
        token = page.request.get(BASE+'/api/admin/session').json()['token']
        headers = {'X-R6-Admin-Token':token}
        def players():
            response = page.request.get(BASE+'/api/admin/roster?team_id=2')
            assert response.ok, response.text()
            return response.json()
        runtime = page.request.get(BASE+'/api/admin/runtime').json()
        assert Path(runtime['sys_executable']) == ROOT/'.venv/Scripts/python.exe'
        assert Path(runtime['server_file']) == ROOT/'r6stats/admin/server.py'
        initial = players()
        assert not any(x['username'] in (USERNAME, ALIAS) for x in initial), 'Temporary username already exists; refusing to touch it.'
        assert len(initial) == 12
        nacho = [x for x in initial if x['username'].casefold()=='nachofries_08']
        assert len(nacho)==1 and nacho[0]['id']==10 and nacho[0]['in_selected_team']
        nanor = next(x for x in initial if x['username']=='Nanor555')
        assert not nanor['in_selected_team'] and nanor['status']=='Active'
        temporary_id = None
        try:
            page.get_by_label('Active admin team').select_option('2')
            page.get_by_role('button', name='Roster', exact=True).click()
            expect(page.locator('#roster-player-10')).to_be_visible()
            expect(page.locator('#roster-player-12')).to_have_count(0)
            expect(page.locator('.roster-row')).to_have_count(6)  # five regulars and the eligible sub-only identity
            expect(page.locator('#roster-player-10').get_by_role('button',name='Remove from roster',exact=True)).to_be_visible()
            page.get_by_label('Ubisoft username',exact=True).fill('NACHOFRIES_08')
            expect(page.locator('.existing-player')).to_contain_text('Existing player: Nachofries_08')
            expect(page.get_by_role('button',name='Already on roster',exact=True)).to_be_disabled()
            page.get_by_role('button',name='Show existing player',exact=True).click()
            expect(page.locator('#roster-player-12')).to_contain_text('Unassigned')
            page.get_by_label('Ubisoft username',exact=True).fill(USERNAME)
            page.get_by_label('Display name (optional)').fill('Temporary roster deletion check')
            page.get_by_label('Regular membership starts').fill('2026-10-07')
            page.get_by_label('Eligible to substitute for any UAH R6 team',exact=True).check()
            with page.expect_response(lambda r:r.url.endswith('/api/admin/roster') and r.request.method=='POST') as result:
                page.get_by_role('button',name='Add player',exact=True).click()
            assert result.value.ok,result.value.text()
            temporary = next(x for x in players() if x['username']==USERNAME)
            temporary_id = temporary['id']
            row = page.locator(f'#roster-player-{temporary_id}')
            expect(row).to_be_visible()
            row.get_by_label('New Ubisoft username / alias').fill(ALIAS)
            with page.expect_response(f'**/api/admin/roster/{temporary_id}/aliases') as result:
                row.get_by_role('button',name='Add alias',exact=True).click()
            assert result.value.ok,result.value.text()
            expect(row.locator('.roster-identity')).to_contain_text(ALIAS)
            row.get_by_label('Effective date').fill('2026-10-07')
            with page.expect_response(f'**/api/admin/roster/{temporary_id}/remove-from-roster') as result:
                row.get_by_role('button',name='Remove from roster',exact=True).click()
            assert result.value.ok,result.value.text()
            expect(row.get_by_role('button',name='Remove from roster',exact=True)).to_have_count(0)
            expect(row).to_contain_text('None (sub-only)')
            temp = next(x for x in players() if x['id']==temporary_id)
            assert temp['status']=='Active' and temp['substitute_eligible'] and not temp['memberships']
            assert set(temp['aliases'])=={USERNAME,ALIAS}
            with page.expect_response(f'**/api/admin/roster/{temporary_id}') as result:
                row.get_by_role('button',name='Mark Alumni',exact=True).click()
            assert result.value.ok
            page.get_by_label('Include Alumni').check()
            expect(row.get_by_role('button',name='Mark Active',exact=True)).to_be_visible()
            with page.expect_response(f'**/api/admin/roster/{temporary_id}') as result:
                row.get_by_role('button',name='Mark Active',exact=True).click()
            assert result.value.ok
            expect(row.get_by_role('button',name='Mark Alumni',exact=True)).to_be_visible()
            page.get_by_label('Ubisoft username',exact=True).fill(USERNAME.lower())
            expect(page.locator('.existing-player')).to_contain_text(ALIAS)
            page.get_by_label('Regular membership starts').fill('2026-10-07')
            with page.expect_response(f'**/api/admin/roster/{temporary_id}/membership') as result:
                page.get_by_role('button',name='Assign existing player',exact=True).click()
            assert result.value.ok,result.value.text()
            expect(row.get_by_role('button',name='Remove from roster',exact=True)).to_be_visible()
            assert len(players())==13
            danger=row.locator('.player-danger-zone')
            with page.expect_response(f'**/api/admin/roster/{temporary_id}/deletion') as result:
                danger.locator('summary').first.click()
            assert result.value.ok and result.value.json()['can_delete']
            typed = danger.get_by_label(f'Type {ALIAS} to confirm')
            typed.fill(USERNAME)
            expect(danger.get_by_role('button',name='Permanently delete player',exact=True)).to_be_disabled()
            # The server independently enforces confirmation, even with a forged client.
            wrong=page.request.delete(BASE+f'/api/admin/roster/{temporary_id}',headers=headers,data={'confirm_username':USERNAME})
            assert wrong.status==400 and 'exact current' in wrong.json()['detail']
            typed.fill(ALIAS)
            expect(danger.get_by_role('button',name='Permanently delete player',exact=True)).to_be_enabled()
            for width in (1440,1100,768,390):
                page.set_viewport_size({'width':width,'height':960})
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),width
                page.screenshot(path=str(OUT/f'danger-{width}.png'),full_page=True)
            with page.expect_response(lambda r:r.url.endswith(f'/api/admin/roster/{temporary_id}') and r.request.method=='DELETE') as result:
                danger.get_by_role('button',name='Permanently delete player',exact=True).click()
            assert result.value.ok,result.value.text()
            expect(row).to_have_count(0)
            assert len(players())==12
            historical=page.locator('#roster-player-1 .player-danger-zone')
            with page.expect_response('**/api/admin/roster/1/deletion') as result:
                historical.locator('summary').first.click()
            audit=result.value.json()
            assert not audit['can_delete']
            expect(historical).to_contain_text('imported match history')
            expect(historical.get_by_role('button',name='Permanently delete player',exact=True)).to_have_count(0)
            blocked=page.request.delete(BASE+'/api/admin/roster/1',headers=headers,data={'confirm_username':'Lgon.'})
            assert blocked.status==400 and 'Mark Alumni' in blocked.json()['detail']
            page.screenshot(path=str(OUT/'historical-blocked-390.png'),full_page=True)
            assert not errors,errors
            report=dict(status='PASS',runtime=runtime,temporary_player_id=temporary_id,temporary_fully_deleted=True,
                typed_confirmation=True,historical_delete_status=blocked.status,historical_audit=audit,
                actions=actions,confirmation_dialogs=dialogs,javascript_errors=errors,viewports=[1440,1100,768,390])
            (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
            print('PASS: actual CMD-launched admin UI; real temporary add/alias/remove/status/reassign/typed delete; historical delete blocked; four widths.')
        finally:
            # Cleanup even if an assertion or browser interaction failed.
            for remaining in players():
                if remaining['id']==temporary_id:
                    result=page.request.delete(BASE+f'/api/admin/roster/{temporary_id}',headers=headers,
                        data={'confirm_username':remaining['username']})
                    assert result.ok, 'Temporary player cleanup failed: '+result.text()
            assert len(players())==12
            browser.close()


if __name__=='__main__':main()
