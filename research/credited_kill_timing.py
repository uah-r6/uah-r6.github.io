"""Packet chronology for the previously independently filmed Stk DBNO case."""
from bisect import bisect_right
import json

from objective_score_structure import observe
from uah_guarded_actor_readonly import snapshot
from v3_final_reserve import ROOT, sha


def main():
    protected=snapshot()
    audit_path=ROOT/'data/research/diagnostics/v3-sal-kill-credit/8580.json'
    body_path=ROOT/'data/research/diagnostics/consumed-stk-dbno-body-reference.json'
    round_=json.loads(audit_path.read_text(encoding='utf-8'))['rounds'][5]
    body=json.loads(body_path.read_text(encoding='utf-8'))
    files=[p for p in (ROOT/'data/research/extracted/v3-corrected-final-sal-8580').rglob(round_['filename']) if p.parent.name==round_['folder']]
    if len(files)!=1 or sha(files[0])!=round_['replay_sha256']: raise ValueError('Consumed replay changed')
    clock=[f for f in observe(files[0])['fields'] if f['kind']=='clock' and f['value']<=600]
    offsets=[f['offset'] for f in clock]; events=[]
    for s in body['body_states']:
        events.append(dict(offset=s['offset'],kind='Stk body',value=s['raw_state'],health=s['health']))
    for row in round_['counter_rows']:
        if row['player']=='Kheyze.TLAW' and row['counter']=='kills' or row['player']=='Maia.TLAW' and row['counter']=='assists':
            events.append(dict(offset=row['offset'],kind=row['player']+' '+row['counter'],value=row['value']))
    for f in round_['feed']:
        if f['feedback'].get('target') in ('Stk.INTZ','Kheyze.TLAW'):
            events.append(dict(offset=f['offset'],kind='Raw elimination',value=f['feedback']['username']+' -> '+f['feedback']['target']))
    for event in events:
        i=bisect_right(offsets,event['offset'])-1
        event['preceding_clock']=clock[i]['value'] if i>=0 else None
        event['preceding_clock_offset']=clock[i]['offset'] if i>=0 else None
    events.sort(key=lambda e:e['offset'])
    result=dict(status='consumed_independently_filmed_case_packet_chronology',events=events,
        sources={audit_path.relative_to(ROOT).as_posix():sha(audit_path),body_path.relative_to(ROOT).as_posix():sha(body_path)},
        replay_sha256=sha(files[0]),protected_hashes=protected,
        conclusion='Kheyze counter5->6 at74275879; Stk independently observed DBNO raw3 at74255864; eliminated raw4 at74275897; Maia finish74276292. Increment is serialized with final elimination, not at the earlier DBNO transition in this case. Packet serialization order is not server causality or subsecond clock precision. No generic credited victim/downer event mapping.')
    target=ROOT/'data/research/credited-kills-v1/timing-stk.json'
    target.parent.mkdir(parents=True,exist_ok=True);target.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    lines=['# Current Y11 credited-kill increment timing — consumed Stk case','',
        'The [official SAL broadcast review](v3-consumed-dbno-vod-review.md) independently shows Stk downed, '
        'Kheyze dead before gaining the kill, and Maia finishing Stk while gaining an assist. '
        'This packet chronology uses that previously reviewed case; it does not infer a credited victim from the nearest counter.','',
        '| Packet offset | Latest serialized clock (seconds) | Observation | Value |', '| ---: | ---: | --- | --- |']
    for e in events: lines.append(f"| {e['offset']} | {e['preceding_clock']} | {e['kind']} | {e['value']} |")
    lines+=['',result['conclusion'],'',
        'The counter retains5 until the observed update to6. That update is18bytes before the eliminated body state '
        'and413bytes before the feed finish; it is20,015bytes after the independently supported downed transition. '
        'Byte distance is not elapsed time. Coarse clock ticks annotate observations only. No direct downer ID '
        'was found in the earlier narrow owned-field probe; downer/DBNO time remains unavailable for generic runtime events.', '',
        'A credited counter observation is a player/round count plus packet offset. It is not an opening, trade '
        'window start, victim mapping or simulated alive-state kill event. Production event features remain unchanged.', '']
    (ROOT/'research/output/credited-kill-timing.md').write_text('\n'.join(lines),encoding='utf-8')
    if snapshot()!=protected: raise ValueError('Protected state changed')
    print(result['conclusion'])


if __name__=='__main__':main()
