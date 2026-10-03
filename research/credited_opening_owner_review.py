"""Independent consumed HUD case; never assign generic victims from counters."""
import json
from pathlib import Path

from objective_player_component_fields import observe, bindings_at
from v3_body_state1_health_audit import numerical_snapshot
from uah_guarded_actor_readonly import snapshot
from v3_final_reserve import ROOT, sha, source_sha


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def main():
    protected = snapshot()
    directory = ROOT / 'data/research/video/sal-opening-order-20261003'
    metadata = directory / 'Day1.info.json'
    meta = read(metadata)
    if (meta['id'], meta['upload_date'], meta['channel_id']) != (
            'Ao6SRRhCmbg', '20260905', 'UCWKHac5bjhsUtSnMDFCT-7A'):
        raise ValueError('Official broadcast provenance differs')
    # Manual observations were made before replay counter/body comparison.
    observations = {
        14872: 'R02, score0-1, clock0:35,5v5; Neskin0/1/1, pino0/1/1; resetz alive0/1/0.',
        14874: 'R02, clock0:33,5v5; resetz taking damage; no elimination feed; Neskin0/1/1, pino0/1/1.',
        14875: 'R02, clock0:32,5v5; resetz POV and observer card both show downed cross; Neskin0/1/1, pino0/1/1.',
        14876: 'R02, clock0:31,5v4; only feed pino.L5 -> resetz.LOUD; Neskin1/1/1, pino0/1/2; resetz dead0/2/0.',
        14880: 'R02, clock0:27,5v4; same sole feed and counters; first final death resetz; no second elimination yet.',
    }
    frames = [dict(seconds=s, path=(directory / f'Day1-{s}-299.jpg').relative_to(ROOT).as_posix(),
                   sha256=sha(directory / f'Day1-{s}-299.jpg'), observation=o)
              for s, o in observations.items()]
    audit = ROOT / 'data/research/diagnostics/v3-sal-kill-credit/8583.json'
    round_ = read(audit)['rounds'][1]
    sources = [p for p in (ROOT / 'data/research/extracted/v3-corrected-final-sal-8583').rglob(round_['filename'])
               if p.parent.name == round_['folder']]
    if len(sources) != 1 or sha(sources[0]) != round_['replay_sha256']:
        raise ValueError('Consumed physical replay identity differs')
    state, owners, slots, fields = observe(sources[0])
    body = []
    for field in fields:
        route = bindings_at(owners, slots, field['offset']).get(field['entity'])
        if (route and route['player'] == 'resetz.LOUD' and route['slot'] == '4154dcc4'
                and field['hash'] == 'e788f6a5' and field['size'] == 4):
            values = numerical_snapshot([f for f in fields if f['entity'] == field['entity']], field)
            body.append(dict(offset=field['offset'], raw_state=field['value'],
                             health=values['health'], route=route))
    first = min(round_['feed'], key=lambda e: e['offset'])
    if (first['feedback']['username'], first['feedback']['target']) != ('pino.L5', 'resetz.LOUD'):
        raise ValueError('Independent first finisher/victim differs')
    counter_rows = [row for row in round_['counter_rows'] if row['player'] in ('pino.L5', 'Neskin.L5')]
    order_path = ROOT / 'data/research/credited-kills-v1/opening-order.json'
    original = read(order_path)
    # A separate, descriptive case-supported ledger. Preserve sealed results.
    # This is not a fitted generic rule: only this explicitly filmed case changes.
    comparison = []
    for row in original['rows']:
        proposed = list(row['packet_first'])
        if row['official_match_id'] == 8583 and row['player'] == 'pino.L5':
            proposed[0] -= 1
        if row['official_match_id'] == 8583 and row['player'] == 'Neskin.L5':
            proposed[0] += 1
        comparison.append(dict(row, case_supported_opening=proposed))
    record = dict(status='consumed_independent_first_death_credit_case_not_generic_runtime_rule',
        official_match_id=8583, map='Clubhouse', round=2,
        video_url='https://www.youtube.com/watch?v=Ao6SRRhCmbg&t=14872s',
        channel_id=meta['channel_id'], upload_date=meta['upload_date'],
        metadata_sha256=sha(metadata), frames=frames, replay_sha256=sha(sources[0]),
        first_finisher_event=first, victim_body_states=body, related_counter_observations=counter_rows,
        credited_owner='Neskin.L5', finisher='pino.L5', victim='resetz.LOUD',
        source_hashes={audit.relative_to(ROOT).as_posix(): sha(audit),
                       order_path.relative_to(ROOT).as_posix(): sha(order_path)},
        helper_sha256=source_sha(Path(__file__)), protected_hashes=protected,
        comparison_rows=comparison,
        counts=dict(player_maps=len(comparison), case_supported_official_matches=sum(
            r['case_supported_opening'] == r['official'] for r in comparison),
            case_supported_public_matches=sum(r['case_supported_opening'] == r['public'] for r in comparison)),
        limits='Independent visible first-death/counter case supports credited owner versus finisher. Sparse frames do not show the damaging shot or identify a generic downer packet, nor establish DBNO-time versus death-time opening policy for competing early downs. No near-counter mapping, live migration, or final study regrading.')
    destination = ROOT / 'data/research/credited-kills-v1/opening-owner-8583.json'
    if destination.exists() and read(destination) != record:
        raise ValueError('Never overwrite changed consumed HUD review')
    destination.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    lines = ['# Independent opening-credit case: Neskin versus pino', '',
        '[Official SAL Stage2 Day1 broadcast](https://www.youtube.com/watch?v=Ao6SRRhCmbg&t=14872s). '
        'This separate consumed review preserves the earlier sealed opening-order result.', '',
        '| Video second | Independently inspected HUD |', '| ---: | --- |']
    lines.extend(f'| {s} | {o} |' for s, o in observations.items())
    lines += ['', 'The first final death is resetz. The feed identifies pino as the finisher, while the '
        'visible scoreboard increments Neskin kills0→1 and pino assists1→2 without a pino kill. '
        'This independently supports assigning this particular opening credit to Neskin; it was not inferred '
        'from the nearest replay counter or the expected map total.', '',
        'Direct temporal UID/body evidence agrees: resetz raw3 at86443440, eliminated raw4 at86448101; '
        'Neskin kills0→1 at86448083, pino finish86448473, pino assist1→2 at86448897. '
        'Byte order is serialization, not server causality or subsecond timing. The damaging shot/downer '
        'identity was not independently observed. No generic victim/downer packet was recovered.', '',
        f'Separate descriptive comparison: {record["counts"]}. Two packet-order corrections plus this '
        'independently filmed owner case explain all consumed SAL map opening-count discrepancies. '
        'This is development corroboration, not a new final accuracy score or validated universal rule. '
        'The original193/200 timer-order and198/200 packet-order results remain unchanged.', '',
        'Production opening/trade/pivot/untraded/headshot semantics remain unchanged. Exact official '
        'opening policy when competing DBNOs precede deaths is still unverified. No historical SQLite write, '
        'public regeneration, Rating-input update or application of this one-off reviewed case.', '']
    (ROOT / 'research/output/credited-kill-opening-owner.md').write_text('\n'.join(lines), encoding='utf-8')
    if snapshot() != protected:
        raise ValueError('Protected state changed')
    print(record['counts'])
    print('Independent Neskin credit/pino finisher first-death control preserved; no generic reassignment')


if __name__ == '__main__':
    main()
