"""Read-only test of upstream's numeric-player-ID/entity ownership lead.

Prior art: wnc-replay/replay-tool dissect/movement.go buildEntityMap.
This diagnostic retains competing matches; it never chooses an objective actor.
No public names/targets are used as inputs.
"""
import argparse
from collections import defaultdict
import json

from objective_encoding_probe import dump_round, inherited_state_events
from objective_production_check import candidate_raw
from objective_reference_graph import references, paths_before
from objective_transition_probe import ROOT, replay_file


def ownership_candidates(data, players):
    results=[]
    for p in players:
        identity=p.get('id')
        if not identity: continue
        pattern=int(identity).to_bytes(8,'little');cursor=0
        while (at:=data.find(pattern,cursor))>=0:
            cursor=at+8
            for flag in range(at+8,min(at+19,len(data)-9)):
                if data[flag:flag+2] not in (b'\x01\xff',b'\x02\xff'):continue
                raw=data[flag+2:flag+10]
                if raw[3]!=0xf0 or raw[4:]!=bytes(4):continue
                results.append({'player':p['username'],'player_id':identity,'offset':at,
                    'flag_offset':flag,'flag':data[flag],'entity':int.from_bytes(raw,'little'),
                    'source':'upstream_adjacent_ref_candidate'})
    return results


def typed_table_candidates(data, players):
    """Exploratory 4139 R07 table shape, not a general identity resolver.

    UID64, f9 01, index, flag/ff, field index, 04, ref64. This shape was
    inspected after the upstream adjacency rule returned no candidates.
    """
    result=[]
    for player in players:
        if not player.get('id'):continue
        uid=int(player['id']).to_bytes(8,'little');cursor=0
        while (at:=data.find(uid,cursor))>=0:
            cursor=at+8;tail=data[at+8:at+23]
            if (len(tail)!=15 or tail[:2]!=b'\xf9\x01' or
                    tail[3:5] not in (b'\x01\xff',b'\x02\xff') or
                    tail[6]!=4 or tail[10]!=0xf0 or tail[11:15]!=bytes(4)):
                continue
            result.append({'player':player['username'],'player_id':player['id'],'offset':at,
                           'entity':int.from_bytes(tail[7:15],'little'),
                           'index':tail[2],'field_index':tail[5],
                           'source':'exploratory_typed_table_candidate'})
    return result


def spawn_evidence(data, entities):
    """Keep entity class evidence so owned drones are not treated as bodies."""
    result=defaultdict(list);cursor=0
    while (at:=data.find(bytes.fromhex('617385fe'),cursor))>=0:
        cursor=at+4
        if at<12 or at+12>len(data):continue
        entity=int.from_bytes(data[at-12:at-8],'little')
        if entity in entities and data[at+4:at+12]==entity.to_bytes(8,'little'):
            result[entity].append({'offset':at,'counter':int.from_bytes(data[at-4:at],'little')})
    return dict(result)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('cases',nargs='+');args=parser.parse_args()
    for case in args.cases:
        mid,number=map(int,case.split(':'));rec,_=replay_file(mid,number)
        raw=candidate_raw(rec.parent);row=raw['rounds'][number-1];header=row.get('header',row)
        data,_=dump_round(mid,number);candidates=ownership_candidates(data,header['players'])
        candidates+=typed_table_candidates(data,header['players'])
        players=defaultdict(list)
        for c in candidates:
            if c['player'] not in players[c['entity']]:players[c['entity']].append(c['player'])
        refs=references(data); states=inherited_state_events(data)
        output={'match_id':mid,'round':number,'players_with_numeric_id':sum(bool(p.get('id')) for p in header['players']),
                'candidates':candidates,'entity_players':dict(players),
                'spawn_evidence':spawn_evidence(data,set(players)),
                'state_paths':[{'state':s,**paths_before(refs,s,players)} for s in states]}
        destination=ROOT/f'data/research/diagnostics/objective-encoding/{mid}-R{number:02d}-player-entities.json'
        destination.write_text(json.dumps(output,indent=2))
        print(json.dumps({k:v for k,v in output.items() if k!='candidates'}))


if __name__=='__main__':main()
