"""Conservative research actor modes; labels are used only after resolution.

Unfrozen until the exact plan, consumed outcomes and regression gates have been
committed. The deployed parser and all historical statistics remain untouched.
"""
from collections import Counter, defaultdict
import json

from objective_actor_liveness import feedback, interaction_span
from objective_clock_candidate import candidate as score_candidate
from objective_disable_structure import score_wave
from objective_clock_candidate import epochs
from objective_score_delta_validation import grade
from objective_state_components import probe
from objective_transition_probe import ROOT


def declared_body_states(raw):
    """Join only the verified direct health slot/class to unique numeric UIDs."""
    names = {p['id']:p['username'] for p in raw['header']['players'] if p.get('id')}
    owners = defaultdict(set)
    for prop in raw['properties']:
        if prop['kind']=='numeric_uid':
            owners[prop['entity']].add(prop['value'])
    components = defaultdict(set)
    component_owners = defaultdict(set)
    for d in raw['declarations']:
        if (d['slot_hash'],d['class_hash'])==('4154dcc4','0c98c63f'):
            components[d['owner']].add(d['component'])
            component_owners[d['component']].add(d['owner'])
    binding = defaultdict(set)
    for owner,uids in owners.items():
        if (len(uids)==1 and next(iter(uids)) in names and len(components[owner])==1
                and len(component_owners[next(iter(components[owner]))])==1):
            binding[names[next(iter(uids))]].update(components[owner])
    reverse = defaultdict(set)
    for name,entities in binding.items():
        for entity in entities:
            reverse[entity].add(name)
    result = {}
    for name,entities in binding.items():
        if len(entities)==1 and len(reverse[next(iter(entities))])==1:
            entity = next(iter(entities))
            result[name] = [p for p in raw['properties'] if p['entity']==entity and p['hash']=='e788f6a5'
                            and p['size']==4]
    return result


def values_during(states, start, end):
    prior = [p for p in states if p['offset']<=start]
    if not prior:
        return []
    return [prior[-1]['value']] + [p['value'] for p in states if start<p['offset']<=end]


def dead_by(name, deaths, offset):
    return any(d['offset']>0 and d['offset']<=offset and (
        (d['feedback']['type']['name']=='Kill' and d['feedback'].get('target')==name) or
        (d['feedback']['type']['name']=='Death' and d['feedback'].get('username')==name)) for d in deaths)


def combine(row, deaths, timers, body, full_feedback, previous_state=0):
    context = {}
    if row['kind'] not in ('plant','disable'):
        return None,'unsupported_objective',context
    if any(e['type']['name']=='PlayerLeave' for e in full_feedback):
        return None,'player_leave_timing_unknown',context
    if any(d['offset']<=0 for d in deaths):
        return None,'unknown_death_offset',context
    players = row['header']['players']
    if (len(players)!=10 or len({p['username'] for p in players})!=10
            or any(not p.get('id') for p in players) or len({p['id'] for p in players})!=10):
        return None,'incomplete_player_roster',context
    side = 'Attack' if row['kind']=='plant' else 'Defense'
    eligible = {p['username'] for p in players if row['header']['teams'][p['teamIndex']]['role']==side}
    if len(eligible)!=5 or any(p not in body or not body[p] for p in eligible):
        return None,'incomplete_declared_body_identity',context
    mapping = {int(k):v[0] for k,v in row['identity']['entity_names'].items() if len(v)==1}
    bound = [p for p in mapping.values() if p in eligible]
    if len(bound)!=5 or len(set(bound))!=5:
        return None,'incomplete_score_identity',context
    span = interaction_span(timers,row['center'],previous_state)
    context['interaction_span'] = span
    if not span:
        return None,'incomplete_interaction_span',context
    start,end = span['first_offset'],row['center']
    states = {p:values_during(body[p],start,end) for p in eligible}
    context['body_states_during_interaction'] = states
    remaining = [p for p in eligible if not dead_by(p,deaths,start)]
    sole = None
    # Unknown state is not a death. Every excluded teammate needs BOTH an
    # existing Kill/Death before interaction and state4 throughout it.
    if len(remaining)==1:
        survivor = remaining[0]
        if (not dead_by(survivor,deaths,end) and states[survivor]
                and set(states[survivor])<= {0,2}
                and all(states[p] and set(states[p])=={4} for p in eligible-{survivor})):
            sole = survivor
    scored,score_reason,interval = score_candidate(row,deaths)
    context.update(score_proposal=scored,score_reason=score_reason,score_interval=interval,sole_proposal=sole)
    # A raw conflicting proposal causes abstention even if its body check
    # subsequently fails. No fallback silently discards conflicting evidence.
    if scored and sole and scored!=sole:
        return None,'evidence_conflict',context
    if scored:
        if (dead_by(scored,deaths,end) or not states[scored] or not set(states[scored])<= {0,2}):
            context['score_guard']='body_or_death_conflict'
            scored = None
        else:
            context['score_guard']='active_body_throughout_interaction'
    if row['kind']=='disable' and sole:
        # Relative scores are supporting evidence only. They never select an
        # actor alone; a unique excess conflicting with the sole mode vetoes it.
        from bisect import bisect_right
        ticks = epochs(row['clock_ticks'])
        index = bisect_right([t['offset'] for t in ticks],end)-1
        if index>=0:
            window_end = ticks[index+2]['offset'] if index+2<len(ticks) else None
            wave = score_wave(row,mapping,eligible,ticks[index]['offset'],window_end)
            context['relative_wave'] = wave
            excess = wave['excess_observation']
            if len(excess)==1 and excess[0]!=sole:
                return None,'relative_wave_conflicts_with_sole',context
    if scored and sole:
        return scored,'score_and_sole_agree',context
    if scored:
        return scored,'standalone_clock_with_body_guard',context
    if sole:
        return sole,'sole_proven_survivor_throughout_interaction',context
    return None,'no_unambiguous_guarded_mode',context


