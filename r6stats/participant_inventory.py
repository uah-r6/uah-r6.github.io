"""Full actual roster proof from ten replay slots, including an explicit empty.

Never fills a missing identity/counter or accepts a nine-player header alone.
"""
from collections import Counter
from uuid import UUID

SOURCE = 'explicit_ten_slot_empty_participant_v1'
EMPTY_UID = (1 << 64) - 1


def inventory_valid(players, proof, *, allow_team_remap=False):
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
