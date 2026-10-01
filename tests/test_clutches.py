"""1vX wins come from the stored death timeline and round winner."""

from r6stats.parser.models import Kill, Match, Objective, Player, Round
from r6stats.stats.calculate import aggregate, calculate_match


def fixture(teammates, opponents, deaths, winner=0, objectives=()):
    players = [Player(name, name, team, side="Attack" if team == 0 else "Defense")
               for team, names in ((0, teammates), (1, opponents))
               for name in names]
    kills = [Kill(index, 100 - index, killer, victim,
                  next((p.team for p in players if p.key == killer), -1),
                  next(p.team for p in players if p.key == victim))
             for index, (killer, victim) in enumerate(deaths)]
    round_ = Round(1, "Site", winner, "Bomb", players, kills, list(objectives))
    return Match("fixture", "2026-09-29T00:00:00Z", "Bank", "Custom Game", "Bomb", [round_])


def assert_clutch(stats, player, size):
    assert stats[player]["clutches"] == int(size > 0)
    for x in range(1, 6):
        assert stats[player][f"clutch_1v{x}"] == int(x == size)


def test_1v1_win():
    stats = calculate_match(fixture(["a", "b"], ["c"], [("c", "b"), ("a", "c")]))
    assert_clutch(stats, "a", 1)


def test_1v2_win():
    stats = calculate_match(fixture(["a", "b"], ["c", "d"],
                                    [("c", "b"), ("a", "c"), ("a", "d")]))
    assert_clutch(stats, "a", 2)


def test_1v3_counts_only_first_size():
    stats = calculate_match(fixture(["a", "b"], ["c", "d", "e"],
                                    [("c", "b"), ("a", "c"), ("a", "d"), ("a", "e")]))
    assert_clutch(stats, "a", 3)
    assert stats["a"]["clutches"] == sum(stats["a"][f"clutch_1v{x}"] for x in range(1, 6))


def test_1v4_and_1v5_buckets():
    for size in (4, 5):
        opponents = [f"enemy{x}" for x in range(size)]
        deaths = [(opponents[0], "b"), *(("a", enemy) for enemy in opponents)]
        stats = calculate_match(fixture(["a", "b"], opponents, deaths))
        assert_clutch(stats, "a", size)


def test_1v2_loss_does_not_count():
    stats = calculate_match(fixture(["a", "b"], ["c", "d"],
                                    [("c", "b"), ("d", "a")], winner=1))
    assert_clutch(stats, "a", 0)


def test_win_without_sole_survivor_does_not_count():
    stats = calculate_match(fixture(["a", "b"], ["c", "d"],
                                    [("a", "c"), ("b", "d")]))
    assert_clutch(stats, "a", 0)
    assert_clutch(stats, "b", 0)


def test_sole_survivor_with_no_opponents_does_not_count():
    stats = calculate_match(fixture(["a", "b"], ["c"],
                                    [("a", "c"), ("b", "b")]))
    assert_clutch(stats, "a", 0)


def test_objective_win_counts_even_if_clutch_player_dies_later():
    stats = calculate_match(fixture(["a", "b"], ["c", "d"],
                                    [("c", "b"), ("d", "a")], winner=0,
                                    objectives=[Objective("plant", "a", 0, 110),
                                                Objective("disable", "c", 1, 90)]))
    assert_clutch(stats, "a", 2)
    assert stats["a"]["deaths"] == 1
    assert stats["a"]["plants"] == 1
    assert stats["a"]["disables"] == 0
    assert stats["a"]["objectives"] == 1
    assert stats["a"]["kost_rounds"] == 1
    assert stats["c"]["disables"] == 1


def test_teamkill_changes_alive_count_without_enemy_kill():
    stats = calculate_match(fixture(["a", "b"], ["c", "d"], [("a", "b")]))
    assert_clutch(stats, "a", 2)
    assert stats["a"]["kills"] == 0
    assert stats["a"]["teamkills"] == 1


def test_dead_player_cannot_be_clutch_candidate():
    stats = calculate_match(fixture(["a", "b"], ["c", "d"], [("c", "a")]))
    assert_clutch(stats, "a", 0)
    assert_clutch(stats, "b", 2)


def test_map_season_and_career_aggregation_preserve_sizes_and_other_stats():
    one = calculate_match(fixture(["a", "b"], ["c"],
                                  [("c", "b"), ("a", "c")],
                                  objectives=[Objective("plant", "a", 0, 105)]))["a"]
    two = calculate_match(fixture(["a", "b"], ["c", "d"],
                                  [("c", "b"), ("a", "c"), ("a", "d")]))["a"]
    season = aggregate([one, two])
    career = aggregate([season])
    for stats in (season, career):
        assert stats["clutches"] == 2
        assert [stats[f"clutch_1v{x}"] for x in range(1, 6)] == [1, 1, 0, 0, 0]
        assert stats["clutches"] == sum(stats[f"clutch_1v{x}"] for x in range(1, 6))
        assert stats["kills"] == 3
        assert stats["deaths"] == 0
        assert stats["plants"] == 1
        assert stats["disables"] == 0
        assert stats["objectives"] == 1
        assert stats["kost_rounds"] == 2
    assert one["clutches"] == one["clutch_1v1"] == 1
    assert two["clutches"] == two["clutch_1v2"] == 1
