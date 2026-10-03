"""Read-only current UAH kill migration proposal; never writes SQLite/public data."""
from collections import Counter
from dataclasses import replace
import json
import sqlite3

from credited_kill_evidence import inspect, DATA
from objective_production_check import candidate_raw
from r6stats.kill_credit import validate_map_credit
from r6stats.manual_kd import map_players
from r6stats.parser.models import Match
from r6stats.stats.calculate import calculate_match
from uah_guarded_actor_readonly import physical_rounds, snapshot
from v3_final_reserve import ROOT, sha


def main():
    protected=snapshot(); maps=[]; totals={}; differences=[]; unknown=[]; reader_checks=[]
    actors=json.loads((ROOT/'data/research/diagnostics/uah-final-actor-correction-proposal.json').read_text())
    if actors['protected_hashes']!=protected: raise ValueError('Actor review baseline differs')
    with sqlite3.connect((ROOT/'data/r6stats.sqlite').resolve().as_uri()+'?mode=ro',uri=True) as db:
        db.row_factory=sqlite3.Row
        roster=[dict(r) for r in db.execute('SELECT id,profile_id,display_name FROM players WHERE tracked=1')]
        stored=[dict(r) for r in db.execute('''SELECT m.id,m.map_name,m.normalized_json,m.replay_data_complete,se.slug
            FROM maps m JOIN series s ON s.id=m.series_id JOIN seasons se ON se.id=s.season_id WHERE s.demo=0''')]
        for p in roster:
            totals[p['profile_id']]=dict(player=p['display_name'],current_kills=0,current_deaths=0,
                observed_credit_kills=0,observed_finisher_kills=0,unresolved_rounds=[],affected_rounds=[],
                hypothetical_kost_kill_delta=0,hypothetical_multikill_extra_delta=0,
                hypothetical_core_objective_kost_delta=0,hypothetical_combined_kost_delta=0)
        for m in stored:
            match=Match.from_dict(json.loads(m['normalized_json']))
            archive=ROOT/'data/replay-archive'/m['slug']/m['id']
            manifest=json.loads((archive/'manifest.json').read_text(encoding='utf-8'))
            rounds=sorted(physical_rounds(archive,manifest),key=lambda row:row[0]); records=[]; observations={}
            for logical,rec,_ in rounds:
                observation=inspect(rec)
                observations[logical]=observation
                records.append(dict(logical_round=logical,physical_round=int(rec.stem.rsplit('-R',1)[1]),
                    segment=rec.parent.relative_to(archive).as_posix(),credit=observation['credit']))
                # One actual decompression/Reader.Read check per map. Remaining
                # rounds reuse cached decoded structure rather than old pipelines.
                if logical==1:
                    actual=inspect(rec,actual_replay=True)
                    if actual['credit']!=observation['credit']:
                        raise ValueError('Actual replay reader differs from cached structural Go validator')
                    raw=candidate_raw(rec.parent,ROOT/'.local-tools/bin/siege-dissect-actors.exe')['rounds'][int(rec.stem.rsplit('-R',1)[1])-1]
                    pinned=raw.get('header',raw)
                    if actual['header']['players']!=pinned['players']:
                        raise ValueError('Actual reader changed pinned operator/player snapshot')
                    reader_checks.append(dict(map_id=m['id'],round=logical,replay_sha256=sha(rec),
                                              credit_and_operator_parity=True))
                print('UAH credit',m['map_name'],logical,'complete',observation['credit']['complete'],flush=True)
            validated=validate_map_credit(records)
            raw_map=calculate_match(match); display={p['player_id']:p for p in map_players(db,m['id'],8)}
            per_player=[]
            for player in roster:
                key=player['profile_id']; label=player['display_name']; current=display.get(player['id'])
                if not current: continue
                total=totals[key]; total['current_kills']+=current['final_kills']; total['current_deaths']+=current['final_deaths']
                row=dict(player=label,current_kills=current['final_kills'],current_deaths=current['final_deaths'],
                         stored_round_finisher_kills=raw_map.get(key,{}).get('kills',0),
                         manual_correction=current['corrected'],observed_credit_kills=0,
                         observed_finisher_kills=0,unresolved_rounds=[],affected_rounds=[],
                         hypothetical_kost_kill_delta=0,hypothetical_multikill_extra_delta=0,
                         hypothetical_core_objective_kost_delta=0,hypothetical_combined_kost_delta=0)
                for r, credit in zip(match.rounds,validated['rounds']):
                    if r.number!=credit['number']: raise ValueError('Physical/stored round mismatch')
                    if key not in {p.key for p in r.players}: continue
                    s=calculate_match(replace(match,rounds=[r]))[key]
                    o=credit['players'].get(key)
                    if not credit['valid'] or not o or o['kills'] is None:
                        issue=dict(map_id=m['id'],map=m['map_name'],round=r.number,player=label,
                                   reason=observations[r.number]['credit']['reason'])
                        unknown.append(issue); row['unresolved_rounds'].append(r.number)
                        total['unresolved_rounds'].append(issue); continue
                    k=o['kills']; row['observed_credit_kills']+=k; row['observed_finisher_kills']+=s['kills']
                    total['observed_credit_kills']+=k; total['observed_finisher_kills']+=s['kills']
                    if k!=s['kills']:
                        detail=dict(map_id=m['id'],map=m['map_name'],round=r.number,
                            physical_round=credit['physical_round'],player=label,credit=k,finishes=s['kills'],
                            difference=k-s['kills'],counter_initial=o['initial'],counter_terminal=o['terminal'],
                            uid=o['uid'],counter_samples=o['samples'],
                            raw_finish_events=observations[r.number]['credit']['finishes'],
                            interpretation='Credit/finish discrepancy; no victim/downer association inferred.')
                        differences.append(detail);row['affected_rounds'].append(r.number);total['affected_rounds'].append(dict(map=m['map_name'],map_id=m['id'],round=r.number,difference=k-s['kills']))
                    # Supported actor corrections are a separate hypothetical
                    # scenario. Unknown historical credits are retained as-is.
                    core_events=[a for a in actors['records'] if a['map_id']==m['id'] and a['round']==r.number and a['actor']]
                    corrected_objectives=[a for a in r.objectives if not any(a.kind==c['kind'] for c in core_events)]
                    participant=next(p for p in r.players if p.key==key)
                    proposed_objective=any(a.player==key and a.team==participant.team and
                        participant.side=={'plant':'Attack','disable':'Defense'}.get(a.kind)
                        for a in corrected_objectives)
                    proposed_objective |= any(c['tracked_player']==label for c in core_events)
                    kill_kost=int(bool(k or s['plants'] or s['disables'] or s['survived'] or s['deaths_traded']))
                    actor_kost=int(bool(s['kills'] or proposed_objective or s['survived'] or s['deaths_traded']))
                    combined=int(bool(k or proposed_objective or s['survived'] or s['deaths_traded']))
                    for field,value in (
                        ('hypothetical_kost_kill_delta',kill_kost-s['kost_rounds']),
                        ('hypothetical_core_objective_kost_delta',actor_kost-s['kost_rounds']),
                        ('hypothetical_combined_kost_delta',combined-s['kost_rounds']),
                        ('hypothetical_multikill_extra_delta',max(k-1,0)-s['multikill_extra'])):
                        row[field]+=value; total[field]+=value
                eligible=validated['complete'] and not row['unresolved_rounds']
                row['credited_kills']=row['observed_credit_kills'] if eligible else None
                row['difference']=row['credited_kills']-row['current_kills'] if eligible else None
                row['proposed_kd']=row['credited_kills']/row['current_deaths'] if eligible and row['current_deaths'] else None
                per_player.append(row)
            maps.append(dict(map_id=m['id'],map=m['map_name'],season=m['slug'],rounds=len(match.rounds),
                map_complete=validated['complete'],issues=validated['issues'],resets=validated['resets'],players=per_player,
                historical_replay_complete=bool(m['replay_data_complete'])))
    for total in totals.values():
        total['credited_kills']=total['observed_credit_kills'] if not total['unresolved_rounds'] and all(m['map_complete'] for m in maps) else None
        total['known_round_difference']=total['observed_credit_kills']-total['observed_finisher_kills']
        total['difference']=total['credited_kills']-total['current_kills'] if total['credited_kills'] is not None else None
        total['proposed_kd']=total['credited_kills']/total['current_deaths'] if total['credited_kills'] is not None and total['current_deaths'] else None
    result=dict(status='read_only_migration_review_not_applied',maps=maps,season_totals=list(totals.values()),
                differences=differences,unresolved=unknown,actual_reader_checks=reader_checks,
                actor_proposal_sha256=sha(ROOT/'data/research/diagnostics/uah-final-actor-correction-proposal.json'),
                protected_hashes=protected,sqlite_open_mode='ro',rating_semantics_changed=False)
    DATA.mkdir(parents=True,exist_ok=True)
    (DATA/'uah-audit.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    lines=['# UAH credited kills migration audit — read-only','',
        'Current stored/displayed K/D includes any existing manual map corrections. The counter derives official-style '
        'credit, not independently filmed UAH ground truth. Unsupported rounds/maps stay unresolved; known-round '
        'subtotals are not substituted for complete season statistics. No events, SQLite, archives or public JSON changed.','',
        '| Player | Current kills | Current deaths | Credited kills | Complete difference | Proposed KD | Known-round credit/finish difference | Unresolved rounds |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |']
    for p in totals.values():
        lines.append(f"| {p['player']} | {p['current_kills']} | {p['current_deaths']} | {p['credited_kills']} | {p['difference']} | {p['proposed_kd']} | {p['known_round_difference']} | {[(r['map'],r['round']) for r in p['unresolved_rounds']]} |")
    lines+=['','## Map totals','', '| Map / ID | Player | Current kills / deaths | Credit | Difference | Proposed KD | Unresolved |', '| --- | --- | --- | ---: | ---: | ---: | --- |']
    for m in maps:
        for p in m['players']: lines.append(f"| {m['map']}/{m['map_id']} | {p['player']} | {p['current_kills']}/{p['current_deaths']} | {p['credited_kills']} | {p['difference']} | {p['proposed_kd']} | {p['unresolved_rounds']} |")
    lines+=['','## Every tracked player-round difference','', '| Map / ID | Logical (physical) round | Player | Credited | Finishes | Delta |', '| --- | --- | --- | ---: | ---: | ---: |']
    for d in differences: lines.append(f"| {d['map']}/{d['map_id']} | {d['round']} ({d['physical_round']}) | {d['player']} | {d['credit']} | {d['finishes']} | {d['difference']} |")
    lines+=['','Exact UID, start/end counter, packet offsets and raw finish events are in ignored `data/research/credited-kills-v1/uah-audit.json`. No discrepancy is called a specific victim/downer reassignment without independent evidence.','',
        '## Hypothetical downstream changes on validated rounds','',
        'These are impact calculations, not authorized production migrations. Core actor scenario replaces only supported same-kind credits and retains unresolved historical credit for review. Missing rounds are excluded from every scenario.','',
        '| Player | Kill-only KOST round delta | Core-only objective KOST delta | Combined KOST delta | Credited multikill extra delta |', '| --- | ---: | ---: | ---: | ---: |']
    for p in totals.values(): lines.append(f"| {p['player']} | {p['hypothetical_kost_kill_delta']} | {p['hypothetical_core_objective_kost_delta']} | {p['hypothetical_combined_kost_delta']} | {p['hypothetical_multikill_extra_delta']} |")
    lines+=['',f'Actual new-reader/structural evidence parity: {len(reader_checks)} first-round checks, one per map; operators/players and full credit/finish report identical. All {len(protected)} protected files unchanged.', '',
        'Core objectives: 18 supported proposals; Kafe R09 body1 remains research-only, Chalet R10 nine-player roster remains unresolved. Review the [separate objective proposal](uah-final-actor-correction-proposal.md). Original v2 input semantics/rating remain unchanged; no v3 fit or final evaluation.','']
    (ROOT/'research/output/credited-kill-uah-audit.md').write_text('\n'.join(lines),encoding='utf-8')
    if snapshot()!=protected: raise ValueError('Protected live data changed')
    print('UAH totals',list(totals.values()),flush=True)


if __name__=='__main__':main()
