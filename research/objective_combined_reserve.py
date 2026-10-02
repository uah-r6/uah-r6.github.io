"""One-shot frozen actor diagnostic on the sealed five-map reserve.

Refuses a dirty tree or changed frozen files. Replay predictions are saved
before any public actor labels are read. Interrupted runs resume identical
cached inputs; a completed result is immutable and only printed on rerun.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

from objective_actor_liveness import feedback
from objective_combined_candidate import combine,declared_body_states
from objective_encoding_probe import inherited_state_events
from objective_production_check import candidate_raw,CANDIDATE
from objective_score_identity import score_identity_candidates
from objective_score_ledger import ledger
from objective_score_structure import observe
from objective_score_delta_validation import grade
from objective_transition_probe import ROOT,PARSER
from objective_state_components import probe


def digest(path):
    contents = path.read_bytes()
    if path.suffix in ('.py','.go','.json','.md'):
        contents = contents.replace(b'\r\n',b'\n')
    return hashlib.sha256(contents).hexdigest()


def inputs(rec,raw,kind):
    cache = ROOT/'data/research/diagnostics/objective-combined-reserve/inputs'
    cache.mkdir(parents=True,exist_ok=True)
    key = hashlib.sha256(rec.read_bytes()+PARSER.read_bytes()+CANDIDATE.read_bytes()+
                         b''.join(Path(__file__).with_name(name).read_bytes() for name in
                                  ('objective_encoding_probe.py','objective_score_ledger.py','objective_score_identity.py'))).hexdigest()
    dest = cache/(key+'.json')
    if not dest.exists():
        with tempfile.TemporaryDirectory() as scratch:
            dumped = Path(scratch)/'round.dump'
            subprocess.run([str(PARSER),'--dump','-o',str(dumped),str(rec)],check=True,capture_output=True)
            data = dumped.read_bytes()
            saved = dict(states=inherited_state_events(data),changes=ledger(data)['events'],
                         identity=score_identity_candidates(data,raw['header']['players']))
            dest.write_text(json.dumps(saved),encoding='utf-8')
    saved = json.loads(dest.read_text())
    states = saved['states']
    eligible = [e for e in states if e['value']==(1 if kind=='plant' else 0)]
    plant = next((e for e in states if e['value']==1),None)
    if kind=='disable':
        eligible = [e for e in eligible if plant and e['offset']>plant['offset']]
    if len(eligible)!=1:
        return None,None,None,None
    center = eligible[0]['offset']
    score,state,feed = observe(rec),probe(rec),feedback(rec)
    if score['feedback']!=raw['matchFeedback'] or state['feedback']!=raw['matchFeedback']:
        raise ValueError('Observer changed parser feedback')
    if [d['feedback'] for d in feed['events']]!=[e for e in raw['matchFeedback'] if e['type']['name'] in ('Kill','Death')]:
        raise ValueError('Death observer changed parser feedback')
    row = dict(kind=kind,center=center,header=raw['header'],identity=saved['identity'],all_changes=saved['changes'],
               clock_ticks=[e for e in score['fields'] if e['kind']=='clock' and e['value']<=600])
    previous = max((e['offset'] for e in states if e['offset']<center),default=0)
    return row,feed,state,previous


def main():
    cache = ROOT/'data/research/diagnostics/objective-combined-reserve'
    cache.mkdir(parents=True,exist_ok=True)
    result_path = cache/'result.json'
    if result_path.exists():
        result = json.loads(result_path.read_text())
        print('Previously recorded immutable result:',result['counts'],result['modes'])
        return
    freeze = json.loads((ROOT/'research/objective-combined-freeze.json').read_text())
    for relative,expected in freeze['sha256'].items():
        if digest(ROOT/relative)!=expected:
            raise ValueError('Frozen input changed: '+relative)
    if subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip():
        raise ValueError('Freeze gate requires a clean repository')
    head = subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    reserve = json.loads((ROOT/'research/objective-actor-reserve.json').read_text())
    run_path = cache/'run.json'
    if run_path.exists():
        run = json.loads(run_path.read_text())
        if run['freeze_sha256']!=digest(ROOT/'research/objective-combined-freeze.json'):
            raise ValueError('An interrupted reserve run cannot change its frozen rule')
    else:
        run = dict(freeze_commit=head,freeze_sha256=digest(ROOT/'research/objective-combined-freeze.json'),
                   phase='replay_predictions',actor_labels_opened=False)
        run_path.write_text(json.dumps(run,indent=2))
    predictions_path = cache/'predictions.json'
    if predictions_path.exists():
        maps = json.loads(predictions_path.read_text())
    else:
        maps = []
        for mapping in reserve['maps']:
            map_cache = cache/f"predictions-{mapping['match_id']}-{mapping['game_id']}.json"
            if map_cache.exists():
                maps.append(json.loads(map_cache.read_text()))
                continue
            records,files = [],[]
            number = 0
            for segment in mapping['physical_segments']:
                folders = [p for p in (ROOT/'data/research/extracted').rglob(segment['folder']) if p.is_dir()]
                if len(folders)!=1:
                    raise ValueError('Ambiguous physical reserve folder')
                raw = candidate_raw(folders[0])
                for filename in segment['included_round_files']:
                    rec = folders[0]/filename
                    physical = int(rec.stem.rsplit('-R',1)[1])
                    round_ = raw['rounds'][physical-1]
                    if 'header' not in round_:
                        round_ = dict(header=round_,matchFeedback=round_['matchFeedback'])
                    number += 1
                    files.append(dict(folder=segment['folder'],filename=filename,sha256=digest(rec)))
                    occurrences = round_['header'].get('objectiveOccurrences',[])
                    for occurrence in occurrences:
                        kind = occurrence['kind']
                        row,feed,state,previous = inputs(rec,round_,kind)
                        if row is None:
                            actor,mode,context = None,'missing_completion_anchor',{}
                        else:
                            actor,mode,context = combine(row,feed['events'],feed['timers'],declared_body_states(state),state['feedback'],previous)
                        records.append(dict(match_id=mapping['match_id'],game_id=mapping['game_id'],
                                            round=number,physical_round=physical,folder=segment['folder'],kind=kind,
                                            build=round_['header']['codeVersion'],candidate=actor,mode=mode,context=context))
                    print('predicted',mapping['match_id'],mapping['game_id'],number,'occurrences',len(occurrences),flush=True)
            if number!=mapping['rounds']:
                raise ValueError('Reserve round count changed')
            result = dict(match_id=mapping['match_id'],game_id=mapping['game_id'],rounds=number,events=records,files=files)
            map_cache.write_text(json.dumps(result,indent=2))
            maps.append(result)
        predictions_path.write_text(json.dumps(maps,indent=2))
    # Durable evidence of label opening, after ALL replay predictions exist.
    run.update(phase='grading_frozen_predictions',actor_labels_opened=True)
    run_path.write_text(json.dumps(run,indent=2))
    sources = {s['siegegg_match_id']:s for s in json.loads((ROOT/'research/sources.json').read_text())['matches']
               if s.get('siegegg_match_id')}
    records,occurrence_errors = [],[]
    for mapping in maps:
        target = json.loads((ROOT/f"data/research/targets/siegegg-match-{mapping['match_id']}-api.json").read_text())
        game = next(g for g in target['games'] if g['id']==mapping['game_id'])
        if len(game['rounds'])!=mapping['rounds']:
            raise ValueError('Target logical round alignment differs')
        used = set()
        for number,round_ in enumerate(game['rounds'],1):
            public = [e for e in round_['events'] if e['type'] in ('plant','disable')]
            for event in public:
                candidates = [r for r in mapping['events'] if r['round']==number and r['kind']==event['type']]
                if len(candidates)>1:
                    raise ValueError('Ambiguous predicted objective')
                if candidates:
                    predicted = candidates[0]
                    used.add((number,event['type']))
                else:
                    predicted = dict(match_id=mapping['match_id'],game_id=mapping['game_id'],round=number,
                                     kind=event['type'],candidate=None,mode='objective_not_detected',context={})
                    occurrence_errors.append(dict(match_id=mapping['match_id'],game_id=mapping['game_id'],round=number,kind=event['type'],error='missed'))
                label = event.get('description',event.get('html',''))
                verdict = grade(predicted['candidate'],label,sources[mapping['match_id']],target)
                records.append(dict(**predicted,verdict=verdict,public_label=label))
        for predicted in mapping['events']:
            if (predicted['round'],predicted['kind']) not in used:
                occurrence_errors.append(dict(match_id=mapping['match_id'],game_id=mapping['game_id'],round=predicted['round'],kind=predicted['kind'],error='extra'))
    counts = {kind:dict(Counter(r['verdict'] for r in records if r['kind']==kind)) for kind in ('plant','disable')}
    modes = {kind:dict(Counter(r['mode'] for r in records if r['kind']==kind and r['candidate'])) for kind in ('plant','disable')}
    result = dict(freeze_commit=run['freeze_commit'],freeze_sha256=run['freeze_sha256'],counts=counts,modes=modes,
                  maps=len(maps),rounds=sum(m['rounds'] for m in maps),occurrence_errors=occurrence_errors,events=records)
    result_path.write_text(json.dumps(result,indent=2))
    run.update(phase='completed_immutable_result')
    run_path.write_text(json.dumps(run,indent=2))
    lines = ['# Frozen combined actor reserve result','',f"Freeze commit: `{run['freeze_commit']}`. Five maps,60 rounds. "
             'All replay predictions saved before actor labels were opened. This reserve is now consumed. '
             'No candidate change or historical data write during validation.', '',f'Counts: `{counts}`. Modes: `{modes}`.',
             '',f'Occurrence errors: `{occurrence_errors}`.','',
             '| Match/game/logical round | Kind | Candidate | Verdict | Mode | Public label |','| --- | --- | --- | --- | --- | --- |']
    for r in records:
        lines.append(f"| {r['match_id']}/{r['game_id']}/R{r['round']:02d} | {r['kind']} | {r['candidate'] or 'unresolved'} | {r['verdict']} | {r['mode']} | {r['public_label']} |")
    lines += ['', 'Eight plants/two disables is a small actor validation sample. Zero wrong credits on this '
              'reserve would not prove all build/gadget/DBNO/disconnect behavior. Additional independent '
              'events are needed before broad production credit. Do not retune and call this set fresh again.', '']
    (ROOT/'research/output/objective-combined-reserve.md').write_text('\n'.join(lines),encoding='utf-8')
    print(counts,modes,'occurrence_errors',occurrence_errors)


if __name__=='__main__':
    main()
