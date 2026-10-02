"""Read-only diagnosis of permanently recorded, now-consumed reserve abstentions."""
from collections import Counter,defaultdict
import html
import json
import re

from objective_combined_candidate import declared_body_states
from objective_state_components import probe
from objective_transition_probe import ROOT


def main():
    base = ROOT/'data/research/diagnostics/objective-combined-reserve'
    result = json.loads((base/'result.json').read_text())
    records = []
    for event in result['events']:
        if event['candidate'] or event['mode']!='incomplete_declared_body_identity':
            continue
        folder = next((ROOT/'data/research/extracted').rglob(event['folder']))
        rec = next(folder.glob(f"*-R{event['physical_round']:02d}.rec"))
        raw = probe(rec)
        bound = declared_body_states(raw)
        owners = defaultdict(set)
        for prop in raw['properties']:
            if prop['kind']=='numeric_uid':
                owners[prop['entity']].add(prop['value'])
        players = []
        for p in raw['header']['players']:
            controllers = [owner for owner,uids in owners.items() if p['id'] in uids]
            paths = [d for d in raw['declarations'] if d['owner'] in controllers and d['slot_hash']=='4154dcc4']
            players.append(dict(player=p['username'],numeric_uid=p['id'],owners={str(owner):sorted(owners[owner]) for owner in controllers},
                                declared_health_paths=paths,body_samples=len(bound.get(p['username'],[]))))
        records.append(dict(match_id=event['match_id'],game_id=event['game_id'],round=event['round'],build=event['build'],players=players))
    (base/'abstention-followup.json').write_text(json.dumps(records,indent=2))
    lines = ['# Consumed reserve abstention follow-up','',
             'The cd28f76 result was permanently saved and committed before this diagnosis. '
             'Candidate and frozen dependencies are unchanged. No fresh evidence is claimed here.', '',
             f"Abstention reasons: `{dict(Counter(r['mode'] for r in result['events'] if not r['candidate']))}`.", '',
             '| Match/game/round | Kind | Frozen outcome | Public label (plain text) |',
             '| --- | --- | --- | --- |']
    for e in result['events']:
        label = ' '.join(html.unescape(re.sub('<[^>]+>',' ',e['public_label'])).split())
        lines.append(f"| {e['match_id']}/{e['game_id']}/R{e['round']:02d} | {e['kind']} | "
                     f"{e['candidate'] or 'unresolved'} / {e['mode']} | {label} |")
    lines += ['', '## Declared identity abstentions', '',
              '| Match/round/player | UID-owner values | Health slot/class declarations | Body samples |',
              '| --- | --- | --- | --- |']
    for row in records:
        for p in row['players']:
            paths = [(d['owner'],d['component'],d['class_hash']) for d in p['declared_health_paths']]
            lines.append(f"| {row['match_id']}/R{row['round']:02d}/{p['player']} | {p['owners']} | {paths} | {p['body_samples']} |")
    lines += ['', 'Missing or contradictory identity evidence remains unresolved. Never weaken the join '
              'because a public target is known. Further unused event validation needs a separate predeclared '
              'manifest and an unchanged frozen rule.', '']
    (ROOT/'research/output/objective-reserve-followup.md').write_text('\n'.join(lines),encoding='utf-8')
    print('identity abstention rounds',len(records))
    for r in records:
        print(r['match_id'],r['round'],[(p['player'],p['owners'],p['body_samples']) for p in r['players'] if not p['body_samples']])


if __name__=='__main__':
    main()
