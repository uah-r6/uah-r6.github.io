"""Compare isolated bonus-health plant proposals on verified private archives."""
from collections import Counter
import json
import sqlite3

from objective_actor_liveness import feedback
from objective_completer_consumed_audit import observation
from objective_player_component_fields import observe
from objective_plant_owner_candidate import candidate as original
from objective_bonus_body_candidate import candidate as proposed
from objective_production_check import candidate_raw
from uah_guarded_actor_readonly import physical_rounds, snapshot
from v3_consumed_cohort_integrity import sealed_sal_cache, PERMANENT_RESULTS
from v3_consumed_apac_credit_probe import sealed_apac_cache
from v3_final_reserve import ROOT, sha


def main():
    protected=snapshot();sealed_sal_cache();sealed_apac_cache()
    with sqlite3.connect((ROOT/'data/r6stats.sqlite').resolve().as_uri()+'?mode=ro',uri=True) as db:
        db.row_factory=sqlite3.Row
        maps=[dict(r) for r in db.execute('''SELECT m.id,m.map_name,se.slug,m.normalized_json
            FROM maps m JOIN series s ON s.id=m.series_id JOIN seasons se ON se.id=s.season_id WHERE s.demo=0''')]
        tracked={r['profile_id']:r['display_name'] for r in db.execute('SELECT profile_id,display_name FROM players WHERE tracked=1') if r['profile_id']}
    records=[];totals=Counter();original38=Counter();parsed={}
    for map_ in maps:
        archive=ROOT/'data/replay-archive'/map_['slug']/map_['id']
        manifest=json.loads((archive/'manifest.json').read_text())
        stored=json.loads(map_['normalized_json'])
        for number,rec,_ in physical_rounds(archive,manifest):
            physical=int(rec.stem.rsplit('-R',1)[1])
            if rec.parent not in parsed:parsed[rec.parent]=candidate_raw(rec.parent,ROOT/'.local-tools/bin/siege-dissect-actors.exe')
            raw=parsed[rec.parent]['rounds'][physical-1];header=raw.get('header',raw)
            state,owners,slots,fields=observe(rec);feed=feedback(rec)['events']
            observed=observation(header,owners,slots,fields)
            data=dict(header=header,observed=observed,owners=owners,slots=slots,properties=state['properties'],
                      deaths=feed,full_feedback=raw['matchFeedback'])
            before=original(**data);after=proposed(**data,body_fields=fields)
            if before[0] and after!=before:raise ValueError('Already-resolved UAH plant actor changed')
            totals['rounds']+=1
            round_=next(r for r in stored['rounds'] if r['number']==number)
            for p in round_['players']:
                if map_['id'] in ('d64d5478cdb3','8a6357ff307c','5adc26f7a402') and tracked.get(p['profile_id'])=='Lgon' and p['side']=='Attack':
                    original38[p['operator']]+=1
            occurrences=[o for o in header.get('objectiveOccurrences',[]) if o['kind']=='plant']
            if not occurrences:
                if after[0]:raise ValueError('UAH false positive without verified occurrence')
                continue
            totals.update(plants=1,original_resolved=int(before[0] is not None),proposed_resolved=int(after[0] is not None))
            actor=next((p for p in header['players'] if p['username']==after[0]),None)
            records.append(dict(map_id=map_['id'],map=map_['map_name'],round=number,physical_round=physical,
                                replay_sha256=sha(rec),original_owner=before[0],isolated_owner=after[0],
                                original_reason=before[1],isolated_reason=after[1],context=after[2],
                                tracked_player=tracked.get(actor.get('profileID')) if actor else None,
                                prior_stored_objectives=round_['objectives'],
                                applied=False,interpretation='Read-only private proposal; historical actor is not ground truth.'))
        print('UAH bonus-body read-only',map_['id'],map_['map_name'],flush=True)
    if original38!={'Zofia':4,'Striker':4,'Gridlock':3,'Ace':2,'Grim':2,'Deimos':1,'Sens':1,'Twitch':1}:
        raise ValueError('Stored validated original38 Lgon operators differ')
    report=dict(status='readonly_bonus_body_hypothesis_not_historical_correction',counts=dict(totals),records=records,
                original38_lgon_attack_unchanged=dict(original38),permanent_results=PERMANENT_RESULTS,protected_hashes=protected)
    path=ROOT/'data/research/diagnostics/uah-bonus-body-readonly.json'
    if path.exists():
        if json.loads(path.read_text())!=report:raise ValueError('Preserved read-only UAH hypothesis differs')
    else:path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    lines=['# UAH isolated bonus-health plant proposals: read-only','',
           f'Counts: `{dict(totals)}`. SQLite opened mode=ro; archive digests verified. '
           'No stored actor, normalized event, aggregate or public JSON is changed. Defense is unchanged.', '',
           '| Map / ID | Round | Current structural owner | Isolated owner | Reason | Tracked teammate | Applied |',
           '| --- | ---: | --- | --- | --- | --- | --- |']
    for r in records:
        if r['original_owner']!=r['isolated_owner'] or r['isolated_owner'] is None:
            lines.append(f"| {r['map']}/{r['map_id']} | {r['round']} | {r['original_owner'] or 'unresolved'} | "
                         f"{r['isolated_owner'] or 'unresolved'} | {r['isolated_reason']} | {r['tracked_player']} | False |")
    lines+=['',f'Validated Lgon original38 Attack usage unchanged: `{dict(original38)}`.', '',
            'Old stored objective identities are comparison context, not authoritative target labels. '
            'Extra proposals are research-only, not applied corrections or independently reviewed collegiate truth. '
            'An incomplete nine-player roster stays unresolved. Full season v3 remains unavailable when any '
            'map remains incomplete; do not zero-fill or calculate a new live Rating here.', '',
            'Both source freezes, both failed final results and all86live hashes unchanged. No SQLite writes, '
            'archive mutation, public regeneration, import, push, publish or deployment.', '']
    (ROOT/'research/output/uah-bonus-body-readonly.md').write_text('\n'.join(lines),encoding='utf-8')
    sealed_sal_cache();sealed_apac_cache()
    if snapshot()!=protected:raise ValueError('Protected database/archive/public state changed')
    print('Read-only UAH bonus-body counts',dict(totals),'Lgon original38',dict(original38),flush=True)


if __name__=='__main__':main()
