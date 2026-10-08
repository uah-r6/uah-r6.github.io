"""Reduced current failure shapes; no private replay files or production DB."""
from copy import deepcopy
import json
from pathlib import Path
import struct
from types import SimpleNamespace

import pytest
from r6stats import credited_refresh as credit, objective_refresh as objectives, rating_credit_evidence as rating_credit
from r6stats.credited_refresh import read_archive as real_read_archive
from r6stats.kill_credit import validate_map_credit
from r6stats.objective_proofs import BOUNDED_BONUS, trusted_actor, proven_no_disable
from r6stats.participant_inventory import inventory_valid, SOURCE as INVENTORY, EMPTY_UID
from r6stats.rating_inputs_v3 import prepare, load_inputs, validate_objectives
from r6stats.parser.models import Objective
from test_rating_evidence_repair import setup


def bonus(occurrence, actor):
    occurrence.actor_uid = 3
    occurrence.actor_source = occurrence.actor_reason = BOUNDED_BONUS
    occurrence.actor_evidence = dict(source=BOUNDED_BONUS, actor_uid=3, profile_id=actor.profile_id,
        username=actor.username, owner=100, body_component=300, body_slot=0xc4dc5441, body_class=0x3fc6980c,
        timer_component=200, timer_slot=0xca8dc027, timer_class=0xf36b21b2, start=100, end=500,
        terminal='explicit_state_2', uid_offsets=[20], samples=[dict(offset=110,seconds=6.97),dict(offset=490,seconds=.002)],
        snapshots=[dict(offset=100,state=1,state_offset=50,health=117,baseline=110,ceiling=130,
            fraction_bits=struct.unpack('<I',struct.pack('<f',7/110))[0],field_offsets=[45,10,15,46]),
            dict(offset=410,state=0,state_offset=400),dict(offset=500,state=0,state_offset=400)])


def inventory(players):
    slots = [dict(name_offset=10+i*100,profile_offset=30+i*100,uid_offset=80+i*100,
        username=p['username'],profile_id=p['profileID'],uid=p['uid'],team=p['team']) for i,p in enumerate(players)]
    slots.append(dict(name_offset=910,operator_offset=920,operator_id=0,profile_offset=930,uid_offset=980,
                      username='',profile_id='',uid=EMPTY_UID))
    return dict(source=INVENTORY,action_offset=990,slots=slots)


@pytest.mark.parametrize('mutation',[None,'missing','fraction','hp','terminal_state1','downed','unknown','uid','profile','name','duplicate_samples','canceled','late_return','missing_field','wrong_side','duplicate_occurrence','conflict'])
def test_bounded_bonus_source_requires_all_structural_facts(tmp_path,monkeypatch,mutation):
    db,mid,m,records=setup(tmp_path,monkeypatch)
    r=m.rounds[0];o=r.objective_occurrences[0];actor=next(p for p in r.players if p.key==o.actor)
    bonus(o,actor);proof=o.actor_evidence
    if mutation=='missing':o.actor_evidence=None
    elif mutation=='fraction':proof['snapshots'][0]['fraction_bits']=0
    elif mutation=='hp':proof['snapshots'][0]['health']=100
    elif mutation=='terminal_state1':proof['snapshots'][-1]['state']=1
    elif mutation=='downed':proof['snapshots'][0]['state']=3
    elif mutation=='unknown':proof['snapshots'][0]['state']=5
    elif mutation=='uid':proof['actor_uid']=999
    elif mutation=='profile':proof['profile_id']='other'
    elif mutation=='name':proof['username']='other'
    elif mutation=='duplicate_samples':proof['samples'][1]['offset']=110
    elif mutation=='canceled':proof['samples'][-1]['seconds']=5
    elif mutation=='late_return':proof['snapshots'][-1]['state_offset']=500
    elif mutation=='missing_field':del proof['snapshots'][0]['field_offsets']
    elif mutation=='wrong_side':actor.side='Defense'
    elif mutation=='duplicate_occurrence':r.objective_occurrences.append(deepcopy(o))
    elif mutation=='conflict':r.objectives[0].player=r.players[0].key
    if mutation is None:
        validate_objectives(m);assert prepare(m,records)[0];assert trusted_actor(o,actor)
    else:
        with pytest.raises(ValueError):validate_objectives(m)


