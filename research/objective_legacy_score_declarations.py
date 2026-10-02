"""Describe consumed SI UID-to-score declarations without choosing an actor."""
from collections import Counter,defaultdict
import json

from objective_combined_reserve import inputs
from objective_production_check import candidate_raw
from objective_state_components import probe
from objective_transition_probe import ROOT


def main():
    extraction = ROOT/'data/research/extracted/actor-si-final-2026-02-15'
    folders = ['Match-2026-02-15_18-28-03-10012','Match-2026-02-15_20-36-51-10012']
    reports = []
    for folder_name,number in zip(folders,(4,17)):
        folder = next(extraction.rglob(folder_name))
        rec = next(folder.glob(f'*-R{number:02d}.rec'))
        parsed = candidate_raw(folder)['rounds'][number-1]
        if 'header' not in parsed:
            parsed = dict(header=parsed,matchFeedback=parsed['matchFeedback'])
        row,_,_,_ = inputs(rec,parsed,'plant')
        raw = probe(rec)
        uid = defaultdict(set)
        for p in raw['properties']:
            if p['kind']=='numeric_uid':
                uid[p['entity']].add(p['value'])
        counters = defaultdict(set)
        for e in row['all_changes']:
            counters[e['entity']].add(e['counter'])
        players = []
        for p in raw['header']['players']:
            owners = [owner for owner,ids in uid.items() if ids=={p['id']}]
            declarations = [d for d in raw['declarations'] if d['owner'] in owners and
                            (d['slot_hash']=='eb219b38' or d['component'] in counters)]
            players.append(dict(player=p['username'],owners=owners,
                                score_component_declarations=[d | dict(counters=sorted(counters[d['component']])) for d in declarations]))
        reports.append(dict(folder=folder_name,round=number,build=raw['header']['codeVersion'],
                            score_bindings=row['identity']['entity_names'],players=players))
    classes = Counter((d['slot_hash'],d['class_hash']) for r in reports for p in r['players'] for d in p['score_component_declarations'])
    out = ROOT/'data/research/diagnostics/objective-legacy-score-declarations.json'
    out.write_text(json.dumps(dict(classes={str(k):v for k,v in classes.items()},rounds=reports),indent=2))
    lines = ['# Consumed SI legacy score declarations','',
             'Two completed, now-consumed SI final rounds. Direct declared links from uniquely typed header '
             'UID owners to components receiving canonical score/kills/assists updates. No actor label '
             'or nearest-ID assignment used; no candidate change.', '',f'Observed slot/class counts: `{dict(classes)}`.','',
             '| Physical folder/round/player | UID owners | Declared score slot/class/component/counters |',
             '| --- | --- | --- |']
    for r in reports:
        for p in r['players']:
            declarations = [(d['slot_hash'],d['class_hash'],d['component'],d['counters']) for d in p['score_component_declarations']]
            lines.append(f"| {r['folder']}/R{r['round']:02d}/{p['player']} | {p['owners']} | {declarations} |")
    lines += ['', 'A different score class needs structural and counter/identity validation before any '
              'new separately frozen diagnostic. Mode B sole-survivor identity can in principle use '
              'the declared body UID without a score binding; the current frozen shared score prerequisite '
              'blocks that independent mode on these builds. Preserve both recorded validation outcomes.', '']
    (ROOT/'research/output/objective-legacy-score-declarations.md').write_text('\n'.join(lines),encoding='utf-8')
    print('classes',dict(classes))
    for r in reports:
        print(r['round'],[(p['player'],[(d['slot_hash'],d['class_hash'],d['counters']) for d in p['score_component_declarations']]) for p in r['players']])


if __name__=='__main__':
    main()
