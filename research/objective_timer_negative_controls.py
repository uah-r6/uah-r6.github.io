"""Resumable consumed negative controls for declared timer state semantics.

All 230 objective-free rounds come from the previously consumed 291-round
encoding cohort. This is not a fresh actor validation and emits no actors.
Reads replay files, writes ignored observation caches and a research report.
"""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path

import objective_player_component_fields as fields_module
import objective_timer_component_episodes as episodes_module
from objective_player_component_fields import observe
from objective_timer_component_episodes import component_episodes
from objective_transition_probe import ROOT, PARSER, replay_file


def completion_like(episode):
    """Descriptive old timer thresholds plus explicit termination, no credit."""
    return (episode['end_reason']=='explicit_state_2' and episode['monotonic_timer']
            and len(episode['samples']) > 1 and episode['first_timer'] is not None
            and 6.5 <= episode['first_timer'] <= 7.1 and episode['last_timer'] is not None
            and 0 <= episode['last_timer'] <= .1)


def observe_row(row, code_hash):
    rec, _ = replay_file(row['match_id'],row['round'])
    signature = hashlib.sha256(rec.read_bytes()+code_hash).hexdigest()
    cache = ROOT/'data/research/diagnostics/player-component-fields/negative-controls'
    cache.mkdir(parents=True,exist_ok=True)
    path = cache/f'{signature}.json'
    if path.exists():
        result = json.loads(path.read_text(encoding='utf-8'))
        if (result['match_id'],result['round']) != (row['match_id'],row['round']):
            raise ValueError('Negative observation cached under different identity')
        return result
    raw,owners,slots,fields = observe(rec)
    result = dict(match_id=row['match_id'],round=row['round'],build=raw['header'].get('codeVersion'),
                  signature=signature,public_objectives=[],actor=None)
    result.update(component_episodes(owners,slots,fields))
    result['completion_like_episodes'] = [i for i,e in enumerate(result['episodes']) if completion_like(e)]
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(result,indent=2,allow_nan=False),encoding='utf-8')
    temp.replace(path)
    return result


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--all-consumed-negative',action='store_true')
    args = parser.parse_args()
    source = ROOT/'data/research/diagnostics/objective-encoding-validation/summary.json'
    rows = [r for r in json.loads(source.read_text(encoding='utf-8'))['rounds'] if not r['public_objectives']]
    if len(rows) != 230:
        raise ValueError('Predeclared consumed negative cohort differs')
    if not args.all_consumed_negative:
        rows = [r for r in rows if (r['match_id'],r['round']) in ((4141,6),(4141,14),(4138,9))]
    code_hash = b''.join(Path(m.__file__).read_bytes() for m in (fields_module,episodes_module))
    code_hash += PARSER.read_bytes()+(ROOT/'.local-tools/bin/state-component-probe.exe').read_bytes()
    results = []
    with ThreadPoolExecutor(max_workers=2) as pool:
        pending = [pool.submit(observe_row,r,code_hash) for r in rows]
        for task in as_completed(pending):
            result = task.result()
            results.append(result)
            print(len(results),'/',len(rows),result['match_id'],result['round'],len(result['episodes']),
                  'runs',len(result['completion_like_episodes']),'completion-like',flush=True)
    results.sort(key=lambda r:(r['match_id'],r['round']))
    episodes = [e for r in results for e in r['episodes']]
    summary = dict(cohort='previously_consumed_negative_rounds',rounds=len(results),
                   rounds_with_runs=sum(bool(r['episodes']) for r in results),
                   runs=len(episodes),terminal_counts=dict(Counter(e['end_reason'] for e in episodes)),
                   completion_like_count=sum(len(r['completion_like_episodes']) for r in results),
                   actor_credits=0,results=results)
    suffix = '-all-consumed' if args.all_consumed_negative else '-three-controls'
    (ROOT/f'data/research/diagnostics/player-component-fields/negative{suffix}.json').write_text(json.dumps(summary,indent=2,allow_nan=False),encoding='utf-8')
    lines = ['# Consumed objective-free timer component controls', '',
             'Predeclared negatives from the previously consumed 291-round encoding cohort. '
             'No fresh-validation claim, actor attribution, target alteration or production change. '
             'Runs split on explicit component state and temporal ownership boundaries, never byte gaps. '
             '"Completion-like" is a descriptive check: state2 termination, monotonic timer, >1 samples, '
             'start6.5..7.1 and last0..0.1. It is not an accepted completion or actor rule.', '',
             f"Rounds{summary['rounds']}; rounds with runs{summary['rounds_with_runs']}; runs{summary['runs']}; "
             f"terminal counts`{summary['terminal_counts']}`; completion-like{summary['completion_like_count']}; actor credits0.", '',
             '| Match / round | Owner observation | State | First / last timer | End reason | Completion-like |',
             '| --- | --- | --- | --- | --- | --- |']
    for result in results:
        for i,e in enumerate(result['episodes']):
            lines.append(f"| {result['match_id']}/R{result['round']:02d} | {e['binding']['player']} | {e['state']} | "
                         f"{e['first_timer']} / {e['last_timer']} | {e['end_reason']} | {i in result['completion_like_episodes']} |")
    lines += ['', 'A low timer without an explicit terminal remains incomplete. Even a completion-like record needs '
              'independent semantics, correct team/phase, verified identity, occurrence/winner evidence and ambiguity checks. '
              'Both mandatory actor controls stay unresolved. Cached per-replay results allow interrupted jobs to resume.', '']
    (ROOT/f'research/output/objective-timer-negative-controls{suffix}.md').write_text('\n'.join(lines),encoding='utf-8')


if __name__ == '__main__':
    main()
