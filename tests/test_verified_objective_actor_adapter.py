"""Only completing-owner source plus stable UID/role can create new credits."""
import copy

import pytest

from r6stats.parser.models import Match
from r6stats.parser.siege_dissect import normalize


def raw_round():
    return dict(gameVersion='Y11S3_Alpha04',timestamp='2026-09-09T15:15:00Z',matchID='test-objective',
        map=dict(name='Villa'),matchType=dict(name='CustomGameOnline'),gamemode=dict(name='Bomb'),
        teams=[dict(role='Attack',won=False,startingScore=0,score=0),
               dict(role='Defense',won=True,startingScore=0,score=1)],
        players=[dict(username=f'p{i}',profileID=f'profile-{i}',id=100+i,teamIndex=0 if i<5 else 1,
                      operator=dict(name='Ace' if i<5 else 'Mute')) for i in range(10)],
        matchFeedback=[],objectiveOccurrences=[
            dict(kind='plant',source='defuser_state_v1',plantStateOffset=100,actor='p0',actorID=100,
                 actorSource='completing_timer_owner_v1',actorReason='completing_timer_owner_v1'),
            dict(kind='disable',source='defuser_state_and_defense_win_v1',plantStateOffset=100,actor='p5',actorID=105,
                 actorSource='completing_timer_owner_v1',actorReason='completing_timer_owner_v1')])


def test_verified_completion_actors_count_once_and_preserve_uid_provenance():
    raw=raw_round()
    # Legacy timer attribution must not double-count or override the owner.
    raw['matchFeedback']=[dict(type='DefuserPlantComplete',username='p1',timeInSeconds=30,objectiveActorSource='player_packet')]
    parsed=normalize([raw])
    assert [(o.kind,o.player) for o in parsed.rounds[0].objectives]==[('plant','profile-0'),('disable','profile-5')]
    assert [(o.actor,o.actor_uid,o.actor_source) for o in parsed.rounds[0].objective_occurrences]==[
        ('profile-0',100,'completing_timer_owner_v1'),('profile-5',105,'completing_timer_owner_v1')]
    assert Match.from_dict(parsed.to_dict())==parsed


@pytest.mark.parametrize('change',[
    'source','reason','uid','uid_bool','name','role','missing_uid','duplicate_uid','duplicate_kind','zero_anchor','attack_winner'])
def test_unverified_or_conflicting_completion_cannot_smuggle_actor(change):
    raw=raw_round();event=raw['objectiveOccurrences'][1]
    if change=='source':event['actorSource']='score_bonus_unique'
    if change=='reason':event['actorReason']='timer_owner_body_unresolved'
    if change=='uid':event['actorID']=999
    if change=='uid_bool':event['actorID']=True
    if change=='name':event['actor']='unknown'
    if change=='role':event.update(actor='p0',actorID=100)
    if change=='missing_uid':raw['players'][9].pop('id')
    if change=='duplicate_uid':raw['players'][9]['id']=105
    if change=='duplicate_kind':raw['objectiveOccurrences'].append(copy.deepcopy(event))
    if change=='zero_anchor':event['plantStateOffset']=0
    if change=='attack_winner':
        raw['teams'][0]['won']=True;raw['teams'][1]['won']=False
    parsed=normalize([raw])
    assert not any(o.kind=='disable' for o in parsed.rounds[0].objectives)


def test_unresolved_actor_keeps_occurrence_and_reason_without_player_credit():
    raw=raw_round()
    for event in raw['objectiveOccurrences']:
        event.update(actor=None,actorReason='timer_owner_body_unresolved')
        event.pop('actorSource');event.pop('actorID')
    parsed=normalize([raw])
    assert parsed.rounds[0].objectives==[]
    assert len(parsed.rounds[0].objective_occurrences)==2
    assert all(o.actor is None and o.actor_reason=='timer_owner_body_unresolved' for o in parsed.rounds[0].objective_occurrences)
