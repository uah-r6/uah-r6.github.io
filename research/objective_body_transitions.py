"""Describe raw body-state transitions on consumed rounds; no eligibility rule."""
from bisect import bisect_right
from collections import Counter
import json

from objective_clock_candidate import epochs
from objective_actor_liveness import feedback
from objective_state_components import probe
from objective_transition_probe import ROOT


def main():
    base = ROOT / 'data/research/diagnostics'
    links = json.loads((base / 'objective-state-components-all-consumed.json').read_text())
    structures = []
    for name in ('development', 'extension'):
        structures += json.loads((base / f'objective-score-structure-{name}.json').read_text())
    rounds = {(r['folder'], r['round']): r for r in structures}
    records = []
    for key, row in rounds.items():
        folder = next((ROOT / 'data/research/extracted').rglob(row['folder']))
        rec = next(folder.glob(f"*-R{row['round']:02d}.rec"))
        raw = probe(rec)
        deaths = feedback(rec)['events']
        clock = epochs(row['clock_ticks'])
        offsets = [c['offset'] for c in clock]
        paths = next(r for r in links if (r['folder'], r['round']) == key)['candidate_links']
        for path in paths:
            if len(path['path']) != 2:
                raise ValueError('Unexpected component path')
            entity = path['path'][-1]
            state_fields = [p for p in raw['properties'] if p['entity'] == entity and p['hash'] == 'e788f6a5']
            hp_fields = [p for p in raw['properties'] if p['entity'] == entity and p['kind'] == 'health']
            previous = None
            transitions = []
            for field in state_fields:
                if field['value'] == previous:
                    continue
                index = bisect_right(offsets, field['offset']) - 1
                health = [p for p in hp_fields if p['offset'] <= field['offset']]
                transitions.append(dict(offset=field['offset'], previous=previous, value=field['value'],
                                        clock=clock[index]['value'] if index >= 0 else None,
                                        hp=health[-1]['value'] if health else None,
                                        after_action_start=field['offset'] > row['header'].get('actionPhaseStartOffset', 0)))
                previous = field['value']
            killed = [d for d in deaths if
                      (d['feedback']['type']['name'] == 'Kill' and d['feedback'].get('target') == path['player']) or
                      (d['feedback']['type']['name'] == 'Death' and d['feedback'].get('username') == path['player'])]
            records.append(dict(match_id=row['match_id'], game_id=row['game_id'], folder=row['folder'],
                                round=row['round'], build=row['build'], player=path['player'], transitions=transitions,
                                deaths=killed, objectives=[dict(kind=e['kind'],offset=e['center']) for e in structures
                                                          if (e['folder'],e['round']) == key]))
    action = Counter((t['previous'],t['value']) for r in records for t in r['transitions'] if t['after_action_start'])
    examples = [r for r in records if any(t['value'] in (2,3) and t['after_action_start'] for t in r['transitions'])]
    (base / 'objective-body-transitions.json').write_text(json.dumps(dict(action_transitions={str(k):v for k,v in action.items()},
                                                                        players=records),indent=2))
    lines = ['# Consumed body-state transitions', '',
             'Raw `e788f6a5` values on direct declared UID-to-health components. Clock values are replay epochs, '
             'not elapsed seconds across resets. Initial snapshots are retained but excluded from action transition counts. '
             'No actor selector or DBNO enum mapping is inferred.', '', f'Action transition counts: `{dict(action)}`.', '',
             '| Match/game/round/player | State timeline (clock, state, last HP) | Death offsets | Objective offsets |',
             '| --- | --- | --- | --- |']
    for r in examples:
        lines.append(f"| {r['match_id']}/{r['game_id']}/R{r['round']:02d}/{r['player']} | "
                     f"{[(t['clock'],t['value'],t['hp'],t['offset']) for t in r['transitions']]} | "
                     f"{[d['offset'] for d in r['deaths']]} | {r['objectives']} |")
    lines += ['', 'Independent HUD sampling must label state2/3 transitions (including round-end transitions) '
              'before either can be a DBNO/death/revive eligibility flag. Fresh reserve remains sealed.', '']
    (ROOT / 'research/output/objective-body-transitions.md').write_text('\n'.join(lines),encoding='utf-8')
    print('player rounds',len(records),'state2/3 action examples',len(examples),'transitions',dict(action))


if __name__ == '__main__':
    main()
