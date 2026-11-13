from r6stats.parser.models import Kill, Match, Player, Round
from r6stats.team_first_kill import round_facts


def test_first_team_kill_after_opponent_opener_and_side_breakdown():
    players=[Player('a','A',0,side='Attack'),Player('b','B',0,side='Attack'),
             Player('x','X',1,side='Defense'),Player('y','Y',1,side='Defense')]
    rounds=[Round(1,'Site',0,'Elimination',players,[
        Kill(1,100,'x','a',1,0),Kill(2,90,'b','x',0,1),Kill(3,80,'b','y',0,1)]),
        Round(2,'Site',1,'Elimination',players,[Kill(1,90,'x','a',1,0)]),
        Round(3,'Site',0,'Elimination',players,[Kill(1,100,'a','b',0,0),Kill(2,90,'a','x',0,1)])]
    match=Match('x','2026-01-01','Border','CustomGame','Bomb',rounds)
    facts=round_facts(match,0,{'a':1,'b':2},{1:{'slug':'a','name':'A'},2:{'slug':'b','name':'B'}})
    assert [(f['status'],f['player_slug']) for f in facts]==[('recorded','b'),('no_kill',None),('recorded','a')]
    assert facts[0]['result']=='Win' and facts[0]['side']=='Attack'


def test_first_team_kill_rejects_invalid_or_dead_victim_and_unbound_player():
    players=[Player('a','A',0),Player('x','X',1),Player('y','Y',1)]
    match=Match('x','2026-01-01','Border','CustomGame','Bomb',[Round(1,'Site',0,'Elimination',players,[
        Kill(1,110,'x','y',1,1),Kill(2,100,'a','y',0,1),Kill(3,90,'a','x',0,1)])])
    assert round_facts(match,0,{}, {})[0]['status']=='unresolved'
    assert round_facts(match,0,{'a':1},{1:{'slug':'a','name':'A'}})[0]['player_slug']=='a'
