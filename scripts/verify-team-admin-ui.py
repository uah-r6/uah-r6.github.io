"""Read-only browser checks against the actual CMD-launched localhost admin."""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright, expect

OUTPUT = Path('data/research/team-architecture-20261007/admin-browser')
OUTPUT.mkdir(parents=True, exist_ok=True)

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(channel='msedge', headless=True)
    context = browser.new_context(viewport={'width':1440,'height':1000})
    page = context.new_page()
    errors, mutations = [], []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.on('request', lambda request: mutations.append(request.url) if request.method not in ('GET','HEAD')
            and '/replays/preview' not in request.url else None)
    page.goto('http://127.0.0.1:8000/admin', wait_until='networkidle')
    expect(page.get_by_text('Choose an active team and season above to open this workspace.', exact=True)).to_be_visible()
    page.get_by_label('Active admin team').select_option('1')
    expect(page.get_by_role('heading',name='Your command center',exact=True)).to_be_visible()
    expect(page.locator('.admin-metrics>div').nth(1).locator('strong')).to_have_text('5')
    expect(page.locator('.admin-metrics>div').nth(2).locator('strong')).to_have_text('7')
    page.get_by_label('Active admin team').select_option('2')
    expect(page.locator('.admin-metrics>div').nth(1).locator('strong')).to_have_text('0')
    expect(page.locator('.admin-metrics>div').nth(2).locator('strong')).to_have_text('0')
    page.get_by_role('button', name='Roster',exact=True).click()
    expect(page.get_by_text('No players in this view. Add a teammate or show other teams to move an existing player.',exact=True)).to_be_visible()
    page.get_by_label('Active admin team').select_option('1')
    expect(page.locator('.roster-row')).to_have_count(5)
    page.reload(wait_until='networkidle')
    expect(page.get_by_label('Active admin team')).to_have_value('1')
    expect(page.get_by_label('Active admin season')).to_have_value('fall-2026')
    page.get_by_role('button',name='Import Match',exact=True).click()
    with page.expect_response(lambda response:'/api/admin/replays?' in response.url, timeout=120000) as response:
        page.get_by_role('button', name='Scan replay folder',exact=True).click()
    scan = response.value.json()
    (OUTPUT/'scan.json').write_text(json.dumps(scan,indent=2)+'\n',encoding='utf-8')
    expect(page.get_by_text('Replay scan completed.',exact=True)).to_be_visible(timeout=120000)
    ranked = [r for r in scan if r.get('match_type')=='Ranked']
    assert all(not r['eligible'] for r in ranked)
    assert all('duplicate round numbers' not in r.get('status','') for r in scan)
    eligible = [r for r in scan if r.get('eligible') and not r.get('duplicate')]
    preview_tested = False
    if eligible:
        # Preview the first selectable Custom Game with roster matches; never import.
        selected = next((r for r in eligible if r.get('tracked_count',0)>=3),None)
        if selected:
            row = page.locator('.replay-item').filter(has_text=selected['timestamp'][:16]).filter(has_text=selected['map']).first
            with page.expect_response('**/api/admin/replays/preview') as response:
                row.get_by_role('button',name='Preview',exact=True).click()
            preview=response.value.json()
            assert response.value.ok, preview
            assert preview['organization_team']=='UAH Blue' and preview['season_slug']=='fall-2026'
            preview_tested = True
            expect(page.get_by_role('button',name='Import to UAH Blue — Fall 2026',exact=True)).to_be_visible()
            page.get_by_label('Active admin team').select_option('2')
            assert page.locator('.preview-panel').count()==0
            assert page.get_by_role('button',name='Import to UAH Blue — Fall 2026',exact=True).count()==0
    if not preview_tested:
        selected = next(r for r in scan if r.get('eligible') and r.get('tracked_count',0)>=3)
        config = page.request.get('http://127.0.0.1:8000/api/admin/settings').json()
        replay_root = Path(config['replay_path']) if config['replay_path'] else Path.home()/'Documents/My Games/Rainbow Six - Siege/MatchReplay'
        source = str(replay_root/selected['name'])
        page.get_by_label('Or paste a complete match folder / ZIP path').fill(source)
        with page.expect_response('**/api/admin/replays/preview') as response:
            page.get_by_role('button',name='Preview path',exact=True).click()
        preview=response.value.json()
        assert response.value.ok, preview
        assert preview['organization_team']=='UAH Blue' and preview['season_slug']=='fall-2026'
        expect(page.get_by_role('button',name='Import to UAH Blue — Fall 2026',exact=True)).to_be_visible()
        page.get_by_label('Active admin team').select_option('2')
        assert page.locator('.preview-panel').count()==0
        page.get_by_label('Or paste a complete match folder / ZIP path').fill(source)
        with page.expect_response('**/api/admin/replays/preview') as response:
            page.get_by_role('button',name='Preview path',exact=True).click()
        assert response.value.status==400
        assert 'No configured roster member' in response.value.json()['detail']
        preview_tested=True
    page.get_by_label('Active admin team').select_option('1')
    for width,height in [(1920,1080),(1366,768),(768,1024),(390,844)]:
        page.set_viewport_size({'width':width,'height':height})
        for name in ['Dashboard','Teams','Roster','Seasons','Matches','Statistics','Publish','Settings']:
            page.get_by_role('button',name=name,exact=True).click()
            expect(page.locator('.admin-heading h1')).to_be_visible()
            page.wait_for_load_state('networkidle')
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1'), (width,name)
        page.get_by_role('button',name='Dashboard',exact=True).click()
        expect(page.locator('.admin-metrics>div').nth(2).locator('strong')).to_have_text('7')
        page.screenshot(path=str(OUTPUT/f'dashboard-{width}.png'),full_page=True)
    assert not errors, errors
    assert not mutations, mutations
    browser.close()
report={'status':'PASS','admin_url':'http://127.0.0.1:8000/admin','javascript_errors':errors, 'preview_tested':preview_tested,
        'database_mutation_requests':mutations,'scanned_replays':len(scan),'ranked_ineligible':len(ranked),
        'viewports':[1920,1366,768,390],'checks':['explicit context','persisted team/season','Blue5/7','White0/0',
        'White roster empty','scan','preview-only','context invalidation','all pages responsive']}
(OUTPUT/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
