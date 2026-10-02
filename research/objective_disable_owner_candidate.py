"""UNFROZEN, disable-only direct timer owner hypothesis on consumed data.

Uses existing occurrence-only Bomb/plant/Defense-win evidence, not score bonus
or inferred win-condition text. Plants are intentionally unsupported. Nothing
here is imported by the tracker or frozen candidate A.
"""
from objective_player_component_fields import bindings_at

BODY_SLOT = '4154dcc4'
BODY_CLASS = '0c98c63f'


def run_end(run):
    if run['end_reason'] == 'ownership_declaration_boundary':
        return run['end_offset']
    # end_record is the record START; timer/state properties can follow it.
    # Use the end of every observed property in the terminal record.
    return max((f['offset']+5+f['size'] for f in run['records'][-1]['fields']),default=0) if run['records'] else None


def complete_disable_run(run, slots):
    if (run['state'] != 1 or not run['monotonic_timer'] or len(run['samples']) < 2
            or run['first_timer'] is None or not 6.5 <= run['first_timer'] <= 7.1
            or run['last_timer'] is None or not 0 <= run['last_timer'] <= .1):
        return False
    if run['end_reason'] == 'explicit_state_2':
        return True
    if run['end_reason'] != 'ownership_declaration_boundary':
        return False
    b=run['binding']
    terminal=[d for d in slots.get((b['owner'],b['slot']),[]) if d['offset']==run['end_offset']]
    return (len(terminal)==1 and terminal[0]['component']==0
            and terminal[0]['class_hash']=='00000000')


def active_body(owner, player, start, end, owners, slots, properties):
    """Known body route throughout; unknown/DBNO/replacement cannot prove active."""
    ds=slots.get((owner,BODY_SLOT),[])
    prior=[d for d in ds if d['offset']<=start]
    if not prior or not prior[-1]['component'] or prior[-1]['class_hash']!=BODY_CLASS:
        return False,'missing_known_body_declaration',[]
    component=prior[-1]['component']
    points={start,end} | {d['offset'] for declarations in slots.values() for d in declarations
                         if start<d['offset']<=end and d['component'] in (0,component)}
    # Check own replacement too, even when it points at another entity.
    points.update(d['offset'] for d in ds if start<d['offset']<=end)
    health=sorted((p for p in properties if p['entity']==component and p['hash']=='e788f6a5' and p['size']==4),
                  key=lambda p:p['offset'])
    preceding=[p for p in health if p['offset']<=start]
    during=[p for p in health if start<p['offset']<=end]
    if not preceding:
        return False,'missing_prior_body_state',[]
    values=[preceding[-1]['value']]+[p['value'] for p in during]
    points.update(p['offset'] for p in during)
    # The preceding state's route must also be uniquely bound at its own offset.
    points.add(preceding[-1]['offset'])
    for point in points:
        b=bindings_at(owners,slots,point).get(component)
        if not b or (b['owner'],b['player'],b['slot'],b['class_hash'])!=(owner,player,BODY_SLOT,BODY_CLASS):
            return False,'body_route_missing_shared_or_changed',values
    if not set(values)<={0,2}:
        return False,'body_state_unresolved_or_ineligible',values
    return True,'known_active_body_throughout',values


def candidate(header, observed, owners, slots, properties, deaths, full_feedback, kind='disable'):
    context={}
    if kind!='disable':
        return None,'plants_unsupported',context
    if header.get('gamemode',{}).get('name')!='Bomb':
        return None,'unsupported_game_mode',context
    teams,players=header.get('teams',[]),header.get('players',[])
    if (len(teams)!=2 or {t.get('role') for t in teams}!={'Attack','Defense'} or len(players)!=10
            or len({p.get('username') for p in players})!=10 or any(not p.get('username') or not p.get('id') for p in players)
            or len({p['id'] for p in players})!=10
            or any(p.get('teamIndex') not in (0,1) for p in players)
            or any(sum(p['teamIndex']==i for p in players)!=5 for i in (0,1))):
        return None,'incomplete_unique_roster_or_roles',context
    deltas=[t['score']-t['startingScore'] for t in teams]
    if sorted(deltas)!=[0,1] or teams[deltas.index(1)]['role']!='Defense':
        return None,'no_unambiguous_defense_score_increment',context
    occurrences=header.get('objectiveOccurrences',[])
    plants=[e for e in occurrences if e['kind']=='plant' and e['source']=='defuser_state_v1']
    disables=[e for e in occurrences if e['kind']=='disable' and e['source']=='defuser_state_and_defense_win_v1']
    if (len(occurrences)!=2 or len(plants)!=1 or len(disables)!=1
            or plants[0]['plantStateOffset']<=0 or plants[0]['plantStateOffset']!=disables[0]['plantStateOffset']):
        return None,'no_verified_plant_and_disable_occurrence',context
    plant=plants[0]['plantStateOffset']
    if any(e['type']['name']=='PlayerLeave' for e in full_feedback):
        return None,'player_leave_timing_unknown',context
    if any(d['offset']<=0 for d in deaths):
        return None,'unknown_death_offset',context
    runs=[r for r in observed['episodes'] if r['state']==1 and r['start_record']>plant]
    complete=[r for r in runs if complete_disable_run(r,slots)]
    context.update(plant_offset=plant,phase1_runs=len(runs),complete_phase1_runs=len(complete))
    if len(complete)!=1:
        return None,'missing_or_competing_complete_disable_runs',context
    run=complete[0]
    end=run_end(run)
    if not end or end<run['samples'][-1]['offset'] or end<=run['start_record']:
        return None,'invalid_terminal_order',context
    # A later attempt proves the selected run was not a final interaction.
    # Unbound timer records after the plant could be a competing player.
    if any(r['start_record']>run['start_record'] for r in runs if r is not run):
        return None,'later_disable_attempt',context
    if any(r['record_start']>plant for r in observed['orphan_records']):
        return None,'unbound_postplant_timer_evidence',context
    binding=run['binding']
    name,owner=binding['player'],binding['owner']
    context.update(owner_observation=name,owner_entity=owner,start=run['start_record'],end=end,
                   terminal=run['end_reason'])
    roster=[p for p in players if p['username']==name]
    if len(roster)!=1 or owners.get(owner)!=name or teams[roster[0]['teamIndex']]['role']!='Defense':
        return None,'timer_owner_identity_or_role_conflict',context
    if (binding['slot'],binding['class_hash'])!=('27c08dca','b2216bf3'):
        return None,'unsupported_timer_component_route',context
    if any(d['offset']<=end and ((d['feedback']['type']['name']=='Kill' and d['feedback'].get('target')==name)
             or (d['feedback']['type']['name']=='Death' and d['feedback'].get('username')==name)) for d in deaths):
        return None,'timer_owner_dead_by_terminal',context
    active,reason,values=active_body(owner,name,run['start_record'],end,owners,slots,properties)
    context.update(body_reason=reason,body_values=values,numeric_uid=roster[0]['id'])
    if not active:
        return None,'timer_owner_body_unresolved',context
    return name,'direct_disable_owner_with_occurrence_and_body',context
