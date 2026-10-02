"""Packet-ordered negative timer endings; no completion or actor changes."""
import json

from objective_actor_liveness import feedback
from objective_state_components import probe
from objective_transition_probe import ROOT, replay_file


def main():
    base = ROOT/'data/research/diagnostics'
    negatives = json.loads((base/'player-component-fields/negative-three-controls.json').read_text(encoding='utf-8'))['results']
    encoding = json.loads((base/'objective-encoding-validation/summary.json').read_text(encoding='utf-8'))['rounds']
    records = []
    for row in negatives:
        rec,_ = replay_file(row['match_id'],row['round'])
        raw,feed = probe(rec),feedback(rec)
        roles = {p['username']:raw['header']['teams'][p['teamIndex']]['role'] for p in raw['header']['players']}
        for episode in row['episodes']:
            if episode['last_timer'] is None or episode['last_timer'] > .1:
                continue
            player = episode['binding']['player']
            opponents = {p for p,side in roles.items() if side != roles[player]}
            missing = set(opponents)
            eliminations = []
            for event in sorted(feed['events'],key=lambda e:e['offset']):
                item = event['feedback']
                victim = item.get('target') if item['type']['name']=='Kill' else item.get('username') if item['type']['name']=='Death' else None
                if victim in missing and event['offset'] > 0:
                    missing.remove(victim)
                    eliminations.append(event)
            target = next(r for r in encoding if (r['match_id'],r['round'])==(row['match_id'],row['round']))
            records.append(dict(match_id=row['match_id'],round=row['round'],owner_observation=player,
                                first_timer=episode['first_timer'],last_timer=episode['last_timer'],
                                last_timer_offset=episode['samples'][-1]['offset'],terminal_offset=episode['end_offset'],
                                terminal_source=episode['end_source'],terminal_reason=episode['end_reason'],
                                opponent_names=sorted(opponents),opponent_deaths=eliminations,
                                all_opponents_dead_offset=eliminations[-1]['offset'] if not missing else None,
                                unmapped_or_living_opponents=sorted(missing),decoded_global_objective_flags=target['events'],
                                cached_parser_win_condition=[t.get('winCondition') for t in raw['header']['teams'] if t.get('won')],
                                actor=None))
    (base/'player-component-fields/negative-ending-audit.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
    lines = ['# Why terminal timer state is insufficient', '',
             'Three predeclared consumed near-zero controls contain no decoded global plant flag and no public objective. '
             'A temporal direct player component nevertheless counts down almost to zero. This is a rejected completion-only '
             'hypothesis, not an actor rule. Exact opponent Kill/Death offsets are independently recorded below; '
             'no universal kill points, byte window or score inference.', '',
             '| Match / round | Owner observation | Last timer / property offset | Terminal record or declaration | All five opponents killed offset | Global objective flags | Cached parser win condition |',
             '| --- | --- | --- | --- | --- | --- | --- |']
    for r in records:
        lines.append(f"| {r['match_id']}/R{r['round']:02d} | {r['owner_observation']} | {r['last_timer']} / {r['last_timer_offset']} | "
                     f"{r['terminal_offset']} / {r['terminal_reason']} | {r['all_opponents_dead_offset']} | "
                     f"{len(r['decoded_global_objective_flags'])} | {r['cached_parser_win_condition']} |")
    lines += ['', '4138/R09 and4141/R14 finish all five opponent kills BEFORE the last timer property. '
              'The timer then terminates with state2 even though no global plant is recorded. '
              '4141/R06 loses its timer component through an explicit slot declaration before the last opposing kill. '
              'No unknown state is converted to a death; exact header names must match recorded victims.', '',
              'The legacy parser\'s cached win-condition text is a derived output, not independent ground truth. '
              'These controls demonstrate why it cannot establish a plant by itself. Production code is unchanged. '
              'A future component-owner resolver must require independently validated objective occurrence and '
              'an unambiguous interaction/phase association. The original A and mandatory disputed actor abstentions remain intact.', '']
    (ROOT/'research/output/objective-timer-cancellation-audit.md').write_text('\n'.join(lines),encoding='utf-8')
    print([(r['match_id'],r['round'],r['last_timer_offset'],r['all_opponents_dead_offset']) for r in records])


if __name__ == '__main__':
    main()
