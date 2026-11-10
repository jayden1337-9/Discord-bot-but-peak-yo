import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import discord
from discord.ext import commands

from cogs import adventure


class CommandRegistrationTests(unittest.IsolatedAsyncioTestCase):
    async def test_all_extensions_load_without_command_collisions(self):
        bot = commands.Bot(
            command_prefix=",",
            intents=discord.Intents.none(),
            help_command=None,
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with (
                patch.object(adventure, "ROOT", root),
                patch.object(adventure, "DB_FILE", root / "peak_game.json"),
                patch.object(adventure, "OLD_DB", root / "missing.sqlite3"),
            ):
                for extension in (
                    "cogs.general",
                    "cogs.adventure",
                    "cogs.progression",
                    "cogs.endgame",
                    "cogs.expeditions",
                    "cogs.ascension",
                    "cogs.social",
                    "cogs.menu",
                ):
                    await bot.load_extension(extension)

                for command in ("guild", "profile", "menu", "attack", "market", "trade"):
                    self.assertIsNotNone(bot.get_command(command), command)
        await bot.close()


if __name__ == "__main__":
    unittest.main()
