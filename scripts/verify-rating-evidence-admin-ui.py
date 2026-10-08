"""Exercise evidence maintenance through the actual CMD-launched admin UI."""
import argparse
import json
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'data/research/series-evidence-repair-20261007/admin-browser'


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--repair',action='store_true');args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True)
        page=browser.new_page(viewport={'width':1440,'height':960});errors=[];results=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto('http://127.0.0.1:8000/admin',wait_until='networkidle')
        page.get_by_role('button',name='Statistics',exact=True).click()
        with page.expect_response('**/api/admin/rating-evidence',timeout=120000) as response:
            page.get_by_role('button',name='Audit Rating Evidence',exact=True).click()
        assert response.value.ok,response.value.text()
        audit=response.value.json()
        assert len(audit)==7 and sum(r['eligible'] for r in audit)==4
        assert all(r['archive']['status']=='Healthy' for r in audit)
        expect(page.locator('.evidence-row')).to_have_count(7)
        for width in (1440,1100,768,390):
            page.set_viewport_size({'width':width,'height':960})
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),width
            page.screenshot(path=str(OUT/f'audit-{width}.png'),full_page=True)
        if args.repair:
            page.on('dialog',lambda d:d.accept())
            for mid in ('b595ffaaec57','5adc26f7a402','8a6357ff307c'):
                row=page.locator('.evidence-row').filter(has_text=mid)
                with page.expect_response(f'**/api/admin/matches/{mid}/rating-evidence',timeout=240000) as result:
                    row.get_by_role('button',name='Repair From Healthy Archive',exact=True).click()
                assert result.value.ok,result.value.text()
                value=result.value.json();results.append(value)
                assert not value['after']['eligible'] and value['changes']==[],value
                expect(page.locator('.evidence-result')).to_contain_text(value['message'])
                expect(page.get_by_role('button',name='Audit Rating Evidence',exact=True)).to_be_enabled(timeout=120000)
                page.locator('.evidence-result summary').click()
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                page.screenshot(path=str(OUT/f'{mid}-checked-390.png'),full_page=True)
            with page.expect_response('**/api/admin/regenerate') as response:
                page.get_by_role('button',name='Regenerate Website Data',exact=True).click()
            assert response.value.ok
        runtime=page.request.get('http://127.0.0.1:8000/api/admin/runtime').json()
        assert Path(runtime['sys_executable'])==(ROOT/'.venv/Scripts/python.exe')
        assert not errors,errors
        report=dict(status='PASS',runtime=runtime,audit=audit,repair_checks=results,javascript_errors=errors)
        (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        print('PASS: actual launcher admin; 7-map audit; responsive 1440/1100/768/390; guarded repair checks:',len(results))
        browser.close()


if __name__=='__main__':main()
