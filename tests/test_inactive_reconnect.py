"""Actual sanitized Y11 inactive account, late reconnect and next-round return."""
from copy import deepcopy
import json
from pathlib import Path
import sqlite3

from fastapi.testclient import TestClient
import pytest

from r6stats import credited_refresh, rating_credit_evidence, rating_evidence, objective_refresh
from r6stats.admin.server import create_app
from r6stats.db import repository as repo
from r6stats.kill_credit import validate_map_credit
from r6stats.parser.models import Match
from r6stats.participant_inventory import inventory_valid
from r6stats.rating_inputs_v3 import prepare, load_inputs

FIXTURE=Path(__file__).parent/'fixtures/inactive-reconnect-map-y11.json'


def fixture():
    value=json.loads(FIXTURE.read_text(encoding='utf-8'))
    return Match.from_dict(value['match']),value['records']


def test_real_three_round_reconnect_requires_all_counters_and_preserves_actual_participation():
    match,records=fixture()
    credit=validate_map_credit(records)
    assert credit['complete'] and credit['issues']==[]
    assert credit['participation_transitions'][0]['round']==2
    assert credit['participation_transitions'][0]['returned_round']==3
    proof=records[1]['credit']['participantEvidence']
    assert inventory_valid(match.rounds[1].players,proof)
    before=match.to_dict()
    stats,rounds=prepare(match,records)
    # No synthetic tenth combatant and no four-kill reconnect restoration.
    assert len(match.rounds[1].players)==9
    assert stats['00000000-0000-0000-0000-00000000000a']['rounds']==2
    assert stats['00000000-0000-0000-0000-00000000000a']['kills']==0
    assert stats['00000000-0000-0000-0000-000000000002']['rounds']==3
    assert match.to_dict()==before


@pytest.mark.parametrize('mutation',[
    'missing','anonymous_source','name','profile','uid','operator','slot','team','owner',
    'action','absent_body','body_at_action','body_component','state','health','missing_vital',
    'duplicate_vital','late_body_sample','uid_at_score','unknown_uid','counter_owner',
    'counter_component','counter_declaration','initial_counter','counter_range','missing_counter',
    'counter_offset','bool_uid',
])
def test_nine_player_proof_rejects_partial_active_or_ambiguous_reconnect(mutation):
    match,records=fixture();proof=records[1]['credit']['participantEvidence']
    r=proof['inactive_reconnect'];slot=proof['slots'][r['slot_index']]
    if mutation=='missing':proof.pop('inactive_reconnect')
    elif mutation=='anonymous_source':proof['source']='explicit_ten_slot_empty_participant_v1'
    elif mutation=='name':slot['username']='Other'
    elif mutation=='profile':slot['profile_id']=str(match.rounds[1].players[0].profile_id)
    elif mutation=='uid':slot['uid']=10
    elif mutation=='operator':slot['operator_id']=1
    elif mutation=='slot':r['slot_index']=0
    elif mutation=='team':r['team']=0
    elif mutation=='owner':r['owner']=0
    elif mutation=='action':proof['action_offset']=r['body_offset']
    elif mutation=='absent_body':r['absent_body_offset']=slot['name_offset']+1
    elif mutation=='body_at_action':r['body_offset']=proof['action_offset']-1
    elif mutation=='body_component':r['body_component']=r['score_component']
    elif mutation=='state':next(f for f in r['body_fields'] if f['tag']==0xa5f688e7)['bits']=0
    elif mutation=='health':r['body_fields'][0]['bits']=110
    elif mutation=='missing_vital':r['body_fields'].pop()
    elif mutation=='duplicate_vital':r['body_fields'][1]=deepcopy(r['body_fields'][0])
    elif mutation=='late_body_sample':r['body_fields'][-1]['offset']=r['uid_offset']+1
    elif mutation=='uid_at_score':r['uid_offset']=r['score_offset']
    elif mutation=='unknown_uid':r['uid']=records[1]['credit']['players'][0]['uid']
    elif mutation=='counter_owner':r['counters'][1]['owner']+=1
    elif mutation=='counter_component':r['counters'][1]['component']+=1
    elif mutation=='counter_declaration':r['counters'][1]['declarationOffset']+=1
    elif mutation=='initial_counter':r['counters'][0]['value']=1
    elif mutation=='counter_range':r['counters'][1]['value']=251
    elif mutation=='missing_counter':r['counters'].pop()
    elif mutation=='counter_offset':r['counters'][0]['offset']=r['uid_offset']+1
    else:r['uid']=True
    assert not inventory_valid(match.rounds[1].players,proof)
    assert not validate_map_credit(records)['complete']


