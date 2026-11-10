import unittest
from core.social import ensure_social_data, next_id, transfer_gold, transfer_item, valid_stack


class SocialCoreTests(unittest.TestCase):
    def test_data_migration_adds_social_collections_without_replacing_existing_data(self):
        data = {"profiles": {"123": {"level": 99}}}
        ensure_social_data(data)
        self.assertEqual(data["profiles"]["123"]["level"], 99)
        self.assertEqual(data["guilds"], {})
        self.assertEqual(data["trades"], {})
        self.assertEqual(data["market"], {})

    def test_ids_are_monotonic(self):
        data = {}
        self.assertEqual(next_id(data, "M"), "M000001")
        self.assertEqual(next_id(data, "M"), "M000002")

    def test_item_transfer_moves_exact_amount(self):
        source = {"inventory": {"cursed_ash": 12}}
        target = {"inventory": {"cursed_ash": 3}}
        transfer_item(source, target, "cursed_ash", 5)
        self.assertEqual(source["inventory"]["cursed_ash"], 7)
        self.assertEqual(target["inventory"]["cursed_ash"], 8)

    def test_symbolic_or_missing_items_are_not_transferable(self):
        profile = {"inventory": {}, "symbolic_rewards": {"inventory": {"rare_item": 999}}}
        self.assertFalse(valid_stack(profile, "rare_item", 1))

    def test_item_transfer_rejects_overflow_without_mutating(self):
        source = {"inventory": {"token": 2}}
        target = {"inventory": {"token": 10**18}}
        with self.assertRaises(ValueError):
            transfer_item(source, target, "token", 1)
        self.assertEqual(source["inventory"]["token"], 2)

    def test_gold_transfer_is_atomic_on_insufficient_funds(self):
        source = {"gold": 5}
        target = {"gold": 0}
        with self.assertRaises(ValueError):
            transfer_gold(source, target, 6)
        self.assertEqual(source["gold"], 5)
        self.assertEqual(target["gold"], 0)


if __name__ == "__main__":
    unittest.main()
