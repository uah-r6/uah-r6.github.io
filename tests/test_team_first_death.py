from r6stats.parser.models import Kill, Match, Player, Round
from r6stats.team_first_death import round_facts


def test_first_team_death_after_own_kill_and_objective_round():
    players = [Player('a', 'A', 0, side='Attack'), Player('b', 'B', 0, side='Attack'),
               Player('x', 'X', 1, side='Defense'), Player('y', 'Y', 1, side='Defense')]
    match = Match('x', '2026-01-01', 'Border', 'CustomGame', 'Bomb', [
        Round(1, 'Site', 1, 'Elimination', players, [
            Kill(1, 110, 'a', 'x', 0, 1), Kill(2, 90, 'y', 'b', 1, 0)]),
        Round(2, 'Site', 0, 'DefuserExploded', players, []),
        Round(3, 'Site', 0, 'Elimination', players, [Kill(1, 90, 'a', 'b', 0, 0)]),
        Round(4, 'Site', 1, 'Elimination', players, [Kill(1, 90, 'a', 'a', 0, 0)])])
    facts = round_facts(match, 0, {'a': 1, 'b': 2},
                        {1: {'slug': 'a', 'name': 'A'}, 2: {'slug': 'b', 'name': 'B'}})
    assert [(f['status'], f['player_slug']) for f in facts] == [
        ('recorded', 'b'), ('no_death', None), ('recorded', 'b'), ('recorded', 'a')]
    assert facts[0]['result'] == 'Loss' and facts[0]['side'] == 'Attack'


def test_first_death_uses_valid_chronology_and_marks_missing_identity_unresolved():
    players = [Player('a', 'A', 0), Player('b', 'B', 0), Player('x', 'X', 1)]
    match = Match('x', '2026-01-01', 'Border', 'CustomGame', 'Bomb', [
        Round(1, 'Site', 1, 'Elimination', players, [
            Kill(1, 110, 'x', 'a', 1, 0), Kill(2, 100, 'x', 'a', 1, 0),
            Kill(3, 90, 'x', 'b', 1, 0)])])
    assert round_facts(match, 0, {}, {})[0]['status'] == 'unresolved'
    assert round_facts(match, 0, {'a': 1}, {1: {'slug': 'a', 'name': 'A'}})[0]['player_slug'] == 'a'
