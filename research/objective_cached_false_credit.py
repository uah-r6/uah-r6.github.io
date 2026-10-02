"""Packet-ordered diagnosis AFTER the cached-map frozen result was committed.

No candidate changes. This set is consumed, not independent validation.
Full evidence stays ignored; compact ordered ledgers are reviewable in Git.
"""
from bisect import bisect_right
import html
import json
import re

from objective_cached_map_validation import inputs
from objective_combined_candidate import declared_body_states
from objective_production_check import candidate_raw
from objective_clock_candidate import epochs
from objective_transition_probe import ROOT


def main():
    base = ROOT / 'data/research/diagnostics/objective-cached-map-validation'
    result = json.loads((base / 'result.json').read_text())
    reports = []
    for event in result['events']:
        if event['verdict'] != 'incorrect':
            continue
        folder = next((ROOT / 'data/research/extracted').rglob(event['folder']))
        rec = next(folder.glob(f"*-R{event['physical_round']:02d}.rec"))
        baseline = candidate_raw(folder)['rounds'][event['physical_round'] - 1]
        if 'header' not in baseline:
            baseline = dict(header=baseline, matchFeedback=baseline['matchFeedback'])
        row, feed, state, previous = inputs(rec, baseline, event['kind'])
        mapping = {int(k): v[0] for k, v in row['identity']['entity_names'].items() if len(v) == 1}
        ticks = epochs(row['clock_ticks'])
        clock_at = lambda offset: ticks[bisect_right([t['offset'] for t in ticks], offset)-1]['value']
        body = declared_body_states(state)
        order = []
        for change in row['all_changes']:
            order.append(dict(offset=change['offset'], kind='counter', player=mapping.get(change['entity'], 'unmapped'),
                              counter=change['counter'], previous=change['previous'], value=change['value'],
                              delta=change['delta'], entity=change['entity']))
        for death in feed['events']:
            order.append(dict(offset=death['offset'], kind='feedback', event=death['feedback']))
        for timer in feed['timers']:
            order.append(dict(offset=timer['offset'], kind='objective_timer', value=timer['value']))
        for player, changes in body.items():
            for change in changes:
                order.append(dict(offset=change['offset'], kind='body', player=player, value=change['value']))
        order += [dict(offset=t['offset'], kind='clock', value=t['value']) for t in ticks]
        order.append(dict(offset=row['center'], kind='completion', value=event['kind']))
        for item in order:
            item['clock'] = clock_at(item['offset'])
        order.sort(key=lambda item: item['offset'])
        plain = ' '.join(html.unescape(re.sub('<[^>]+>', ' ', event['public_label'])).split())
        reports.append(dict(event=event, plain_label=plain, row=row, feed=feed,
                            body_identity=body, complete_order=order,
                            identity_declarations=row['identity']))
    (base / 'false-credit-diagnosis.json').write_text(json.dumps(reports, indent=2), encoding='utf-8')
    lines = ['# Consumed cached-map false-credit diagnosis', '',
             'The frozen result was permanently committed as 91594f3 before this analysis. '
             'No actor rule, immutable output, live data or Rating is changed. '
             'Clock epochs describe serialization order, not decoded network frames.', '']
    for report in reports:
        event, row = report['event'], report['row']
        lines += [f"## {event['match_id']}/{event['game_id']}/R{event['round']:02d}, build {event['build']}", '',
                  f"Frozen candidate: {event['candidate']}. Public target: {report['plain_label']}.", '',
                  f"Interaction: `{event['context']['interaction_span']}`. Completion offset: {row['center']}. "
                  f"Frozen score interval: `{event['context']['score_interval']}`.", '',
                  '### Stable score identity', '', '| Player | UID | Score entities |', '| --- | --- | --- |']
        for p in row['header']['players']:
            entities = [k for k,v in row['identity']['entity_names'].items() if v == [p['username']]]
            lines.append(f"| {p['username']} | {p.get('id')} | {entities} |")
        lines += ['', '### Ordered score and Kill/Death records (whole round)', '',
                  '| Offset | Clock | Type | Evidence |', '| --- | --- | --- | --- |']
        for item in report['complete_order']:
            if item['kind'] not in ('counter', 'feedback', 'completion'):
                continue
            details = {k:v for k,v in item.items() if k not in ('offset', 'clock', 'kind')}
            lines.append(f"| {item['offset']} | {item['clock']} | {item['kind']} | {details} |")
        lines += ['', '### Interaction and completion clock epochs', '',
                  '| Offset | Clock | Type | Evidence |', '| --- | --- | --- | --- |']
        index = bisect_right([t['offset'] for t in epochs(row['clock_ticks'])], row['center'])-1
        end = epochs(row['clock_ticks'])[index+3]['offset']
        start = event['context']['interaction_span']['first_offset']
        for item in report['complete_order']:
            if not start <= item['offset'] < end:
                continue
            # Keep the actual timer start/end; full timer samples are cached.
            if item['kind'] == 'objective_timer' and item['offset'] not in (start, event['context']['interaction_span']['last_offset']):
                continue
            details = {k:v for k,v in item.items() if k not in ('offset', 'clock', 'kind')}
            lines.append(f"| {item['offset']} | {item['clock']} | {item['kind']} | {details} |")
    lines += ['', 'A unique +100 immediately after completion is an association, not proof of its scoring cause. '
              'Investigate stable identity, score counter history, actual planter interaction and independent broadcast evidence '
              'before proposing any correction. No per-event blacklist or score-window retuning.', '']
    (ROOT / 'research/output/objective-cached-false-credit.md').write_text('\n'.join(lines), encoding='utf-8')
    for report in reports:
        print(report['event']['match_id'], report['event']['round'], report['plain_label'], flush=True)
        for item in report['complete_order']:
            if item['kind'] in ('counter', 'feedback', 'completion') and item['offset'] >= report['event']['context']['interaction_span']['first_offset']:
                print(item)


if __name__ == '__main__':
    main()
