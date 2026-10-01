"""Discovery join through explicit component declaration and numeric identity.

This does not establish objective attribution. Names come only from parser
headers; public objective names are never inputs to the join.
"""
from collections import defaultdict


def score_identity_candidates(data, players):
    uid_names=defaultdict(set)
    for p in players:
        if p.get('id'):uid_names[int(p['id'])].add(p['username'])
    controller_names=defaultdict(set)
    cursor=0;tag=bytes.fromhex('eed445c8')
    while (at:=data.find(tag,cursor))>=0:
        cursor=at+4
        if at<9 or at+13>len(data) or data[at-9]!=0x23 or data[at-4:at]!=bytes(4) or data[at+4]!=8:continue
        uid=int.from_bytes(data[at+5:at+13],'little')
        names=uid_names.get(uid,set())
        if len(names)==1:controller_names[int.from_bytes(data[at-8:at-4],'little')].update(names)
    result=defaultdict(set);evidence=[];cursor=0;tag=bytes.fromhex('eb219b38')
    while (at:=data.find(tag,cursor))>=0:
        cursor=at+4
        if (at<9 or at+16>len(data) or data[at-9]!=0x1b or data[at-4:at]!=bytes(4)
                or data[at+8:at+12]!=bytes(4) or data[at+12:at+16]!=bytes.fromhex('18a591a1')):continue
        controller=int.from_bytes(data[at-8:at-4],'little')
        component=int.from_bytes(data[at+4:at+8],'little')
        names=controller_names.get(controller,set())
        if len(names)==1:
            result[component].update(names)
            evidence.append({'offset':at,'controller':controller,'score_component':component,'names':sorted(names)})
    return {'entity_names':{str(k):sorted(v) for k,v in result.items()},'evidence':evidence,
            'controllers':{str(k):sorted(v) for k,v in controller_names.items()}}
