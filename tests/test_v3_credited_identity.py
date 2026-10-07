from copy import deepcopy
from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research'))
from v3_credited_derive import bind_lan_counts
from r6stats.kill_credit import validate_map_credit
from test_credited_production import fixture


def test_exact_all_nil_lan_uid_name_adapter_preserves_ten_player_team_identity():
    match,records=fixture()
    for r in match.rounds:
        for p in r.players:p.profile_id='00000000-0000-0000-0000-000000000000'
    for r in records:
        for p in r['credit']['players']:p['profileID']='00000000-0000-0000-0000-000000000000'
    credit=validate_map_credit(records)
    counts=bind_lan_counts(match,credit)
    assert counts[1]['p0']==2 and counts[2]['p1']==0
    match.rounds[0].players[0].username='other'
    with pytest.raises(ValueError,match='Exact unique LAN'):bind_lan_counts(match,credit)


def test_known_profile_is_never_replaced_by_exact_username():
    match,records=fixture()
    match.rounds[0].players[0].profile_id=''
    with pytest.raises(ValueError,match='Mixed unknown'):bind_lan_counts(match,validate_map_credit(records))
