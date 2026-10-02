"""Unfrozen consumed-data hypothesis: sole mode needs body identity, not score.

The cd28f76 candidate and both recorded validations remain unchanged. This
wrapper tests only the unnecessary shared scoreboard prerequisite discovered
on the now-consumed SI build. No legacy score identity is guessed.
"""
from objective_actor_liveness import interaction_span
from objective_combined_candidate import combine,dead_by,values_during


def independent_sole(row,deaths,timers,body,full_feedback,previous_state=0):
    actor,mode,context = combine(row,deaths,timers,body,full_feedback,previous_state)
    if mode!='incomplete_score_identity':
        return actor,mode,context
    # combine already verified a full distinct roster, unique declared body
    # identity for all five eligible players, no disconnect and timed deaths.
    # The failed score join cannot establish a score actor or contradiction.
    side = 'Attack' if row['kind']=='plant' else 'Defense'
    eligible = {p['username'] for p in row['header']['players']
                if row['header']['teams'][p['teamIndex']]['role']==side}
    span = interaction_span(timers,row['center'],previous_state)
    if not span:
        return None,'incomplete_interaction_span_without_score_binding',context
    start,end = span['first_offset'],row['center']
    states = {p:values_during(body[p],start,end) for p in eligible}
    remaining = [p for p in eligible if not dead_by(p,deaths,start)]
    context.update(interaction_span=span,body_states_during_interaction=states,
                   identity_source='unique_direct_declared_body_uid',score_evidence='unavailable_not_assumed_zero')
    if len(remaining)!=1:
        return None,'not_sole_without_score_binding',context
    survivor = remaining[0]
    if (dead_by(survivor,deaths,end) or not states[survivor] or not set(states[survivor])<={0,2}
            or not all(states[p] and set(states[p])=={4} for p in eligible-{survivor})):
        return None,'body_or_death_conflict_without_score_binding',context
    return survivor,'sole_declared_body_without_score_binding',context