@pytest.mark.parametrize('mutation',[None,'missing','wrong_winner','different_entity','late_zero','duplicate_zero','score','actor','second_occurrence','wrong_side'])
def test_false_disable_removal_requires_positive_repeat_proof(tmp_path,monkeypatch,mutation):
    db,mid,m,records=setup(tmp_path,monkeypatch);r=m.rounds[0];o=r.objective_occurrences[0]
    r.starting_scores=(2,3);r.ending_scores=(3,3)
    o.actor_evidence=dict(no_disable=dict(source='repeated_plant_zero_before_transition_v1',actor_uid=o.actor_uid,
        plant_offset=o.plant_state_offset,start=100,end=500,legacy_disable_count=1,winning_team=0,
        starting_scores=[2,3],ending_scores=[3,3],zero_samples=[dict(offset=450,text='0.008',entity=200),dict(offset=480,text='0.004',entity=200)]))
    old=deepcopy(m);old.rounds[0].objectives.append(Objective('disable',r.players[5].key,1,44))
    proof=o.actor_evidence['no_disable']
    if mutation=='missing':o.actor_evidence=None
    elif mutation=='wrong_winner':r.winner=1
    elif mutation=='different_entity':proof['zero_samples'][1]['entity']=201
    elif mutation=='late_zero':proof['zero_samples'][1]['offset']=600
    elif mutation=='duplicate_zero':proof['zero_samples'][1]['offset']=450
    elif mutation=='score':proof['ending_scores'][1]=4
    elif mutation=='actor':proof['actor_uid']=999
    elif mutation=='second_occurrence':r.objective_occurrences.append(deepcopy(o))
    elif mutation=='wrong_side':next(p for p in r.players if p.key==o.actor).side='Defense'
    if mutation is None:
        assert proven_no_disable(r,o)
        new,changes=objectives.overlay(old,m)
        assert changes[0]['actor'] is None and changes[0]['kind']=='disable'
        assert not any(x.kind=='disable' for x in new.rounds[0].objectives)
        assert prepare(new,records)[0]
        assert old.rounds[0].kills==new.rounds[0].kills
    else:assert not proven_no_disable(r,o)


def nine_fixture(tmp_path,monkeypatch):
    db,mid,m,records=setup(tmp_path,monkeypatch)
    for r,record in zip(m.rounds,records):
        r.players.pop();record['credit']['players'].pop()
        record['credit']['participantEvidence']=inventory(record['credit']['players'])
        record['credit']['actionStartOffset']=record['credit']['participantEvidence']['action_offset']
        r.objective_occurrences[0].actor_evidence=dict(participant_inventory=record['credit']['participantEvidence'])
    db.execute('UPDATE maps SET normalized_json=? WHERE id=?',(json.dumps(m.to_dict()),mid));db.commit()
    return db,mid,m,records


@pytest.mark.parametrize('mutation',[None,'missing','source_only','active_empty','profile','uid','offset','nil_uid','team','duplicate','changed_identity','reconnect','stale_action'])
def test_explicit_empty_slot_proves_actual_nine_without_inventing_player(tmp_path,monkeypatch,mutation):
    db,mid,m,records=nine_fixture(tmp_path,monkeypatch);report=records[0]['credit'];proof=report['participantEvidence']
    if mutation=='missing':report.pop('participantEvidence')
    elif mutation=='source_only':report['participantEvidence']={'source':INVENTORY}
    elif mutation=='active_empty':proof['slots'][-1]['operator_id']=123
    elif mutation=='profile':proof['slots'][0]['profile_id']=proof['slots'][1]['profile_id']
    elif mutation=='uid':proof['slots'][0]['uid']=999
    elif mutation=='offset':proof['slots'][0]['uid_offset']=0
    elif mutation=='nil_uid':proof['slots'][-1]['uid']=0
    elif mutation=='team':proof['slots'][0]['team']=1
    elif mutation=='duplicate':proof['slots'].append(deepcopy(proof['slots'][0]))
    elif mutation=='changed_identity':records[1]['credit']['players'][0]['profileID']=records[1]['credit']['players'][1]['profileID']
    elif mutation=='reconnect':records[1]['credit']['players'][0]['uid']=999
    elif mutation=='stale_action':report['actionStartOffset']=991
    if mutation is None:
        assert inventory_valid(report['players'],proof)
        assert validate_map_credit(records)['complete'];assert prepare(m,records)[0]
        assert len(m.rounds[0].players)==9
    else:
        assert not validate_map_credit(records)['complete']
        with pytest.raises(ValueError):prepare(m,records)


