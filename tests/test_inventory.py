import unittest

from core.inventory import consume_item, has_item


class InventoryTests(unittest.TestCase):
    def test_has_item_checks_finite_inventory(self):
        profile = {"inventory": {"potion": 7}}
        self.assertTrue(has_item(profile, "potion", 7))
        self.assertFalse(has_item(profile, "potion", 8))

    def test_consume_exact_amount(self):
        profile = {"inventory": {"potion": 7}}
        self.assertTrue(consume_item(profile, "potion", 7))
        self.assertNotIn("potion", profile["inventory"])

    def test_failed_consumption_does_not_change_inventory(self):
        profile = {"inventory": {"potion": 5}}
        self.assertFalse(consume_item(profile, "potion", 6))
        self.assertEqual(profile["inventory"], {"potion": 5})

    def test_invalid_amount_is_rejected(self):
        profile = {"inventory": {"potion": 5}}
        self.assertFalse(has_item(profile, "potion", 0))
        self.assertFalse(consume_item(profile, "potion", -1))
        self.assertEqual(profile["inventory"], {"potion": 5})


if __name__ == "__main__":
    unittest.main()
