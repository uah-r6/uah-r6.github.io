"""Independent consumed HUD samples against direct declared health state."""
from collections import Counter
import json

from objective_liveness_vod_audit import SAMPLES
from objective_state_components import probe
from objective_transition_probe import ROOT


def main():
    base = ROOT / 'data/research/diagnostics'
    structures = json.loads((base / 'objective-score-structure-extension.json').read_text())
    row = next(r for r in structures if r['match_id'] == 3563 and r['game_id'] == 6675 and r['round'] == 2 and r['kind'] == 'plant')
    folder = next((ROOT / 'data/research/extracted').rglob(row['folder']))
    raw = probe(next(folder.glob('*-R02.rec')))
    links = next(r for r in json.loads((base / 'objective-state-components.json').read_text())
                 if r['folder'] == row['folder'] and r['round'] == 2)['candidate_links']
    records = []
    for second, phase, clock, alive in SAMPLES:
        if phase == 'prep':
            continue  # No independently established byte alignment for prep.
        ticks = [t for t in row['clock_ticks'] if row['header']['actionPhaseStartOffset'] < t['offset'] < row['center']
                 and t['value'] == clock]
        # First occurrence in action phase; repeated 44 after plant is different.
        query = ticks[0]['offset']
        for link in links:
            states = [p for p in raw['properties'] if p['entity'] == link['path'][-1]
                      and p['hash'] == 'e788f6a5' and p['offset'] <= query]
            state = states[-1]['value'] if states else None
            records.append(dict(vod_seconds=second, player=link['player'], query_offset=query,
                                hud_alive=link['player'] in alive, raw_component_state=state))
    # Independent visual counterexamples to treating every nonzero state as dead
    # or downed. These values persist across the sampled clock epoch, avoiding
    # ambiguous positioning of a change within one displayed second.
    all_links = json.loads((base / 'objective-state-components-all-consumed.json').read_text())
    for number,second,clock,player,evidence in (
        (1,650,70,'Ambi','Active HUD card, weapon ammunition, no downed icon'),
        (1,700,20,'Canadian','Selected first-person view aiming/reloading; active HUD card'),
        (3,1180,85,'Nuers','Active HUD card with ammunition; no downed icon'),
    ):
        sample = next(r for r in structures if r['match_id']==3563 and r['game_id']==6673 and r['round']==number)
        physical = next((ROOT / 'data/research/extracted').rglob(sample['folder']))
        observed = probe(next(physical.glob(f'*-R{number:02d}.rec')))
        direct = next(r for r in all_links if r['folder']==sample['folder'] and r['round']==number)
        path = next(p for p in direct['candidate_links'] if p['player']==player)
        query = next(t['offset'] for t in sample['clock_ticks'] if t['value']==clock
                     and sample['header']['actionPhaseStartOffset']<t['offset']<sample['center'])
        states = [p for p in observed['properties'] if p['entity']==path['path'][-1]
                  and p['hash']=='e788f6a5' and p['offset']<=query]
        state = states[-1]['value'] if states else None
        records.append(dict(vod_seconds=second,player=player,query_offset=query,hud_alive=True,
                            raw_component_state=state,visual_evidence=evidence,game_id=6673,round=number))
    counts = {str(k): v for k,v in Counter((r['hud_alive'], r['raw_component_state']) for r in records).items()}
    (base / 'objective-state-hud-audit.json').write_text(json.dumps(dict(counts=counts, states=records), indent=2))
    lines = ['# Independent HUD versus declared component state', '',
             'Same manually labeled official VOD samples as `objective_liveness_vod_audit.py`; '
             'three Bank action-phase snapshots, 30 player states, plus three independently inspected '
             'Nighthaven Labs player snapshots. Preparation sample excluded because '
             'its byte position was not independently aligned. No fresh actor reserve used.', '',
             f'Counts `(HUD alive, raw state)`: `{counts}`.', '',
             'Source: [official grand-final VOD](https://www.youtube.com/watch?v=pTsWYqy7H2k). '
             'Additional samples: Nighthaven R01, t650/action1:10 Ambi active; t700/action0:20 '
             'Canadian selected and aiming/reloading; R03 t1180/action1:25 Nuers active. '
             'All three have raw state2. Frame cache filenames use video seconds and format298.', '',
             'These samples support state0 and state2 for living active players, and state4 for eliminated '
             'players. State2 must not be a hard DBNO/death exclusion. Two further visual samples show '
             'downed HUD crosses: R01 njr t644/1:16 and kyno t713/7.79. Corresponding raw paths have '
             'state3 between nearby clock ticks (njr77->76; kyno8->7), then state4. Their transitions '
             'occur within a displayed second, so no exact byte/frame alignment or universal state3 '
             'eligibility rule is claimed. Revive and disconnect semantics remain unvalidated. '
             'Positive HP alone was already shown insufficient by seven confirmed death cases.', '']
    (ROOT / 'research/output/objective-state-hud-audit.md').write_text('\n'.join(lines), encoding='utf-8')
    print(counts)


if __name__ == '__main__':
    main()
