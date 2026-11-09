import os
import random
from datetime import datetime, timezone

import discord
from discord.ext import commands

RESTART_FLAG = __import__("pathlib").Path(__file__).resolve().parent.parent / ".restart_requested"


class General(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    def embed(self, title: str, description: str = "", color: discord.Color = discord.Color.dark_teal()) -> discord.Embed:
        result = discord.Embed(title=title, description=description, color=color, timestamp=datetime.now(timezone.utc))
        result.set_footer(text="Peak Bot")
        return result

    @commands.command(name="ping")
    async def ping(self, ctx: commands.Context) -> None:
        latency = round(self.bot.latency * 1000)
        await ctx.reply(embed=self.embed("Connection status", f"Gateway latency: **{latency} ms**"), mention_author=False)

    @commands.command(name="about")
    async def about(self, ctx: commands.Context) -> None:
        embed = self.embed("Peak Bot", "A modular Discord bot with utility tools and cooperative adventures.")
        embed.add_field(name="Servers", value=f"{len(self.bot.guilds):,}", inline=True)
        embed.add_field(name="Users", value=f"{sum(g.member_count or 0 for g in self.bot.guilds):,}", inline=True)
        embed.add_field(name="Latency", value=f"{round(self.bot.latency * 1000)} ms", inline=True)
        embed.add_field(name="Library", value=f"discord.py {discord.__version__}", inline=True)
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="help")
    async def help_command(self, ctx: commands.Context) -> None:
        p = ctx.clean_prefix
        embed = self.embed("Command directory", "Commands are grouped by what they do.")
        embed.add_field(name="General", value=f"`{p}ping` — connection latency\n`{p}about` — bot information\n`{p}userinfo [member]` — member details\n`{p}serverinfo` — server details\n`{p}avatar [member]` — view an avatar\n`{p}roll [sides]` — roll a die\n`{p}choose <options>` — choose between options\n`{p}8ball <question>` — ask a question", inline=False)
        embed.add_field(name="Adventure", value=f"`{p}bosses` — list bosses\n`{p}boss challenge <name>` — start a server encounter\n`{p}boss status` — view current boss\n`{p}attack` — attack the active boss", inline=False)
        embed.add_field(name="Owner", value=f"`{p}reload` — pull updates and restart", inline=False)
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="userinfo")
    async def userinfo(self, ctx: commands.Context, member: discord.Member = None) -> None:
        member = member or ctx.author
        embed = self.embed(f"User information · {member}", color=discord.Color.blurple())
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="User ID", value=str(member.id), inline=True)
        embed.add_field(name="Account created", value=discord.utils.format_dt(member.created_at, style="D"), inline=True)
        if isinstance(member, discord.Member):
            embed.add_field(name="Joined server", value=discord.utils.format_dt(member.joined_at, style="D") if member.joined_at else "Unknown", inline=True)
            embed.add_field(name="Top role", value=member.top_role.mention if member.top_role else "None", inline=True)
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="serverinfo")
    @commands.guild_only()
    async def serverinfo(self, ctx: commands.Context) -> None:
        guild = ctx.guild
        embed = self.embed(f"Server information · {guild.name}", color=discord.Color.blurple())
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        embed.add_field(name="Members", value=f"{guild.member_count:,}", inline=True)
        embed.add_field(name="Channels", value=f"{len(guild.channels):,}", inline=True)
        embed.add_field(name="Roles", value=f"{len(guild.roles):,}", inline=True)
        embed.add_field(name="Created", value=discord.utils.format_dt(guild.created_at, style="D"), inline=True)
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="avatar")
    async def avatar(self, ctx: commands.Context, member: discord.Member = None) -> None:
        member = member or ctx.author
        embed = self.embed(f"Avatar · {member}", color=discord.Color.blurple())
        embed.set_image(url=member.display_avatar.url)
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="roll")
    async def roll(self, ctx: commands.Context, sides: commands.Range[int, 2, 1000000] = 6) -> None:
        value = random.randint(1, sides)
        await ctx.reply(embed=self.embed("Dice roll", f"{ctx.author.mention} rolled **{value}** on a **{sides}**-sided die.", discord.Color.blurple()), mention_author=False)

    @commands.command(name="choose")
    async def choose(self, ctx: commands.Context, *, options: str) -> None:
        choices = [part.strip() for part in options.split("|") if part.strip()]
        if len(choices) < 2:
            await ctx.reply(embed=self.embed("Not enough options", f"Separate at least two options with `|`.", discord.Color.orange()), mention_author=False)
            return
        if len(choices) > 20:
            await ctx.reply(embed=self.embed("Too many options", "You can provide up to 20 options.", discord.Color.orange()), mention_author=False)
            return
        await ctx.reply(embed=self.embed("Decision", f"Selected: **{random.choice(choices)}**", discord.Color.blurple()), mention_author=False)

    @commands.command(name="8ball")
    async def eight_ball(self, ctx: commands.Context, *, question: str) -> None:
        answers = ["Yes.", "No.", "Probably.", "Unlikely.", "Ask again later.", "The outlook is good.", "There is not enough information."]
        embed = self.embed("Magic 8-ball", f"**Question:** {question}\n**Answer:** {random.choice(answers)}", discord.Color.blurple())
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="reload")
    @commands.is_owner()
    async def reload_bot(self, ctx: commands.Context) -> None:
        await ctx.reply(embed=self.embed("Update requested", "The supervisor will pull the latest GitHub version and restart the bot."))
        RESTART_FLAG.touch()
        await self.bot.close()

    @reload_bot.error
    async def reload_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        if isinstance(error, commands.NotOwner):
            await ctx.reply(embed=self.embed("Permission denied", "Only the configured bot owner can use this command.", discord.Color.red()), mention_author=False)
        else:
            raise error


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(General(bot))
