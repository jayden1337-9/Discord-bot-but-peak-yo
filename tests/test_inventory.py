import unittest

from core.inventory import consume_item, has_item


class InventoryTransactionTests(unittest.TestCase):
    def test_normal_stack_is_consumed_first(self):
        profile = {"inventory": {"potion": 7}, "symbolic_rewards": {"inventory": {}, "inventory_spent": {}}}
        self.assertTrue(has_item(profile, "potion", 5))
        self.assertTrue(consume_item(profile, "potion", 5))
        self.assertEqual(profile["inventory"]["potion"], 2)
        self.assertEqual(profile["symbolic_rewards"]["inventory_spent"], {})

    def test_mixed_normal_and_symbolic_stack_is_consumed(self):
        profile = {
            "inventory": {"potion": 3},
            "symbolic_rewards": {"inventory": {"potion": 1}, "inventory_spent": {}},
        }
        self.assertTrue(consume_item(profile, "potion", 8))
        self.assertNotIn("potion", profile["inventory"])
        self.assertEqual(profile["symbolic_rewards"]["inventory_spent"]["potion"], 5)

    def test_failed_consume_does_not_partially_remove_normal_items(self):
        profile = {
            "inventory": {"potion": 3},
            "symbolic_rewards": {"inventory": {}, "inventory_spent": {}},
        }
        before = {
            "inventory": dict(profile["inventory"]),
            "symbolic_rewards": {
                "inventory": dict(profile["symbolic_rewards"]["inventory"]),
                "inventory_spent": dict(profile["symbolic_rewards"]["inventory_spent"]),
            },
        }
        self.assertFalse(consume_item(profile, "potion", 4))
        self.assertEqual(profile, before)

    def test_symbolic_stack_satisfies_finite_request(self):
        profile = {"inventory": {}, "symbolic_rewards": {"inventory": {"rare": 1}, "inventory_spent": {}}}
        self.assertTrue(has_item(profile, "rare", 10**100))
        self.assertTrue(consume_item(profile, "rare", 10**100))
        self.assertEqual(profile["symbolic_rewards"]["inventory_spent"]["rare"], 10**100)

    def test_non_positive_amount_is_rejected(self):
        profile = {"inventory": {"potion": 5}, "symbolic_rewards": {"inventory": {}, "inventory_spent": {}}}
        self.assertFalse(has_item(profile, "potion", 0))
        self.assertFalse(consume_item(profile, "potion", -1))
        self.assertEqual(profile["inventory"]["potion"], 5)


if __name__ == "__main__":
    unittest.main()
