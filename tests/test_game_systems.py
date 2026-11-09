import unittest

from cogs.adventure import DIMENSIONS, SKILL_TREE, WEAPON_RECIPES, BOSSES, apply_level_ups, mastery_tier, raid_phase, symbolic_quantity, swarm_label
from cogs.endgame import GEAR, TOWER_BOSSES, Endgame
from cogs.progression import Progression, TITLE_RULES, utc_day


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

    def test_character_mastery_tiers(self):
        self.assertEqual(mastery_tier(0), 0)
        self.assertEqual(mastery_tier(1000), 1)
        self.assertEqual(mastery_tier(5000), 2)
        self.assertEqual(mastery_tier(20000), 3)

    def test_symbolic_rewards_unlock_high_tier_titles(self):
        profile = {"wins": 0, "damage": 0, "race": "human", "symbolic_rewards": {"wins": 1, "damage": 1}}
        self.assertTrue(TITLE_RULES["conqueror"][2](profile))
        self.assertTrue(TITLE_RULES["calamity"][2](profile))

    def test_symbolic_swarm_completes_daily_damage_contract(self):
        profile = {
            "wins": 0,
            "damage": 0,
            "symbolic_rewards": {"wins": 0, "damage": 1},
            "quests": {
                "daily_period": utc_day(),
                "daily_claimed": False,
                "daily_baseline_wins": 0,
                "daily_baseline_damage": 0,
                "daily_baseline_symbolic_wins": 0,
                "daily_baseline_symbolic_damage": 0,
                "daily_objective": "damage",
            },
        }
        progress, target, _ = Progression(None).quest_progress(profile, "daily")
        self.assertGreaterEqual(progress, target)

    def test_expansion_content_is_connected(self):
        self.assertGreaterEqual(len(BOSSES), 15)
        self.assertGreaterEqual(len(WEAPON_RECIPES), 9)
        self.assertGreaterEqual(len(SKILL_TREE), 10)
        self.assertGreaterEqual(len(DIMENSIONS), 10)
        self.assertEqual(len(TOWER_BOSSES), 10)
        self.assertGreaterEqual(len(GEAR), 8)

    def test_all_gear_has_valid_slots_and_materials(self):
        for key, item in GEAR.items():
            self.assertIn(item["slot"], {"armor", "relic", "core"}, key)
            self.assertGreaterEqual(item["level"], 1, key)
            self.assertTrue(item["materials"], key)
            self.assertTrue(all(amount > 0 for amount in item["materials"].values()), key)

    def test_tower_enemy_scales_with_floor(self):
        game = Endgame(None)
        first = game.tower_enemy(1)
        tenth = game.tower_enemy(10)
        self.assertEqual(first["hp"], 650)
        self.assertEqual(tenth["hp"], 65000)
        self.assertGreater(tenth["damage"][1], first["damage"][1])

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
