"""Verify production maintenance through the actual CMD-launched admin UI.

Read-only unless --repair is supplied. Private diagnostics stay ignored.
"""
import argparse
import json
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'data/research/rating-evidence-production-20261008/admin-browser'


def import_status_fixture(browser):
    """Intercept every write: exercise both import result UIs without DB imports."""
    context=browser.new_context(viewport={'width':390,'height':960})
    context.add_init_script("localStorage.setItem('uah-admin-team','2');localStorage.setItem('uah-admin-season','fall-2026')")
    context.route('**/api/admin/**',lambda r:r.abort() if r.request.method!='GET' else r.continue_())
    context.route('**/api/admin/replays?*',lambda r:r.fulfill(json=[]))
    preview=dict(organization_team='UAH White',team_id=2,season_slug='fall-2026',season_name='Fall 2026',
        preview_token='intercepted-fixture-only',map='Fixture',timestamp='2026-10-08T12:00:00',match_type='Custom Game',
        game_mode='Bomb',rounds=2,score=[1,1],our_team=0,tracked_players=['Fixture Player'],
        teams=[dict(index=0,players=['Fixture Player']),dict(index=1,players=['Opponent'])],
        ambiguous=None,duplicate=False,active_season='fall-2026',competition_if_confirmed='NECC')
    rehost={**preview,'segments':[dict(segment=i,source_name=f'Fixture {i}',players=[['Fixture Player'],['Opponent']],
        absent=[[],[]],added=[[],[]],physical_start=[0,0],logical_start=[0,0],score_mode='continue') for i in (1,2)],
        'physical_rounds':[],'roster_change_required':False,'score_override_required':False}
    calls=[]
    for mode in ('normal','rehost'):
        endpoint='/api/admin/replays'+('/rehost' if mode=='rehost' else '')
        context.route('**'+endpoint+'/preview',lambda r,request,v=preview if mode=='normal' else rehost:r.fulfill(json=v))
        context.route('**'+endpoint+'/import',lambda r:r.fulfill(json=dict(ok=True,map_id='intercepted-fixture',rounds=2,
            rating=dict(eligible=False,status='UNAVAILABLE',reason='Incomplete credited-kill evidence',changes=[],
                blockers=['Exact intercepted reader failure']))))
        page=context.new_page();page.on('dialog',lambda d:d.accept())
        page.goto('http://127.0.0.1:8000/admin',wait_until='networkidle')
        page.get_by_role('button',name='Import Match',exact=True).click()
        if mode=='normal':
            page.locator('.manual-path input').fill('Fixture path')
            page.get_by_role('button',name='Preview path',exact=True).click()
            page.get_by_label('Opponent name',exact=True).fill('Fixture opponent')
        else:
            page.get_by_role('button',name='Rehosted map',exact=True).click()
            for i,item in enumerate(page.locator('.rehost-segment input').all()):item.fill(f'Fixture {i}')
            page.get_by_role('button',name='Preview physical rounds',exact=True).click()
            page.get_by_label('Opponent',exact=True).fill('Fixture opponent')
        for checkbox in page.locator('.preview-panel .confirm-line input').all():checkbox.check()
        page.locator('.preview-panel').get_by_role('button',name='Import to UAH White',exact=False).click()
        card=page.locator('.rating-status-card')
        expect(card).to_contain_text('Map imported successfully')
        expect(card).to_contain_text('Rating eligible: NO')
        expect(card).to_contain_text('Incomplete credited-kill evidence')
        card.locator('summary').click()
        expect(card).to_contain_text('Exact intercepted reader failure')
        context.route('**/api/admin/matches/intercepted-fixture/rating-evidence',lambda r:r.fulfill(json=dict(
            before=dict(eligible=False),after=dict(eligible=True,exclusion=None),changes=['objective evidence'],blockers=[],
            message='Rating evidence repaired; full v3 validation passed.')))
        card.get_by_role('button',name='Repair Rating Evidence From Archive',exact=True).click()
        expect(card).to_contain_text('Rating eligible: YES')
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
        page.screenshot(path=str(OUT/f'{mode}-import-status-fixture.png'),full_page=True)
        calls.append(mode);page.close()
    context.close()
    return calls


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repair', action='store_true')
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=True)
        page = browser.new_page(viewport={'width':1440,'height':960})
        page.add_init_script("localStorage.setItem('uah-admin-team','2');localStorage.setItem('uah-admin-season','fall-2026')")
        errors, results = [], []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.on('dialog', lambda d: d.accept())
        page.goto('http://127.0.0.1:8000/admin', wait_until='networkidle')
        runtime = page.request.get('http://127.0.0.1:8000/api/admin/runtime').json()
        assert Path(runtime['sys_executable']) == ROOT/'.venv/Scripts/python.exe'
        page.get_by_role('button', name='Matches', exact=True).click()
        page.locator('.series-maps>div').filter(has_text='Nighthaven Labs').get_by_role('button',name='Open map',exact=True).click()
        card = page.locator('.rating-status-card')
        expect(card).to_contain_text('035ff71d4884')
        if args.repair:
            expect(card).to_contain_text('Rating eligible: NO')
            expect(card).to_contain_text('Whole map has unsupported core objective evidence.')
            with page.expect_response('**/api/admin/matches/035ff71d4884/rating-evidence', timeout=240000) as response:
                card.get_by_role('button',name='Repair Rating Evidence From Archive',exact=True).click()
            assert response.value.ok, response.value.text()
            repair = response.value.json()
            assert repair['after']['eligible'] and repair['changes']==['supported objective actor correction'], repair
            results.append(repair)
        expect(card).to_contain_text('Rating eligible: YES')
        expect(card.get_by_role('button',name='Repair Rating Evidence From Archive',exact=True)).to_be_disabled()
        page.screenshot(path=str(OUT/'white-repaired.png'), full_page=True)
        page.get_by_role('button',name='Statistics',exact=True).click()
        with page.expect_response('**/api/admin/rating-evidence',timeout=120000) as response:
            page.get_by_role('button',name='Audit Rating Evidence',exact=True).click()
        audit = response.value.json()
        assert len(audit)==9 and sum(r['eligible'] for r in audit)==6, audit
        assert all(r['archive']['status']=='Healthy' for r in audit)
        expect(page.locator('.evidence-row')).to_have_count(9)
        if args.repair:
            with page.expect_response('**/api/admin/rating-evidence/repair-all',timeout=360000) as response:
                page.get_by_role('button',name='Audit / Repair All Rating Evidence',exact=True).click()
            assert response.value.ok,response.value.text()
            bulk = response.value.json()
            assert (bulk['audited'],bulk['already_eligible'],bulk['repaired'],bulk['blocked'])==(9,6,0,3),bulk
            assert all(not r['changes'] for r in bulk['results']),bulk
            results.append(bulk)
            for item in page.locator('.evidence-bulk details').all(): item.locator('summary').click()
        for width in (1440,1100,768,390):
            page.set_viewport_size({'width':width,'height':960})
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),width
            page.screenshot(path=str(OUT/f'audit-{width}.png'),full_page=True)
        assert not errors,errors
        fixtures=import_status_fixture(browser)
        report=dict(status='PASS',runtime=runtime,audit=audit,repairs=results,intercepted_import_modes=fixtures,javascript_errors=errors)
        (OUT/('report.json' if args.repair else 'readonly-report.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        print('PASS: CMD-launched admin; 9-map audit; White eligible; four responsive widths; normal/rehost import status fixtures',
            '; real detail/bulk repair checked' if args.repair else '; production writes disabled')
        browser.close()


if __name__=='__main__': main()
