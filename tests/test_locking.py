import asyncio
import unittest

from core.locking import serialized


class FakeGame:
    def __init__(self):
        self.lock = asyncio.Lock()


class FakeBot:
    def __init__(self, game):
        self.game = game

    def get_cog(self, name):
        return self.game if name == "Adventure" else None


class FakeCog:
    def __init__(self, bot):
        self.bot = bot
        self.events = []

    @serialized
    async def update(self, ctx, value):
        self.events.append(("start", value))
        await asyncio.sleep(0)
        self.events.append(("end", value))


class SharedLockTests(unittest.IsolatedAsyncioTestCase):
    async def test_mutating_commands_share_one_lock(self):
        game = FakeGame()
        cog = FakeCog(FakeBot(game))
        await asyncio.gather(cog.update(None, "a"), cog.update(None, "b"))
        self.assertEqual(cog.events[0][0], "start")
        self.assertEqual(cog.events[1][0], "end")
        self.assertEqual(cog.events[2][0], "start")
        self.assertEqual(cog.events[3][0], "end")

    async def test_lock_is_released_after_command_error(self):
        game = FakeGame()
        bot = FakeBot(game)

        class BrokenCog:
            def __init__(self):
                self.bot = bot

            @serialized
            async def fail(self, ctx):
                raise RuntimeError("expected")

        cog = BrokenCog()
        with self.assertRaises(RuntimeError):
            await cog.fail(None)
        self.assertFalse(game.lock.locked())


if __name__ == "__main__":
    unittest.main()
