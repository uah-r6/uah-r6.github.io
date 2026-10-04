from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"research"))
from credited_history_go_controls import compare_history


def control():
    items=[{"ordinal":0,"start":25,"end":87,"kind_byte":1,"opaque_scalar":10,"raw_hex":"aa","first":{"uid":1,"username":"A","role_image":30,"alliance":3}}]
    old={"cumulative":{"complete":True,"items":items,"scalar_ties":{},"scalars_nondecreasing":True},"containers":[]}
    new={"complete":True,"production_authoritative":False,"items":[{**items[0],"first":{**items[0]["first"],"team":0,"profile_id":"p"},"elapsed_seconds":None}],"containers":[],"scalar_ties":{},"scalars_nondecreasing":True}
    header={"players":[{"id":1,"teamIndex":0,"profileID":"p"}]}
    return old,new,header


def test_go_parity_rejects_changed_uid_profile_and_event_scalar():
    old,new,header=control()
    assert compare_history(old,new,header)["match"]
    new["items"][0]["first"]["profile_id"]="other"
    new["items"][0]["opaque_scalar"]=11
    r=compare_history(old,new,header)
    assert not r["match"] and "item0:first:header_team_profile" in r["differences"] and "item0:opaque_scalar" in r["differences"]


def test_go_parity_rejects_inferred_seconds_or_production_authority():
    old,new,header=control()
    new["production_authoritative"]=True
    new["items"][0]["elapsed_seconds"]=1.0
    r=compare_history(old,new,header)
    assert not r["match"] and "item0:clock_not_unresolved" in r["differences"]


def test_go_parity_rejects_silent_scalar_sort_of_list():
    old,new,header=control()
    old["cumulative"]["items"].append({**old["cumulative"]["items"][0],"ordinal":1,"raw_hex":"bb"})
    new["items"].append({**new["items"][0],"ordinal":1,"raw_hex":"bb"})
    new["items"].reverse()
    assert not compare_history(old,new,header)["match"]
