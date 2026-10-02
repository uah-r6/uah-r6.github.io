"""Independent manual HUD labels versus consumed replay liveness; no attribution."""
import json
from pathlib import Path

from objective_actor_liveness import feedback, player_ledger

ROOT = Path(__file__).resolve().parents[1]

# Manually inspected official VOD pTsWYqy7H2k frames, cached by prior session.
# Clock phase is explicit: post-plant 0:44 must not be confused with action 0:44.
SAMPLES = [
    (6900, 'prep', None, ['Fultz', 'J9O', 'kyno', 'njr', 'Nuers', 'Rexen', 'Spoit', 'Canadian', 'Ambi', 'Surf']),
    (7020, 'action', 84, ['J9O', 'njr', 'Rexen', 'Surf']),
    (7060, 'action', 44, ['J9O', 'njr', 'Surf']),
    (7092, 'action', 12, ['J9O', 'njr', 'Surf']),
]


def main():
    base = ROOT / 'data/research/diagnostics'
    folder = next((ROOT / 'data/research/extracted').rglob('Match-2026-05-17_18-07-03-14704'))
    parsed = feedback(next(folder.glob('*-R02.rec')))
    event = next(e for e in json.loads((base / 'objective-player-ledger-v2.json').read_text())['consumed_events']
                 if e['match_id'] == 3563 and e['game_id'] == 6675 and e['round'] == 2 and e['kind'] == 'plant')
    before_plant = [e for e in parsed['events'] if 0 < e['offset'] < event['center']]
    results = []
    for second, phase, clock, alive in SAMPLES:
        occurred = [] if phase == 'prep' else [e for e in before_plant if e['feedback']['timeInSeconds'] > clock]
        boundary = max((e['offset'] for e in occurred), default=0)
        diagnostic = [p for side in ('Attack', 'Defense') for p in
                      player_ledger(parsed['header'], parsed['events'], [], {'entity_names': {}}, boundary, side)]
        for p in diagnostic:
            truth = p['player'] in alive
            results.append({'vod_seconds': second, 'phase': phase, 'clock': clock,
                            'query_offset': boundary, 'player': p['player'],
                            'hud_alive': truth, 'diagnostic_alive': p['alive_at_completion'],
                            'agrees': p['alive_at_completion'] == truth})
    counts = {'states': len(results), 'hud_alive': sum(r['hud_alive'] for r in results),
              'hud_dead': sum(not r['hud_alive'] for r in results),
              'diagnostic_unknown': sum(r['diagnostic_alive'] is None for r in results),
              'disagreements': sum(not r['agrees'] for r in results)}
    (base / 'objective-liveness-vod-audit.json').write_text(json.dumps({'counts': counts, 'states': results}, indent=2))
    lines = ['# Independent HUD liveness check', '',
             'Source: [official DarkZero–Shopify grand-final VOD](https://www.youtube.com/watch?v=pTsWYqy7H2k&t=7020s), '
             'Bank R02, match 3563/game6675. Frames were manually inspected before comparison. '
             'This is one consumed round, not broad build validation.', '',
             f'Results: `{json.dumps(counts)}`.', '',
             '| VOD seconds | Phase / clock | HUD alive | HUD dead | Diagnostic disagreements |',
             '| --- | --- | ---: | ---: | ---: |']
    for second, phase, clock, alive in SAMPLES:
        subset = [r for r in results if r['vod_seconds'] == second]
        lines.append(f'| {second} | {phase} / {clock} | {len(alive)} | {10-len(alive)} | {sum(not r["agrees"] for r in subset)} |')
    lines += ['', 'The query offset is the last kill packet strictly before the HUD clock, restricted to the pre-plant '
              'phase. This checks victim identity/order against an independent visible roster; it does not establish '
              'the exact byte-to-video timestamp relationship. Surf dies at replay clock 0:44 **after planting**; '
              'including that packet at action-phase 0:44 would incorrectly mark him dead. Packet order and phase '
              'prevent this clock-reset mistake.', '',
              '## Unvalidated states and failure modes', '',
              '- A positive value is absence of an earlier decoded death. Missing kills or disconnected players '
              'can therefore appear alive. It is not proof of interaction eligibility.',
              '- The probe currently retains Kill/Death only, omitting PlayerLeave. No disconnected-player eligibility claim is justified.',
              '- The parser Death branch has no killOffset assignment; those events have zero offset and yield unknown, never dead.',
              '- DBNO and revive are not represented by this diagnostic. Health entity nearest-ID mapping is unverified '
              'for actor work and must not be used to fill the gap.',
              '- No independent rehost/missing-roster, post-round or DBNO ground truth was acquired in this audit. '
              'The broadcast cuts away before the disable; no new actor label follows from it.',
              '- Existing unit tests verify before/after-death and unknown-offset mechanics, not replay completeness.', '',
              'Decision: keep liveness as provisional supporting evidence. This small HUD check does not justify a universal hard actor filter.', '']
    (ROOT / 'research/output/objective-liveness-vod-audit.md').write_text('\n'.join(lines), encoding='utf-8')
    print(counts)


if __name__ == '__main__':
    main()
