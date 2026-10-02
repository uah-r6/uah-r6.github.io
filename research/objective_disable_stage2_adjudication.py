"""Append independent review of a consumed disagreement, never regrade a freeze."""
import hashlib
import json

from objective_actor_liveness import feedback
from objective_official_disable_review import objective_projection, constrained_disable_labels
from objective_player_component_fields import observe
from objective_production_check import candidate_raw
from objective_timer_lifecycle_comparison import cached_states
from objective_timer_component_episodes import component_episodes
from objective_disable_owner_candidate import run_end
from objective_transition_probe import ROOT
from uah_guarded_actor_readonly import snapshot


def main():
    protected = snapshot()
    original_path = ROOT/'data/research/diagnostics/objective-disable-stage2-validation/result.json'
    original_sha = hashlib.sha256(original_path.read_bytes()).hexdigest()
    original = json.loads(original_path.read_text(encoding='utf-8'))
    disputed = [e for e in original['events'] if e['verdict'] == 'incorrect']
    if len(disputed) != 1 or original['counts'] != {'correct': 5, 'incorrect': 1}:
        raise ValueError('Expected the preserved original 5/1 result')
    event = disputed[0]
    if (event['match_id'], event['game_id'], event['round']) != (6170,10592,7):
        raise ValueError('Review is limited to the documented September disagreement')
    folders = [p for p in (ROOT/'data/research/extracted').rglob(event['folder']) if p.is_dir()]
    if len(folders) != 1:
        raise ValueError('Ambiguous physical replay')
    recs = list(folders[0].glob('*-R07.rec'))
    if len(recs) != 1 or hashlib.sha256(recs[0].read_bytes()).hexdigest() != event['rec_sha256']:
        raise ValueError('Replay differs from the frozen prediction')
    rec = recs[0]
    header = candidate_raw(rec.parent)['rounds'][6]
    header = header.get('header',header)
    state, owners, slots, fields = observe(rec)
    episodes = component_episodes(owners, slots, fields)
    deaths = feedback(rec)['events']
    starts = [e for e in episodes['episodes'] if e['state'] == 1]
    if len(starts) != 1 or starts[0]['binding']['player'] != event['proposal']:
        raise ValueError('Frozen owner no longer matches structural evidence')
    ep = starts[0]
    end = run_end(ep)
    owner = ep['binding']['owner']
    body_declarations = slots.get((owner,'4154dcc4'),[])
    bodies = {d['component'] for d in body_declarations if d['offset'] <= end and d['component']}
    body_states = [p for p in state['properties'] if p['entity'] in bodies
                   and p['hash'] == 'e788f6a5' and p['offset'] <= end]
    base = ROOT/'data/research/diagnostics/player-component-fields'
    official_path = base/'official-8285-next.json'
    official = json.loads(official_path.read_text(encoding='utf-8'))['props']['pageProps']['pageData']['match']
    games = [g for g in official['games'] if g['map']['name'] == 'Villa']
    if len(games) != 1:
        raise ValueError('Official Villa identity ambiguous')
    projection = objective_projection(games[0])
    constraints = constrained_disable_labels(projection)
    labels = [l for t in constraints for l in t['constrained_round_labels'] if l['round'] == 7]
    if len(labels) != 1 or labels[0]['id'] != 995 or labels[0]['player'].lower() != 'gunnar':
        raise ValueError('Official totals do not independently constrain Gunnar R07')
    records = []
    for e in original['events']:
        records.append(dict(match_id=e['match_id'],game_id=e['game_id'],round=e['round'],
            proposal=e['proposal'],original_label=e['public_label'],original_verdict=e['verdict'],
            reviewed_verdict='correct' if e is event else e['verdict'],
            label_tier='official_map_totals_and_round_context' if e is event else 'original_third_party_unreviewed'))
    report = dict(status='consumed_separate_adjudication',classification='B_external_label_error',
        original_result_sha256=original_sha,original_counts=original['counts'],
        original_acceptance=original['acceptance'],reviewed_counts=dict(correct=6,incorrect=0,unresolved=0),
        reviewed_counts_scope='one adjudicated label; five original agreements not independently reverified',
        records=records,disputed_replay=dict(rec_sha256=event['rec_sha256'],physical_round=7,
            build=header['codeVersion'],map=header['map'],occurrences=header['objectiveOccurrences'],
            teams=header['teams'],owner_roster=[p for p in header['players'] if p['username']==event['proposal']],
            owner_numeric_uid=event['context']['numeric_uid'],owner_entity=owner,timer_episode=ep,
            timer_terminal_property_end=end,owner_slot_declarations=slots.get((owner,'27c08dca'),[]),
            body_declarations=body_declarations,body_states=body_states,
            ordered_deaths=deaths,global_defuser_states=cached_states(rec)),
        official=dict(url='https://www.ubisoft.com/en-us/esports/rainbow-six/siege/match/8285',
            cache_sha256=hashlib.sha256(official_path.read_bytes()).hexdigest(),
            projection=projection,constraints=constraints),
        vod=dict(url='https://www.youtube.com/watch?v=1TqU0qsLfDU',title='NAL 2026 - Stage 2 | Group Stage - Day 1',
            upload_date='20260909',visible_interaction_seconds=[12245,12246,12247,12248,12249],
            limits='Small gameplay inset shows counter-defuse device and highlighted first M80 card; completion obscured by player cameras. Camera subject is not actor evidence.'),
        actor_rule_changed=False,production_promoted=False)
    if snapshot() != protected or hashlib.sha256(original_path.read_bytes()).hexdigest() != original_sha:
        raise ValueError('Protected files or original frozen result changed')
    (base/'stage2-disable-adjudication.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    lines = ['# September Villa R07: separate actor adjudication','',
        '**Classification B: external-label error.** The frozen timer owner is Gunnar.M80; the original '
        'third-party label says Savage. No actor rule changed during review. The permanent primary '
        'result is still five agreements, one disagreement, zero occurrence mismatches, and a FAILED '
        'predeclared gate. Its exact result SHA256 is `'+original_sha+'`.','',
        '## Replay evidence','',
        'Physical R07, build9883691. Verified plant state1 at47185499; existing Bomb + plant + '
        'Defense win occurrence independently establishes a disable. One postplant state1 episode: '
        'start47297207, terminal state2 record'+str(ep['end_record'])+', exact last property end'+str(end)+'. '
        'Timer component '+str(ep['entity'])+' binds through slot27c08dca/classb2216bf3 to owner '
        '4027874753, Gunnar numeric UID10462818329288152675. Known body route stays active (state0). '
        'No competing run, replacement, disconnect or owner death precedes completion. Timer '+
        str(ep['first_timer'])+' -> '+str(ep['last_timer'])+' across '+str(len(ep['samples']))+' samples. '
        'M80 is Defense; score increment2->3 (Shopify4 unchanged) is secondary winner evidence, '
        'not an actor-selection feature. All literal fields and ordered events are cached in the separate ignored review.','',
        '| Offset | Kill |','| --- | --- |']
    for d in deaths:
        f=d['feedback']
        lines.append(f"| {d['offset']} | {f.get('username')} -> {f.get('target')} ({f.get('time')}) |")
    lines += ['', 'The final opposing killer is **Gaveni**, while the disputed public label says **Savage**. '
        'The last-killer coincidence in the three earlier disagreements is not a universal explanation.','',
        '## Independent official constraints','',
        '[Ubisoft match8285](https://www.ubisoft.com/en-us/esports/rainbow-six/siege/match/8285), '
        'Villa official game10622: M80(team229)3, Shopify(team43)7. Defuser=3 round methods identify '
        'R05 Shopify and R07 M80 as the only disables. M80 totals Gunnar995=1; Savage1004=0; '
        'dfuzr1696=0; Ashn1578=0; Gaveni1183=0. Therefore the sole M80 disable necessarily belongs '
        'to Gunnar in R07. Shopify Spoit1000=1 constrains R05. This inference uses official totals '
        'and complete round context, no replay actor or Rating fields. Separate sources may still '
        'share underlying measurement pipelines. Official cache SHA256 `'+report['official']['cache_sha256']+'`.','',
        '## Official broadcast review','',
        '[Rainbow Six Esports Day1](https://www.youtube.com/watch?v=1TqU0qsLfDU&t=12245s), '
        'uploaded September9. At12150 Villa R07 begins M80 2-4 Shopify;12220 shows planted40.21; '
        '12235 shows Gaveni killing Rexen (last attacker), postplant25.22. At12245/46/47/48/49 a '
        'small gameplay inset shows the counter-defuse device and highlighted first M80 card, '
        'consistent with Gunnar. The inset is small; the main view is a player camera. '
        'Completion is obscured when the inset disappears, so this is visible interaction support, '
        'not frame-perfect completion proof. At12300 R08 prep is M80 3-4, confirming R07 Defense win. '
        'Do not infer the actor from the camera subject. Cached frames are ignored, not committed.','',
        '## Separate reviewed comparison','',
        'Original frozen comparison: **5 agreements / 1 disagreement / 0 unresolved**. '
        'Reviewed mixed-source comparison: **6 agreements / 0 disagreements / 0 unresolved**. '
        'Only the disputed label was independently adjudicated; the other five remain original '
        'third-party agreements. This is not six independently visually verified disables, '
        'not a new untouched evaluation and not retroactive passage of the original gate.','',
        'The latest user instructions also release the former Aiden/Raid hard abstention: official '
        'Fortress R07 VOD supports Aiden, while original Raid targets and frozen outcomes remain '
        'preserved. Future structural plant candidates may credit Aiden only from completing-owner '
        'evidence, never from a case-name exception.','',
        f'Reproduce: `.venv/Scripts/python.exe research/objective_disable_stage2_adjudication.py`. '
        f'{len(protected)} protected database/archive/public hashes unchanged. No runtime, target, '
        'live v2, SQLite, archive or public-data change. NEXT: broad consumed plant/disable structural '
        'completion-owner audit, including Kason/Hotancold and all negative controls.','']
    (ROOT/'research/output/objective-disable-stage2-adjudication.md').write_text('\n'.join(lines),encoding='utf-8')
    print(report['classification'],report['original_counts'],report['reviewed_counts'],'protected',len(protected))


if __name__ == '__main__':
    main()
