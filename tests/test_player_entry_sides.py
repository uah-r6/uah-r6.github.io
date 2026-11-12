from copy import deepcopy

from r6stats.parser.models import Match, Round, Player, Kill
from r6stats.stats.calculate import calculate_match, aggregate
from r6stats.credited_refresh import display_stats


def fixture():
    players=[Player('a','Alpha',0,'Ace','Attack'),Player('b','Bravo',0,'Buck','Attack'),
             Player('x','Xray',1,'Mute','Defense'),Player('y','Yankee',1,'Smoke','Defense')]
    defense=deepcopy(players)
    for p in defense:p.side='Defense' if p.team==0 else 'Attack'
    return Match('entry','2026-11-11T00:00:00Z','Bank','CustomGame','Bomb',[
        Round(1,'Site',0,'KilledOpponents',players,[Kill(0,90,'a','x',0,1),Kill(1,80,'y','b',1,0)]),
        Round(2,'Site',1,'KilledOpponents',defense,[Kill(0,90,'x','a',1,0)]),
        Round(3,'Site',0,'KilledOpponents',deepcopy(players),[
            Kill(0,110,'b','b',0,0),Kill(1,100,'a','x',0,1)])])


def test_entry_side_counts_use_first_valid_opposing_kill_and_aggregate():
    match=fixture();stats=calculate_match(match)
    a=stats['a']
    assert (a['opening_kills'],a['opening_deaths'])==(2,1)
    assert (a['sides']['Attack']['opening_kills'],a['sides']['Attack']['opening_deaths'])==(2,0)
    assert (a['sides']['Defense']['opening_kills'],a['sides']['Defense']['opening_deaths'])==(0,1)
    assert stats['y']['opening_kills']==0
    assert stats['b']['opening_deaths']==0
    combined=aggregate([stats['a'],stats['a']])
    assert combined['sides']['Attack']['opening_kills']==4
    assert combined['sides']['Defense']['opening_deaths']==2
    assert display_stats(match,None)['a']['sides']==a['sides']


def test_side_counts_are_additive_without_changing_any_existing_statistics():
    match=fixture();whole=calculate_match(match)
    for key in whole:
        assert whole[key]['opening_kills']==sum(s['opening_kills'] for s in whole[key]['sides'].values())
        assert whole[key]['opening_deaths']==sum(s['opening_deaths'] for s in whole[key]['sides'].values())
    legacy=deepcopy(whole['a'])
    for s in legacy['sides'].values():s.pop('opening_kills');s.pop('opening_deaths')
    total=aggregate([legacy])
    assert total['kills']==whole['a']['kills'] and total['rating']==whole['a']['rating']
