"""Append independent HUD evidence; leave frozen body/actor rules unchanged."""
import json

from v3_consumed_cohort_integrity import sealed_sal_cache, PERMANENT_RESULTS
from v3_consumed_apac_credit_probe import sealed_apac_cache
from v3_final_reserve import ROOT, sha
from uah_guarded_actor_readonly import snapshot


def main():
    protected=snapshot();sealed_sal_cache();sealed_apac_cache()
    video=ROOT/'data/research/video/sal-20260905'
    metadata=json.loads((video/'8580.info.json').read_text())
    if (metadata['id'],metadata['channel_id'],metadata['upload_date']) != (
            'Ao6SRRhCmbg','UCWKHac5bjhsUtSnMDFCT-7A','20260905'):
        raise ValueError('Official broadcast provenance differs')
    inventory=ROOT/'data/research/diagnostics/consumed-unknown-body-inventory.json'
    case=next(r for r in json.loads(inventory.read_text())['records'] if r['official_match_id']==8581)
    if case['timer_owner_observation']!='kds.FaZe' or case['context']['body_values']!=[0,1]:
        raise ValueError('Consumed unknown-body replay case changed')
    health=ROOT/'data/research/diagnostics/consumed-body-state1-health.json'
    state=next(p for p in json.loads(health.read_text())['state1_properties'] if (
        p['official_match_id'],p['logical_round'],p['player'])==(8581,6,'kds.FaZe'))
    values=state['numerical']
    if (values['health'],values['baseline_field'],values['ceiling_field'])!=(120,100,120):
        raise ValueError('Recorded positive-bonus state differs')
    observations={
        8457:'Villa R06, score2-3, clock1:34. KDS alive before plant. NearZ independently displays DBNO cross.',
        8458:'Clock1:33. KDS card becomes yellow and explicitly says Planting the Defuser.',
        8460:'Clock1:31. KDS still Planting the Defuser; blue circular boost indicators appear above all five Attack cards. NearZ still has DBNO cross.',
        8463:'Clock1:28. KDS still Planting the Defuser, blue boost indicator present; no KDS DBNO/death indicator.',
        8464:'Clock1:27. KDS still Planting the Defuser with blue boost indicator.',
        8465:'Global DEFUSER IS PLANTED banner and44.77postplanttimer appear. KDS card leaves planting state and remains alive/boosted. Camera remains xSexyCake, not KDS.'}
    frames=[dict(seconds=s,filename=f'8580-{s}-299.jpg',sha256=sha(video/f'8580-{s}-299.jpg'),observation=o)
            for s,o in observations.items()]
    record=dict(status='consumed_separate_current_y11_hud_review_no_actor_or_rating_change',
                official_match_id=8581,map='Villa',round=6,video_url='https://www.youtube.com/watch?v=Ao6SRRhCmbg&t=8458s',
                channel=metadata['channel'],upload_date=metadata['upload_date'],metadata_sha256=sha(video/'8580.info.json'),
                frames=frames,inventory_sha256=sha(inventory),numerical_audit_sha256=sha(health),replay_case=case,
                positive_state=state,classification='Known timer owner is actively planting under visible boost; state1 is not a valid reason to declare this case inactive',
                limitations='HUD independently identifies planting player and global completion, not a close-up of planting hands. '
                            'Numeric120HP comes from replay; broadcast does not show a numeric KDS HP value. '
                            'The review establishes one bonus-health plant case, not a universal enum mapping or fresh validation.',
                permanent_results=PERMANENT_RESULTS,protected_hashes=protected)
    path=ROOT/'data/research/diagnostics/bonus-body-vod-review.json'
    if path.exists():
        if json.loads(path.read_text())!=record:raise ValueError('Preserved independent HUD review changed')
    else:path.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    lines=['# Current Y11 HUD review: bonus-health planter false abstention','',
           '[Official SAL Stage2 Day1 broadcast, 8458 seconds](https://www.youtube.com/watch?v=Ao6SRRhCmbg&t=8458s), '
           'Rainbow Six Esports, uploaded2026-09-05. Consumed match8581/FaZe-Imperial, Villa physicalR06.', '',
           '| VOD seconds | Independently visible HUD evidence |','| ---: | --- |']
    lines += [f'| {s} | {o} |' for s,o in observations.items()]
    c=case['context']
    lines += ['', '## Replay evidence and conclusion', '',
              f"Unique timer owner KDS numericUID`{case['timer_uid']}`, body component`{case['body_declaration']['component']}`. "
              f"Verified plant offset`{c['plant_offset']}`, interaction`{c['start']}`–`{c['end']}` with explicit state2 terminal. "
              'No body route replacement/sharing, prior actor death, all-opponents-dead interruption or competing completer.', '',
              f"Body state0→1 at offset`{state['state_offset']}`. Same declared component has120HP, observed100baseline/120ceiling "
              f"and positive fraction`{values['bonus_fraction']}`. The production guard rejects state1 and remains unchanged.", '',
              'The HUD identifies KDS actively planting while boosted and global completion follows. This independently '
              'supports a false abstention in this case. It is an explicit HUD association, not camera-subject attribution. '
              'The camera follows xSexyCake; the replay supplies numeric HP, which is not visually readable on KDS’s card. '
              'Do not call it direct close-up visual verification or universal state1 semantics.', '',
              'Next: isolated consumed-data candidate accepting state1 only with structurally validated positive bonus '
              'health, full temporal UID/body identity and all existing occurrence/episode/cancellation/liveness guards. '
              'Run broad negative controls and separately freeze unused actor validation before any production change. '
              'Keep original SAL/APAC exclusions, predictions and permanent failed Rating results unchanged.', '',
              'No production body enum, operator/action logic, Rating formula/default, SQLite, archive or public JSON change. '
              'Both frozen source checks, both failed final hashes and all86protected live hashes remain unchanged. No push/publish.', '']
    (ROOT/'research/output/v3-bonus-body-vod-review.md').write_text('\n'.join(lines),encoding='utf-8')
    if snapshot()!=protected:raise ValueError('Protected live files changed')
    print('Independent KDS planting/boost HUD review preserved; no actor rule change',flush=True)


if __name__=='__main__':main()
