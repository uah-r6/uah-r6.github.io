"""Additive official HUD corroboration; do not revise sealed input/results."""
import json

from uah_guarded_actor_readonly import snapshot
from v3_final_reserve import ROOT, sha, source_sha


def main():
    protected=snapshot();directory=ROOT/'data/research/video/sal-opening-order-20261003'
    meta=json.loads((directory/'Day1.info.json').read_text(encoding='utf-8'))
    if (meta['id'],meta['upload_date'],meta['channel_id'])!=('Ao6SRRhCmbg','20260905','UCWKHac5bjhsUtSnMDFCT-7A'):
        raise ValueError('Official broadcast provenance differs')
    observations={
        15122:'Round3, score1-1, action clock0:43; 5v5, all ten observer cards alive; no death feed.',
        15130:'Round3, action clock0:35; 5v5; live LOUD observer card shows Planting Defuser.',
        15133:'Round3, action clock0:32; sampled instant still5v5; live LOUD Planting Defuser.',
        15135:'Round3, action clock0:30;4v5; feed Gabu7z.LOUD -> pino.L5; pino dead card1/2/2, Gabu2/2/0.',
        15140:'Round3, postplant clock41.19; DEFUSER IS PLANTED;3v4; feed Neskin.L5 -> Flastryy.LOUD above stemp.LOUD -> WIZARD.L5. pino/WIZARD/Flastryy dead, Neskin3/1/1.'}
    frames=[dict(seconds=s,path=(directory/f'Day1-{s}-299.jpg').relative_to(ROOT).as_posix(),
                 sha256=sha(directory/f'Day1-{s}-299.jpg'),observation=observation)
            for s,observation in observations.items()]
    old_path=ROOT/'data/research/diagnostics/v3-sal-kill-credit/8583.json'
    r=json.loads(old_path.read_text(encoding='utf-8'))['rounds'][2]
    feed=[dict(offset=e['offset'],finisher=e['feedback']['username'],victim=e['feedback']['target'],clock=e['feedback']['time']) for e in r['feed']]
    record=dict(status='consumed_separate_hud_clock_epoch_control_no_runtime_change',
        official_match_id=8583,map='Clubhouse',round=3,video_url='https://www.youtube.com/watch?v=Ao6SRRhCmbg',
        title=meta['title'],channel_id=meta['channel_id'],upload_date=meta['upload_date'],
        metadata_sha256=sha(directory/'Day1.info.json'),frames=frames,raw_events=feed,
        original_credit_audit_sha256=sha(old_path),helper_sha256=source_sha(ROOT/'research/credited_opening_hud_review.py'),
        protected_hashes=protected,limits='Sparse independently inspected frames show relative final-death order and countdown phase change. They do not identify unseen DBNO downers, resolve remaining pino/Neskin map opening-owner discrepancies, or supply subsecond event times.')
    out=ROOT/'data/research/credited-kills-v1/opening-hud-8583.json'
    if out.exists() and json.loads(out.read_text(encoding='utf-8'))!=record:raise ValueError('Never overwrite changed consumed HUD review')
    out.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    lines=['# Official HUD control: preplant and postplant opening order','',
        '[Official SAL Stage2 Day1 broadcast](https://www.youtube.com/watch?v=Ao6SRRhCmbg&t=15122s), '
        'upload20260905, RainbowSixEsports channel. This is a separate consumed observation after the '
        'credited-count checkpoint `eeca495`; it does not revise that checkpoint or any frozen final.', '',
        '| Video seconds | Independently inspected HUD |', '| ---: | --- |']
    for s,observation in observations.items():lines.append(f'| {s} | {observation} |')
    lines+=['','The first observed final elimination is Gabu ->pino before planting, while Neskin ->Flastryy '
        'appears after defuser completion/reset. The raw packet order agrees. Original feedback records action0:32 '
        'for the first event and postplant0:43 for Neskin ->Flastryy. Sorting all round events by remaining seconds '
        'reverses those two phases. This case supports a clock-epoch/order explanation, not a DBNO time claim.', '',
        'Preserve raw finisher/victim/packet order and countdown provenance. A future elapsed-time/trade path must '
        'recognize a independently verified plant reset rather than subtract two remaining values across phases. '
        'No live opening/trade/pivot/clutch/KOST/Rating source changes; no historical correction or export.', '',
        'Still unresolved: the separate map-level opening kill ownership difference pino vsNeskin. These frames '
        'verify round3 order but do not explain that residual across other rounds. No credited victim is assigned '
        'by nearest counter, aggregate total or camera-subject identity.', '']
    (ROOT/'research/output/credited-kill-opening-hud.md').write_text('\n'.join(lines),encoding='utf-8')
    if snapshot()!=protected:raise ValueError('Protected state changed')
    print('Independent pre/postplant death-order HUD control preserved; no event-feature migration')


if __name__=='__main__':main()
