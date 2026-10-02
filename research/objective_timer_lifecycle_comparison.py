"""Consumed successful/canceled timer teardown comparison, no actor credits."""
import hashlib
import json

from objective_actor_liveness import feedback
from objective_cached_map_validation import inputs
from objective_player_component_fields import observe, controls
from objective_production_check import candidate_raw, CANDIDATE
from objective_timer_component_episodes import component_episodes
from objective_transition_probe import ROOT, PARSER, replay_file
from uah_guarded_actor_readonly import snapshot


def cached_states(rec):
    # Exact existing cache signature; no new low-level parser or byte windows.
    key = hashlib.sha256(rec.read_bytes()+PARSER.read_bytes()+CANDIDATE.read_bytes()+
                         b''.join((ROOT/'research'/name).read_bytes() for name in
                                  ('objective_encoding_probe.py','objective_score_ledger.py','objective_score_identity.py'))).hexdigest()
    path = ROOT/f'data/research/diagnostics/objective-cached-map-validation/inputs/{key}.json'
    if not path.exists():
        raw = candidate_raw(rec.parent)['rounds'][int(rec.stem.rsplit('-R',1)[1])-1]
        if 'header' not in raw:
            raw = dict(header=raw,matchFeedback=raw['matchFeedback'])
        # Reuse the existing adapter's cache builder. Older consumed controls
        # used a different cache directory; do not manually copy cache files.
        inputs(rec,raw,'plant')
    return json.loads(path.read_text(encoding='utf-8'))['states']


