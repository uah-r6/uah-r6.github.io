import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"research"))
from credited_refrag_clock_controls import audit,band
from credited_clock_prefix_controls import clock_regions


PLAYERS=[{"id":i+1,"username":f"P{i}","teamIndex":i//5} for i in range(10)]


def kill(offset,a,b,remaining):
    return {"offset":offset,"feedback":{"type":{"name":"Kill"},"username":a,"target":b,"timeInSeconds":remaining}}


def clock(values):
    return clock_regions([{"entity":123,"offset":i*10+1,"unsigned_bits":v} for i,v in enumerate(values)])


def test_finisher_refrag_identity_and_raw_window_are_separate_from_credit():
    r=audit([kill(6,"P0","P5",10),kill(26,"P6","P0",9)],PLAYERS,clock((10000,9966,9000,8966)))
    assert r["raw_band_counts"]=={"within_candidate_raw_window":1}
    pair=r["finisher_refrag_pairs"][0]
    assert not pair["credited_identity_resolved"] and pair["earlier"]["credited_uid"] is None
    assert pair["raw_countdown_span"]["elapsed_seconds"] is None


def test_coarse_eight_second_expression_can_disagree_with_raw_band():
    r=audit([kill(6,"P0","P5",10),kill(26,"P6","P0",2)],PLAYERS,clock((10510,10490,2010,1990)))
    p=r["finisher_refrag_pairs"][0]
    assert p["legacy_8s_numeric_expression"] and p["raw_band"]=="beyond_candidate_raw_window"
    assert not r["actual_trade_policy_promoted"]


def test_refrag_clock_reset_refuses_elapsed_band():
    r=audit([kill(6,"P0","P5",10),kill(26,"P6","P0",44)],PLAYERS,clock((10000,9966,44966,44932)))
    assert r["raw_band_counts"]=={"unresolved_raw_clock_band":1}


def test_duplicate_victim_is_preserved_and_not_recounted():
    r=audit([kill(6,"P0","P5",10),kill(16,"P1","P5",10),kill(26,"P6","P0",9)],PLAYERS,clock((10000,9966,9000,8966)))
    assert len(r["duplicate_victim_refusals"])==1
    assert len(r["processed_eliminations"])==2 and len(r["finisher_refrag_pairs"])==1


def test_teamkill_suicide_and_death_remove_alive_without_refrags():
    sources=[kill(6,"P0","P1",10),kill(16,"P5","P5",10),
             {"offset":26,"feedback":{"type":{"name":"Death"},"username":"P7","timeInSeconds":9}}]
    r=audit(sources,PLAYERS,clock((10000,9966,9000,8966)))
    assert r["finisher_refrag_pairs"]==[]
    assert r["processed_eliminations"][-1]["alive_after"]==[1,3,4,5,7,9,10]


def test_refrag_threshold_band_keeps_uncertainty():
    span={"status":"bounded_raw_countdown_difference_only","lower_raw_units":7990,"upper_raw_units":8010}
    assert band(span)=="straddles_candidate_raw_window"
