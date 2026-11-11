import unittest

from cogs.adventure import apply_level_ups, display_number


class AdventureMathTests(unittest.TestCase):
    def test_level_ups_preserve_large_finite_xp(self):
        profile = {"xp": 10**1000, "level": 1, "points": 0}
        gained = apply_level_ups(profile)
        self.assertGreater(gained, 0)
        self.assertGreater(profile["level"], 1)
        self.assertGreaterEqual(profile["xp"], 0)

    def test_large_numbers_use_scientific_notation(self):
        self.assertEqual(display_number(10**100), "1.00e100")
        self.assertEqual(display_number(10**1991), "1.00e1991")
        self.assertEqual(display_number(10**3984), "1.00e3984")

    def test_small_numbers_keep_grouping(self):
        self.assertEqual(display_number(1234567), "1,234,567")


if __name__ == "__main__":
    unittest.main()
