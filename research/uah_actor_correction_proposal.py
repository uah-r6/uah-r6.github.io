"""Final proposed historical actor report; private SQLite is opened read-only."""
from collections import Counter
import json
import sqlite3

from objective_bonus_body_asia_identity_review import verify_preserved
from objective_disable_owner_candidate import candidate as disable
from objective_plant_owner_candidate import candidate as plant
from objective_completer_consumed_audit import observation
from objective_player_component_fields import observe
from objective_actor_liveness import feedback
from objective_production_check import candidate_raw
from uah_guarded_actor_readonly import physical_rounds, snapshot
from v3_final_reserve import ROOT, sha


def main():
    verify_preserved(); protected=snapshot()
    core=json.loads((ROOT/'data/research/diagnostics/uah-completer-readonly.json').read_text())
    bonus=json.loads((ROOT/'data/research/diagnostics/uah-bonus-body-readonly.json').read_text())
    if core['database_sha256']!=protected['data/r6stats.sqlite']:
        raise ValueError('Database differs from reviewed UAH baseline')
    core_events={(e['map_id'],e['round'],e['kind']):e for e in core['events']}
    bonus_events={(e['map_id'],e['round']):e for e in bonus['records']}
    with sqlite3.connect((ROOT/'data/r6stats.sqlite').resolve().as_uri()+'?mode=ro',uri=True) as db:
        db.row_factory=sqlite3.Row
        maps=[dict(r) for r in db.execute('''SELECT m.id,m.map_name,se.slug,m.normalized_json FROM maps m
            JOIN series s ON s.id=m.series_id JOIN seasons se ON se.id=s.season_id WHERE s.demo=0''')]
        tracked={r['profile_id']:r['display_name'] for r in db.execute('SELECT profile_id,display_name FROM players WHERE tracked=1')}
    records=[];stored_counts=Counter();proposed_counts=Counter();seen=set()
    for map_ in maps:
        stored=json.loads(map_['normalized_json']);archive=ROOT/'data/replay-archive'/map_['slug']/map_['id']
        manifest=json.loads((archive/'manifest.json').read_text(encoding='utf-8'))
        for number,rec,_ in physical_rounds(archive,manifest):
            old=next(r for r in stored['rounds'] if r['number']==number)
            names={(p['profile_id'] or p['username'].casefold()):p for p in old['players']}
            for o in old['objectives']:
                p=names.get(o['player']); label=tracked.get(p['profile_id']) if p else None
                if label: stored_counts[label,o['kind']]+=1
            expected=[(key,e) for key,e in core_events.items() if key[:2]==(map_['id'],number)]
            if not expected: continue
            raw=candidate_raw(rec.parent,ROOT/'.local-tools/bin/siege-dissect-actors.exe')['rounds'][int(rec.stem.rsplit('-R',1)[1])-1]
            header=raw.get('header',raw); state,owners,slots,fields=observe(rec);feed=feedback(rec)['events']
            observed=observation(header,owners,slots,fields)
            data=dict(header=header,observed=observed,owners=owners,slots=slots,properties=state['properties'],
                      deaths=feed,full_feedback=raw['matchFeedback'])
            for key,event in expected:
                kind=event['kind']; actor,reason,context=(plant if kind=='plant' else disable)(**data)
                if actor!=event['completing_owner']: raise ValueError('Current core research/Go actor differs')
                seen.add(key);occurrence=next(o for o in header['objectiveOccurrences'] if o['kind']==kind)
                prior=[]
                for objective in old['objectives']:
                    if objective['kind']!=kind: continue
                    p=names.get(objective['player']);prior.append(dict(username=p['username'] if p else objective['player'],count=1))
                selected=next((p for p in header['players'] if p['username']==actor),None)
                label=tracked.get(selected.get('profileID')) if selected else None
                if label: proposed_counts[label,kind]+=1
                additional=bonus_events.get(key[:2]) if kind=='plant' else None
                records.append(dict(map_id=map_['id'],map=map_['map_name'],round=number,physical_round=int(rec.stem.rsplit('-R',1)[1]),
                    kind=kind,actor=actor,timer_owner=context.get('owner_entity'),numeric_uid=context.get('numeric_uid'),
                    timer_start=context.get('start'),timer_end=context.get('end'),terminal=context.get('terminal'),
                    completion_evidence={k:v for k,v in occurrence.items() if k not in ('actor','actorSource','actorReason')},
                    body_state_status=context.get('body_reason'),body_states=context.get('body_values',[]),reason=reason,
                    confidence='core_structural_completion_owner' if actor else 'unresolved',stored_actor_counts=prior,
                    proposed_action='replace_or_add_actor' if actor and [p['username'] for p in prior]!=[actor] else 'keep_actor' if actor else 'leave_unresolved_no_correction',
                    proposed_actor=actor,tracked_player=label,replay_sha256=sha(rec),applied=False,
                    research_only_bonus_actor=additional['isolated_owner'] if additional and additional['isolated_owner']!=actor else None))
    if seen!=set(core_events):raise ValueError('Incomplete UAH occurrence coverage')
    if snapshot()!=protected:raise ValueError('Protected state changed')
    totals=[dict(player=p,kind=k,stored=stored_counts[p,k],core_proposed=proposed_counts[p,k]) for p in sorted(tracked.values()) for k in ('plant','disable')]
    result=dict(status='final_readonly_correction_proposal_pending_user_review',records=records,tracked_totals=totals,
                counts=dict(objectives=len(records),core_resolved=sum(bool(r['actor']) for r in records),
                            unresolved=sum(not r['actor'] for r in records)),protected_hashes=protected,
                core_readiness='Production-quality conservative guarded resolver; supported versions only; unknown data abstains.',
                bonus_readiness='Not production-quality yet: prospective rare-case coverage insufficient.',
                applied=False,sqlite_open_mode='ro')
    destination=ROOT/'data/research/diagnostics/uah-final-actor-correction-proposal.json'
    if destination.exists():
        if json.loads(destination.read_text(encoding='utf-8'))!=result:raise ValueError('Preserved final proposal differs')
    else:destination.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    lines=['# Final proposed UAH actor corrections — read-only','',
           'The conservative core timer-owner resolver is production-quality for supported, complete replay structures. '
           'The rare bonus-health extension is not approved. This report prepares historical corrections for user review; none are applied. '
           'Structural confidence is not independently filmed UAH ground truth. SQLite opens mode=ro; all 86 protected files remain identical.','',
           f'Five maps / 62 rounds / 20 objectives: {result["counts"]["core_resolved"]} core actor proposals, two unresolved plants.','',
           '| Map / ID | Round (physical) | Kind | Core actor | Timer owner; start–end; terminal | Body states / status | Stored actors (count) | Proposed correction |',
           '| --- | ---: | --- | --- | --- | --- | --- | --- |']
    for r in records:
        previous='; '.join(f'{p["username"]} ({p["count"]})' for p in r['stored_actor_counts']) or 'none (0)'
        timer=f'{r["timer_owner"]}; {r["timer_start"]}–{r["timer_end"]}; {r["terminal"]}'
        lines.append(f'| {r["map"]}/{r["map_id"]} | {r["round"]} ({r["physical_round"]}) | {r["kind"]} | {r["actor"] or "unresolved"} | {timer} | {r["body_states"]} / {r["body_state_status"] or r["reason"]} | {previous} | {r["proposed_action"]}: {r["proposed_actor"] or "none"} |')
    lines+=['','## Completion evidence by objective','']
    for r in records:
        lines.append(f'- {r["map_id"]} R{r["round"]:02d} {r["kind"]}: `{r["completion_evidence"]}`; reason `{r["reason"]}`; confidence `{r["confidence"]}`; UID `{r["numeric_uid"]}`.')
    lines+=['','## Tracked player counts, proposed core only','','| Player | Kind | Stored | Core proposed |','| --- | --- | ---: | ---: |']
    for row in totals:lines.append(f'| {row["player"]} | {row["kind"]} | {row["stored"]} | {row["core_proposed"]} |')
    lines+=['','These are counts of resolved core proposals, not exact post-correction season totals. Unresolved historical credits '
            'are excluded from the proposed count column. Applying only the resolved replacements while retaining an old unresolved '
            'credit would produce different totals; that unresolved-credit policy must be reviewed before any database change. '
            'In particular the stored Tallman Kafe R09 credit is unverified, not independently confirmed by leaving that round unchanged.','',
            'Kafe R09 Kenbot.USU is a **research-only bonus-health proposal**, excluded from the core correction counts. '
            'Chalet logical R10 / physical R02 has only nine identities; no tenth player is invented and no actor correction is proposed. '
            'Unresolved objectives need explicit missing-data handling during any later approved correction, not zero-filled certainty.','',
            'Core evidence: 569 consumed rounds / 142 of 146 plants / 33 of 33 disables / 423 objective-free controls with zero false proposals; '
            'Go matched all 175 named research proposals. SAL and APAC independent sole-player constraints and official/VOD adjudication support core ownership. '
            'September original 5 agreements / 1 disagreement remains historically failed; the separate official/VOD-reviewed tier supports Gunnar, '
            'without rewriting the original labels/result. ASIA remains insufficient. Bonus development 894 rounds recovers three plants '
            'with zero changed old actors and zero false positives across 673 no-plant controls; this is development evidence.','',
            'No operator/action boundary, kills/deaths, Rating, normalized events, aggregate, database, archive or public JSON changed. '
            'No import, reparse replacement, push or publish. Live siege_style_v2 and both failed v3 finals remain untouched.','']
    (ROOT/'research/output/uah-final-actor-correction-proposal.md').write_text('\n'.join(lines),encoding='utf-8')
    verify_preserved();print(result['counts'],totals)


if __name__=='__main__': main()
