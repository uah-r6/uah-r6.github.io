"""Inspect explicit numeric UID -> live component -> timer field ownership.

This is an evidence ledger, NOT an actor resolver. All material is consumed.
The literal timer is decoded inside its 0x23/0x22 property record, not joined
by byte proximity. Ownership may still differ from verified physical actor.
Mandatory disputed controls remain actor-unresolved. No frozen rule changes.
"""
from collections import Counter
import json

from objective_actor_liveness import feedback, interaction_span
from objective_player_component_fields import observe, bindings_at, controls
from objective_transition_probe import ROOT


def ledger(row, rec, previous_state=0):
    raw,owners,slots,fields = observe(rec)
    feed = feedback(rec)
    span = interaction_span(feed['timers'],row['center'],previous_state)
    if not span:
        return dict(status='missing_interaction',samples=[],packet_owners=[])
    direct = {f['offset']-1:f for f in fields if f['hash']=='a9c858d9' and f['inherited']}
    samples = []
    for timer in feed['timers']:
        if not span['first_offset'] <= timer['offset'] <= span['last_offset']:
            continue
        prop = direct.get(timer['offset'])
        if prop and prop['value'] != timer['value']:
            raise ValueError('Direct record timer and existing observer disagree')
        binding = bindings_at(owners,slots,prop['offset']).get(prop['entity']) if prop else None
        samples.append(dict(timer=timer, record=prop, binding=binding))
    names = sorted({s['binding']['player'] for s in samples if s['binding']})
    entities = sorted({s['record']['entity'] for s in samples if s['record']})
    complete = all(s['record'] and s['binding'] for s in samples)
    associated = [f for f in fields if f['entity'] in entities and f['hash'] in ('e58c06e9','e9a37feb')
                  and span['first_offset']-1 <= f['offset'] <= row['center']]
    # State/progress at timer START may precede it in the same record. Find it
    # using record_start, never a fixed byte distance or nearest entity.
    starts = {s['record']['record_start'] for s in samples[:1] if s['record']}
    associated += [f for f in fields if f['record_start'] in starts and f['hash'] in ('e58c06e9','e9a37feb')
                   and f['offset'] < span['first_offset']]
    associated.sort(key=lambda f:f['offset'])
    return dict(status='complete_unique_declared_timer_owner' if complete and len(names)==1 and len(entities)==1 else 'ambiguous_or_missing_timer_owner',
                span=span, samples=samples, packet_owners=names, components=entities, related_state_fields=associated,
                actor=None, actor_reason='research_ownership_semantics_not_promoted')


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--all-consumed', action='store_true')
    args = parser.parse_args()
    structures = []
    for name in ('development','extension'):
        structures += json.loads((ROOT / f'data/research/diagnostics/objective-score-structure-{name}.json').read_text(encoding='utf-8'))
    records = []
    for row in structures if args.all_consumed else controls():
        folder = next((ROOT / 'data/research/extracted').rglob(row['folder']))
        rec = next(folder.glob(f"*-R{row['round']:02d}.rec"))
        previous = max((r['center'] for r in structures if r['folder']==row['folder'] and r['round']==row['round'] and r['center']<row['center']),default=0)
        observed = ledger(row,rec,previous)
        records.append({k:row[k] for k in ('match_id','game_id','round','kind','build')} | observed)
        print(row['match_id'],row['round'],row['kind'],observed['status'],observed['packet_owners'],len(observed['samples']),flush=True)
    suffix = '-all-consumed' if args.all_consumed else ''
    dest = ROOT / f'data/research/diagnostics/player-component-fields/declared-timer{suffix or "-controls"}.json'
    dest.write_text(json.dumps(records,indent=2),encoding='utf-8')
    lines = ['# Explicit declared timer component owners — research only', '',
             'Each ASCII a9c858d9 timer field is framed inside a 0x23 entity record with 0x22 continuation. '
             'A temporal direct slot declaration links that entity to a unique typed numeric UID owner. '
             'No nearby-ID, score, drone or packet-window join. All timer values exactly match the existing observer. '
             '**No actor is credited**: physical interaction semantics require independent validation; '
             'both mandatory disputed controls stay unresolved. All cases consumed.', '',
             f"Statuses: `{dict(Counter(r['status'] for r in records))}`.", '',
             '| Match/game/round/kind | Build | Status | Packet owner observation | Bound timer samples | Classes / slots |',
             '| --- | --- | --- | --- | --- | --- |']
    for r in records:
        routes = sorted({(s['binding']['slot'],s['binding']['class_hash']) for s in r['samples'] if s['binding']})
        lines.append(f"| {r['match_id']}/{r['game_id']}/R{r['round']:02d}/{r['kind']} | {r['build']} | {r['status']} | {r['packet_owners']} | "
                     f"{sum(bool(s['binding']) for s in r['samples'])}/{len(r['samples'])} | {routes} |")
    lines += ['', 'The field is demonstrably player-linked, but that alone is not sufficient actor proof. '
              'The Raid/Aiden and J9O/njr controls must not be silently reclassified. '
              'Separate official broadcast review supports kyno in ChaletR04; the new FortressR07 video '
              'also presents a target contradiction, recorded separately while its resolver remains unresolved. '
              'NEXT compare all consumed interaction records, interrupted timers and non-objective controls, '
              'then independently validate component class/state and ownership across builds. No production or Rating changes.', '']
    (ROOT / f'research/output/objective-declared-timer-owner{suffix}.md').write_text('\n'.join(lines),encoding='utf-8')


if __name__ == '__main__':
    main()
