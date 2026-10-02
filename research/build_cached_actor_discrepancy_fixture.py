"""Reduce the consumed, broadcast-reviewed Chalet packet evidence for tests."""
from bisect import bisect_right
import json

from objective_clock_candidate import epochs
from objective_transition_probe import ROOT


def main():
    record = json.loads((ROOT / 'data/research/diagnostics/objective-cached-map-validation/false-credit-diagnosis.json').read_text(encoding='utf-8'))[0]
    event, row, feed = record['event'], record['row'], record['feed']
    span = event['context']['interaction_span']
    ticks = epochs(row['clock_ticks'])
    index = bisect_right([t['offset'] for t in ticks], row['center'])-1
    ticks = ticks[index-1:index+4]
    lower, upper = ticks[0]['offset'], ticks[-1]['offset']
    body = {}
    for name, fields in record['body_identity'].items():
        before = [f for f in fields if f['offset'] <= span['first_offset']]
        during = [f for f in fields if span['first_offset'] < f['offset'] <= row['center']]
        body[name] = [dict(offset=f['offset'], value=f['value']) for f in before[-1:]+during]
    fixture = dict(case='3554-6679-R04-plant', expected='kyno', mode='standalone_clock_with_body_guard',
                   original_public_label='Fultz plants defuser', original_primary_verdict='incorrect',
                   independent_source='https://www.youtube.com/watch?v=ISlfYfpK4Tw',
                   independent_frame_seconds=[8817,8822,8824],
                   row=dict(kind='plant', center=row['center'],
                            clock_ticks=[dict(offset=t['offset'], value=t['value']) for t in ticks],
                            all_changes=[{k:c[k] for k in ('counter','delta','offset','entity')} for c in row['all_changes'] if lower <= c['offset'] < upper],
                            identity=dict(entity_names=row['identity']['entity_names']),
                            header=dict(players=[{k:p[k] for k in ('id','username','teamIndex')} for p in row['header']['players']],
                                        teams=[dict(role=t['role']) for t in row['header']['teams']])),
                   deaths=[dict(offset=d['offset'],feedback={k:v for k,v in d['feedback'].items() if k in ('type','username','target')}) for d in feed['events']],
                   timers=[t for t in feed['timers'] if span['first_offset'] <= t['offset'] <= span['last_offset']],
                   body=body, full_feedback=[], previous_state=0)
    (ROOT / 'tests/fixtures/objective-cached-actor-discrepancy.json').write_text(json.dumps(fixture,indent=2),encoding='utf-8')


if __name__ == '__main__':
    main()
