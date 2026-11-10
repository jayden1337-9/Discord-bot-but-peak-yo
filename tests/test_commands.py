import asyncio
import unittest

from cogs.ascension import Ascension


class FakeAuthor:
    id = 123


class FakeContext:
    author = FakeAuthor()

    def __init__(self):
        self.replies = []

    async def reply(self, **kwargs):
        self.replies.append(kwargs)


class FakeGame:
    def __init__(self):
        self.lock = asyncio.Lock()
        self.data = {
            "world_boss": {
                "active": True,
                "name": "The World Eater",
                "players": {},
            }
        }
        self.profile = {"attack_mode": None}

    def p(self, user_id):
        return self.profile

    def flush(self):
        pass

    def embed(self, title, description=""):
        return (title, description)


class FakeBot:
    def __init__(self, game):
        self.game = game

    def get_cog(self, name):
        return self.game if name == "Adventure" else None


class WorldBossCommandTests(unittest.IsolatedAsyncioTestCase):
    async def test_join_registers_player_and_sets_attack_mode(self):
        game = FakeGame()
        cog = Ascension(FakeBot(game))
        ctx = FakeContext()

        await Ascension.worldboss_join.callback(cog, ctx)

        self.assertIn("123", game.data["world_boss"]["players"])
        self.assertEqual(game.profile["attack_mode"], "worldboss")
        self.assertEqual(len(ctx.replies), 1)
        self.assertIn("joined", ctx.replies[0]["embed"][1].lower())


if __name__ == "__main__":
    unittest.main()
