import unittest

from cogs.adventure import apply_level_ups, raid_phase, symbolic_quantity, swarm_label


class GameSystemTests(unittest.TestCase):
    def test_boss_phase_thresholds(self):
        self.assertEqual(raid_phase(100, 100), 1)
        self.assertEqual(raid_phase(75, 100), 2)
        self.assertEqual(raid_phase(50, 100), 3)
        self.assertEqual(raid_phase(25, 100), 4)
        self.assertEqual(raid_phase(0, 100), 4)

    def test_symbolic_googolplex_label_is_exact(self):
        self.assertEqual(swarm_label("googolplex"), "10^(10^100) (googolplex)")
        self.assertEqual(symbolic_quantity(1), "10^(10^100)")
        self.assertEqual(symbolic_quantity(3), "3 × 10^(10^100)")

    def test_level_up_math(self):
        profile = {"level": 1, "xp": 250, "points": 0}
        self.assertEqual(apply_level_ups(profile), 1)
        self.assertEqual(profile["level"], 2)
        self.assertEqual(profile["xp"], 0)
        self.assertEqual(profile["points"], 1)

    def test_huge_existing_profile_values_remain_integers(self):
        huge = 10 ** 1991
        profile = {"level": 1, "xp": huge, "points": 0}
        gained = apply_level_ups(profile)
        self.assertGreater(gained, 0)
        self.assertGreater(profile["level"], 1)
        self.assertGreaterEqual(profile["xp"], 0)


if __name__ == "__main__":
    unittest.main()
