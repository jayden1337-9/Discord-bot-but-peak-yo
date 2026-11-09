import unittest

from cogs.adventure import DIMENSIONS, SKILL_TREE, SKILL_CATEGORIES, WEAPON_CATEGORIES, WEAPON_RECIPES, BOSSES, CLANS, PETS, BOSS_KEY_POOLS, ITEM_RECIPES, ITEMS, DEFAULT, BOSS_RARE_DROPS, BOSS_DIMENSIONS, CHEST_TIERS, CHEST_LOOT, JJK_BOSSES, JJK_NO_CURSED_ENERGY, apply_level_ups, mastery_tier, raid_phase, symbolic_quantity, swarm_label, boss_chest_weights
from cogs.endgame import GEAR, TOWER_BOSSES, Endgame
from cogs.progression import Progression, TITLE_RULES, utc_day
from cogs.render_ui import inventory_image, gear_image
from cogs.expeditions import ROUTES, expedition_scale, daily_login_reward
from PIL import Image


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

    def test_starter_bosses_are_easier_and_have_anime_keys(self):
        expected = {
            "bandit": 220,
            "buggy": 360,
            "mizuki": 480,
            "fishbone_d": 620,
            "hand_demon": 780,
            "sludge_villain": 920,
            "raditz": 1150,
            "low_rank_curse": 1350,
        }
        for key, hp in expected.items():
            self.assertIn(key, BOSSES)
            self.assertEqual(BOSSES[key][1], hp)
            self.assertLess(BOSSES[key][2][1], 30)
            self.assertTrue(BOSSES[key][4])

    def test_clan_and_boss_key_systems_are_connected(self):
        self.assertEqual(set(BOSS_KEY_POOLS), {"jjk_key", "jojo_key", "naruto_key"})
        self.assertEqual(set(CLANS), {"satoru", "zenin", "kamo", "akatsuki", "konoha", "otogakure", "king"})
        self.assertIsNone(DEFAULT["clan"])
        self.assertEqual(DEFAULT["clan_rolls"], 1)
        for key, bosses in BOSS_KEY_POOLS.items():
            self.assertIn(key, ITEMS)
            self.assertTrue(bosses)
            for boss in bosses:
                self.assertIn(boss, BOSSES)
        for key, recipe in ITEM_RECIPES.items():
            self.assertIn(key, ITEMS)
            for material in recipe["materials"]:
                self.assertIn(material, ITEMS)

    def test_new_anime_bosses_have_valid_drops(self):
        expected = {"jogo", "hanami", "toji", "jjk_sukuna", "jjk_gojo", "jjk_mahito",
                    "dio", "pucci", "dio_vampire", "diavolo", "kira",
                    "itachi", "hashirama", "momoshiki", "isshiki", "naruto_six_paths"}
        self.assertTrue(expected.issubset(BOSSES))
        for key in expected:
            for item in BOSSES[key][4]:
                self.assertIn(item, ITEMS)

    def test_boss_worlds_and_five_chest_tiers_are_complete(self):
        self.assertEqual(set(BOSS_DIMENSIONS), set(BOSSES))
        self.assertEqual(set(CHEST_TIERS), {"common", "rare", "diamond", "ruby", "mythic"})
        for key in CHEST_TIERS:
            self.assertIn(f"{key}_chest", ITEMS)
            self.assertTrue(CHEST_LOOT[key], key)
            self.assertTrue(all(item in ITEMS for item in CHEST_LOOT[key]), key)
            self.assertAlmostEqual(sum(boss_chest_weights("bandit")), 100.0)
        self.assertGreater(boss_chest_weights("rimuru_demon_lord")[-1], boss_chest_weights("bandit")[-1])
        self.assertEqual(DEFAULT["gold"], 0)
        self.assertEqual(DEFAULT["gems"], 0)

    def test_gojo_and_sukuna_have_exclusive_rare_drops(self):
        self.assertEqual(dict(BOSS_RARE_DROPS["gojo"])["six_eyes"], 0.025)
        self.assertEqual(dict(BOSS_RARE_DROPS["jjk_gojo"])["six_eyes"], 0.025)
        for key, boss in BOSSES.items():
            if key not in {"gojo", "jjk_gojo"}:
                self.assertNotIn("six_eyes", boss[4], key)
            if key not in {"sukuna", "jjk_sukuna"}:
                for item in ("cursed_fingers", "sukuna_relic", "malevolent_essence", "shrine_fragment", "king_of_curses_seal"):
                    self.assertNotIn(item, boss[4], key)

    def test_black_flash_residue_only_drops_from_cursed_energy_jjk_bosses(self):
        for key in JJK_BOSSES - JJK_NO_CURSED_ENERGY:
            self.assertIn("black_flash_residue", BOSSES[key][4], key)
        for key in JJK_NO_CURSED_ENERGY:
            self.assertNotIn("black_flash_residue", BOSSES[key][4], key)

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

    def test_weapon_skill_categories_and_equipped_slots(self):
        self.assertEqual(set(SKILL_CATEGORIES), set(SKILL_TREE))
        self.assertEqual(set(WEAPON_CATEGORIES), set(WEAPON_RECIPES))
        self.assertEqual(set(SKILL_CATEGORIES.values()), {"melee", "sword", "magic"})
        self.assertEqual(set(WEAPON_CATEGORIES.values()), {"melee", "sword", "magic"})
        self.assertEqual(DEFAULT["equipped_skills"], {"melee": [], "sword": [], "magic": []})
        self.assertEqual(DEFAULT["weapon_inventory"], {})

    def test_tower_enemy_scales_with_floor(self):
        game = Endgame(None)
        first = game.tower_enemy(1)
        tenth = game.tower_enemy(10)
        self.assertEqual(first["hp"], 650)
        self.assertEqual(tenth["hp"], 65000)
        self.assertGreater(tenth["damage"][1], first["damage"][1])

    def test_pillow_inventory_image_renders_huge_and_symbolic_stacks(self):
        profile = {
            "inventory": {"cursed_ash": 12, "dragon_scale": 10 ** 1991},
            "symbolic_rewards": {
                "inventory": {"void_ore": 2},
                "inventory_spent": {"void_ore": 1},
            },
        }
        image_file = inventory_image(profile, {"cursed_ash": "Cursed Ash", "dragon_scale": "Dragon Scale", "void_ore": "Void Ore"})
        image = Image.open(image_file)
        self.assertEqual(image.format, "PNG")
        self.assertGreater(image.width, 500)
        self.assertGreater(image.height, 200)

    def test_pillow_gear_image_renders_empty_and_equipped_slots(self):
        profile = {"gear_owned": ["cursed_mantle"], "gear_equipped": {"armor": "cursed_mantle", "relic": None, "core": None}}
        image_file = gear_image(profile, GEAR)
        image = Image.open(image_file)
        self.assertEqual(image.format, "PNG")
        self.assertEqual(image.size, (900, 520))

    def test_rift_expeditions_have_three_valid_stages(self):
        self.assertEqual(len(ROUTES), 4)
        for route in ROUTES.values():
            self.assertEqual(len(route["stages"]), 3)
            for stage in route["stages"]:
                self.assertIn(stage[3], ITEMS)
            self.assertIn(route["bonus"], ITEMS)

    def test_expedition_scaling_is_bounded(self):
        self.assertEqual(expedition_scale(1), 1.0)
        self.assertGreater(expedition_scale(20), expedition_scale(5))
        self.assertEqual(expedition_scale(999999), expedition_scale(51))

    def test_companions_have_balanced_attack_and_defense_bonuses(self):
        self.assertGreaterEqual(len(PETS), 5)
        for pet in PETS.values():
            self.assertGreaterEqual(pet["attack"], 0)
            self.assertLessEqual(pet["attack"], 0.15)
            self.assertGreaterEqual(pet["defense"], 0)
            self.assertLessEqual(pet["defense"], 0.12)

    def test_daily_login_streak_reward_caps_at_seven(self):
        self.assertEqual(daily_login_reward(1), {"xp": 200, "points": 1, "token": False})
        self.assertEqual(daily_login_reward(7), {"xp": 500, "points": 3, "token": True})
        self.assertEqual(daily_login_reward(8), daily_login_reward(1))
        self.assertEqual(daily_login_reward(14), daily_login_reward(7))

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