def evaluate(name):
    base = ROOT / 'data/research/diagnostics'
    rows = json.loads((base / f'objective-score-structure-{name}.json').read_text())
    sources = {s['siegegg_match_id']:s for s in json.loads((ROOT/'research/sources.json').read_text())['matches']
               if s.get('siegegg_match_id')}
    labels = json.loads((base/'objective-score-delta-validation/summary.json').read_text())['events']
    development = json.loads((base/'objective-encoding-validation/summary.json').read_text())['rounds']
    records = []
    for row in rows:
        folder = next((ROOT/'data/research/extracted').rglob(row['folder']))
        rec = next(folder.glob(f"*-R{row['round']:02d}.rec"))
        raw,feed = probe(rec),feedback(rec)
        previous = max((r['center'] for r in rows if r['folder']==row['folder'] and r['round']==row['round']
                        and r['center']<row['center']),default=0)
        actor,mode,context = combine(row,feed['events'],feed['timers'],declared_body_states(raw),raw['feedback'],previous)
        # Targets first accessed here, after the candidate is returned.
        if name=='development':
            reference = next(d for d in development if (d['match_id'],d['round'])==(row['match_id'],row['round']))
            label = next(e for e in reference['public_objectives'] if e['type']==row['kind'])
            label = label.get('description',label.get('html',''))
        elif row['match_id']==4139:
            label = 'Raid plants defuser'
        else:
            reference = next(e for e in labels if all(e[k]==row[k] for k in ('match_id','game_id','round','kind')))
            label = reference['public_actor'] + (' plants ' if row['kind']=='plant' else ' disables ') + 'defuser'
        target = json.loads((ROOT/f"data/research/targets/siegegg-match-{row['match_id']}-api.json").read_text())
        verdict = grade(actor,label,sources[row['match_id']],target)
        records.append({k:row[k] for k in ('match_id','game_id','round','kind','build')}
                       | dict(candidate=actor,mode=mode,verdict=verdict,context=context))
    if name=='development':
        for row in development:
            for event in row['public_objectives']:
                if not any((r['match_id'],r['round'],r['kind'])==(row['match_id'],row['round'],event['type']) for r in records):
                    records.append(dict(match_id=row['match_id'],game_id=None,round=row['round'],kind=event['type'],
                                        build=None,candidate=None,mode='missing_completion_anchor',verdict='unresolved',context={}))
    cohort = [r for r in records if name=='development' or r['match_id']!=4139]
    counts = {kind:dict(Counter(r['verdict'] for r in cohort if r['kind']==kind)) for kind in ('plant','disable')}
    modes = {kind:dict(Counter(r['mode'] for r in cohort if r['kind']==kind and r['candidate'])) for kind in ('plant','disable')}
    (base/f'objective-combined-candidate-{name}.json').write_text(json.dumps(dict(counts=counts,modes=modes,events=records),indent=2))
    lines = ['# Combined guarded objective diagnostic: '+name,'',
             'Consumed development only; not independently validated or deployed. Exact modes in '
             '`objective_combined_candidate.py`. All candidates require a complete seven-second timer run, '
             'stable declared body identity and scoreboard identity, no unknown death offsets or PlayerLeave, '
             'and active state0/2 throughout interaction. Sole mode requires every other teammate killed before '
             'interaction plus state4 throughout. Standalone plant mode retains clock and kill/assist guards. '
             'Conflicts abstain; relative disable score never selects an actor alone.', '',
             f'Counts: `{counts}`. Resolved modes: `{modes}`.', '',
             '| Match/game/round/kind | Candidate | Verdict | Mode / abstention |','| --- | --- | --- | --- |']
    for r in records:
        lines.append(f"| {r['match_id']}/{r['game_id']}/R{r['round']:02d}/{r['kind']} | {r['candidate'] or 'unresolved'} | {r['verdict']} | {r['mode']} |")
    lines += ['', 'State2 is independently seen on active players, so it is not excluded as DBNO. '
              'State3/unknown never establishes eligibility or teammate death. Fresh reserve remains sealed '
              'until specification, consumed results, targeted tests and a clean local freeze commit.', '']
    (ROOT/f'research/output/objective-combined-candidate-{name}.md').write_text('\n'.join(lines),encoding='utf-8')
    print(name,counts,modes,'wrong',[r for r in records if r['verdict']=='incorrect'])


if __name__=='__main__':
    evaluate('development')
    evaluate('extension')
