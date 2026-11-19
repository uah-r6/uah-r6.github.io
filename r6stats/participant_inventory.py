"""Full actual roster proof from ten replay slots, including an explicit empty.

Never fills a missing identity/counter or accepts a nine-player header alone.
"""
from collections import Counter
from copy import deepcopy
from uuid import UUID

SOURCE = 'explicit_ten_slot_empty_participant_v1'
EMPTY_UID = (1 << 64) - 1
RECONNECT_SOURCE = 'explicit_inactive_reconnect_participant_v1'


def _empty_inventory_valid(players, proof, *, allow_team_remap=False):
    if not isinstance(proof, dict) or proof.get('source') != SOURCE or len(players) != 9:
        return False
    def item(p):
        if isinstance(p, dict):
            return (p.get('profileID'), p.get('username'), p.get('team', p.get('teamIndex')), p.get('uid', p.get('id')))
        return p.profile_id, p.username, p.team, None
    expected = [item(p) for p in players]
    try:
        slots, action = proof['slots'], proof['action_offset']
        if (len(slots) != 10 or type(action) is not int or action <= 0
                or Counter(p[2] for p in expected) not in (Counter({0:5,1:4}), Counter({0:4,1:5}))):
            return False
        positions = [s['name_offset'] for s in slots]
        if positions != sorted(set(positions)):
            return False
        active, empty = [], []
        for i, s in enumerate(slots):
            end = positions[i+1] if i+1<len(slots) else action
            if (not all(type(s[k]) is int and 0 < s[k] < end for k in ('name_offset','profile_offset','uid_offset'))
                    or not s['name_offset'] < s['profile_offset'] < s['uid_offset']
                    or type(s['uid']) is not int):
                return False
            if s['username'] == '':
                if (s['profile_id'] != '' or s['uid'] != EMPTY_UID or type(s['operator_id']) is not int
                        or s['operator_id'] != 0 or type(s['operator_offset']) is not int
                        or not s['name_offset'] < s['operator_offset'] < s['profile_offset']):
                    return False
                empty.append(s)
            else:
                if (not 0 < s['uid'] < EMPTY_UID or not UUID(s['profile_id']).int
                        or type(s['team']) is not int or s['team'] not in (0,1)):
                    return False
                active.append((s['profile_id'],s['username'],s['team'],s['uid']))
        if (len(empty) != 1 or len(active) != 9 or len({p[0] for p in active}) != 9
                or len({p[1] for p in active}) != 9 or len({p[3] for p in active}) != 9):
            return False
        bound = {(p,n):(t,uid) for p,n,t,uid in active}
        if len(bound) != len(expected) or any((p,n) not in bound or (uid is not None and uid != bound[p,n][1]) for p,n,t,uid in expected):
            return False
        pairs = {(bound[p,n][0], t) for p,n,t,uid in expected}
        return pairs == {(0,0),(1,1)} or (allow_team_remap and pairs == {(0,1),(1,0)})
    except (KeyError, TypeError, ValueError, AttributeError):
        return False


def inventory_valid(players, proof, *, allow_team_remap=False):
    if not isinstance(proof, dict) or proof.get('source') != RECONNECT_SOURCE:
        return _empty_inventory_valid(players, proof, allow_team_remap=allow_team_remap)
    try:
        r, slots, action = proof['inactive_reconnect'], proof['slots'], proof['action_offset']
        integer = lambda v: type(v) is int
        keys = ('team','slot_index','owner','uid','uid_offset','absent_body_offset',
                'body_component','body_offset','score_component','score_offset')
        if (not all(integer(r[k]) for k in keys) or not integer(action) or len(slots) != 10
                or not 1 <= r['slot_index'] <= 9 or r['team'] != r['slot_index']//5
                or not isinstance(r['username'],str) or not r['username']
                or not 0 < r['uid'] < EMPTY_UID or r['owner'] <= 0
                or r['body_component'] <= 0 or r['score_component'] <= 0
                or r['body_component'] == r['score_component']):
            return False
        slot, previous = slots[r['slot_index']], slots[r['slot_index']-1]
        if (slot['username'] != r['username'] or slot['profile_id'] != str(UUID(int=0))
                or type(slot['uid']) is not int or slot['uid'] != EMPTY_UID
                or not integer(slot['operator_id']) or slot['operator_id'] != 0
                or not previous['uid_offset']+13 < r['absent_body_offset'] < slot['name_offset'] < action
                or not action < r['body_offset'] < r['score_offset'] < r['uid_offset']):
            return False
        fields = r['body_fields']
        tags = {0xc9762625,0x72a64911,0xdad23f01,0x7bcfad80,0xa5f688e7}
        if (len(fields) != 5 or {f['tag'] for f in fields} != tags
                or [f['offset'] for f in fields] != sorted({f['offset'] for f in fields})):
            return False
        for f in fields:
            if (not all(integer(f[k]) for k in ('offset','entity','tag','size','bits'))
                    or f['entity'] != r['body_component'] or f['size'] != 4
                    or not r['body_offset'] < f['offset'] < r['uid_offset']
                    or f['bits'] != (4 if f['tag']==0xa5f688e7 else 0)):
                return False
        a,b = r['counters']
        for s in (a,b):
            if (not all(integer(s[k]) for k in ('offset','value','component','owner','declarationOffset'))
                    or s['owner'] != r['owner'] or s['component'] != r['score_component']
                    or s['declarationOffset'] != r['score_offset'] or not 0 <= s['value'] <= 250):
                return False
        if not r['score_offset'] < a['offset'] < r['uid_offset'] < b['offset'] or a['value'] != 0:
            return False
        # The nine active identities must pass the original complete ten-slot
        # proof. Only this independently proven inactive slot is canonicalized.
        canonical = deepcopy(proof)
        canonical['source'] = SOURCE
        canonical['slots'][r['slot_index']].update(username='', profile_id='')
        if not _empty_inventory_valid(players, canonical, allow_team_remap=allow_team_remap):
            return False
        active = [s for i,s in enumerate(slots) if i != r['slot_index']]
        return all(r['uid'] != s['uid'] and r['username'] != s['username'] for s in active)
    except (KeyError, TypeError, ValueError, AttributeError, IndexError):
        return False
