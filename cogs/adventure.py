import asyncio
import random
import time
from collections import defaultdict

import discord
from discord.ext import commands

BOSSES = {
    "warden": {"name": "The Ashen Warden", "hp": 1200, "damage": (35, 75), "reward": 350, "description": "An ancient guardian clad in scorched iron."},
    "leviathan": {"name": "The Drowned Leviathan", "hp": 2200, "damage": (55, 105), "reward": 700, "description": "A colossal creature said to sleep beneath the deepest waters."},
    "sovereign": {"name": "The Hollow Sovereign", "hp": 4000, "damage": (80, 145), "reward": 1400, "description": "A forgotten ruler whose presence bends the air around it."},
}


class Adventure(commands.Cog):
    """A lightweight cooperative boss mode."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.encounters = {}
        self.cooldowns = {}
        self.lock = asyncio.Lock()

    def make_embed(self, title: str, description: str = "", color: discord.Color = discord.Color.dark_teal()) -> discord.Embed:
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_footer(text="Adventure")
        return embed

    @commands.group(name="boss", invoke_without_command=True)
    async def boss(self, ctx: commands.Context) -> None:
        prefix = ctx.clean_prefix
        embed = self.make_embed(
            "Boss encounters",
            f"Use `{prefix}bosses` to view available bosses.\n"
            f"Use `{prefix}boss challenge <name>` to start an encounter.\n"
            f"Use `{prefix}attack` to deal damage and `{prefix}boss status` to check its health.",
        )
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="bosses")
    async def bosses(self, ctx: commands.Context) -> None:
        embed = self.make_embed("Available bosses", "Choose a challenge for your server.")
        for key, boss in BOSSES.items():
            embed.add_field(
                name=f"{boss['name']} · {key}",
                value=f"{boss['description']}\nHealth: **{boss['hp']:,}** · Reward: **{boss['reward']:,} credits**",
                inline=False,
            )
        await ctx.reply(embed=embed, mention_author=False)

    @boss.command(name="challenge")
    @commands.guild_only()
    async def challenge(self, ctx: commands.Context, *, name: str) -> None:
        key = name.lower().strip()
        if key not in BOSSES:
            await ctx.reply(embed=self.make_embed("Unknown boss", f"Use `{ctx.clean_prefix}bosses` to see the available encounters.", discord.Color.orange()), mention_author=False)
            return
        async with self.lock:
            if ctx.guild.id in self.encounters:
                await ctx.reply(embed=self.make_embed("Encounter already active", "Defeat the current boss before starting another one.", discord.Color.orange()), mention_author=False)
                return
            boss = BOSSES[key]
            self.encounters[ctx.guild.id] = {"key": key, "hp": boss["hp"], "max_hp": boss["hp"], "damage": defaultdict(int), "started": time.monotonic()}
        embed = self.make_embed(f"{boss['name']} has appeared", f"{boss['description']}\n\nHealth: **{boss['hp']:,}**\nReward: **{boss['reward']:,} credits**\n\nUse `{ctx.clean_prefix}attack` to join the fight.")
        await ctx.reply(embed=embed, mention_author=False)

    @boss.command(name="status")
    @commands.guild_only()
    async def status(self, ctx: commands.Context) -> None:
        encounter = self.encounters.get(ctx.guild.id)
        if not encounter:
            await ctx.reply(embed=self.make_embed("No active encounter", f"Start one with `{ctx.clean_prefix}boss challenge warden`."), mention_author=False)
            return
        boss = BOSSES[encounter["key"]]
        hp = max(0, encounter["hp"])
        embed = self.make_embed(boss["name"], f"Health: **{hp:,} / {encounter['max_hp']:,}**")
        embed.add_field(name="Damage dealt", value=f"**{sum(encounter['damage'].values()):,}**", inline=True)
        embed.add_field(name="Contributors", value=f"**{len(encounter['damage'])}**", inline=True)
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="attack")
    @commands.guild_only()
    async def attack(self, ctx: commands.Context) -> None:
        now = time.monotonic()
        key = (ctx.guild.id, ctx.author.id)
        remaining = self.cooldowns.get(key, 0) - now
        if remaining > 0:
            embed = self.make_embed("Catch your breath", f"You can attack again in **{remaining:.1f}s**.", discord.Color.orange())
            await ctx.reply(embed=embed, mention_author=False)
            return
        async with self.lock:
            encounter = self.encounters.get(ctx.guild.id)
            if not encounter:
                await ctx.reply(embed=self.make_embed("No active encounter", f"Start a fight with `{ctx.clean_prefix}boss challenge warden`."), mention_author=False)
                return
            boss = BOSSES[encounter["key"]]
            damage = random.randint(65, 130)
            dealt = min(damage, encounter["hp"])
            encounter["hp"] -= dealt
            encounter["damage"][ctx.author.id] += dealt
            self.cooldowns[key] = now + 5
            defeated = encounter["hp"] <= 0
            if defeated:
                results = sorted(encounter["damage"].items(), key=lambda item: item[1], reverse=True)
                del self.encounters[ctx.guild.id]
        if defeated:
            embed = self.make_embed(f"{boss['name']} defeated", f"The encounter is over. **{boss['reward']:,} credits** have been recorded as the reward pool.", discord.Color.green())
            top = "\n".join(f"<@{user_id}> — **{amount:,} damage**" for user_id, amount in results[:5])
            if top:
                embed.add_field(name="Top contributors", value=top, inline=False)
            embed.add_field(name="Next step", value="More adventure features are coming soon.", inline=False)
        else:
            embed = self.make_embed("Attack landed", f"{ctx.author.mention} dealt **{dealt:,} damage** to {boss['name']}.", discord.Color.blurple())
            embed.add_field(name="Boss health", value=f"**{encounter['hp']:,} / {encounter['max_hp']:,}**", inline=True)
            embed.add_field(name="Next attack", value="Available in 5 seconds.", inline=True)
        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Adventure(bot))
