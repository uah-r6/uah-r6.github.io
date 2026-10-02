"""Reduce already consumed public packet evidence for actor regression tests."""
import json

from bisect import bisect_right
from objective_actor_liveness import feedback, interaction_span
from objective_clock_candidate import epochs
from objective_combined_candidate import declared_body_states
from objective_state_components import probe
from objective_transition_probe import ROOT


def main():
    base = ROOT/'data/research/diagnostics'
    rows = []
    for name in ('development','extension'):
        rows += json.loads((base/f'objective-score-structure-{name}.json').read_text())
    wanted = [
        (4139,None,7,'plant',None,'no_unambiguous_guarded_mode'),
        (4139,None,4,'plant','Hotancold.100T','standalone_clock_with_body_guard'),
        (4150,None,7,'plant','Hotancold.100T','standalone_clock_with_body_guard'),
        (3563,6675,2,'disable',None,'no_unambiguous_guarded_mode'),
        (3563,6675,2,'plant','Surf','sole_proven_survivor_throughout_interaction'),
        (3639,None,3,'disable','Lollo.HERETICS','sole_proven_survivor_throughout_interaction'),
    ]
    fixtures = []
    for mid,gid,number,kind,expected,mode in wanted:
        row = next(r for r in rows if (r['match_id'],r['game_id'],r['round'],r['kind'])==(mid,gid,number,kind))
        folder = next((ROOT/'data/research/extracted').rglob(row['folder']))
        rec = next(folder.glob(f'*-R{number:02d}.rec'))
        raw,feed = probe(rec),feedback(rec)
        previous = max((r['center'] for r in rows if r['folder']==row['folder'] and r['round']==number
                        and r['center']<row['center']),default=0)
        span = interaction_span(feed['timers'],row['center'],previous)
        body = {}
        for name,fields in declared_body_states(raw).items():
            prior = [e for e in fields if e['offset']<=span['first_offset']]
            selected = prior[-1:] + [e for e in fields if span['first_offset']<e['offset']<=row['center']]
            body[name]=[dict(offset=e['offset'],value=e['value']) for e in selected]
        ticks = epochs(row['clock_ticks'])
        index = bisect_right([t['offset'] for t in ticks],row['center'])-1
        selected_ticks = ticks[max(0,index-1):index+4]
        lower = selected_ticks[0]['offset']
        upper = selected_ticks[-1]['offset'] if index+3<len(ticks) else float('inf')
        changes = [{k:e[k] for k in ('counter','delta','offset','entity')} for e in row['all_changes']
                   if lower<=e['offset']<upper]
        fixtures.append(dict(case=f'{mid}-{gid}-R{number:02d}-{kind}',expected=expected,mode=mode,
                             row=dict(kind=kind,center=row['center'],clock_ticks=[dict(offset=t['offset'],value=t['value']) for t in selected_ticks],
                                      all_changes=changes,identity=dict(entity_names=row['identity']['entity_names']))
                             | dict(header=dict(players=[{k:p[k] for k in ('id','username','teamIndex')} for p in row['header']['players']],
                                                teams=[dict(role=t['role']) for t in row['header']['teams']])),
                             deaths=[dict(offset=d['offset'],feedback={k:v for k,v in d['feedback'].items() if k in ('type','username','target')}) for d in feed['events']],
                             timers=[t for t in feed['timers'] if span['first_offset']<=t['offset']<=span['last_offset']],
                             body=body,full_feedback=[e for e in raw['feedback'] if e['type']['name']=='PlayerLeave'],previous_state=previous))
    path = ROOT/'tests/fixtures/objective-combined-cases.json'
    path.write_text(json.dumps(fixtures,indent=2),encoding='utf-8')
    print(path,len(fixtures))


if __name__=='__main__':
    main()
