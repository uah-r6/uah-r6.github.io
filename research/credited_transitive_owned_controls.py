"""Consumed declared component ancestry; numeric references are not causality.

Expands the previous direct-owner scope using only explicit latest declarations.
Unknown ancestry, cycles and shared parents refuse. No objective/player enum or
action-start/default replay decoder is changed.
"""
from collections import defaultdict
import json
from pathlib import Path

from credited_owned_property_controls import fixed_selection, TYPED, GO
from credited_late_history_development import immutable_write
from credited_round_dataset import read
from objective_player_component_fields import primitive_fields, owners_and_slots
from v3_final_reserve import ROOT,sha,source_sha

DATA=ROOT/'data/research/credited-transitive-owned-controls-v1'


class Routes:
    def __init__(self, roots):
        self.roots=roots;self.latest={};self.parents=defaultdict(dict)

    def declare(self,d):
        key=(d['owner'],d['slot_hash']);old=self.latest.get(key)
        if old:self.parents[old['component']].pop(key,None)
        self.latest[key]=d
        if d['component'] and d['class_hash']!='00000000':self.parents[d['component']][key]=d

    def resolve(self,entity,seen=None):
        seen=set() if seen is None else seen
        if entity in seen:return None,'cycle'
        if entity in self.roots:
            if self.parents[entity]:return None,'uid_root_has_competing_declared_parent'
            return dict(root=entity,uid=self.roots[entity],path=[]),'exact_uid_root'
        parents=list(self.parents[entity].values())
        if len(parents)!=1:return None,'shared_parent' if parents else 'unknown_ancestry'
        d=parents[0];prior,why=self.resolve(d['owner'],seen|{entity})
        if prior is None:return None,why
        return prior|dict(path=prior['path']+[d]),'single_declared_ancestry_only'


def closure(roots,declarations):
    nodes=set(roots)
    changed=True
    while changed:
        changed=False
        for d in declarations:
            if d['owner'] in nodes and d['component'] and d['component'] not in nodes:
                nodes.add(d['component']);changed=True
    return nodes


def analyze(fields,declarations,roots,target_uid,action_start):
    routes=Routes(roots);ds=iter(sorted(declarations,key=lambda d:d['offset']));next_d=next(ds,None)
    refs=[];counts=defaultdict(int);refusals=defaultdict(int)
    for f in sorted(fields,key=lambda f:f['offset']):
        while next_d is not None and next_d['offset']<=f['offset']:
            routes.declare(next_d);next_d=next(ds,None)
        if f['offset']<=action_start:continue
        owner,why=routes.resolve(f['entity'])
        if owner is None:refusals[why]+=1;continue
        depth=len(owner['path']);counts[str(depth)]+=1
        if type(f['value']) is not int or f['size'] not in (4,8):continue
        target=None
        if f['size']==8 and f['value']==target_uid:target={'uid':target_uid,'path':[],'method':'exact_uint64_uid_value'}
        elif 0<f['value']<=0xffffffff:
            r,_=routes.resolve(f['value'])
            if r and r['uid']==target_uid:target=r|{'method':'exact_numeric_declared_entity_value'}
        if target and owner['uid']!=target_uid:
            refs.append(dict(field=f,source_route=owner,target_route=target,interpretation='numeric_reference_candidate_only_not_damage_or_credit'))
    return dict(fields_by_ancestry_depth=dict(counts),refusal_counts=dict(refusals),incoming_numeric_candidates=refs,
        credited_victim_uid=None,causal_actor_uid=None,limits='Explicit declared ancestry and numeric equality only; property semantics unknown, prefix scope bounded, no actual event timing')


def main():
    selection=fixed_selection()
    reservation=dict(base_commit='b1023d4',selection=selection,source_hashes={n:source_sha(ROOT/n) for n in
        ('research/credited_transitive_owned_controls.py','research/objective_player_component_fields.py')},
        hypothesis='Direct-owner absence may miss declared transitive components; numeric incoming refs remain hypotheses, never damage/credit proof')
    immutable_write(DATA/'reservation.json',reservation);records=[]
    lifecycle=read(ROOT/'data/research/credited-history-lifecycle-controls/sample-74.json')['records']
    for s in selection:
        replay=s['replay_sha256'];typed=read(TYPED/'records'/(replay+'.json'));dump=ROOT/typed['dump_path']
        if sha(dump)!=typed['dump_sha256']:raise ValueError('Cached source buffer differs')
        header=read(GO/'headers'/(replay+'.json'))['header']
        previous=next(r for r in lifecycle if r['replay_sha256']==replay)
        state_paths=[n for n in previous['inputs'] if n.startswith('data/research/diagnostics/state-components/')]
        if len(state_paths)!=1:raise ValueError('Exact sealed lifecycle state input required')
        state_path=ROOT/state_paths[0]
        if sha(state_path)!=previous['inputs'][state_paths[0]]:raise ValueError('Original lifecycle state differs')
        state=read(state_path)
        names={p['username']:p['id'] for p in header['players']}
        if {(p['username'],p['id']) for p in state['header']['players']}!=set(names.items()):raise ValueError('Exact header state identity differs')
        owners,_=owners_and_slots(state);roots={entity:names[name] for entity,name in owners.items()}
        target=names[s['observation']['player']]
        if len(roots)!=10 or len(set(roots.values()))!=10:raise ValueError('Ten unique exact UID roots required')
        nodes=closure(roots,state['declarations']);fields=primitive_fields(dump.read_bytes(),nodes)
        finding=analyze(fields,state['declarations'],roots,target,header['actionPhaseStartOffset'])
        row=s|dict(finding=finding,potential_declared_entities=len(nodes),direct_uid_roots=len(roots),
            inputs={state_path.relative_to(ROOT).as_posix():sha(state_path),typed['dump_path']:typed['dump_sha256']})
        immutable_write(DATA/'records'/(replay+'.json'),row);records.append(row)
        print(s['event'],s['map_id'],s['round'],s['observation']['player'],finding['fields_by_ancestry_depth'],
              'incoming',len(finding['incoming_numeric_candidates']),flush=True)
    immutable_write(DATA/'result.json',dict(records=records,credited_identity_promoted=False))


if __name__=='__main__':main()
