"""Locate consumed raw1 observations relative to completing-owner intervals."""
from collections import Counter
import json
from pathlib import Path

from objective_bonus_body_oce_cohort import DATA
from objective_bonus_body_oce_review import verify_prelabel
from v3_final_reserve import ROOT, sha, source_sha


def main():
    verify_prelabel()
    path = DATA/'consumed-body-class-lifecycle.json'
    source = json.loads(path.read_text(encoding='utf-8'))
    plants = {(r['official_match_id'], r['round']): r for r in source['actor_intervals']}
    counts, rows = Counter(), []
    for p in source['state_properties']:
        if p['raw_value'] != 1:
            continue
        plant = plants.get((p['official_match_id'], p['round']))
        if plant is None:
            relation = 'no_plant_round'
        else:
            ownership = 'same_owner' if p['player'] == plant['timer_owner'] else 'other_player'
            timing = 'before' if p['offset'] < plant['start'] else 'during' if p['offset'] <= plant['end'] else 'after'
            relation = ownership+'_'+timing
        counts[relation] += 1
        rows.append(dict(official_match_id=p['official_match_id'], round=p['round'], player=p['player'],
                         offset=p['offset'], relation=relation,
                         completing_interval=plant['interval']['states'] if plant else None))
    record = dict(tier='consumed_temporal_raw1_inventory_not_actor_recovery', counts=dict(counts), records=rows,
                  lifecycle_sha256=sha(path), source_sha256=source_sha(Path(__file__)),
                  prospective_bonus_recoveries_added=0, candidate_changed=False)
    output = DATA/'consumed-raw1-relative-to-plants.json'
    if output.exists():
        if json.loads(output.read_text(encoding='utf-8')) != record:
            raise ValueError('Preserved timing inventory differs')
    else:
        output.write_text(json.dumps(record, indent=2)+'\n', encoding='utf-8')
    lines = ['# Consumed OCE raw1 observation timing', '', f'Counts: `{dict(counts)}`.', '',
             'All47observed raw1 properties on the older class are included, not just player-rounds '
             'with objectives. Thirty-six occur in rounds without plants. Eleven occur in plant rounds, '
             'but seven belong to another player before the interaction, two belong to another player '
             'afterward, and two belong to the completing owner before the interaction. No raw1 property '
             'occurs on the completing owner during the interaction. The31full interval inventories retain '
             'the last preceding property too: all interval values remain0/2.', '',
             'A boost observation elsewhere in an objective round is not a bonus-health plant actor case. '
             'Neither an earlier same-owner state1 nor a later teammate state1 can replace the authoritative '
             'interaction interval. These are property counts, not47unique rounds/boost episodes or independent '
             'visual confirmations. No effects, operators or boost durations are inferred.', '',
             'The pooled OCE prospective result stays permanently insufficient with zero bonus recoveries. '
             'No new event, candidate, actor, Rating, runtime, SQL/archive/public changes, push or publish.', '']
    (ROOT/'research/output/objective-bonus-body-oce-raw1-timing.md').write_text('\n'.join(lines), encoding='utf-8')
    verify_prelabel()
    print('Consumed raw1 timing', dict(counts))


if __name__ == '__main__':
    main()
