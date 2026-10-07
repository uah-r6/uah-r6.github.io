"""Reserve all APAC N Stage1 BO1 group archives before any Rating targets."""
from datetime import datetime,timezone
import json

from credited_late_history_development import immutable_write
from v3_apac1_metadata import nextdata
from v3_cnl_metadata import DATA
from v3_final_reserve import ROOT,sha,source_sha

RESERVE=ROOT/'research/v3-native-final-apac1-reservation.json'
EVENT='Asia Pacific League Stage 1 - APAC N 2026'


def main():
    page=DATA/'competition-505-15000-native-final-discovery.html';official=nextdata(page.read_text(encoding='utf-8'))
    if official['competition']['id']!=505 or official['params']['phaseId']!=15000:raise ValueError('Official event differs')
    matches=sorted([m for step in official['phaseDetails']['steps'] for m in step['matches']],key=lambda m:(m['date'],m['id']))
    metas=[(p,json.loads(p.read_text(encoding='utf-8'))) for p in DATA.glob('apac1-metadata-*.json')]
    development=json.loads((ROOT/'data/research/v3-native-order-development-v1/dataset.json').read_text(encoding='utf-8'))
    used={r['match_id'] for r in development['rows']}
    inventory=[]
    for m in matches:
        selected=bool(m.get('replayLink'));scores=[sorted(t['score'] for t in g['teams']) for g in m['games'] if sum(t['score'] for t in g['teams'])]
        candidates=[(p,meta) for p,meta in metas if meta['competition_id']==110 and meta['date'][:19]==m['date'][:19]]
        if len(candidates)!=1:raise ValueError('Unique independent schedule pairing required')
        path,meta=candidates[0]
        if meta['id'] in used or len(scores)!=1 or len(meta['games'])!=1:raise ValueError('Previously consumed or non-BO1 match')
        if [sorted([g['win_score'],g['loss_score']]) for g in meta['games']]!=scores:raise ValueError('Independent score differs')
        if any(p.get('stats') is not None for p in meta['players']):raise ValueError('Unexpected Rating/stat data in metadata')
        inventory.append(dict(official_match_id=m['id'],siegegg_match_id=meta['id'],date=m['date'],archive_url=m.get('replayLink'),selected=selected,
            official_page=f"https://www.ubisoft.com/en-us/esports/rainbow-six/siege/match/{m['id']}",team_ids=sorted(t['id'] for t in m['teams']),
            official_scores=scores,metadata_sha256=sha(path),rosters=[dict(id=t['id'],name=t['name']) for t in meta['rosters']],
            games=[dict(id=g['id'],map=g['map']['name'],win_roster_id=g['win_roster_id'],loss_roster_id=g['loss_roster_id'],win_score=g['win_score'],loss_score=g['loss_score']) for g in meta['games']]))
    if len(inventory)!=28 or not all(m['selected'] for m in inventory):raise ValueError('Expected entire28linked group-stage snapshot')
    immutable_write(RESERVE,dict(event=EVENT,official_competition_id=505,siegegg_competition_id=110,created_at=datetime.now(timezone.utc).isoformat(),
        matches=inventory,selection='All28officially linked BO1 group-stage archives; playoffs remain reserved and outside this fixed final snapshot. No outcome/feature-selected archives.',
        exposure='Previously cached official overview for actor source discovery; new official group schedule, SiegeGG results schedule and metadata APIs only. No Rating targets/pages/snippets inspected for APAC N Stage1. Prior Asia Stage1 Daystar-Weibo/Psykn-SoulsHeart is a distinct region/event. APAC N Stage2 remains permanently consumed.',
        candidate_sha256=source_sha(ROOT/'research/v3-native-order-candidate.json'),plan_sha256=source_sha(ROOT/'research/v3-native-order-plan.json'),
        metadata_page_sha256=sha(page),ratings_opened=False,quality_policy='All physical/header/identity/counter/core-objective/native-order gates established before targets. No digit stripping or remaining-player aliases. Original final80%/MAE/max/subgroup gates unchanged.'))
    print('Reserved28APAC N Stage1 group-stage archives; no Rating targets opened',flush=True)


if __name__=='__main__':main()
