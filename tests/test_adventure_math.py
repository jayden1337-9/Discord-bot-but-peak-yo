import unittest

from cogs.adventure import apply_level_ups, display_number, swarm_label, swarm_value, symbolic_quantity


class AdventureMathTests(unittest.TestCase):
    def test_level_up_boundaries(self):
        profile = {"xp": 249, "level": 1, "points": 0}
        self.assertEqual(apply_level_ups(profile), 0)
        self.assertEqual(profile, {"xp": 249, "level": 1, "points": 0})

        profile = {"xp": 250, "level": 1, "points": 0}
        self.assertEqual(apply_level_ups(profile), 1)
        self.assertEqual(profile, {"xp": 0, "level": 2, "points": 1})

        profile = {"xp": 750, "level": 1, "points": 0}
        self.assertEqual(apply_level_ups(profile), 2)
        self.assertEqual(profile, {"xp": 0, "level": 3, "points": 2})

    def test_huge_level_up_is_constant_time_math(self):
        profile = {"xp": 10**1000, "level": 1, "points": 0}
        levels = apply_level_ups(profile)
        self.assertGreater(levels, 0)
        self.assertEqual(profile["level"], levels + 1)
        self.assertEqual(profile["points"], levels)
        self.assertGreaterEqual(profile["xp"], 0)
        self.assertLess(profile["xp"], 250 * profile["level"])

    def test_scientific_notation_has_correct_exponent(self):
        self.assertEqual(display_number(10**100), "1.00e100")
        self.assertEqual(display_number(10**1991), "1.00e1991")
        self.assertEqual(display_number(10**3984), "1.00e3984")

    def test_symbolic_googolplex_is_exact(self):
        self.assertEqual(swarm_label("googolplex"), "10^(10^100) (googolplex)")
        self.assertEqual(swarm_value("googolplex"), 1)
        self.assertEqual(symbolic_quantity(1), "10^(10^100)")
        self.assertEqual(symbolic_quantity(3, 20), "3 × 10^(10^100) - 20")
        self.assertEqual(swarm_value(1000), 1000)


if __name__ == "__main__":
    unittest.main()
