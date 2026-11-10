import unittest

from cogs.adventure import Adventure


class ProfileMigrationTests(unittest.TestCase):
    def test_invalid_container_fields_are_repaired_without_resetting_progress(self):
        cog = Adventure.__new__(Adventure)
        cog.data = {
            "profiles": {
                "123": {
                    "level": 900,
                    "gold": None,
                    "inventory": {"bad": "not-a-number", "valid": "12"},
                    "symbolic_rewards": None,
                    "equipped_skills": None,
                    "unlocked_skills": None,
                }
            }
        }

        profile = cog.p(123)

        self.assertEqual(profile["level"], 900)
        self.assertEqual(profile["gold"], 0)
        self.assertEqual(profile["inventory"], {"valid": 12})
        self.assertIsInstance(profile["symbolic_rewards"], dict)
        self.assertIsInstance(profile["equipped_skills"], dict)
        self.assertEqual(profile["unlocked_skills"], [])


if __name__ == "__main__":
    unittest.main()
