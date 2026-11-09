import asyncio
import logging
import os

import discord
from discord.ext import commands

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("peakbot")


class PeakBot(commands.Bot):
    async def setup_hook(self) -> None:
        await self.load_extension("cogs.general")
        log.info("Extensions loaded")

    async def on_ready(self) -> None:
        log.info("Logged in as %s (ID: %s)", self.user, self.user.id)

    async def is_owner(self, user: discord.User | discord.Member) -> bool:
        owner_id = os.getenv("BOT_OWNER_ID")
        if owner_id and owner_id.isdigit():
            return user.id == int(owner_id)
        return await super().is_owner(user)


async def main() -> None:
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("DISCORD_TOKEN environment variable is missing")

    intents = discord.Intents.default()
    intents.message_content = True

    bot = PeakBot(
        command_prefix=os.getenv("COMMAND_PREFIX", "!"),
        intents=intents,
        help_command=None,
    )

    try:
        await bot.start(token)
    finally:
        if not bot.is_closed():
            await bot.close()


if __name__ == "__main__":
    asyncio.run(main())
