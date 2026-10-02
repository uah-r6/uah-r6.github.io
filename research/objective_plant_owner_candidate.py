"""Separate consumed-data plant completer hypothesis; frozen A/D stay unchanged.

Requires a validated global plant, exactly one complete state0 episode before
that anchor, temporal unique attacker ownership and eligible body throughout.
Timer progress/state2 by themselves never establish objective occurrence.
No labels, bonus scores, last killer, packet proximity or name exceptions.
"""
from objective_disable_owner_candidate import active_body, run_end


def candidate(header, observed, owners, slots, properties, deaths, full_feedback):
    context = {}
    if header.get('gamemode',{}).get('name') != 'Bomb':
        return None,'unsupported_game_mode',context
    teams,players=header.get('teams',[]),header.get('players',[])
    if (len(teams)!=2 or {t.get('role') for t in teams}!={'Attack','Defense'} or len(players)!=10
            or len({p.get('username') for p in players})!=10 or any(not p.get('username') or not p.get('id') for p in players)
            or len({p['id'] for p in players})!=10
            or any(p.get('teamIndex') not in (0,1) for p in players)
            or any(sum(p['teamIndex']==i for p in players)!=5 for i in (0,1))):
        return None,'incomplete_unique_roster_or_roles',context
    plants=[e for e in header.get('objectiveOccurrences',[]) if e.get('kind')=='plant']
    if (len(plants)!=1 or plants[0].get('source')!='defuser_state_v1'
            or not isinstance(plants[0].get('plantStateOffset'),int) or plants[0]['plantStateOffset']<=0):
        return None,'no_unique_verified_plant_occurrence',context
    anchor=plants[0]['plantStateOffset']
    if any(e['type']['name']=='PlayerLeave' for e in full_feedback):
        return None,'player_leave_timing_unknown',context
    if any(d['offset']<=0 for d in deaths):
        return None,'unknown_death_offset',context
    runs=[r for r in observed['episodes'] if r['state']==0 and r['start_record']<anchor]
    complete=[r for r in runs if r['end_reason']=='explicit_state_2' and r['monotonic_timer']
              and len(r['samples'])>=2 and r['first_timer'] is not None and 6.5<=r['first_timer']<=7.1
              and r['last_timer'] is not None and 0<=r['last_timer']<=.1
              and run_end(r) is not None and run_end(r)<anchor]
    context.update(plant_offset=anchor,phase0_runs=len(runs),complete_phase0_runs=len(complete),
                   attempted_owners=[r['binding']['player'] for r in runs])
    if len(complete)!=1:
        return None,'missing_or_competing_complete_plant_runs',context
    run=complete[0]
    end=run_end(run)
    if end<run['samples'][-1]['offset'] or end<=run['start_record']:
        return None,'invalid_terminal_order',context
    # Explicit later/restarted or unresolved evidence can invalidate association
    # with the global completion even when an earlier canceled run approached0.
    if any(r['start_record']>run['start_record'] for r in runs if r is not run):
        return None,'later_preplant_attempt',context
    if any(r['start_record']<run['start_record'] and (run_end(r) is None or run_end(r)>run['start_record'])
           for r in runs if r is not run):
        return None,'overlapping_plant_attempts',context
    if any(r['record_start']<anchor for r in observed['orphan_records']):
        return None,'unbound_preplant_timer_evidence',context
    binding=run['binding']
    name,owner=binding['player'],binding['owner']
    context.update(owner_observation=name,owner_entity=owner,start=run['start_record'],end=end,
                   terminal=run['end_reason'])
    roster=[p for p in players if p['username']==name]
    if len(roster)!=1 or owners.get(owner)!=name or teams[roster[0]['teamIndex']]['role']!='Attack':
        return None,'timer_owner_identity_or_role_conflict',context
    expected_class='a859ffff' if header.get('codeVersion')==9734089 else 'b2216bf3'
    if (binding['slot'],binding['class_hash'])!=('27c08dca',expected_class):
        return None,'unsupported_timer_component_route',context
    dead=set()
    for d in deaths:
        if d['offset']>end:
            continue
        f=d['feedback']
        victim=f.get('target') if f['type']['name']=='Kill' else f.get('username') if f['type']['name']=='Death' else None
        if victim is not None:
            dead.add(victim)
    if name in dead:
        return None,'timer_owner_dead_by_terminal',context
    opponents={p['username'] for p in players if p['teamIndex']!=roster[0]['teamIndex']}
    if opponents<=dead:
        return None,'all_opponents_dead_by_terminal',context
    active,reason,values=active_body(owner,name,run['start_record'],end,owners,slots,properties)
    context.update(body_reason=reason,body_values=values,numeric_uid=roster[0]['id'])
    if not active:
        return None,'timer_owner_body_unresolved',context
    return name,'direct_plant_completer_with_occurrence_and_body',context
