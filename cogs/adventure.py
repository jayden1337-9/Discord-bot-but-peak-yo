import asyncio
import random
import time
from collections import defaultdict

import discord
from discord.ext import commands

BOSSES = {
    "warden": {"name": "THE ASHEN WARDEN", "hp": 1200, "reward": 350, "description": "An ancient guardian sealed inside scorched iron."},
    "leviathan": {"name": "THE DROWNED LEVIATHAN", "hp": 2200, "reward": 700, "description": "A colossal creature said to sleep beneath the deepest waters."},
    "sovereign": {"name": "THE HOLLOW SOVEREIGN", "hp": 4000, "reward": 1400, "description": "A forgotten ruler whose presence bends the air around it."},
}


class Adventure(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.encounters = {}
        self.cooldowns = {}
        self.lock = asyncio.Lock()

    def make_embed(self, title: str, description: str = "", color: discord.Color = discord.Color.from_rgb(77, 54, 92)) -> discord.Embed:
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_footer(text="PEAK  /  ADVENTURE")
        return embed

    @commands.group(name="boss", invoke_without_command=True, aliases=["hunt"])
    async def boss(self, ctx: commands.Context) -> None:
        p = ctx.clean_prefix
        embed = self.make_embed("Adventure terminal", f"`{p}bosses` opens the catalogue.\n`{p}boss challenge <name>` starts an encounter.\n`{p}boss status` checks the active target.\n`{p}attack` deals damage.")
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="bosses", aliases=["bestiary"])
    async def bosses(self, ctx: commands.Context) -> None:
        embed = self.make_embed("The bestiary", "Three known threats. Choose your target carefully.")
        for key, boss in BOSSES.items():
            embed.add_field(name=f"{boss['name']}  /  {key}", value=f"{boss['description']}\n**{boss['hp']:,} HP**  ·  **{boss['reward']:,} credits** reward pool", inline=False)
        await ctx.reply(embed=embed, mention_author=False)

    @boss.command(name="challenge", aliases=["start", "summon"])
    @commands.guild_only()
    async def challenge(self, ctx: commands.Context, *, name: str) -> None:
        key = name.lower().strip()
        if key not in BOSSES:
            await ctx.reply(embed=self.make_embed("Target not found", f"Use `{ctx.clean_prefix}bosses` to inspect the bestiary.", discord.Color.orange()), mention_author=False)
            return
        async with self.lock:
            if ctx.guild.id in self.encounters:
                await ctx.reply(embed=self.make_embed("Encounter in progress", "The current target must be defeated before another can be summoned.", discord.Color.orange()), mention_author=False)
                return
            boss = BOSSES[key]
            self.encounters[ctx.guild.id] = {"key": key, "hp": boss["hp"], "max_hp": boss["hp"], "damage": defaultdict(int), "started": time.monotonic()}
        embed = self.make_embed(f"TARGET ACQUIRED  /  {boss['name']}", f"{boss['description']}\n\n**VITALITY**\n{boss['hp']:,} HP\n\n**REWARD POOL**\n{boss['reward']:,} credits\n\nUse `{ctx.clean_prefix}attack` to join the encounter.", discord.Color.dark_red())
        await ctx.reply(embed=embed, mention_author=False)

    @boss.command(name="status", aliases=["info"])
    @commands.guild_only()
    async def status(self, ctx: commands.Context) -> None:
        encounter = self.encounters.get(ctx.guild.id)
        if not encounter:
            await ctx.reply(embed=self.make_embed("No active target", f"Summon one with `{ctx.clean_prefix}boss challenge warden`."), mention_author=False)
            return
        boss = BOSSES[encounter["key"]]
        hp = max(0, encounter["hp"])
        ratio = hp / encounter["max_hp"]
        filled = round(ratio * 16)
        bar = "█" * filled + "░" * (16 - filled)
        embed = self.make_embed(boss["name"], f"`{bar}`\n**{hp:,} / {encounter['max_hp']:,} HP**")
        embed.add_field(name="Total damage", value=f"{sum(encounter['damage'].values()):,}", inline=True)
        embed.add_field(name="Contributors", value=str(len(encounter["damage"])), inline=True)
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="attack", aliases=["strike", "hit"])
    @commands.guild_only()
    async def attack(self, ctx: commands.Context) -> None:
        now = time.monotonic()
        key = (ctx.guild.id, ctx.author.id)
        remaining = self.cooldowns.get(key, 0) - now
        if remaining > 0:
            await ctx.reply(embed=self.make_embed("Action cooling down", f"Attack available in **{remaining:.1f} seconds**.", discord.Color.orange()), mention_author=False)
            return
        async with self.lock:
            encounter = self.encounters.get(ctx.guild.id)
            if not encounter:
                await ctx.reply(embed=self.make_embed("No active target", f"Summon a boss with `{ctx.clean_prefix}boss challenge warden`."), mention_author=False)
                return
            boss = BOSSES[encounter["key"]]
            dealt = min(random.randint(65, 130), encounter["hp"])
            encounter["hp"] -= dealt
            encounter["damage"][ctx.author.id] += dealt
            self.cooldowns[key] = now + 5
            defeated = encounter["hp"] <= 0
            if defeated:
                results = sorted(encounter["damage"].items(), key=lambda item: item[1], reverse=True)
                del self.encounters[ctx.guild.id]
        if defeated:
            embed = self.make_embed(f"TARGET ELIMINATED  /  {boss['name']}", f"The encounter has concluded. **{boss['reward']:,} credits** are recorded as the reward pool.", discord.Color.green())
            ranking = "\n".join(f"**{index}.** <@{user_id}> — {amount:,} damage" for index, (user_id, amount) in enumerate(results[:5], 1))
            if ranking:
                embed.add_field(name="Damage rankings", value=ranking, inline=False)
            embed.add_field(name="Encounter report", value=f"{len(results)} contributors participated.", inline=False)
        else:
            embed = self.make_embed("Strike confirmed", f"{ctx.author.mention} dealt **{dealt:,} damage** to {boss['name']}.", discord.Color.blurple())
            hp = encounter["hp"]
            maximum = encounter["max_hp"]
            filled = round((hp / maximum) * 16)
            embed.add_field(name="Remaining vitality", value=f"`{'█' * filled}{'░' * (16 - filled)}`\n**{hp:,} / {maximum:,} HP**", inline=False)
        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Adventure(bot))
