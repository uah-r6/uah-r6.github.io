"""Independent official HUD order control on already consumed Bank8594R07."""
import json
from pathlib import Path

from uah_guarded_actor_readonly import snapshot
from v3_final_reserve import ROOT, sha, source_sha


def main():
    protected = snapshot()
    directory = ROOT / 'data/research/video/sal-opening-order-20261003'
    metadata = directory / 'Day3.info.json'
    meta = json.loads(metadata.read_text(encoding='utf-8'))
    if (meta['id'], meta['upload_date'], meta['channel_id']) != (
            '4Qxi72CtGNA', '20260912', 'UCWKHac5bjhsUtSnMDFCT-7A'):
        raise ValueError('Official broadcast provenance differs')
    observations = {
        18624: 'R07, score2-4, action6.99,5v5; Bassetto planting; cyber visibly downed; no final-death feed.',
        18626: 'R07, action4.99,4v5; sole feed vitaking.FaZe -> Bassetto.L5; Bassetto dead0/5/0, vitaking4/2/2; no plant completion.',
        18630: 'R07, action0.97,2v3 on transition; feed ordered oldest-first vitaking->Bassetto, vitaking->PSYCHO, pino->kds, soulz1->pino, Neskin->vitaking, Neskin->cyber; WIZARD planting.',
        18635: 'R07, action0.00 with planting overtime,2v2; WIZARD still planting; Handyy7/2/1, Neskin alive4/5/3.',
        18640: 'R07, postplant41.92, DEFUSER IS PLANTED,1v2; feed Handyy.FaZe -> Neskin.L5; Handyy8/2/1, Neskin dead4/6/3.',
        18643: 'R07, postplant38.92,1v2; same Handyy->Neskin feed and completed plant banner.',
    }
    frames = [dict(seconds=s, path=(directory / f'Day3-{s}-299.jpg').relative_to(ROOT).as_posix(),
                   sha256=sha(directory / f'Day3-{s}-299.jpg'), observation=o)
              for s, o in observations.items()]
    source = ROOT / 'data/research/diagnostics/v3-sal-kill-credit/8594.json'
    row = json.loads(source.read_text(encoding='utf-8'))['rounds'][6]
    record = dict(status='consumed_independent_pre_postplant_order_control_no_runtime_change',
        official_match_id=8594, map='Bank', round=7,
        video_url='https://www.youtube.com/watch?v=4Qxi72CtGNA&t=18624s',
        channel_id=meta['channel_id'], upload_date=meta['upload_date'],
        metadata_sha256=sha(metadata), frames=frames, original_audit_sha256=sha(source),
        raw_events=row['feed'], helper_sha256=source_sha(Path(__file__)), protected_hashes=protected,
        limits='Independent observed final-death order/countdown phases only. Replay coarse seconds6 and42 are from different clocks. Frames do not establish a generic credited-victim/downer relation or precise trade timing; no production feature change.')
    destination = ROOT / 'data/research/credited-kills-v1/opening-hud-8594.json'
    if destination.exists() and json.loads(destination.read_text(encoding='utf-8')) != record:
        raise ValueError('Never overwrite changed consumed HUD review')
    destination.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    lines = ['# Independent Bank preplant/postplant order control', '',
        '[Official SAL Stage2 Day3 broadcast](https://www.youtube.com/watch?v=4Qxi72CtGNA&t=18624s). '
        'This separate consumed review preserves the earlier credited-count and opening-order seals.', '',
        '| Video second | Independently inspected HUD |', '| ---: | --- |']
    lines.extend(f'| {s} | {o} |' for s, o in observations.items())
    lines += ['', 'Raw packet order records vitaking ->Bassetto first at91880758/action0:06, while '
        'Handyy ->Neskin is later at91938582/postplant0:42. The official broadcast independently '
        'corroborates that order and clock reset. A round-wide decreasing-seconds sort wrongly puts '
        'Handyy first. Both changed SAL rounds now have independent preplant/postplant HUD controls.', '',
        'Action0.00 persists during planting overtime; an elapsed-time/trade model must represent that '
        'interval as well as the postplant reset. Sparse screenshots are not subsecond synchronization. '
        'Packet ordering suffices for final-death order in these two cases, but cannot by itself identify '
        'the credited owner or DBNO-causing player of every final death.', '',
        'No live opening/trade/pivot/clutch/KOST/Rating change, database write, corrected public export '
        'or regrading of any historical final. A universal opening-credit policy still needs explicit '
        'identity-linked DBNO/death evidence, particularly when competing downs precede deaths.', '']
    (ROOT / 'research/output/credited-kill-opening-bank-hud.md').write_text('\n'.join(lines), encoding='utf-8')
    if snapshot() != protected:
        raise ValueError('Protected state changed')
    print('Independent Bank clock-reset/order corroboration preserved; production event logic unchanged')


if __name__ == '__main__':
    main()
