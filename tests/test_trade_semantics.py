"""Behavioural trade cases for the existing normalized replay statistics path."""
from r6stats.parser.models import Kill, Match, Objective, Player, Round
from r6stats.stats.calculate import calculate_match


PLAYERS = [Player(name, name, team, side='Attack' if team == 0 else 'Defense')
           for team, names in ((0, 'abc'), (1, 'xyz')) for name in names]


def kill(seq, remaining, killer, victim):
    teams = {p.key: p.team for p in PLAYERS}
    return Kill(seq, remaining, killer, victim, teams.get(killer, -1), teams[victim])


def stats(events, *, window=8, objectives=(), second_round=()):
    rounds = [Round(1, '', 0, '', PLAYERS, events, list(objectives))]
    if second_round:
        rounds.append(Round(2, '', 1, '', PLAYERS, list(second_round)))
    return calculate_match(Match('test', '', '', '', 'Bomb', rounds), window)


def test_original_killer_must_be_refragged_within_window():
    actual = stats([kill(0, 100, 'x', 'a'), kill(1, 94, 'b', 'x')])
    assert (actual['a']['deaths_traded'], actual['x']['kills_traded'], actual['b']['refrag_kills']) == (1, 1, 1)
    unrelated = stats([kill(0, 100, 'x', 'a'), kill(1, 94, 'b', 'y')])
    assert unrelated['a']['deaths_traded'] == unrelated['x']['kills_traded'] == 0
    assert stats([kill(0, 100, 'x', 'a'), kill(1, 91, 'b', 'x')], window=8)['a']['deaths_traded'] == 0
    assert stats([kill(0, 100, 'x', 'a'), kill(1, 92, 'b', 'x')], window=8)['a']['deaths_traded'] == 1


def test_chain_and_intervening_kill_do_not_cancel_links():
    result = stats([kill(0, 100, 'x', 'a'), kill(1, 98, 'c', 'y'),
                    kill(2, 96, 'b', 'x'), kill(3, 94, 'z', 'b')])
    assert result['a']['deaths_traded'] == 1
    assert result['x']['deaths_traded'] == result['x']['kills_traded'] == 1
    assert result['b']['deaths_traded'] == 0
    assert result['b']['kills_traded'] == 1
    assert result['b']['refrag_kills'] == result['z']['refrag_kills'] == 1


def test_same_timer_uses_sequence_and_round_end_is_included():
    result = stats([kill(0, 0, 'x', 'a'), kill(1, 0, 'b', 'x')])
    assert result['a']['deaths_traded'] == 1
    assert result['b']['refrag_kills'] == 1
    reverse = stats([kill(0, 0, 'b', 'x'), kill(1, 0, 'x', 'a')])
    assert reverse['a']['deaths_traded'] == 0


def test_teamkill_suicide_and_environment_cannot_complete_trade():
    teamkill = stats([kill(0, 100, 'x', 'y'), kill(1, 98, 'z', 'x')])
    assert teamkill['y']['deaths_traded'] == 0
    suicide = stats([kill(0, 100, 'x', 'x'), kill(1, 98, 'a', 'y')])
    assert suicide['x']['kills_traded'] == 0
    environmental = stats([kill(0, 100, 'x', 'a'), kill(1, 98, '', 'x')])
    assert environmental['a']['deaths_traded'] == 0
    assert environmental['x']['untraded_kills'] == 1


def test_multiple_earlier_victims_one_refrag_and_no_duplicate_credit():
    result = stats([kill(0, 100, 'x', 'a'), kill(1, 99, 'x', 'b'),
                    kill(2, 98, 'c', 'x')])
    assert result['a']['deaths_traded'] == result['b']['deaths_traded'] == 1
    assert result['x']['kills_traded'] == 2
    assert result['c']['refrag_kills'] == 1


def test_objectives_and_round_boundaries_are_independent():
    original = [kill(0, 100, 'x', 'a')]
    result = stats(original, objectives=[Objective('plant', 'b', 0, 95)],
                   second_round=[kill(0, 99, 'b', 'x')])
    assert result['a']['deaths_traded'] == 0
    assert result['x']['kills_traded'] == 0
    assert result['b']['plants'] == 1
    assert result['b']['refrag_kills'] == 0
