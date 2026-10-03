"""Opt-in native feedback-envelope development check on consumed APAC8156.

The original credited-count study and strict unknown-offset refusal remain
sealed. Targets never participate in deriving identity, counters or offsets.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
from uuid import UUID

from credited_kill_evidence import inspect, EXE as ORIGINAL_EXE
from uah_guarded_actor_readonly import snapshot
from v3_final_reserve import ROOT, sha, source_sha

EXE = ROOT / '.local-tools/bin/siege-kill-credit-envelope.exe'
DATA = ROOT / 'data/research/credited-kills-v1/native-envelope'
SOURCE = 'stable_uid_scoreboard_delta_native_feedback_envelope_v1'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def native(rec):
    key = hashlib.sha256(EXE.read_bytes() + bytes.fromhex(sha(rec))).hexdigest()
    cache = DATA / (key + '.json')
    if not cache.exists():
        result = subprocess.run([str(EXE), str(rec)], check=True, capture_output=True, encoding='utf-8')
        observation = json.loads(result.stdout)
        observation.update(replay_sha256=sha(rec), executable_sha256=sha(EXE))
        cache.write_text(json.dumps(observation, indent=2) + '\n', encoding='utf-8')
    return read(cache)


def original_reader(rec):
    key = hashlib.sha256(ORIGINAL_EXE.read_bytes() + bytes.fromhex(sha(rec))).hexdigest()
    cache = DATA / ('original-reader-' + key + '.json')
    if not cache.exists():
        result = subprocess.run([str(ORIGINAL_EXE), str(rec)], check=True, capture_output=True, encoding='utf-8')
        cache.write_text(json.dumps(json.loads(result.stdout), indent=2) + '\n', encoding='utf-8')
    return read(cache)


def main():
    protected = snapshot(); DATA.mkdir(parents=True, exist_ok=True)
    old_path = ROOT / 'data/research/diagnostics/v3-apac-kill-credit/8156.json'
    old = read(old_path)
    rows = []; totals = Counter(); previous = None; deaths = Counter(); recovered = []
    if len(old['rounds']) != 10 or len({r['folder'] for r in old['rounds']}) != 1:
        raise ValueError('This isolated check supports only the recorded single-segment map')
    for ordinal, row in enumerate(old['rounds'], 1):
        if row['logical_round'] != ordinal or row['physical_round'] != ordinal:
            raise ValueError('Consumed physical chronology differs')
        sources = [p for p in (ROOT / 'data/research/extracted/v3-final-apac-n-8156').rglob(row['filename'])
                   if p.parent.name == row['folder']]
        if len(sources) != 1 or sha(sources[0]) != row['replay_sha256']:
            raise ValueError('Consumed replay differs')
        observation = native(sources[0]); credit = observation['credit']
        default = inspect(sources[0])
        actual_default = original_reader(sources[0])
        if observation['header'] != actual_default['header']:
            raise ValueError('Native observer changed player/operator/action/header output')
        if observation['originalFinishes'] != actual_default['credit']['finishes']:
            raise ValueError('Native observer changed default reader raw feedback')
        if actual_default['credit']['complete'] and credit['players'] != actual_default['credit']['players']:
            raise ValueError('Native observer changed already-supported credit counters')
        if credit['source'] != SOURCE or not credit['complete']:
            raise ValueError('Native-envelope counters incomplete')
        if observation['originalFinishes'] != row['feed']:
            raise ValueError('Original finisher/death event mutated')
        current = {}
        for p in credit['players']:
            profile = UUID(p['profileID'])
            if not profile.int or str(profile) in current:
                raise ValueError('Full exact stable profile identity required')
            current[str(profile)] = p
            if p['kills'] != row['players'][p['username']]['delta']:
                raise ValueError('Native counters differ from prior direct counter observations')
            totals[p['username']] += p['kills']
        if len(current) != 10:
            raise ValueError('Full roster unavailable')
        if previous is not None and (previous.keys() != current.keys() or any(
                current[key]['initial'] != previous[key]['terminal'] for key in current)):
            raise ValueError('Native map continuity changed')
        previous = current
        for original, observed in zip(observation['originalFinishes'], credit['finishes'], strict=True):
            if original['feedback'] != observed['feedback']:
                raise ValueError('Raw victim/finisher data changed')
            f = original['feedback']; kind = f['type']['name']
            victim = f['target'] if kind == 'Kill' else f['username']
            deaths[victim] += 1
            if original['offset'] != observed['offset']:
                if kind != 'Death' or original['offset'] != 0:
                    raise ValueError('Only legacy unknown Death envelope may differ')
                recovered.append(dict(round=ordinal, victim=victim, original_offset=original['offset'],
                                      native_offset=observed['offset'], envelopes=[e for e in observation['nativeEnvelopes']
                                      if e['feedback']['type']['name'] == 'Death' and e['feedback']['username'] == victim]))
        rows.append(dict(round=ordinal, replay_sha256=sha(sources[0]),
                         native_complete=credit['complete'], original_complete=default['credit']['complete'],
                         actual_reader_header_operator_parity=True, actual_reader_raw_feedback_parity=True,
                         original_reason=default['credit']['reason'], players=credit['players'],
                         native_envelopes=observation['nativeEnvelopes']))
        print('native-envelope consumed8156/R%02d' % ordinal, flush=True)
    # Only now open already-consumed primary/public outcomes for comparison.
    primary_path = ROOT / 'data/research/v3-final-apac-n-stage2/consumed-primary-review-v2/8156.json'
    primary = read(primary_path)
    page = ROOT / 'data/research/diagnostics/v3-event-metadata/match-8156.html'
    if sha(page) != primary['source_sha256']:
        raise ValueError('Independently verified primary provenance changed')
    comparisons = [dict(player=p['player'], credit=totals[p['player']], official=p['official_kd'][0],
        public=p['public_kd'][0], deaths=deaths[p['player']], official_deaths=p['official_kd'][1])
        for p in primary['primary_kd_rows']]
    if len(comparisons) != 10:
        raise ValueError('Complete independent identity review required')
    uah_path = ROOT / 'data/research/credited-kills-v1/uah-audit.json'
    uah_checks = []
    for control in read(uah_path)['actual_reader_checks']:
        archive = ROOT / 'data/replay-archive/fall-2026' / control['map_id']
        sources = [p for p in archive.rglob('*-R01.rec') if sha(p) == control['replay_sha256']]
        if len(sources) != 1:
            raise ValueError('Archived UAH first-round control unavailable')
        new, prior = native(sources[0]), original_reader(sources[0])
        if (new['header'] != prior['header'] or new['originalFinishes'] != prior['credit']['finishes']
                or new['credit']['players'] != prior['credit']['players']):
            raise ValueError('UAH native observer changed header/operator/raw feedback/counters')
        uah_checks.append(dict(map_id=control['map_id'], round=1,
                               replay_sha256=sha(sources[0]), header_operator_feedback_counter_parity=True))
    record = dict(status='separate_consumed_native_envelope_development_not_default_or_final_regrading',
        official_match_id=8156, map=old['map'], rounds=rows, recovered_death_envelopes=recovered,
        comparisons=comparisons, uah_first_round_controls=uah_checks,
        executable_sha256=sha(EXE), helper_sha256=source_sha(Path(__file__)),
        original_reader_executable_sha256=sha(ORIGINAL_EXE),
        source_hashes={old_path.relative_to(ROOT).as_posix(): sha(old_path),
                       primary_path.relative_to(ROOT).as_posix(): sha(primary_path),
                       uah_path.relative_to(ROOT).as_posix(): sha(uah_path),
                       page.relative_to(ROOT).as_posix(): sha(page)}, protected_hashes=protected,
        counts=dict(rounds=len(rows), complete_native_rounds=sum(r['native_complete'] for r in rows),
            uah_first_round_parity_controls=len(uah_checks),
            actual_reader_header_operator_parity=sum(r['actual_reader_header_operator_parity'] for r in rows),
            actual_reader_raw_feedback_parity=sum(r['actual_reader_raw_feedback_parity'] for r in rows),
            complete_original_rounds=sum(r['original_complete'] for r in rows), recovered_death_envelopes=len(recovered),
            official_matches=sum(p['credit'] == p['official'] for p in comparisons),
            official_mismatches=sum(p['credit'] != p['official'] for p in comparisons),
            public_matches=sum(p['credit'] == p['public'] for p in comparisons),
            official_death_matches=sum(p['deaths'] == p['official_deaths'] for p in comparisons)),
        limits='Exact decoder invocation supplies an envelope byte boundary, not a precise event time, cause of Death, killer or downer. Default v1 source and all baseline guards unchanged. Native source is not accepted by current Python map validator; explicit integration/verification needed before any promotion.')
    destination = DATA / ('8156-parity-audit-' + sha(EXE)[:12] + '.json')
    if destination.exists() and read(destination) != record:
        raise ValueError('Never overwrite changed consumed native audit')
    destination.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    lines = ['# Exact native feedback-envelope recovery: consumed APAC8156', '',
        str(record['counts']), '',
        'The existing readMatchFeedback empty-killer branch emits a Death without setting its private '
        'killOffset. The separate observer wraps that existing callback once, records its exact marker/entry/end '
        'and the index of its single emitted event. It does not duplicate low-level replay parsing or match '
        'by proximity. Existing MatchFeedback and the original v1 refusal are preserved.', '',
        'Jin.RRX/R03 has original offset0 and exact native envelope41873708..41873781, legacy clock1:11. '
        'This boundary now permits the unchanged pre-action/pre-death baseline validator to verify all ten '
        'rounds in this isolated map. Unknown, duplicate, bad-marker, ambiguous and late-baseline evidence still '
        'refuses. It does not assign a credited victim or infer whether this Death was suicide/teamkill/other cause.', '',
        '| Player | Native credited kills | Official / public | Victim deaths / official |',
        '| --- | ---: | --- | --- |']
    lines.extend(f'| {p["player"]} | {p["credit"]} | {p["official"]} / {p["public"]} | '
                 f'{p["deaths"]} / {p["official_deaths"]} |' for p in comparisons)
    lines += ['', 'The eeca495 study remains31complete maps/280official matches/40unavailable at its sealed '
        'hash. These ten additional consumed agreements are a separate structural improvement, not a '
        'retroactive regrade of that study or either failed v3 final. No live source migration, SQLite/public '
        'write, actor promotion, operator/action-start change or Rating recomputation.', '', record['limits'], '']
    (ROOT / 'research/output/credited-kill-native-envelope.md').write_text('\n'.join(lines), encoding='utf-8')
    if snapshot() != protected:
        raise ValueError('Protected state changed')
    print(record['counts'])


if __name__ == '__main__':
    main()
