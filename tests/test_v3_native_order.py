from copy import deepcopy
from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research'))
from r6stats.parser.models import Kill,Player,Round
from v3_cnl_order_audit import ordered_states,verify_native
from fit_models import FEATURES
from v3_native_order_fit import features,fit


def fixture():
    players=[Player('',f'{t}{i}',t) for t in (0,1) for i in range(5)]
    # Countdown resets after plant: native 12,11,10,9 precede 44,43,42,41,40.
    kills=[Kill(i,12-i,'10',f'0{i}',1,0) for i in range(4)]
    kills += [Kill(4+i,44-i,'04',f'1{i}',0,1) for i in range(5)]
    r=Round(1,'',0,'DisabledDefuser',players,kills)
    obs={'header':{'players':[{'username':p.username} for p in players]},'credit':{'finishes':[
        {'offset':100+i*10,'feedback':{'type':{'name':'Kill'},'username':k.killer,
         'target':k.victim,'timeInSeconds':k.remaining,'headshot':False}} for i,k in enumerate(kills)]}}
    return r,obs


def test_reset_keeps_first_sole_size_and_opening_before_later_postplant_deaths():
    r,obs=fixture()
    assert verify_native(r,obs)==list(range(100,190,10))
    state=ordered_states(r)
    assert state['opening']==('10','00')
    assert state['clutch']==('04',5)
    r.winner=1
    # Objective-based team win qualifies even if its last player later dies.
    assert ordered_states(r)['clutch']==('14',1)


def test_exact_event_identity_and_offset_parity_refuses_wrong_source():
    r,obs=fixture()
    obs['credit']['finishes'][0]['feedback']['target']='01'
    with pytest.raises(ValueError,match='parity'):verify_native(r,obs)
    _,obs=fixture();obs['credit']['finishes'][0]['offset']=200
    with pytest.raises(ValueError,match='offsets'):verify_native(r,obs)


def test_deaths_change_alive_and_dead_players_never_become_clutch_candidates():
    r,_=fixture()
    r.kills[0]=Kill(0,12,'','00',-1,0)
    r.kills[1]=Kill(1,11,'02','01',0,0)  # teammate kill, not opening
    assert ordered_states(r)['clutch']==('04',5)
    assert ordered_states(r)['opening']==('10','02')
    r.kills.append(deepcopy(r.kills[-1]));r.kills[-1].sequence=9
    with pytest.raises(ValueError,match='Duplicate physical death'):ordered_states(r)


def test_zero_opponents_at_first_sole_is_not_a_clutch():
    r,_=fixture()
    for i,k in enumerate(r.kills):k.sequence=(i+5 if i<4 else i-4)
    assert ordered_states(r)['clutch'] is None


def test_size_transforms_leave_original_event_counts_and_other_families_untouched():
    r={k:0 for k in ('kills','teamkills','opening_kills','opening_deaths','clutches','kost_rounds',
        'survived','deaths_traded','kills_traded','plants','disables',*(f'clutch_1v{x}' for x in range(1,6)))}
    r.update(kills=3,clutches=1,clutch_1v3=1)
    row={'rounds':[r],'legacy_corrected_rounds':[deepcopy(r)]};before=deepcopy(row)
    vectors=[features(row,v) for v in ('native_count','native_linear_size','native_triangular_size')]
    index=FEATURES.index('clutch')
    assert [v[index] for v in vectors]==[1,3,6]
    assert all(v[:index]+v[index+1:]==vectors[0][:index]+vectors[0][index+1:] for v in vectors)
    assert row==before
    row['rounds'][0]['clutches']=2
    with pytest.raises(ValueError,match='breakdown'):features(row,'native_linear_size')


def test_unconsumed_or_unverified_final_rows_cannot_enter_new_fit():
    row=dict(reserved_for_final_test=True,consumed_development=False,native_event_order_complete=False)
    with pytest.raises(ValueError,match='consumed native-order'):fit([row],'native_count')