def sealed_fixture(tmp_path,monkeypatch):
    db,mid,m,records=nine_fixture(tmp_path,monkeypatch)
    prior=deepcopy(records)
    for r in prior:
        r['credit'].pop('participantEvidence');r['credit']['complete']=False
        for p in r['credit']['players']:p.update(initial=None,terminal=None,kills=None,reason='incomplete_roster')
    credit.store(db,mid,prior,'old-binary')
    monkeypatch.setattr(credit,'read_archive',lambda *a:(deepcopy(records),'new-binary'))
    monkeypatch.setattr(rating_credit,'verify',lambda *a:dict(status='Healthy',path=str(tmp_path)))
    monkeypatch.setattr(rating_credit,'sha256',lambda *a:'manifest-sha')
    return db,mid,m,records


def test_rating_only_sidecar_preserves_all_historical_display_and_complete_evidence(tmp_path,monkeypatch):
    db,mid,m,records=sealed_fixture(tmp_path,monkeypatch)
    # Explicit credit != finisher, with complete direct deltas. Display unchanged.
    for n,r in enumerate(records,1):
        for i,p in enumerate(r['credit']['players']):
            k=2 if i==0 else 1 if i==7 else 0;p.update(initial=(n-1)*k,terminal=n*k,kills=k)
    before=[dict(r) for r in db.execute('SELECT * FROM map_kill_credit')]
    normalized=db.execute('SELECT normalized_json FROM maps').fetchone()[0]
    display=credit.display_stats(m,None)
    with db:rating_credit.store(db,tmp_path,mid,records,'new-binary')
    assert [dict(r) for r in db.execute('SELECT * FROM map_kill_credit')]==before
    assert db.execute('SELECT normalized_json FROM maps').fetchone()[0]==normalized
    assert credit.load(db,mid) is None
    values,reason=load_inputs(db,mid)
    assert reason is None and values[m.rounds[0].players[0].key]['kills']==4
    assert credit.display_stats(m,None)==display
    with db:rating_credit.store(db,tmp_path,mid,records,'new-binary')
    assert db.execute('SELECT count(*) FROM rating_evidence_audit').fetchone()[0]==1
    db.execute("UPDATE map_v3_kill_evidence SET normalized_sha256='stale'");db.commit()
    assert 'Stale' in load_inputs(db,mid)[1]
    db.execute("UPDATE map_v3_kill_evidence SET evidence_sha256='corrupt'");db.commit()
    with pytest.raises(ValueError,match='integrity'):load_inputs(db,mid)


