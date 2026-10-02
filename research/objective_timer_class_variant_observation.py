"""Consumed declaration-field variant, isolated from default/frozen rules.

The same direct timer slot and property grammar exist in build9734089, but its
observed declaration class field is a859ffff. This script loads a separate
instance of the research state observer to examine that exact declared class;
it changes neither the default observer nor an actor/parser allowlist.
"""
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path

from objective_cached_map_validation import inputs
from objective_player_component_fields import observe, bindings_at
from objective_production_check import candidate_raw
from objective_timer_negative_controls import completion_like
from objective_transition_probe import ROOT


def main():
    manifest = json.loads((ROOT/'research/objective-actor-reserve.json').read_text(encoding='utf-8'))
    consumed_path = ROOT/'data/research/diagnostics/objective-combined-reserve/result.json'
    before = hashlib.sha256(consumed_path.read_bytes()).hexdigest()
    consumed = json.loads(consumed_path.read_text(encoding='utf-8'))
    map_ = next(m for m in manifest['maps'] if m['game_id']==7016)
    spec = importlib.util.spec_from_file_location('isolated_timer_class_observer',Path(__file__).with_name('objective_timer_component_episodes.py'))
    isolated = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(isolated)
    default_class = isolated.CLASS
    isolated.CLASS = 'a859ffff'
    records = []
    logical = 0
    for segment in map_['physical_segments']:
        folders = [p for p in (ROOT/'data/research/extracted').rglob(segment['folder']) if p.is_dir()]
        if len(folders)!=1:
            raise ValueError('Ambiguous consumed replay segment')
        folder = folders[0]
        raw = candidate_raw(folder)
        for filename in segment['included_round_files']:
            logical += 1
            rec = folder/filename
            physical = int(rec.stem.rsplit('-R',1)[1])
            state,owners,slots,fields = observe(rec)
            routes = Counter()
            for field in fields:
                if field['hash']=='a9c858d9' and field['value']:
                    link = bindings_at(owners,slots,field['offset']).get(field['entity'])
                    routes[(link['slot'],link['class_hash']) if link else ('unknown','unknown')] += 1
            observed = isolated.component_episodes(owners,slots,fields)
            positives = [e for e in consumed['events'] if e['game_id']==7016 and e['round']==logical]
            anchors = []
            for event in positives:
                base = raw['rounds'][physical-1]
                if 'header' not in base:
                    base = dict(header=base,matchFeedback=base['matchFeedback'])
                row,_,_,previous = inputs(rec,base,event['kind'])
                anchors.append(dict(kind=event['kind'],center=row['center'] if row else None,previous_anchor=previous))
            record = dict(match_id=map_['match_id'],game_id=7016,round=logical,physical_round=physical,
                          build=state['header']['codeVersion'],source_sha256=hashlib.sha256(rec.read_bytes()).hexdigest(),
                          timer_route_counts=[dict(slot=s,class_hash=c,samples=n) for (s,c),n in routes.items()],
                          declared_variant_class=isolated.CLASS,default_class_unchanged=default_class,
                          completion_anchors=anchors,component_runs=observed,
                          completion_like=[i for i,e in enumerate(observed['episodes']) if completion_like(e)],actor=None)
            records.append(record)
            print(logical,'runs',len(observed['episodes']),'complete-like',len(record['completion_like']),'anchors',anchors,flush=True)
    if hashlib.sha256(consumed_path.read_bytes()).hexdigest()!=before:
        raise ValueError('Original immutable result changed')
    dest = ROOT/'data/research/diagnostics/player-component-fields/timer-class-variant.json'
    dest.write_text(json.dumps(records,indent=2,allow_nan=False),encoding='utf-8')
    lines = ['# Consumed timer declaration class variant', '',
             'Build9734089,game7016: the directly declared slot27c08dca has class fielda859ffff rather thanb2216bf3. '
             'The same explicitly framed statee58c06e9, progresse9a37feb and ASCII timera9c858d9 occur on those components. '
             'An isolated instance of the research state observer inspects the declared variant; the default strict class '
             'and frozen actor rule are unchanged. No generic unknown-class fallback or actor credit. All12rounds previously consumed.', '',
             '| Logical / physical round | Direct timer routes | Run owner / state / first-last / terminal | Global anchors |',
             '| --- | --- | --- | --- |']
    for r in records:
        runs = '; '.join(f"{e['binding']['player']} / {e['state']} / {e['first_timer']}-{e['last_timer']} / {e['end_reason']}" for e in r['component_runs']['episodes'])
        lines.append(f"| {r['round']} / {r['physical_round']} | {r['timer_route_counts']} | {runs or 'none'} | {r['completion_anchors']} |")
    lines += ['', 'These observations recover the three previously missing component runs, not the original A validation outcomes. '
              'Negative rounds in the same consumed map are retained, including canceled attempts. The declaration field '
              'is recorded literally; do not infer an engine class name or promote a new build allowlist from these cases alone. '
              'A future candidate needs explicit semantics/specification, regression controls and a separately frozen validation.', '']
    (ROOT/'research/output/objective-timer-class-variant.md').write_text('\n'.join(lines),encoding='utf-8')


if __name__ == '__main__':
    main()
