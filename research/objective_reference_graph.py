"""Discovery-only reference graph; paths are not ownership or actor evidence.

Only contiguous typed uint64 references with a zero high word are considered.
Latest values are retained by source/property before each plant state. This
tests a broader structural join than the previously unsuccessful owner hash.
"""
import argparse
from collections import defaultdict, deque
import json

from objective_encoding_probe import dump_round, inherited_state_events
from objective_transition_probe import ROOT


def references(data):
    result = {}
    cursor = 0
    while (start:=data.find(b'\x23',cursor))>=0:
        cursor=start+1
        if start+14>len(data) or data[start+5:start+9]!=bytes(4): continue
        source=int.from_bytes(data[start+1:start+5],'little')
        at=start+9
        while at+5<len(data):
            size=data[at+4]
            if size not in (1,2,4,8) or at+5+size>len(data): break
            if size==8:
                raw=data[at+5:at+13]
                target=int.from_bytes(raw,'little')
                # Zero/deleted links are retained to invalidate older edges.
                result[at]={'offset':at,'source':source,'hash':data[at:at+4].hex(),
                            'target':target if target<=0xffffffff else None}
            end=at+5+size
            if end>=len(data) or data[end]!=0x22: break
            at=end+1
    return [result[k] for k in sorted(result)]


def paths_before(refs, state, players):
    latest={}
    for ref in refs:
        if ref['offset']>=state['offset']: break
        latest[(ref['source'],ref['hash'])]=ref
    graph=defaultdict(list)
    for edge in latest.values():
        if not edge['target']: continue
        graph[edge['source']].append((edge['target'],edge))
        graph[edge['target']].append((edge['source'],edge))
    queue=deque([(state['entity'],[])])
    seen={state['entity']}; hits=[]
    while queue:
        node,path=queue.popleft()
        if node in players: hits.append({'players':players[node],'path':path})
        if len(path)>=3: continue
        for target,edge in graph[node]:
            if target not in seen:
                seen.add(target);queue.append((target,path+[edge]))
    return {'adjacent_edges':graph[state['entity']],'player_paths':hits,
            'reachable_entities_within_3_edges':len(seen)}


def declaration_contexts(data, entity):
    """Uninterpreted component-declaration context, not a proven owner link."""
    pattern=entity.to_bytes(8,'little');cursor=0;result=[]
    while (at:=data.find(pattern,cursor))>=0:
        cursor=at+8
        if at<13 or at+12>len(data) or data[at-13]!=0x1b or data[at-8:at-4]!=bytes(4):continue
        result.append({'offset':at,'container_candidate':int.from_bytes(data[at-12:at-4],'little'),
                       'prefix_hash':data[at-4:at].hex(),'suffix_hash':data[at+8:at+12].hex()})
    return result


def main():
    parser=argparse.ArgumentParser();parser.add_argument('cases',nargs='+');args=parser.parse_args()
    for case in args.cases:
        mid,number=map(int,case.split(':'));data,row=dump_round(mid,number)
        names=json.loads((ROOT/f'data/research/diagnostics/defuser-ids-{mid}.json').read_text(encoding='utf-8-sig'))[row['physical_file']]
        players=defaultdict(list)
        for name,encoded in names.items(): players[int.from_bytes(bytes.fromhex(encoded),'little')].append(name)
        refs=references(data); states=inherited_state_events(data)
        results=[{'state':state,**paths_before(refs,state,players),
                  'declaration_contexts':declaration_contexts(data,state['entity'])} for state in states]
        output={'match_id':mid,'round':number,'reference_updates':len(refs),'states':results}
        path=ROOT/f'data/research/diagnostics/objective-encoding/{mid}-R{number:02d}-reference-graph.json'
        path.write_text(json.dumps(output,indent=2));print(json.dumps(output))


if __name__=='__main__': main()