@pytest.mark.parametrize('mutation',['reader','sources','uid','partial','archive','prior_corrupt','complete_prior','ambiguous_empty','audit_failure'])
def test_rating_only_recovery_refuses_stale_conflicting_or_ambiguous_sources(tmp_path,monkeypatch,mutation):
    db,mid,m,records=sealed_fixture(tmp_path,monkeypatch)
    if mutation=='reader':monkeypatch.setattr(credit,'read_archive',lambda *a:([],'other-binary'))
    elif mutation=='sources':records[1]['physical_round']=3
    elif mutation=='uid':records[0]['credit']['players'][0]['uid']=999
    elif mutation=='partial':records[0]['credit']['complete']=False
    elif mutation=='archive':monkeypatch.setattr(rating_credit,'verify',lambda *a:dict(status='Corrupt'))
    elif mutation=='prior_corrupt':db.execute("UPDATE map_kill_credit SET evidence_sha256='corrupt'");db.commit()
    elif mutation=='complete_prior':
        payload=json.dumps(records,sort_keys=True,separators=(',',':'));db.execute('UPDATE map_kill_credit SET evidence_json=?,evidence_sha256=?',(payload,rating_credit.digest(payload)));db.commit()
    elif mutation=='ambiguous_empty':records[0]['credit']['participantEvidence']['slots'][-1]['operator_id']=1
    else:
        def fail(*a,**k):raise ValueError('audit failed')
        monkeypatch.setattr('r6stats.rating_evidence.record_audit',fail)
    prior=[dict(r) for r in db.execute('SELECT * FROM map_kill_credit')]
    with pytest.raises(ValueError),db:
        db.execute('BEGIN IMMEDIATE')
        rating_credit.store(db,tmp_path,mid,records,'new-binary')
    assert [dict(r) for r in db.execute('SELECT * FROM map_kill_credit')]==prior
    assert not db.execute("SELECT 1 FROM sqlite_master WHERE name='map_v3_kill_evidence'").fetchone()


def test_reader_cache_key_changes_with_binary_and_preserves_successful_cache(tmp_path,monkeypatch):
    archive=tmp_path/'archive';archive.mkdir();rec=archive/'Match-R01.rec';rec.write_bytes(b'private fixture')
    from r6stats.replay_archive import sha256
    (archive/'manifest.json').write_text(json.dumps(dict(archive_format_version=1,files=[dict(physical_round_number=1,filename=rec.name,sha256=sha256(rec))])))
    monkeypatch.setattr(credit,'verify',lambda *a:dict(status='Healthy',path=str(archive)))
    calls=[]
    def run(*a,**k):calls.append(a);return SimpleNamespace(stdout=json.dumps({'credit':{'source':'fixture'}}))
    monkeypatch.setattr(credit.subprocess,'run',run)
    exe=tmp_path/'reader.exe';exe.write_bytes(b'binary-one')
    a=real_read_archive(None,tmp_path/'archive-root','fixture',exe)
    assert real_read_archive(None,tmp_path/'archive-root','fixture',exe)==a and len(calls)==1
    exe.write_bytes(b'binary-two');b=real_read_archive(None,tmp_path/'archive-root','fixture',exe)
    assert b[1]!=a[1] and len(calls)==2
    assert len(list((tmp_path/'kill-credit-cache').glob('*.json')))==2


def test_archive_maintenance_commits_nine_player_rating_proof_and_objective_together(tmp_path,monkeypatch):
    from r6stats import rating_evidence as maintenance
    db,mid,fresh,records=sealed_fixture(tmp_path,monkeypatch)
    old=deepcopy(fresh);old.rounds[1].objectives=[];old.rounds[1].objective_occurrences=[]
    db.execute('UPDATE maps SET normalized_json=? WHERE id=?',(json.dumps(old.to_dict()),mid));db.commit()
    monkeypatch.setattr(maintenance.objective_refresh,'parse_archive',lambda *a:deepcopy(fresh))
    prior=[dict(r) for r in db.execute('SELECT * FROM map_kill_credit')]
    original_rounds=[tuple(r) for r in db.execute('SELECT * FROM rounds')]
    result=maintenance.repair(db,tmp_path,mid)
    assert result['after']['eligible'] and result['changes']==['supported objective actor correction','Rating-only credited evidence'], result
    assert load_inputs(db,mid)[0] is not None
    assert [dict(r) for r in db.execute('SELECT * FROM map_kill_credit')]==prior
    assert [tuple(r) for r in db.execute('SELECT * FROM rounds')]==original_rounds
    assert maintenance.repair(db,tmp_path,mid)['changes']==[]
