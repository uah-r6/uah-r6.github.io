"""Categorize all consumed disables using clock groups and explicit state paths."""
from bisect import bisect_right
from collections import Counter
import json

from objective_actor_liveness import feedback, interaction_span, player_ledger
from objective_clock_candidate import epochs
from objective_state_components import probe
from objective_transition_probe import ROOT


def score_wave(row, mapping, eligible, start, end):
    changes = [e for e in row['all_changes'] if e['counter']=='score' and e['delta']>0
               and start is not None and start <= e['offset'] and (end is None or e['offset'] < end)
               and mapping.get(e['entity']) in eligible]
    delta = {p:sum(e['delta'] for e in changes if mapping[e['entity']]==p) for p in sorted(eligible)}
    majority = [amount for amount,n in Counter(delta.values()).items() if n>=3 and amount>0]
    residuals = [p for p in sorted(eligible) if len(majority)==1 and delta[p]-majority[0]==100]
    singleton = [p for p in sorted(eligible) if delta[p]>0]
    return dict(deltas=delta,common_delta_observation=majority,excess_observation=residuals,
                standalone_observation=singleton if len(singleton)==1 and delta[singleton[0]]==100 else [],
                changes=changes)


def main():
    base = ROOT / 'data/research/diagnostics'
    state_rows = json.loads((base / 'objective-state-components-all-consumed.json').read_text())
    structures = []
    for name in ('development','extension'):
        structures += json.loads((base / f'objective-score-structure-{name}.json').read_text())
    reports = []
    for row in structures:
        if row['kind'] != 'disable':
            continue
        folder = next((ROOT / 'data/research/extracted').rglob(row['folder']))
        rec = next(folder.glob(f"*-R{row['round']:02d}.rec"))
        state = next(s for s in state_rows if (s['folder'],s['round']) == (row['folder'],row['round']))
        raw = probe(rec)
        deaths = feedback(rec)
        mapping = {int(k):v[0] for k,v in row['identity']['entity_names'].items() if len(v)==1}
        eligible = {p['username'] for p in row['header']['players'] if row['header']['teams'][p['teamIndex']]['role']=='Defense'}
        ticks = epochs(row['clock_ticks'])
        index = bisect_right([t['offset'] for t in ticks], row['center']) - 1
        start = ticks[index]['offset'] if index >= 0 else None
        end = ticks[index+1]['offset'] if index+1 < len(ticks) else None
        current = score_wave(row,mapping,eligible,start,end)
        expanded_end = ticks[index+2]['offset'] if index+2 < len(ticks) else None
        expanded = score_wave(row,mapping,eligible,start,expanded_end)
        expanded['window_end'] = expanded_end
        expanded['following_clock'] = ticks[index+1]['value'] if index+1<len(ticks) else None
        expanded['kill_death_events'] = [d for d in deaths['events'] if d['offset']>0 and start is not None
                                       and start<=d['offset'] and (expanded_end is None or d['offset']<expanded_end)]
        expanded['counter_events'] = [e for e in row['all_changes'] if e['counter'] in ('kills','assists') and e['delta']>0
                                      and start is not None and start<=e['offset'] and (expanded_end is None or e['offset']<expanded_end)]
        ledger = player_ledger(row['header'], deaths['events'], row['all_changes'],row['identity'],row['center'],'Defense')
        not_dead = [p['player'] for p in ledger if p['alive_at_completion'] is True]
        body = {}
        for p in eligible:
            links = [l for l in state['candidate_links'] if l['player']==p and len(l['path'])==2]
            if len(links)!=1:
                body[p] = None
                continue
            states = [e for e in raw['properties'] if e['entity']==links[0]['path'][-1] and e['hash']=='e788f6a5' and e['offset']<=row['center']]
            body[p] = states[-1]['value'] if states else None
        category = ('unknown_death_timing' if any(p['alive_at_completion'] is None for p in ledger)
                    else 'sole_not_eliminated_with_body_state_0' if len(not_dead)==1 and body[not_dead[0]]==0
                    else 'multiple_not_eliminated_no_actor_owner' if len(not_dead)>1
                    else 'body_or_liveness_unresolved')
        reports.append({k:row[k] for k in ('match_id','game_id','round','build')}
                       |dict(category=category, clock_window=dict(start=start,end=end,value=ticks[index]['value'] if index>=0 else None),
                             **current, completion_and_next_epoch=expanded,
                             not_eliminated=not_dead, raw_body_state=body,
                             player_leave_events=[e for e in raw['feedback'] if e['type']['name']=='PlayerLeave']))
    # Older February disable is a known occurrence with no typed state anchor.
    reports.append(dict(match_id=3073,game_id=None,round=8,build=None,category='no_completion_state_anchor',
                        clock_window={},deltas={},common_delta_observation=[],excess_observation=[],not_eliminated=[],raw_body_state={}))
    counts = dict(Counter(r['category'] for r in reports))
    (base/'objective-disable-structure.json').write_text(json.dumps(dict(counts=counts,events=reports),indent=2))
    lines = ['# Consumed disable clock/state evidence', '',
             'Twenty consumed disables. A score interval is the distinct clock epoch containing the validated '
             'completion state; if no subsequent tick exists, it extends to the physical round EOF. '
             'Deltas use the complete existing ledger. This is a descriptive diagnostic, not an actor resolver. '
             'Majority delta and +100 excess remain observations, not a causal decomposition. '
             'A second fixed structural observation also includes the immediately following distinct clock epoch '
             '(including reset-to-zero when present), ending at the next epoch or EOF. This captures score waves '
             'serialized after the completion epoch ends without a label-selected byte/time threshold.', '',
             f'Unresolved/support categories: `{counts}`.', '',
             '| Match/game/round | Category | Clock | Team deltas | +100 excess observation | Raw body state at completion |',
             '| --- | --- | --- | --- | --- | --- |']
    for r in reports:
        lines.append(f"| {r['match_id']}/{r['game_id']}/R{r['round']:02d} | {r['category']} | {r['clock_window']} | {r['deltas']} | {r['excess_observation']} | {r['raw_body_state']} |")
    lines += ['', '## Completion epoch plus immediately following epoch', '',
              '| Match/game/round | Following clock | Team deltas | Common / excess / standalone observations | Kill/death / counter collisions |',
              '| --- | --- | --- | --- | --- |']
    for r in reports:
        expanded = r.get('completion_and_next_epoch')
        if not expanded:
            continue
        lines.append(f"| {r['match_id']}/{r['game_id']}/R{r['round']:02d} | {expanded['following_clock']} | {expanded['deltas']} | "
                     f"{expanded['common_delta_observation']} / {expanded['excess_observation']} / {expanded['standalone_observation']} | "
                     f"{len(expanded['kill_death_events'])} / {len(expanded['counter_events'])} |")
    lines += ['', 'The disputed 3563/6675 R02 residual remains njr while public actor is J9O; both have '
              'body state0 and no earlier decoded death. Body state therefore cannot break that ambiguity. '
              'Do not replace the public label or promote relative-score selection. State2/3, DBNO/revive '
              'and disconnect timing remain unknown. Fresh reserve stays sealed.', '']
    (ROOT/'research/output/objective-disable-structure.md').write_text('\n'.join(lines),encoding='utf-8')
    print(counts)


if __name__ == '__main__':
    main()
