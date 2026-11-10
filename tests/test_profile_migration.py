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
                    "character": [],
                    "race": {},
                    "weapon": [],
                    "clan": [],
                    "active_dimension": [],
                    "attack_mode": [],
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
        self.assertEqual(profile["character"], "sukuna")
        self.assertEqual(profile["race"], "human")
        self.assertIsNone(profile["weapon"])
        self.assertIsNone(profile["clan"])
        self.assertEqual(profile["active_dimension"], "earth")
        self.assertIsNone(profile["attack_mode"])


if __name__ == "__main__":
    unittest.main()
