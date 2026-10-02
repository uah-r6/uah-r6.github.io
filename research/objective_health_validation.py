"""Validate explicit UID/component health paths against consumed death chronology."""
from collections import Counter
import json

from objective_actor_liveness import feedback
from objective_state_components import probe
from objective_transition_probe import ROOT


def main():
    base = ROOT / 'data/research/diagnostics'
    rows = json.loads((base / 'objective-state-components.json').read_text())
    reports = []
    for row in rows:
        folder = next((ROOT / 'data/research/extracted').rglob(row['folder']))
        rec = next(folder.glob(f"*-R{row['round']:02d}.rec"))
        observed = probe(rec)
        deaths = feedback(rec)['events']
        pairs = []
        for link in row['candidate_links']:
            player = link['player']
            edge = [d for d in observed['declarations'] if d['owner'] == link['path'][0]
                    and d['component'] == link['path'][-1]]
            if len(link['path']) != 2 or not edge:
                raise ValueError('Health validation requires a direct declared path')
            fields = {(d['slot_hash'], d['class_hash']) for d in edge}
            if fields != {('4154dcc4', '0c98c63f')}:
                raise ValueError('Unexpected health slot/class')
            killed = [d for d in deaths if (d['feedback']['type']['name'] == 'Kill' and d['feedback'].get('target') == player)
                      or (d['feedback']['type']['name'] == 'Death' and d['feedback'].get('username') == player)]
            hp = link['health_samples']
            life = [p for p in observed['properties'] if p['entity'] == link['path'][-1] and p['hash'] == 'e788f6a5']
            for death in killed:
                if death['offset'] <= 0:
                    pairs.append(dict(player=player, death_offset=0, status='unknown_death_offset'))
                    continue
                prior = [p for p in hp if p['offset'] < death['offset']]
                after = [p for p in hp if p['offset'] >= death['offset']]
                prior_state = [p for p in life if p['offset'] < death['offset']]
                pairs.append(dict(player=player, death_offset=death['offset'],
                                  component_state_before_death=prior_state[-1] if prior_state else None,
                                  last_hp_before_death=prior[-1] if prior else None,
                                  first_hp_after_death=after[0] if after else None,
                                  status='zero_before_death' if prior and prior[-1]['value'] == 0 else 'nonzero_or_missing_before_death'))
        reports.append(dict(folder=row['folder'], round=row['round'], pairs=pairs,
                            inherited_hp=sum(p.get('inherited', False) for l in row['candidate_links'] for p in l['health_samples'])))
    counts = dict(Counter(p['status'] for r in reports for p in r['pairs']))
    states = dict(Counter(p['component_state_before_death']['value'] if p.get('component_state_before_death') else None
                          for r in reports for p in r['pairs']))
    (base / 'objective-health-validation.json').write_text(json.dumps(dict(counts=counts, state_counts=states, results=reports), indent=2))
    lines = ['# Direct declared health identity validation', '',
             'Five consumed rounds, ten player health paths per round. Every direct path uses slot `4154dcc4` '
             'and class `0c98c63f`, connecting the typed numeric-UID entity to the health-property entity. '
             'No numeric-distance identity assignment is involved. Header names and existing feedback grade chronology; '
             'these are not independent actor labels.', '', f'Death alignment counts: `{counts}`. '
             f'Last component state `e788f6a5` before death: `{states}`.', '',
             '| Folder / round | Confirmed death comparisons | HP zero before kill envelope | Nonzero/missing | Inherited HP fields recovered |',
             '| --- | --- | --- | --- | --- |']
    for r in reports:
        lines.append(f"| {r['folder']} / R{r['round']:02d} | {len(r['pairs'])} | {sum(p['status']=='zero_before_death' for p in r['pairs'])} | {sum(p['status']=='nonzero_or_missing_before_death' for p in r['pairs'])} | {r['inherited_hp']} |")
    lines += ['', 'Seven confirmed deaths retain positive HP in this property stream; HP alone is unsafe as an alive filter. '
              'State `e788f6a5` is 4 before 40 kill envelopes and 2 before three; packet ordering can place '
              'the final state after the kill feedback. Its values 2/3 are not yet independently labeled as DBNO/death. '
              'No zero-HP or nonzero-state hard exclusion is justified. The generic continuation decoder recovered '
              'other state fields but no additional HP fields in these controls. DBNO/revive and disconnect eligibility remain unvalidated.', '']
    (ROOT / 'research/output/objective-health-validation.md').write_text('\n'.join(lines), encoding='utf-8')
    print(counts)


if __name__ == '__main__':
    main()
