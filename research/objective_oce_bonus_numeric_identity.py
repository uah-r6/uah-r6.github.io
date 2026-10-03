"""Additional consumed numeric-field ownership controls on an unknown class."""
from collections import Counter
import json
from pathlib import Path

from objective_bonus_body_oce_cohort import DATA
from objective_bonus_body_oce_review import verify_prelabel
from objective_player_component_fields import observe, bindings_at
from uah_guarded_actor_readonly import snapshot
from v3_final_reserve import ROOT, sha, source_sha


def main():
    verify_prelabel()
    protected = snapshot()
    checkpoint = json.loads((ROOT/'research/objective-oce-consumed-lifecycle-checkpoint.json').read_text(encoding='utf-8'))
    source = DATA/'consumed-body-class-lifecycle.json'
    if sha(source) != checkpoint['result_hashes'][source.relative_to(ROOT).as_posix()]:
        raise ValueError('Preserved consumed lifecycle inventory changed')
    inventory = json.loads(source.read_text(encoding='utf-8'))
    cache, records, counts = {}, [], Counter()
    for p in inventory['state_properties']:
        if p['raw_value'] != 1:
            continue
        key = p['official_match_id'], p['round']
        if key not in cache:
            prediction = json.loads((DATA/str(key[0])/'replay-predictions.json').read_text(encoding='utf-8'))
            row = next(r for r in prediction['rounds'] if r['round'] == key[1])
            rec = ROOT/row['replay_path']
            if sha(rec) != row['replay_sha256']:
                raise ValueError('Sealed physical replay changed')
            state, owners, slots, _ = observe(rec)
            cache[key] = state, owners, slots, row
        state, owners, slots, row = cache[key]
        expected = tuple(p['route'][k] for k in ('owner', 'player', 'slot', 'class_hash'))
        field_routes = []
        for tag, field in p['numerical']['exact_fields'].items():
            bound = bindings_at(owners, slots, field['offset']).get(field['entity'])
            matches = bound is not None and tuple(bound[k] for k in ('owner', 'player', 'slot', 'class_hash')) == expected
            field_routes.append(dict(tag=tag, offset=field['offset'], width=field['size'], route=bound,
                                     exact_observation_matches_state_owner=matches,
                                     observed_no_later_than_state=field['offset'] <= p['offset']))
        identity_consistent = (len(field_routes) == 4 and all(
            f['exact_observation_matches_state_owner'] and f['observed_no_later_than_state'] and f['width'] == 4
            for f in field_routes))
        counts.update(state1_properties=1, numerical_pattern_consistent=int(p['numerical']['consistent_positive_bonus']),
                      all_four_numeric_routes_consistent=int(identity_consistent),
                      properties_with_unknown_death_offsets=int(p['unknown_death_offset']),
                      properties_after_known_death=int(p['known_death_before_property']),
                      state1_in_verified_plant_round=int(row['verified_plant']))
        records.append(dict(official_match_id=key[0], round=key[1], player=p['player'], state_offset=p['offset'],
                            state_record=p['record_start'], component=p['component'], numeric=p['numerical'],
                            numeric_field_routes=field_routes, all_four_routes_consistent=identity_consistent,
                            active_body_verified=False, actor_credit_proposed=False))
    record = dict(tier='consumed_unknown_class_numeric_identity_control_not_bonus_eligibility',
                  counts=dict(counts), records=records, lifecycle_sha256=sha(source),
                  source_sha256=source_sha(Path(__file__)), protected_hashes=protected,
                  candidate_changed=False, actor_credit_proposed=False)
    path = DATA/'consumed-unknown-class-bonus-numeric-identity.json'
    if path.exists():
        if json.loads(path.read_text(encoding='utf-8')) != record:
            raise ValueError('Preserved numeric identity diagnostic differs')
    else:
        path.write_text(json.dumps(record, indent=2)+'\n', encoding='utf-8')
    lines = ['# Consumed older-class numerical bonus identity control', '', f'Counts: `{dict(counts)}`.', '',
             'For every raw1 property in the fixed complete build9734089 cohort, the four numerical fields '
             'are checked at their own observation offsets against the unique declared UID/body-slot/class '
             'route seen at the state observation. Width4 and observation no later than state are required. '
             'Component equality alone does not establish historical ownership. The raw health, baseline, '
             'ceiling and fraction relationship remains a numerical correlation on an unknown class, '
             'not an approved body state or independent visible boost.', '',
             'Some raw1 properties may occur elsewhere in rounds that also contain a plant. '
             'The full31plant-interval inventory already showed no raw1 on the completing owner during the '
             'interaction. These observations add zero bonus-health actor recoveries and cannot change '
             'the prospective insufficient result. Unknown death timing remains explicitly unknown.', '',
             'No candidate, class allowlist, actor, Rating, action-start/operator/kill behavior, SQLite/archive/public '
             'data or historical result changes. No new event selection, push or publish.', '']
    (ROOT/'research/output/objective-bonus-body-oce-numeric-identity.md').write_text('\n'.join(lines), encoding='utf-8')
    verify_prelabel()
    if snapshot() != protected:
        raise ValueError('Protected live files changed')
    print('Consumed numerical identity control', dict(counts))


if __name__ == '__main__':
    main()
