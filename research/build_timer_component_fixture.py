"""Reduce consumed component controls to public-safe structural test data.

Keeps explicit state records and the first/last timer record of every run.
No replay binary bytes, raw dumps, private paths or Ubisoft profile IDs.
"""
import hashlib
import json

from objective_player_component_fields import observe, controls
from objective_timer_component_episodes import component_episodes, STATE, TIMER, PROGRESS
from objective_transition_probe import ROOT, replay_file


def main():
    structures = json.loads((ROOT/'data/research/diagnostics/objective-score-structure-development.json').read_text(encoding='utf-8'))
    chosen = controls()+[next(r for r in structures if r['match_id']==4150 and r['round']==11)]
    cases = []
    for row in chosen:
        folders = [p for p in (ROOT/'data/research/extracted').rglob(row['folder']) if p.is_dir()]
        if len(folders) != 1:
            raise ValueError('Ambiguous control folder')
        recs = list(folders[0].glob(f"*-R{row['round']:02d}.rec"))
        if len(recs) != 1:
            raise ValueError('Ambiguous control round')
        cases.append((row['match_id'],row['game_id'],row['round'],recs[0]))
    cases += [(m,None,n,replay_file(m,n)[0]) for m,n in ((4141,6),(4141,14),(4138,9))]
    reduced = []
    for match,game,number,rec in cases:
        raw,owners,slots,fields = observe(rec)
        full = component_episodes(owners,slots,fields)
        entities = {e['entity'] for e in full['episodes']}
        records = {f['record_start'] for f in fields if f['entity'] in entities and f['hash']==STATE}
        for episode in full['episodes']:
            if episode['samples']:
                boundaries = {episode['samples'][0]['offset'],episode['samples'][-1]['offset']}
                records.update(f['record_start'] for f in fields if f['offset'] in boundaries)
        kept = [f for f in fields if f['entity'] in entities and f['record_start'] in records and f['hash'] in (STATE,TIMER,PROGRESS)]
        histories = [ds for ds in slots.values() if any(d['component'] in entities for d in ds)]
        declarations = [d for ds in histories for d in ds]
        compact = component_episodes(owners,{(ds[0]['owner'],ds[0]['slot_hash']):ds for ds in histories},kept)
        expected = [dict(player=e['binding']['player'],state=e['state'],first_timer=e['first_timer'],
                         last_timer=e['last_timer'],end_reason=e['end_reason'],actor=None) for e in full['episodes']]
        actual = [dict(player=e['binding']['player'],state=e['state'],first_timer=e['first_timer'],
                       last_timer=e['last_timer'],end_reason=e['end_reason'],actor=e['actor']) for e in compact['episodes']]
        if actual != expected or full['orphan_records'] or compact['orphan_records']:
            raise ValueError('Reduced control differs from full observation')
        reduced.append(dict(match_id=match,game_id=game,round=number,replay_sha256=hashlib.sha256(rec.read_bytes()).hexdigest(),
                            owners=owners,declarations=declarations,fields=kept,expected=expected))
    dest = ROOT/'tests/fixtures/objective-timer-components.json'
    dest.write_text(json.dumps(dict(status='consumed_structural_observations_never_actor_credit',
                                    sampling='state records and first/last timer records only',cases=reduced),indent=2),encoding='utf-8')
    print(len(reduced),'cases',dest.stat().st_size,'bytes')


if __name__ == '__main__':
    main()
