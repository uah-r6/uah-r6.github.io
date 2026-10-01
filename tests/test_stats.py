import unittest

from r6stats.parser.models import Kill, Match, Objective, Player, Round
from r6stats.stats.calculate import RatingEngine, calculate_match, empty, finalize


def players():
    return [Player("a", "Logan", 0, "Buck", "Attack"), Player("b", "Teammate", 0, "Ash", "Attack"),
            Player("c", "EnemyA", 1, "Wamai", "Defense"), Player("d", "EnemyB", 1, "Azami", "Defense")]


def match(kills, objectives=None):
    return Match("fixture", "2026-09-29T00:00:00Z", "Bank", "Custom Game", "Bomb",
                 [Round(1, "Site", 0, "KilledOpponents", players(), kills, objectives or [])])


class StatsTests(unittest.TestCase):
    def test_trade_original_killer(self):
        s = calculate_match(match([Kill(0, 100, "c", "a", 1, 0), Kill(1, 94, "b", "c", 0, 1)]))
        self.assertEqual(s["a"]["deaths_traded"], 1)
        self.assertEqual(s["a"]["kost_rounds"], 1)
        self.assertEqual(s["b"]["refrag_kills"], 1)
        self.assertEqual(s["c"]["kills_traded"], 1)

    def test_unrelated_kill_is_not_trade(self):
        s = calculate_match(match([Kill(0, 100, "c", "a", 1, 0), Kill(1, 94, "b", "d", 0, 1)]))
        self.assertEqual(s["a"]["deaths_traded"], 0)
        self.assertEqual(s["b"]["refrag_kills"], 0)

    def test_trade_window(self):
        s = calculate_match(match([Kill(0, 100, "c", "a", 1, 0), Kill(1, 91, "b", "c", 0, 1)]), 8)
        self.assertEqual(s["a"]["deaths_traded"], 0)

    def test_opening_ignores_teamkill(self):
        s = calculate_match(match([Kill(0, 120, "c", "d", 1, 1), Kill(1, 100, "a", "c", 0, 1)]))
        self.assertEqual(s["a"]["opening_kills"], 1)
        self.assertEqual(s["a"]["kills"], 1)
        self.assertEqual(s["c"]["teamkills"], 1)

    def test_survival_and_objective_kost(self):
        s = calculate_match(match([Kill(0, 100, "c", "a", 1, 0)], [Objective("plant", "a", 0, 110)]))
        self.assertEqual(s["b"]["kost_rounds"], 1)
        self.assertEqual(s["b"]["survived"], 1)
        self.assertEqual(s["a"]["kost_rounds"], 1)
        self.assertEqual(s["a"]["plants"], 1)

    def test_historical_role_impossible_objectives_do_not_affect_statistics(self):
        death = [Kill(0, 100, "b", "c", 0, 1), Kill(1, 90, "d", "a", 1, 0)]
        baseline = calculate_match(match(death))
        invalid = calculate_match(match(death, [Objective("plant", "c", 1, 110),
                                               Objective("disable", "a", 0, 95),
                                               Objective("plant", "b", 1, 85)]))
        self.assertEqual(invalid, baseline)
        self.assertEqual(invalid["c"]["plants"], 0)
        self.assertEqual(invalid["a"]["disables"], 0)

    def test_valid_side_and_team_objectives_still_count(self):
        values = calculate_match(match([], [Objective("plant", "a", 0, 90),
                                           Objective("disable", "c", 1, 40)]))
        self.assertEqual(values["a"]["plants"], 1)
        self.assertEqual(values["c"]["disables"], 1)

    def test_pivot_examples(self):
        own = [Player(str(i), str(i), 0) for i in range(5)]
        foe = [Player(str(i+5), str(i+5), 1) for i in range(5)]
        r = Round(1, "Site", 0, "", own+foe,
                  [Kill(0, 100, "0", "5", 0, 1),  # 5v5: yes
                   Kill(1, 90, "6", "1", 1, 0),  # 5v4 foe behind: yes
                   Kill(2, 80, "6", "2", 1, 0),  # 4v4: yes
                   Kill(3, 70, "6", "3", 1, 0),  # 4v3 foe ahead: no
                   Kill(4, 60, "4", "7", 0, 1)]) # 4v2 own behind: yes
        s = calculate_match(Match("x", "2026-01-01T00:00:00Z", "Bank", "Custom Game", "Bomb", [r]))
        self.assertEqual(s["0"]["pivot_kills"], 1)
        self.assertEqual(s["6"]["pivot_kills"], 2)
        self.assertEqual(s["4"]["pivot_kills"], 1)

    def test_pivot_tied_behind_and_ahead(self):
        team_a = [Player(f"a{i}", f"a{i}", 0) for i in range(5)]
        team_b = [Player(f"b{i}", f"b{i}", 1) for i in range(5)]
        events = [Kill(0, 150, "b0", "a0", 1, 0),
                  Kill(1, 140, "b1", "a1", 1, 0),  # 3v5
                  Kill(2, 130, "a2", "b0", 0, 1),  # 3v4, pivot
                  Kill(3, 120, "a2", "b1", 0, 1),  # 3v3, pivot
                  Kill(4, 110, "a2", "b2", 0, 1),  # 3v2, pivot
                  Kill(5, 100, "a2", "b3", 0, 1)]  # 3v1, ahead: no
        stats = calculate_match(Match("x", "2026-01-01T00:00:00Z", "Bank", "Custom Game", "Bomb",
                                      [Round(1, "Site", 0, "", team_a+team_b, events)]))
        self.assertEqual(stats["a2"]["pivot_kills"], 3)
        self.assertEqual(stats["b3"]["pivot_deaths"], 0)

    def test_rating_snapshot(self):
        s = empty()
        s.update({"rounds": 10, "kills": 8, "deaths": 7, "pivot_kills": 4,
                  "untraded_kills": 6, "pivot_deaths": 3, "untraded_deaths": 5,
                  "plants": 1, "kost_rounds": 7, "kills_traded": 2, "deaths_traded": 2})
        self.assertAlmostEqual(RatingEngine.calculate(s), 1.212008379142857)


if __name__ == "__main__":
    unittest.main()
