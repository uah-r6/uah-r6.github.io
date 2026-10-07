"""Prospective whole-event CNL selection with no Rating-target access."""
import json
from datetime import datetime,timezone

from credited_late_history_development import immutable_write
from v3_cnl_metadata import DATA,official
from v3_final_reserve import ROOT,sha,source_sha

RESERVE=ROOT/'research/v3-credited-final-cnl-reservation.json'


def main():
    data,matches=official()
    metas=[json.loads(p.read_text(encoding='utf-8')) for p in DATA.glob('cnl1-metadata-*.json')]
    metas=[m for m in metas if m['competition_id']==105]
    used={m.get('siegegg_match_id') for m in json.loads((ROOT/'research/sources.json').read_text(encoding='utf-8'))['matches']}
    inventory=[]
    for m in matches:
        scores=[sorted(t['score'] for t in g['teams']) for g in m['games'] if sum(t['score'] for t in g['teams'])]
        entry=dict(official_match_id=m['id'],date=m['date'],archive_url=m.get('replayLink'),
            official_page=f"https://www.ubisoft.com/en-us/esports/rainbow-six/siege/match/{m['id']}",
            team_ids=sorted(t['id'] for t in m['teams']),official_scores=scores,selected=bool(m.get('replayLink')))
        if entry['selected']:
            candidates=[p for p in metas if p['date'][:19]==m['date'][:19]]
            if len(candidates)!=1:raise ValueError('Unique independent schedule date pairing required')
            meta=candidates[0]
            if meta['id'] in used or [sorted([g['win_score'],g['loss_score']]) for g in meta['games']]!=scores:
                raise ValueError('Previously consumed match or official/public score discrepancy')
            if any(p.get('stats') is not None for p in meta['players']):raise ValueError('Metadata endpoint unexpectedly contains player stats')
            entry.update(siegegg_match_id=meta['id'],siegegg_page='https://siege.gg'+meta['web_url'],
                metadata_sha256=sha(DATA/f"cnl1-metadata-{meta['id']}.json"),
                rosters=[dict(id=t['id'],name=t['name']) for t in meta['rosters']],
                games=[dict(id=g['id'],map=g['map']['name'],win_roster_id=g['win_roster_id'],loss_roster_id=g['loss_roster_id'],win_score=g['win_score'],loss_score=g['loss_score']) for g in meta['games']])
        inventory.append(entry)
    if len(inventory)!=45 or sum(e['selected'] for e in inventory)!=27:raise ValueError('Unexpected prospective event scope')
    immutable_write(RESERVE,dict(event='China League 2026 Stage 1',official_competition_id=517,siegegg_competition_id=105,
        created_at=datetime.now(timezone.utc).isoformat(),matches=inventory,
        selection='All27officially linked group-stage BO3 archives at checkpoint, not selected by outcomes/objectives; other18scheduled matches remain reserved outside fixed snapshot.',
        exposure='Schedule and metadata-only API projection; no player-stat targets or match/player Rating pages opened. ChinaStage2 excluded because prior search snippets exposed Ratings.',
        metadata_page_sha256=sha(DATA/'competition-517-15026-sequential-discovery.html'),
        candidate_sha256=source_sha(ROOT/'research/v3-credited-candidate.json'),
        plan_sha256=source_sha(ROOT/'research/v3-credited-development-plan.json'),ratings_opened=False))
    print('Reserved CNL Stage1:45scheduled/27linked; no Rating targets opened')


if __name__=='__main__':main()
