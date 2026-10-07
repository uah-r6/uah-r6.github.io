"""Read-only checks of the real CMD-launched admin and intercepted controls."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT/'data/research/substitutes-20261007/admin-browser'


def verify():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge', headless=True)
        page=browser.new_page(viewport={'width':1440,'height':960})
        errors,mutations=[],[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.on('request',lambda r:mutations.append(r.url) if r.method not in ('GET','HEAD') and not r.url.endswith('/replays/preview') else None)
        page.goto('http://127.0.0.1:8000/admin',wait_until='networkidle')
        page.get_by_label('Active admin team').select_option('1')
        page.get_by_role('button',name='Roster',exact=True).click()
        expect(page.locator('.roster-row')).to_have_count(5)
        expect(page.locator('.admin-heading')).to_contain_text('Substitute eligibility permits play for any UAH team')
        expect(page.get_by_label('Substitute eligible for any UAH R6 team')).to_have_count(5)
        for width in (1440,1100,768,390):
            page.set_viewport_size({'width':width,'height':960})
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),('roster',width)
            page.screenshot(path=str(OUTPUT/f'roster-{width}.png'),full_page=True)
        page.set_viewport_size({'width':1440,'height':960})
        page.get_by_role('button',name='Import Match',exact=True).click()
        page.get_by_label('Or paste a complete match folder / ZIP path').fill(str(ROOT/'data/replay-archive/fall-2026/d64d5478cdb3'))
        with page.expect_response('**/api/admin/replays/preview',timeout=120000) as response:
            page.get_by_role('button',name='Preview path',exact=True).click()
        preview=response.value.json()
        assert response.value.ok,preview
        assert preview['map']=='Fortress' and preview['rounds']==10
        assert len(preview['appearances'])==5 and all(p['appearance_role']=='roster' for p in preview['appearances'])
        assert preview['duplicate'] is True
        (OUTPUT/'real-preview.json').write_text(json.dumps(preview,indent=2),encoding='utf8')
        for width in (1440,1100,768,390):
            page.set_viewport_size({'width':width,'height':960})
            expect(page.locator('.appearance-list>div')).to_have_count(5)
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),('preview',width)
            page.screenshot(path=str(OUTPUT/f'preview-{width}.png'),full_page=True)
        page.get_by_role('button',name='Matches',exact=True).click()
        page.get_by_role('button',name='Open map',exact=True).first.click()
        expect(page.locator('.map-detail .appearance-list>div')).to_have_count(5)
        expect(page.locator('.map-detail .appearance-list')).to_contain_text('Regular roster: UAH Blue')
        for width in (1440,1100,768,390):
            page.set_viewport_size({'width':width,'height':960})
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),('match detail',width)
            page.screenshot(path=str(OUTPUT/f'match-{width}.png'),full_page=True)
        # Browser-only fake roster state proves the controls without writing to
        # the launched production API. Backend tests exercise real temp SQLite.
        fixture=browser.new_page(viewport={'width':1440,'height':960})
        fixture.on('pageerror',lambda e:errors.append(str(e)))
        player={'id':99,'slug':'fixture','display_name':'Fixture Sub','username':'Fixture','status':'Active','tracked':1,
                'profile_bound':False,'aliases':['Fixture'],'memberships':[],'in_selected_team':False,'substitute_eligible':1}
        actions=[]
        def intercept(r):
            if r.request.method=='GET':r.fulfill(json=[player])
            else:
                actions.append({'method':r.request.method,'payload':r.request.post_data_json})
                if r.request.method=='PATCH':player.update(r.request.post_data_json)
                r.fulfill(json={'ok':True})
        fixture.route('**/api/admin/roster**',intercept)
        fixture.goto('http://127.0.0.1:8000/admin',wait_until='networkidle')
        fixture.get_by_label('Active admin team').select_option('1')
        fixture.get_by_role('button',name='Roster',exact=True).click()
        expect(fixture.locator('.roster-row')).to_contain_text('Global substitute pool')
        fixture.get_by_label('Show other teams and unassigned players').check()
        fixture.get_by_label('Substitute eligible for any UAH R6 team',exact=True).uncheck()
        expect(fixture.get_by_label('Substitute eligible for any UAH R6 team',exact=True)).to_be_enabled()
        fixture.get_by_label('Substitute eligible for any UAH R6 team',exact=True).check()
        fixture.get_by_label('No regular roster (sub-only)').check()
        expect(fixture.get_by_label('Regular membership starts')).to_be_disabled()
        fixture.get_by_label('Ubisoft username',exact=True).fill('NewFixture')
        fixture.get_by_role('button',name='Add player',exact=True).click()
        fixture.wait_for_timeout(200)
        assert actions[0]['payload']=={'substitute_eligible':False}
        assert actions[1]['payload']=={'substitute_eligible':True}
        assert actions[2]['payload']['team_id'] is None and actions[2]['payload']['substitute_eligible'] is True
        for width in (1440,1100,768,390):
            fixture.set_viewport_size({'width':width,'height':960})
            assert fixture.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),('sub-only admin',width)
        assert not mutations,mutations
        assert not errors,errors
        browser.close()
    report={'status':'PASS','viewports':[1440,1100,768,390], 'real_preview':{'map':preview['map'],'rounds':preview['rounds'],'roles':[a['appearance_role'] for a in preview['appearances']]},
            'database_mutations':mutations,'intercepted_actions':actions,'javascript_errors':errors}
    (OUTPUT/'report.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':verify()
