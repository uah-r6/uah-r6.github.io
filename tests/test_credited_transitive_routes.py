from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research'))
from credited_transitive_owned_controls import Routes, analyze, closure


def declaration(owner,component,offset=1,slot='slot'):
    return dict(owner=owner,component=component,offset=offset,slot_hash=slot,class_hash='opaque-nonzero')


def test_transitive_declared_path_and_slot_replacement():
    r=Routes({1:101})
    r.declare(declaration(1,2));r.declare(declaration(2,3))
    path,why=r.resolve(3)
    assert path['uid']==101 and len(path['path'])==2
    r.declare(declaration(1,4,3))
    assert r.resolve(3)[0] is None
    assert r.resolve(4)[0]['uid']==101


def test_shared_unknown_parent_and_cycles_refuse_even_when_one_route_known():
    r=Routes({1:101})
    r.declare(declaration(1,2));r.declare(declaration(9,2))
    assert r.resolve(2)==(None,'shared_parent')
    r=Routes({1:101});r.declare(declaration(2,3));r.declare(declaration(3,2))
    assert r.resolve(2)==(None,'cycle')
    r.declare(declaration(9,4))
    assert r.resolve(4)==(None,'unknown_ancestry')


def test_numeric_entity_reference_preserves_paths_and_never_promotes_causality():
    ds=[declaration(1,2),declaration(2,3),declaration(4,5)]
    fields=[dict(entity=3,offset=10,size=4,value=5,hash='unknown')]
    result=analyze(fields,ds,{1:101,4:404},404,0)
    assert result['fields_by_ancestry_depth']=={'2':1}
    assert len(result['incoming_numeric_candidates'])==1
    assert result['credited_victim_uid'] is None and result['causal_actor_uid'] is None
    assert closure({1:101,4:404},ds)=={1,2,3,4,5}
