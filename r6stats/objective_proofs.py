"""Defined objective actor proofs; unknown sources fail closed.

Numeric bonus proof is limited to a timer completing after the same body has
returned to an already-supported active state. It is not a state-1 allowlist.
"""
import math
import struct

CORE = 'completing_timer_owner_v1'
BOUNDED_BONUS = 'terminal_active_numeric_bonus_timer_owner_v1'
TRUSTED_OBJECTIVE_ACTOR_SOURCES = frozenset((CORE, BOUNDED_BONUS))


def positive(value):
    return type(value) is int and value > 0


def bounded_bonus(proof, actor, uid, anchor):
    if not isinstance(proof, dict):
        return False
    try:
        start, end = proof['start'], proof['end']
        if (proof['source'] != BOUNDED_BONUS or proof['actor_uid'] != uid
                or proof['profile_id'] != actor.profile_id or proof['username'] != actor.username
                or not all(positive(proof[k]) for k in ('owner', 'body_component', 'timer_component', 'start', 'end'))
                or proof['body_slot'] != 0xc4dc5441 or proof['body_class'] != 0x3fc6980c
                or proof['timer_slot'] != 0xca8dc027 or proof['timer_class'] != 0xf36b21b2
                or proof['terminal'] != 'explicit_state_2' or not start < end < anchor
                or not proof['uid_offsets'] or not all(positive(x) and x < start for x in proof['uid_offsets'])):
            return False
        samples, states = proof['samples'], proof['snapshots']
        offsets = [s['offset'] for s in samples]
        seconds = [s['seconds'] for s in samples]
        if (len(samples) < 2 or offsets != sorted(set(offsets))
                or not all(positive(x) and start <= x < end for x in offsets)
                or not all(type(x) in (int, float) and math.isfinite(x) for x in seconds)
                or not 6.5 <= seconds[0] <= 7.1 or not 0 <= seconds[-1] <= .1
                or any(a < b for a, b in zip(seconds, seconds[1:]))):
            return False
        points = [s['offset'] for s in states]
        if (len(states) < 3 or points != sorted(set(points)) or points[0] != start or points[-1] != end
                or states[-1]['state'] not in (0, 2) or not start < states[-1]['state_offset'] < end):
            return False
        bonus = False
        for s in states:
            if type(s['state']) is not int or s['state'] not in (0, 1, 2) or not positive(s['state_offset']) or s['state_offset'] > s['offset']:
                return False
            if s['state'] != 1:
                continue
            bonus = True
            hp, base, ceiling, bits = (s[k] for k in ('health', 'baseline', 'ceiling', 'fraction_bits'))
            if (not all(type(x) is int for x in (hp, base, ceiling, bits)) or not 0 < base < hp <= ceiling
                    or ceiling - base != 20 or not 0 <= bits <= 0xffffffff
                    or len(s['field_offsets']) != 4 or not all(positive(x) and x <= s['offset'] for x in s['field_offsets'])):
                return False
            fraction = struct.unpack('<f', struct.pack('<I', bits))[0]
            if not math.isfinite(fraction) or fraction <= 0 or abs(fraction-(hp-base)/base) >= 1e-6:
                return False
        return bonus
    except (KeyError, TypeError, ValueError, OverflowError, struct.error):
        return False


def trusted_actor(occurrence, actor):
    if (not actor or occurrence.actor_source != occurrence.actor_reason
            or occurrence.actor_source not in TRUSTED_OBJECTIVE_ACTOR_SOURCES
            or not positive(occurrence.actor_uid) or not positive(occurrence.plant_state_offset)):
        return False
    if occurrence.actor_source == CORE:
        return True
    return occurrence.kind == 'plant' and bounded_bonus(occurrence.actor_evidence, actor,
                                                       occurrence.actor_uid, occurrence.plant_state_offset)


def proven_no_disable(round_, occurrence):
    """Positive raw proof of legacy repeated-zero misclassification, not absence."""
    actor = next((p for p in round_.players if p.key == occurrence.actor), None)
    if not trusted_actor(occurrence, actor) or occurrence.kind != 'plant' or actor.side != 'Attack' or actor.team != round_.winner:
        return False
    try:
        proof = occurrence.actor_evidence['no_disable']
        zeros = proof['zero_samples']
        offsets = [s['offset'] for s in zeros]
        return (proof['source'] == 'repeated_plant_zero_before_transition_v1'
                and proof['actor_uid'] == occurrence.actor_uid and proof['plant_offset'] == occurrence.plant_state_offset
                and all(positive(proof[k]) for k in ('start', 'end', 'legacy_disable_count'))
                and proof['start'] < proof['end'] < occurrence.plant_state_offset
                and len(zeros) == proof['legacy_disable_count'] + 1
                and offsets == sorted(set(offsets)) and len({s['entity'] for s in zeros}) == 1
                and all(positive(s['entity']) and proof['start'] < s['offset'] < proof['end']
                        and isinstance(s['text'], str) and s['text'].startswith('0.00')
                        and 0 <= float(s['text']) <= .01 for s in zeros)
                and tuple(proof['starting_scores']) == round_.starting_scores
                and tuple(proof['ending_scores']) == round_.ending_scores
                and proof['winning_team'] == round_.winner
                and all(type(x) is int and x >= 0 for x in (*proof['starting_scores'], *proof['ending_scores']))
                and [b-a for a,b in zip(proof['starting_scores'],proof['ending_scores'])] ==
                    [int(i == round_.winner) for i in range(2)]
                and len(round_.objective_occurrences) == 1)
    except (KeyError, TypeError, ValueError, OverflowError):
        return False
