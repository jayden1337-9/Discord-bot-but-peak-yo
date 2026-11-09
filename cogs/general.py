import os
from pathlib import Path

import discord
from discord.ext import commands

RESTART_FLAG = Path(__file__).resolve().parent.parent / ".restart_requested"


class General(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(name="ping")
    async def ping(self, ctx: commands.Context) -> None:
        latency = round(self.bot.latency * 1000)
        await ctx.reply(f"pong · {latency} ms", mention_author=False)

    @commands.command(name="about")
    async def about(self, ctx: commands.Context) -> None:
        embed = discord.Embed(
            title="Discord-bot-but-peak-yo",
            description="A modular Discord bot, running on Wispbyte.",
            color=discord.Color.blurple(),
        )
        embed.add_field(name="Servers", value=str(len(self.bot.guilds)))
        embed.add_field(name="Latency", value=f"{round(self.bot.latency * 1000)} ms")
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="help")
    async def help_command(self, ctx: commands.Context) -> None:
        prefix = os.getenv("COMMAND_PREFIX", "!")
        embed = discord.Embed(title="Bot commands", color=discord.Color.blurple())
        embed.description = (
            f"`{prefix}ping` — check bot latency\n"
            f"`{prefix}about` — show bot information\n"
            f"`{prefix}help` — show this message\n"
            f"`{prefix}reload` — pull GitHub updates and restart (owner only)"
        )
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="reload")
    @commands.is_owner()
    async def reload_bot(self, ctx: commands.Context) -> None:
        await ctx.reply("Pulling the latest version from GitHub and restarting…")
        RESTART_FLAG.touch()
        await self.bot.close()

    @reload_bot.error
    async def reload_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        if isinstance(error, commands.NotOwner):
            await ctx.reply("You aren't allowed to reload this bot.")
        else:
            raise error


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(General(bot))
