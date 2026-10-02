"""Append independent broadcast evidence; never relabel frozen Rating data."""
import json

from v3_corrected_final_pipeline import DATA, RESULT, ROOT, sha
from uah_guarded_actor_readonly import snapshot


def main():
    protected, permanent = snapshot(), sha(RESULT)
    directory = ROOT/'data/research/video/sal-20260905'
    meta = json.loads((directory/'8580.info.json').read_text())
    if (meta['id'],meta['upload_date'],meta['channel_id']) != ('Ao6SRRhCmbg','20260905','UCWKHac5bjhsUtSnMDFCT-7A'):
        raise ValueError('Independent broadcast provenance differs')
    observations = {
        3484: 'R06, score4-1, clock1:03. Stk INTZ has the DBNO cross on his observer card. Kheyze has5kills/3deaths/5assists; Maia6/3/0.',
        3485: 'Clock1:02. Stk cross remains visible; observer main perspective is Ar7hr. Kheyze5/3/5, Maia6/3/0.',
        3486: 'Clock1:01. Feed displays AngelzZ INTZ eliminates Kheyze TLAW. Kheyze card becomes5/4/5; Stk still DBNO. Maia6/3/0.',
        3487: 'Clock1:00. Stk card transitions to dead. Kheyze card now6/4/5 while already dead; Maia remains6/3/0 at this sampled instant.',
        3488: 'Clock0:59. Feed displays Maia TLAW eliminates Stk INTZ. Maia card6/3/1: killsunchanged, assistincreases. Kheyze card6/4/5.',
        3500: 'Clock0:47. Maia6/3/1, Kheyze6/4/5, Stk1/6/0 confirm persistent scoreboard values.'}
    frames = [dict(seconds=sec,filename=f'8580-{sec}-'+('298' if sec==3500 else '299')+'.jpg',observation=text)
              for sec,text in observations.items()]
    for frame in frames:
        frame['sha256'] = sha(directory/frame['filename'])
    evidence = json.loads((ROOT/'data/research/diagnostics/v3-sal-kill-credit/8580.json').read_text())
    round_ = next(r for r in evidence['rounds'] if r['logical_round']==6)
    if not round_['full_counter_binding']:
        raise ValueError('Independent direct-UID counter evidence unavailable')
    maia, kheyze = round_['players']['Maia.TLAW'],round_['players']['Kheyze.TLAW']
    if (maia['delta'],maia['feed_finishes'],kheyze['delta'],kheyze['feed_finishes']) != (0,1,1,0):
        raise ValueError('Consumed replay case differs from reviewed broadcast')
    kill = next(e for e in round_['feed'] if e['feedback'].get('username')=='Maia.TLAW')
    if kill['feedback']['target'] != 'Stk.INTZ':
        raise ValueError('Displayed finisher victim differs')
    record = dict(status='consumed_separate_broadcast_review_no_frozen_relabel',official_match_id=8580,
                  physical_file=round_['filename'],replay_sha256=round_['replay_sha256'],round=6,
                  video_url='https://www.youtube.com/watch?v=Ao6SRRhCmbg',title=meta['title'],
                  channel=meta['channel'],channel_url=meta['channel_url'],upload_date=meta['upload_date'],
                  metadata_cache_sha256=sha(directory/'8580.info.json'),frames=frames,
                  replay_counter_rows=[r for r in round_['counter_rows'] if r['player'] in ('Maia.TLAW','Kheyze.TLAW')],
                  feed_event=kill,classification='Current Y11 displayed finisher differs from scoreboard kill credit',
                  limits='Sparse sampled frames; direct downing shot by Kheyze is not visibly observed. No camera-subject identity inference. One current Y11 case independently reviewed, not every disputed kill in the dataset.',
                  permanent_result_sha256=permanent,metric_or_parser_change=False)
    (DATA/'consumed-dbno-vod-review.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    lines = ['# Independent current Y11 DBNO credit / finisher review', '',
             'Consumed SAL official8580/TLAW-INTZ Lair physicalR06. '
             'The official broadcast confirms that displayed finisher and credited-kill owner differ. '
             'The replay feedback correctly records the displayed finisher in this case. '
             'The current tracker counts these feed finishes as kills; those counts can differ from official credited kills. '
             'No normalized event, statistic, Rating feature, model or historical data is changed.', '',
             '## Independent visual evidence', '',
             '[Official Rainbow Six Esports SAL Stage2 Day1 broadcast](https://www.youtube.com/watch?v=Ao6SRRhCmbg&t=3484s), '
             'uploaded20260905. Exact cached frames and SHA256 provenance remain ignored.', '',
             '| Broadcast seconds | Observed UI |', '| ---: | --- |']
    for frame in frames:
        lines.append(f"| {frame['seconds']} | {frame['observation']} |")
    lines += ['', 'Stk is visibly DBNO before elimination. Maia appears as his finisher in the feed, '
              'but Maia gains an assist and no kill; Kheyze gains the kill while already dead. '
              'This demonstrates the credit/finisher split in current Y11. The particular downing shot is not visible '
              'in the sampled frames; the stronger claim that the camera directly shows Kheyze downing Stk is not made. '
              'One independently reviewed case does not visually adjudicate all43 map-count differences.', '',
              '## Replay evidence retained separately', '',
              f'Physical replay SHA256 `{round_["replay_sha256"]}`. Existing parser feed event at '
              f'{kill["offset"]}, clock{kill["feedback"]["time"]}: Maia.TLAW -> Stk.INTZ. '
              f'Direct declared scoreboard UID routes give Kheyze numericUID{kheyze["uid"]} '
              f'kill delta1, feed finishes0; Maia numericUID{maia["uid"]} kill delta0, feed finishes1. '
              'Counter ownership is established without public labels or matching a desired kill total. '
              'The separate full-map counter audit records exact raw offsets, owner/component references, '
              'initial/terminal counters and between-round continuity.', '',
              '## Methodology consequence', '',
              'Map-level exact K/D matching does not establish every round-level credited kill: '
              'Kheyze has one positive and one negative credit/finisher difference in R06/R13, canceling at map level. '
              'This limits the current research quality gate and can affect round-level multikill/KOST/opening inputs. '
              'The magnitude of those effects is not measured here; no per-victim credited event is guessed or reassigned.', '',
              'Historical [Ubisoft DBNO notes, August18,2021](https://www.ubisoft.com/en-us/game/rainbow-six/siege/news-updates/1YPQ5yw9TaRhQwghjStqn2) '
              'document a downing player receiving the kill credit while a teammate finisher is shown in the feed. '
              'The current broadcast independently corroborates the distinction rather than relying solely on historical notes.', '',
              'A future credited-kill study needs explicit stable UID counter ownership plus victim/event association '
              'and DBNO/revive/rehost evidence. Preserve finisher identity and death timing. Do not rewrite killer names '
              'from the last scoreboard update or use aggregate totals to choose identities. '
              'This is a data-definition limitation and a research next step, not an approved runtime correction.', '',
              f'Permanent failed SAL result SHA256 `{permanent}` and all{len(protected)} protected live hashes unchanged. '
              'No final refit, gate relaxation, import, public regeneration, push or publishing.', '']
    (ROOT/'research/output/v3-consumed-dbno-vod-review.md').write_text('\n'.join(lines),encoding='utf-8')
    if sha(RESULT)!=permanent or snapshot()!=protected:
        raise ValueError('Permanent result/live files changed')
    print('Independent Y11 credit/finisher broadcast case recorded; no metric changes',flush=True)


if __name__=='__main__':main()