@pytest.mark.parametrize('mutation',[
    'no_prior','no_return','prior_name','prior_profile','prior_team','prior_uid',
    'prior_counter','active_prior_counter','active_prior_uid','return_name',
    'return_profile','return_uid','return_counter','active_return_counter','active_return_uid',
    'new_segment','gap',
])
def test_reconnect_requires_exact_surrounding_round_identity_and_counter_evidence(mutation):
    _,records=fixture();previous,current,following=[r['credit'] for r in records]
    before=next(p for p in previous['players'] if p['username']=='Player10')
    after=next(p for p in following['players'] if p['username']=='Player10')
    if mutation=='no_prior':records=records[1:];records[0]['logical_round']=1;records[1]['logical_round']=2
    elif mutation=='no_return':records.pop()
    elif mutation=='prior_name':before['username']='Other'
    elif mutation=='prior_profile':before['profileID']='00000000-0000-0000-0000-000000000063'
    elif mutation=='prior_team':before['team']=0
    elif mutation=='prior_uid':before['uid']=10
    elif mutation=='prior_counter':before['initial']=before['terminal']=5;before['kills']=0
    elif mutation=='active_prior_counter':previous['players'][0].update(initial=99,terminal=99,kills=0)
    elif mutation=='active_prior_uid':previous['players'][0]['uid']=99
    elif mutation=='return_name':after['username']='Other'
    elif mutation=='return_profile':after['profileID']='00000000-0000-0000-0000-000000000063'
    elif mutation=='return_uid':after['uid']=99
    elif mutation=='return_counter':after.update(initial=99,terminal=99,kills=0)
    elif mutation=='active_return_counter':following['players'][0].update(initial=99,terminal=99,kills=0)
    elif mutation=='active_return_uid':following['players'][0]['uid']=99
    elif mutation=='new_segment':records[1]['segment']='unknown-folder'
    else:records[2]['physical_round']+=1
    assert not validate_map_credit(records)['complete']


def test_admin_archive_repair_seals_reconnect_evidence_without_changing_history(tmp_path,monkeypatch):
    match,records=fixture()
    root=tmp_path
    (root/'config').mkdir()
    (root/'config/settings.json').write_text(json.dumps({'team':{},'stats':{
        'rating_version':'siege_style_v3','trade_window_seconds':8}}),encoding='utf-8')
    db=repo.connect(root/'data/r6stats.sqlite')
    repo.season_create(db,'Fall 2026')
    for p in match.rounds[0].players:
        if p.team==0:repo.roster_add(db,p.username,team_id=1)
    mid=repo.insert_map(db,match,'fingerprint',0,'Opponent',organization_team_id=1)
    original=deepcopy(records);broken=original[1]['credit']
    broken.pop('participantEvidence');broken.update(complete=False,reason='incomplete_or_ambiguous_uid_roster')
    for p in broken['players']:
        p.update(initial=None,terminal=None,kills=None,samples=[],reason=broken['reason'])
    credited_refresh.store(db,mid,original,'old-binary')
    tables=('maps','rounds','round_players','kill_events','objective_events','players','map_kill_credit','rating_input_snapshots')
    history={t:[tuple(r) for r in db.execute('SELECT * FROM '+t)] for t in tables}
    db.close()
    monkeypatch.setattr(credited_refresh,'read_archive',lambda *args:(deepcopy(records),'current-binary'))
    monkeypatch.setattr(rating_evidence.replay_archive,'verify',lambda *args:{'status':'Healthy','path':str(root)})
    monkeypatch.setattr(rating_evidence.replay_archive,'sha256',lambda *args:'manifest-sha')
    monkeypatch.setattr(rating_credit_evidence,'verify',lambda *args:{'status':'Healthy','path':str(root)})
    monkeypatch.setattr(rating_credit_evidence,'sha256',lambda *args:'manifest-sha')
    monkeypatch.setattr(objective_refresh,'parse_archive',lambda *args,**kwargs:deepcopy(match))
    with TestClient(create_app(root)) as client:
        headers={'X-R6-Admin-Token':client.get('/api/admin/session').json()['token']}
        response=client.post(f'/api/admin/matches/{mid}/rating-evidence',headers=headers,json={'confirm_map_id':mid})
        assert response.status_code==200,response.text
        result=response.json()
        assert result['after']['eligible'] and result['after']['credited_issues']==[] and result['blockers']==[]
        assert result['after']['credited_status']=='complete (Rating only)'
        assert result['after']['display_credited_status']=='incomplete'
        assert client.post(f'/api/admin/matches/{mid}/rating-evidence',headers=headers,json={'confirm_map_id':mid}).json()['changes']==[]
    with sqlite3.connect(root/'data/r6stats.sqlite') as db:
        db.row_factory=sqlite3.Row
        for table,rows in history.items():assert [tuple(r) for r in db.execute('SELECT * FROM '+table)]==rows,table
        assert load_inputs(db,mid)[1] is None
    public=json.loads((root/f'web/public/data/matches/{mid}.json').read_text(encoding='utf-8'))
    assert public['rating_eligible'] and all(p['rating'] is not None for p in public['players'])