def main():
    protected = snapshot()
    base = ROOT/'data/research/diagnostics'
    development = json.loads((base/'objective-encoding-validation/summary.json').read_text(encoding='utf-8'))['rounds']
    extensions = json.loads((base/'player-component-fields/consumed-extensions-observations.json').read_text(encoding='utf-8'))
    cases = []
    for row in extensions:
        if row['cohort']=='si-final' and row['kind']=='disable':
            folders = [p for p in (ROOT/'data/research/extracted').rglob(row['folder']) if p.is_dir()]
            if len(folders)!=1:
                raise ValueError('Ambiguous consumed SI segment')
            recs = list(folders[0].glob(f"*-R{row['physical_round']:02d}.rec"))
            if len(recs)!=1:
                raise ValueError('Ambiguous consumed SI physical round')
            cases.append((row['match_id'],row['game_id'],row['round'],recs[0],cached_states(recs[0])))
    for match,number in ((3073,8),(4141,6),(4141,14),(4138,9)):
        rec,_ = replay_file(match,number)
        states = next(r['events'] for r in development if (r['match_id'],r['round'])==(match,number))
        cases.append((match,None,number,rec,states))
    # Two same-build control disables: one disputed, one prior confirmed label.
    for row in controls()[1:3]:
        folder = next((ROOT/'data/research/extracted').rglob(row['folder']))
        rec = next(folder.glob(f"*-R{row['round']:02d}.rec"))
        cases.append((row['match_id'],row['game_id'],row['round'],rec,cached_states(rec)))
    results = []
    for match,game,number,rec,global_states in cases:
        state,owners,slots,fields = observe(rec)
        runs = component_episodes(owners,slots,fields)
        feed = feedback(rec)
        roles = {p['username']:state['header']['teams'][p['teamIndex']]['role'] for p in state['header']['players']}
        winners = [t['role'] for t in state['header']['teams'] if t.get('won')]
        # Include all deaths and declarations, not an arbitrary neighborhood.
        ordered = [dict(offset=e['offset'],kind=e['feedback']['type']['name'],
                        details=e['feedback']) for e in feed['events']]
        ordered += [dict(offset=s['offset'],kind='global_defuser_state',details=s) for s in global_states]
        observations = []
        for ep in runs['episodes']:
            owner = ep['binding']['owner']
            clear = [d for d in slots.get((owner,ep['binding']['slot']),[]) if d['offset']==ep['end_offset']]
            for event in ep['records']:
                for f in event['fields']:
                    if f['hash']=='e58c06e9':
                        ordered.append(dict(offset=f['offset'],kind='player_timer_state',
                                            details=dict(owner=ep['binding']['player'],state=f['value'],record_start=f['record_start'])))
            for sample in ep['samples'][:1]+ep['samples'][-1:]:
                ordered.append(dict(offset=sample['offset'],kind='timer_boundary_sample',
                                    details=dict(owner=ep['binding']['player'],text=sample['text'])))
            if clear:
                ordered.append(dict(offset=clear[0]['offset'],kind='terminal_slot_declaration',details=clear[0]))
            observations.append(dict(owner_observation=ep['binding']['player'],role=roles.get(ep['binding']['player']),
                                     state=ep['state'],first_timer=ep['first_timer'],last_timer=ep['last_timer'],
                                     start_record=ep['start_record'],terminal=ep['end_reason'],end_offset=ep['end_offset'],
                                     literal_terminal_declarations=clear,actor=None))
        zero_clears = [d for ds in slots.values() for d in ds if d['slot_hash']=='27c08dca' and d['component']==0
                       and d['class_hash']=='00000000' and d['offset']>max((e['start_record'] for e in runs['episodes']),default=0)]
        raw = candidate_raw(rec.parent)['rounds'][int(rec.stem.rsplit('-R',1)[1])-1]
        header = raw.get('header',raw)
        results.append(dict(match_id=match,game_id=game,round=number,build=state['header']['codeVersion'],
                            winner_roles=winners,global_states=global_states,
                            occurrence_only_header=header.get('objectiveOccurrences',[]),
                            runs=observations,ordered_ledger=sorted(ordered,key=lambda e:e['offset']),
                            timer_slot_clears_after_last_start=zero_clears,actor=None))
        print(match,game,number,winners,[(e['owner_observation'],e['state'],e['terminal']) for e in observations],flush=True)
    if snapshot()!=protected:
        raise ValueError('Protected data changed during lifecycle observation')
    dest = base/'player-component-fields/timer-lifecycle-comparison.json'
    dest.write_text(json.dumps(results,indent=2,allow_nan=False),encoding='utf-8')
    lines = ['# Consumed timer lifecycle and round teardown comparison', '',
             'Explicit numeric UID ownership, complete state-record runs and literal terminal declarations. '
             'All actor fields remain null. No missing property is synthesized and no unknown state becomes dead. '
             'The cached parser win-condition string is deliberately not used as ground truth. '
             'A literal slot clear is teardown, not completion by itself.', '',
             '| Match / game / round | Winner role | Global defuser state writes | Timer owner / state / last / terminal |',
             '| --- | --- | --- | --- |']
    for r in results:
        states = ', '.join(f"{s['value']}@{s['offset']}" for s in r['global_states']) or 'none'
        observations = '; '.join(f"{e['owner_observation']} / {e['state']} / {e['last_timer']} / {e['terminal']}" for e in r['runs'])
        lines.append(f"| {r['match_id']}/{r['game_id']}/R{r['round']:02d} | {r['winner_roles']} | {states} | {observations} |")
    lines += ['', 'SI BankR03 kds and FortressR17 handyy have unique directly bound state1 timers reaching0.002 and0.012 '
              'respectively, followed by an explicit owner-slot clear(component0,class00000000). Neither has a terminal '
              'state2 or global defuser state0. Each has a preceding verified global plant state1 and a Defense winner. '
              'Their absence is a real serialization/lifecycle difference, not a lost scoreboard identity join. '
              'The strict observer still gives no actor proposal for either.', '',
              'Older consumed3073/R08 has no global state0 but does have an explicit state2 on the disable component. '
              'Thus missing global and player-component terminal writes are separate limitations. '
              'The three negative controls have Attack winners and no global plant flag; a similar timer/clear pattern '
              'cannot establish a plant. State2 can also terminate canceled attempts.', '',
              'A potential disable-by-phase hypothesis requires independently validated plant occurrence, a Defense winner, '
              'unique state1 interaction owner with correct role, coherent identity/liveness and no competing run. '
              'This is not yet a frozen actor rule: the disputed J9O/njr control and target contradictions need resolution '
              'before standalone owner credit. Existing A and all immutable results remain unchanged.', '',
              f'{len(protected)} protected database/archive/public SHA256 values unchanged. Detailed complete ordered '
              'ledgers remain in ignored research JSON; no raw replay or dump is committed.', '']
    (ROOT/'research/output/objective-timer-lifecycle-comparison.md').write_text('\n'.join(lines),encoding='utf-8')


if __name__ == '__main__':
    main()
