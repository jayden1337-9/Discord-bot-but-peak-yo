import asyncio
import time
import unittest

from cogs.social import MarketPurchaseConfirm, Social, TradeOfferView


class FakeGame:
    def __init__(self):
        self.lock = asyncio.Lock()
        self.data = {"guilds": {}, "trades": {}, "market": {}, "social_sequence": 0}
        self.profiles = {}

    def p(self, user_id):
        return self.profiles.setdefault(str(user_id), {"inventory": {}, "gold": 0, "gems": 0})

    def flush(self):
        pass


class FakeBot:
    def __init__(self, game):
        self.game = game

    def get_cog(self, name):
        return self.game if name == "Adventure" else None


class FakeResponse:
    def __init__(self):
        self.edited = None
        self.sent = None

    async def edit_message(self, **kwargs):
        self.edited = kwargs

    async def send_message(self, *args, **kwargs):
        self.sent = (args, kwargs)


class FakeInteraction:
    def __init__(self, user_id, guild_id):
        self.user = type("User", (), {"id": user_id})()
        self.guild_id = guild_id
        self.response = FakeResponse()


class SocialViewTests(unittest.IsolatedAsyncioTestCase):
    async def test_trade_accept_button_transfers_items_once(self):
        game = FakeGame()
        game.profiles["10"] = {"inventory": {"cursed_ash": 8}, "gold": 0}
        game.profiles["20"] = {"inventory": {}, "gold": 0}
        game.data["trades"]["T000001"] = {
            "from": "10", "to": "20", "server_id": 55,
            "item": "cursed_ash", "amount": 5, "expires": int(time.time()) + 300,
        }
        social = Social(FakeBot(game))
        view = TradeOfferView(social, "T000001", 55, 10, 20)
        interaction = FakeInteraction(20, 55)

        await view.children[0].callback(interaction)

        self.assertEqual(game.profiles["10"]["inventory"]["cursed_ash"], 3)
        self.assertEqual(game.profiles["20"]["inventory"]["cursed_ash"], 5)
        self.assertNotIn("T000001", game.data["trades"])
        self.assertIsNotNone(interaction.response.edited)

    async def test_trade_button_rejects_wrong_recipient(self):
        game = FakeGame()
        game.profiles["10"] = {"inventory": {"cursed_ash": 8}, "gold": 0}
        game.profiles["20"] = {"inventory": {}, "gold": 0}
        game.data["trades"]["T000001"] = {
            "from": "10", "to": "20", "server_id": 55,
            "item": "cursed_ash", "amount": 5, "expires": int(time.time()) + 300,
        }
        social = Social(FakeBot(game))
        view = TradeOfferView(social, "T000001", 55, 10, 20)
        interaction = FakeInteraction(99, 55)

        await view.children[0].callback(interaction)

        self.assertEqual(game.profiles["10"]["inventory"]["cursed_ash"], 8)
        self.assertIn("T000001", game.data["trades"])
        self.assertTrue(interaction.response.sent[1]["ephemeral"])

    async def test_market_confirmation_transfers_gold_and_escrowed_item(self):
        game = FakeGame()
        game.profiles["20"] = {"inventory": {}, "gold": 500}
        game.profiles["10"] = {"inventory": {}, "gold": 0}
        game.data["market"]["M000001"] = {
            "id": "M000001", "seller": "10", "server_id": 55,
            "item": "dragon_scale", "amount": 3, "price": 120, "created": int(time.time()),
        }
        social = Social(FakeBot(game))
        view = MarketPurchaseConfirm(social, 55, 20, "M000001")
        interaction = FakeInteraction(20, 55)

        await view.children[0].callback(interaction)

        self.assertEqual(game.profiles["20"]["gold"], 380)
        self.assertEqual(game.profiles["10"]["gold"], 120)
        self.assertEqual(game.profiles["20"]["inventory"]["dragon_scale"], 3)
        self.assertNotIn("M000001", game.data["market"])
        self.assertIsNotNone(interaction.response.edited)


if __name__ == "__main__":
    unittest.main()
