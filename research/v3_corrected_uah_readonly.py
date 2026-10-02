"""Corrected-KOST frozen v3 contributions on complete archived maps; no corrections."""
from collections import Counter,defaultdict
import copy
import json
import sqlite3

from objective_production_check import candidate_raw
from objective_transition_probe import ROOT
from r6stats.parser.models import Match,Objective,ObjectiveOccurrence
from r6stats.parser.siege_dissect import normalize
from r6stats.stats.calculate import calculate_match
from fit_models import FEATURES,predict
from uah_comparison import player_rounds,contribution
from uah_guarded_actor_readonly import snapshot,physical_rounds
from v3_corrected_final_reserve import FREEZE,sha


def paired_rounds(old,new,key):
    a=player_rounds(old,key);b=player_rounds(new,key)
    for x,y in zip(a,b):
        for field in x:
            if field not in ('kost_rounds','plants','disables') and x[field]!=y[field]:
                raise ValueError('Unrelated gameplay feature changed')
    return b


def main():
    before=snapshot();frozen=json.loads(FREEZE.read_text(encoding='utf-8'))
    executable=ROOT/frozen['parser_binary']
    if sha(executable)!=frozen['parser_sha256']:raise ValueError('Frozen actor binary changed')
    with sqlite3.connect((ROOT/'data/r6stats.sqlite').resolve().as_uri()+'?mode=ro',uri=True) as db:
        db.row_factory=sqlite3.Row
        maps=[dict(m) for m in db.execute('''SELECT m.id,m.map_name,m.our_team,se.slug,m.normalized_json
            FROM maps m JOIN series s ON s.id=m.series_id JOIN seasons se ON se.id=s.season_id WHERE s.demo=0''')]
        tracked={r['profile_id']:r['display_name'] for r in db.execute('SELECT profile_id,display_name FROM players WHERE tracked=1') if r['profile_id']}
    parsed={};details=[];availability=[];season=defaultdict(list);incomplete=[]
    for saved in maps:
        old=Match.from_dict(json.loads(saved['normalized_json']));new=copy.deepcopy(old)
        archive=ROOT/'data/replay-archive'/saved['slug']/saved['id']
        manifest=json.loads((archive/'manifest.json').read_text(encoding='utf-8'))
        unresolved=[];counts=Counter();seen=set()
        for number,rec,_ in physical_rounds(archive,manifest):
            if rec.parent not in parsed:parsed[rec.parent]=candidate_raw(rec.parent,executable)
            physical=int(rec.stem.rsplit('-R',1)[1]);raw=parsed[rec.parent]['rounds'][physical-1]
            port=normalize([raw],round_numbers=[number]).rounds[0]
            target=next(r for r in new.rounds if r.number==number);seen.add(number)
            if {p.username:p.side for p in target.players}!={p.username:p.side for p in port.players}:
                raise ValueError('Stored/archive roster or side differs')
            target.objectives=[];target.objective_occurrences=[]
            for o in port.objective_occurrences:
                counts[o.kind]+=1
                p=next((p for p in port.players if p.key==o.actor),None)
                canonical=next((p2 for p2 in target.players if p and p2.username==p.username),None)
                if not canonical or o.actor_source!='completing_timer_owner_v1' or o.actor_reason!='completing_timer_owner_v1':
                    unresolved.append(dict(round=number,kind=o.kind,reason=o.actor_reason));continue
                target.objectives.append(Objective(o.kind,canonical.key,canonical.team,0.0))
                target.objective_occurrences.append(ObjectiveOccurrence(o.kind,o.source,o.plant_state_offset,
                    canonical.key,o.actor_uid,o.actor_source,o.actor_reason))
        if seen!={r.number for r in old.rounds}:raise ValueError('Archive logical coverage differs')
        availability.append(dict(map_id=saved['id'],map=saved['map_name'],rounds=len(old.rounds),counts=dict(counts),
            complete=not unresolved,unresolved=unresolved))
        if unresolved:
            incomplete.append(saved['id']);continue
        current=calculate_match(old,rating_version='siege_style_v2')
        for p in old.rounds[0].players:
            if p.team!=saved['our_team'] or p.profile_id not in tracked:continue
            name=tracked[p.profile_id];rounds=paired_rounds(old,new,p.key);row=dict(rounds=rounds)
            a=predict(frozen['baseline_model'],row,{});b=predict(frozen['model'],row,{})
            ca=contribution(frozen['baseline_model'],row);cb=contribution(frozen['model'],row)
            n=sum(r['plants']+r['disables'] for r in rounds)
            details.append(dict(player=name,map=saved['map_name'],map_id=saved['id'],rounds=len(rounds),
                objectives=n,stored_data_v2=current[p.key]['rating'],controlled_v2=a,controlled_v3=b,
                delta=b-a,contributions_v2=ca,contributions_v3=cb,
                direct_objective_addition=n/len(rounds)*frozen['model']['weights_standardized']['objectives']/frozen['model']['scales']['objectives']))
            season[name].extend(rounds)
    partial=[]
    for name,rounds in sorted(season.items()):
        row=dict(rounds=rounds)
        partial.append(dict(player=name,rounds=len(rounds),objectives=sum(r['plants']+r['disables'] for r in rounds),
            controlled_v2=predict(frozen['baseline_model'],row,{}),controlled_v3=predict(frozen['model'],row,{})))
    record=dict(status='read_only_failed_gate_candidate_not_proposed_deployment',maps=availability,details=details,
        partial_complete_map_aggregate=partial,full_season_v3_available=not incomplete,excluded_maps=incomplete,
        database_sha256=before['data/r6stats.sqlite'],freeze_sha256=sha(FREEZE),protected_files=len(before))
    (ROOT/'data/research/diagnostics/v3-corrected-uah-readonly.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    lines=['# UAH corrected-KOST v3 contributions: read-only, failed SAL final gate','',
        'Frozen v3 improves new-event MAE but fails its predeclared within0.05 gate. No deployment or historical correction is proposed. '
        'SQLite mode=ro; exact archive digests/logical mapping checked. Only complete-actor maps receive a v3 prediction. '
        'Whole season v3 is unavailable while any map has unresolved objective ownership. Missing ownership is never zero.','',
        '| Map / ID | Rounds | Objectives | Available | Reason |','| --- | ---: | --- | --- | --- |']
    for r in availability:lines.append(f"| {r['map']}/{r['map_id']} | {r['rounds']} | {r['counts']} | {r['complete']} | {r['unresolved'] or 'all actors verified'} |")
    lines+=['','## Player-map controlled comparison','',
        'Stored-data v2 is an in-memory recomputation with the unchanged live v2 on stored normalized data. '
        'Controlled v2/v3 both use fully objective-corrected KOST and verified objectives, as frozen for the separate corrected-KOST research comparison; other gameplay inputs unchanged. '
        'Objective-only addition is raw objective coefficient times objectives/round; total delta also includes frozen coefficient/intercept drift.','',
        '| Player / map / ID | Rounds | Verified objectives | Stored-data v2 | Controlled v2 | Controlled v3 | Delta | Objective-only addition |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for r in details:lines.append(f"| {r['player']}/{r['map']}/{r['map_id']} | {r['rounds']} | {r['objectives']} | {r['stored_data_v2']:.3f} | {r['controlled_v2']:.3f} | {r['controlled_v3']:.3f} | {r['delta']:+.3f} | {r['direct_objective_addition']:+.3f} |")
    lines+=['','## Partial aggregation over complete maps only','',
        'These are not full-season ratings: Kafe and Chalet are excluded entirely, including their already-resolved objectives.','',
        '| Player | Included rounds | Objectives | Controlled v2 | Controlled v3 |','| --- | ---: | ---: | ---: | ---: |']
    for r in partial:lines.append(f"| {r['player']} | {r['rounds']} | {r['objectives']} | {r['controlled_v2']:.3f} | {r['controlled_v3']:.3f} |")
    lines+=['','## Every standardized feature contribution change','',
        'Entries are v3 minus v2 centered contributions; their sum plus the intercept delta equals total rating delta. '
        'Centered objective contribution may be negative for zero-objective players; the objective-only addition above has no centering offset.','',
        '| Player / map ID | '+' | '.join(FEATURES)+' |','| --- | '+' | '.join(['---:']*len(FEATURES))+' |']
    for r in details:lines.append(f"| {r['player']}/{r['map_id']} | "+' | '.join(f"{r['contributions_v3'][n]-r['contributions_v2'][n]:+.4f}" for n in FEATURES)+' |')
    lines+=['',f"Intercept delta {frozen['model']['intercept']-frozen['baseline_model']['intercept']:+.8f}.",
        'All86 protected live file hashes unchanged; no SQLite statistics write, reparse/import, archive mutation, public regeneration or publishing.','']
    (ROOT/'research/output/v3-corrected-uah-readonly.md').write_text('\n'.join(lines),encoding='utf-8')
    if snapshot()!=before:raise ValueError('Protected live data changed')
    print('Readonly complete maps',sum(r['complete'] for r in availability),'excluded',incomplete,'partial',partial,flush=True)


if __name__=='__main__':main()
