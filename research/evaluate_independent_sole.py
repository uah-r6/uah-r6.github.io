"""Grade only affected scoreless modes on consumed original/SI evidence."""
from collections import Counter
import json

from objective_actor_liveness import feedback
from objective_combined_candidate import declared_body_states
from objective_independent_sole_candidate import independent_sole
from objective_production_check import candidate_raw
from objective_score_delta_validation import grade
from objective_si_final_validation import inputs
from objective_state_components import probe
from objective_transition_probe import ROOT


def main():
    base = ROOT/'data/research/diagnostics'
    sources = {s['siegegg_match_id']:s for s in json.loads((ROOT/'research/sources.json').read_text())['matches']
               if s.get('siegegg_match_id')}
    si = json.loads((ROOT/'research/objective-si-final-reserve.json').read_text())
    sources[3173] = dict(players=si['player_aliases'])
    development = json.loads((base/'objective-encoding-validation/summary.json').read_text())['rounds']
    original = json.loads((base/'objective-combined-candidate-development.json').read_text())['events']
    frozen_si = json.loads((base/'objective-si-final-validation/result.json').read_text())['events']
    structures = json.loads((base/'objective-score-structure-development.json').read_text())
    records = []
    for cohort,events in (('original',original),('consumed_si',frozen_si)):
        for event in events:
            if event['mode']!='incomplete_score_identity':
                continue
            if cohort=='original':
                row = next(r for r in structures if (r['match_id'],r['round'],r['kind'])==(event['match_id'],event['round'],event['kind']))
                folder = next((ROOT/'data/research/extracted').rglob(row['folder']))
                rec = next(folder.glob(f"*-R{row['round']:02d}.rec"))
                raw,feed = probe(rec),feedback(rec)
                previous = max((r['center'] for r in structures if r['folder']==row['folder'] and r['round']==row['round']
                                and r['center']<row['center']),default=0)
                reference = next(r for r in development if (r['match_id'],r['round'])==(event['match_id'],event['round']))
                reference = next(e for e in reference['public_objectives'] if e['type']==event['kind'])
                label = reference.get('description',reference.get('html',''))
            else:
                folder = next((ROOT/'data/research/extracted/actor-si-final-2026-02-15').rglob(event['folder']))
                rec = next(folder.glob(f"*-R{event['physical_round']:02d}.rec"))
                parsed = candidate_raw(folder)['rounds'][event['physical_round']-1]
                if 'header' not in parsed:
                    parsed = dict(header=parsed,matchFeedback=parsed['matchFeedback'])
                row,feed,raw,previous = inputs(rec,parsed,event['kind'])
                label = event['public_label']
            actor,mode,context = independent_sole(row,feed['events'],feed['timers'],declared_body_states(raw),raw['feedback'],previous)
            target = json.loads((ROOT/f"data/research/targets/siegegg-match-{event['match_id']}-api.json").read_text())
            verdict = grade(actor,label,sources[event['match_id']],target)
            records.append({k:event[k] for k in ('match_id','game_id','round','kind')}
                           | dict(cohort=cohort,old_candidate=event['candidate'],candidate=actor,mode=mode,verdict=verdict,context=context))
    counts = {cohort:dict(Counter(r['verdict'] for r in records if r['cohort']==cohort)) for cohort in ('original','consumed_si')}
    (base/'objective-independent-sole.json').write_text(json.dumps(dict(counts=counts,events=records),indent=2))
    lines = ['# Independent declared-body sole mode: consumed hypothesis','',
             'Unfrozen follow-up. cd28f76 candidate and both one-shot outputs are unchanged. '
             'Only the incomplete-score-identity cases can change; all other guarded modes delegate '
             'to the frozen function. No legacy scoreboard identity is guessed. Sole eligibility '
             'retains the full UID/body/kill/death/timer/disconnect safeguards.', '',
             f'Affected-case counts: `{counts}`. These are consumed development outcomes, not fresh validation.', '',
             '| Cohort/match/game/round/kind | Candidate | Verdict | Mode |','| --- | --- | --- | --- |']
    for r in records:
        lines.append(f"| {r['cohort']}/{r['match_id']}/{r['game_id']}/R{r['round']:02d}/{r['kind']} | "
                     f"{r['candidate'] or 'unresolved'} | {r['verdict']} | {r['mode']} |")
    lines += ['', 'Missing disable anchors stay unresolved. State3 never excludes a teammate. '
              'Score evidence is unavailable, not zero. No class allowlist or score threshold changed. '
              'A revised candidate needs a new local freeze and unused actor set; do not retroactively '
              'increase either recorded validation result or change historical SQLite/public/v2.', '']
    (ROOT/'research/output/objective-independent-sole.md').write_text('\n'.join(lines),encoding='utf-8')
    print(counts)
    print('resolved',[(r['match_id'],r['round'],r['candidate'],r['verdict']) for r in records if r['candidate']])


if __name__=='__main__':
    main()
