import asyncio
import random
import sqlite3
import time
from collections import defaultdict
from pathlib import Path

import discord
from discord.ext import commands

DB_PATH = Path("/home/container/peak_adventure.sqlite3")

BOSSES = {
    "hollowfang": {"name": "HOLLOWFANG, THE DEVOURER", "hp": 1400, "reward": 350, "damage": (25, 43), "description": "A calamity-born beast that feeds on the battle spirit of fallen warriors."},
    "tideemperor": {"name": "THE TIDE EMPEROR", "hp": 2600, "reward": 700, "damage": (36, 59), "description": "An exiled sea monarch who commands pressure, storms and crushing waves."},
    "eclipse": {"name": "THE ECLIPSE TYRANT", "hp": 4600, "reward": 1400, "damage": (50, 78), "description": "An ancient warlord whose aura can silence an entire battlefield."},
}

WEAPONS = {
    "ironblade": {"name": "Ironblade", "level": 1, "damage": (75, 110), "ability": "cleave", "ability_name": "Rising Cleave", "ability_damage": (145, 190), "cost": 1},
    "frostfang": {"name": "Frostfang", "level": 3, "damage": (65, 125), "ability": "frostbite", "ability_name": "Winter Prison", "ability_damage": (175, 220), "cost": 2},
    "stormcaller": {"name": "Stormcaller", "level": 6, "damage": (90, 135), "ability": "thunderfall", "ability_name": "Heaven’s Breaker", "ability_damage": (210, 270), "cost": 2},
    "voidreaper": {"name": "Voidreaper", "level": 10, "damage": (115, 160), "ability": "soulrend", "ability_name": "Abyssal Sever", "ability_damage": (270, 340), "cost": 3},
}

class Adventure(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.encounters = {}
        self.lock = asyncio.Lock()
        self.db = sqlite3.connect(DB_PATH)
        self.db.execute("""CREATE TABLE IF NOT EXISTS profiles (
            user_id INTEGER PRIMARY KEY, xp INTEGER NOT NULL DEFAULT 0,
            level INTEGER NOT NULL DEFAULT 1, skill_points INTEGER NOT NULL DEFAULT 0,
            weapon TEXT NOT NULL DEFAULT 'ironblade', unlocked TEXT NOT NULL DEFAULT ''
        )""")
        self.db.commit()

    def profile(self, user_id: int):
        row = self.db.execute("SELECT xp, level, skill_points, weapon, unlocked FROM profiles WHERE user_id=?", (user_id,)).fetchone()
        if row is None:
            self.db.execute("INSERT INTO profiles(user_id) VALUES(?)", (user_id,))
            self.db.commit()
            return self.profile(user_id)
        return {"xp": row[0], "level": row[1], "points": row[2], "weapon": row[3], "unlocked": set(filter(None, row[4].split(",")))}

    def save_profile(self, user_id: int, profile: dict) -> None:
        self.db.execute("UPDATE profiles SET xp=?, level=?, skill_points=?, weapon=?, unlocked=? WHERE user_id=?",
                        (profile["xp"], profile["level"], profile["points"], profile["weapon"], ",".join(sorted(profile["unlocked"])), user_id))
        self.db.commit()

    def make_embed(self, title: str, description: str = "", color: discord.Color = discord.Color.from_rgb(77, 54, 92)) -> discord.Embed:
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_footer(text="PEAK  /  THE AWAKENING")
        return embed

    def weapon_for(self, user_id: int):
        profile = self.profile(user_id)
        return WEAPONS.get(profile["weapon"], WEAPONS["ironblade"])

    @commands.group(name="boss", invoke_without_command=True, aliases=["hunt"])
    async def boss(self, ctx: commands.Context) -> None:
        p = ctx.clean_prefix
        await ctx.reply(embed=self.make_embed("HUNTER GUILD", f"`{p}bosses` view calamities  ·  `{p}boss challenge <name>` start a raid\\n`{p}join` enter  ·  `{p}attack [technique]` take your turn\\n`{p}boss status` inspect the battlefield"), mention_author=False)
`{p}join` enter  ·  `{p}attack [ability]` take your turn
`{p}boss status` encounter status"), mention_author=False)

    @commands.command(name="bosses", aliases=["bestiary"])
    async def bosses(self, ctx: commands.Context) -> None:
        embed = self.make_embed("CALAMITY REGISTER", "Threats recorded by the Hunter Guild. Each boss retaliates after every adventurer’s turn.")
        for key, boss in BOSSES.items():
            embed.add_field(name=f"{boss['name']}  /  {key}", value=f"{boss['description']}\n**{boss['hp']:,} HP**  ·  **{boss['damage'][0]}–{boss['damage'][1]} damage** per turn", inline=False)
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
                await ctx.reply(embed=self.make_embed("Encounter in progress", "Defeat the current target before summoning another.", discord.Color.orange()), mention_author=False)
                return
            boss = BOSSES[key]
            self.encounters[ctx.guild.id] = {"key": key, "hp": boss["hp"], "max_hp": boss["hp"],
                "damage": defaultdict(int), "players": {ctx.author.id: 250}, "turns": [ctx.author.id], "turn": 0}
        embed = self.make_embed(f"TARGET ACQUIRED  /  {boss['name']}", f"{boss['description']}\n\n**VITALITY**\n{boss['hp']:,} HP\n\n**FIRST TURN**\n{ctx.author.mention}\n\nOther players can use `{ctx.clean_prefix}join`.")
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="join")
    @commands.guild_only()
    async def join(self, ctx: commands.Context) -> None:
        async with self.lock:
            encounter = self.encounters.get(ctx.guild.id)
            if not encounter:
                await ctx.reply(embed=self.make_embed("No active encounter", "There is no boss to join."), mention_author=False)
                return
            if ctx.author.id in encounter["players"]:
                await ctx.reply(embed=self.make_embed("Already enlisted", "You are already in this encounter."), mention_author=False)
                return
            encounter["players"][ctx.author.id] = 250
            encounter["turns"].append(ctx.author.id)
            position = len(encounter["turns"])
        await ctx.reply(embed=self.make_embed("Adventurer enlisted", f"{ctx.author.mention} joined with **250 HP**. Turn position: **{position}**."), mention_author=False)

    @boss.command(name="status", aliases=["info"])
    @commands.guild_only()
    async def status(self, ctx: commands.Context) -> None:
        encounter = self.encounters.get(ctx.guild.id)
        if not encounter:
            await ctx.reply(embed=self.make_embed("No active target", f"Summon one with `{ctx.clean_prefix}boss challenge warden`."), mention_author=False)
            return
        boss = BOSSES[encounter["key"]]
        hp = max(0, encounter["hp"])
        filled = round((hp / encounter["max_hp"]) * 16)
        alive = [uid for uid in encounter["turns"] if encounter["players"].get(uid, 0) > 0]
        current = alive[encounter["turn"] % len(alive)] if alive else None
        roster = "\n".join(f"<@{uid}> — {health}/250 HP" for uid, health in encounter["players"].items())
        embed = self.make_embed(boss["name"], f"`{'█' * filled}{'░' * (16-filled)}`\n**{hp:,} / {encounter['max_hp']:,} HP**")
        embed.add_field(name="Current turn", value=f"<@{current}>" if current else "None", inline=True)
        embed.add_field(name="Damage dealt", value=f"{sum(encounter['damage'].values()):,}", inline=True)
        embed.add_field(name="Party", value=roster[:1024] or "No players", inline=False)
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="weapons")
    async def weapons(self, ctx: commands.Context) -> None:
        profile = self.profile(ctx.author.id)
        lines = []
        for key, weapon in WEAPONS.items():
            state = "equipped" if profile["weapon"] == key else "unlocked" if profile["level"] >= weapon["level"] else f"locked · level {weapon['level']}"
            lines.append(f"**{weapon['name']}** — {weapon['damage'][0]}–{weapon['damage'][1]} damage\nAbility: **{weapon['ability_name']}** ({weapon['ability_damage'][0]}–{weapon['ability_damage'][1]} damage, {weapon['cost']} skill points)\n{state}")
        await ctx.reply(embed=self.make_embed("Armoury", "\n\n".join(lines)), mention_author=False)

    @commands.command(name="weapon")
    async def weapon(self, ctx: commands.Context, *, name: str) -> None:
        key = name.lower().strip()
        profile = self.profile(ctx.author.id)
        weapon = WEAPONS.get(key)
        if not weapon:
            await ctx.reply(embed=self.make_embed("Weapon not found", "Use `,weapons` to view weapon names."), mention_author=False)
            return
        if profile["level"] < weapon["level"]:
            await ctx.reply(embed=self.make_embed("Weapon locked", f"Reach level **{weapon['level']}** to equip {weapon['name']}.", discord.Color.orange()), mention_author=False)
            return
        profile["weapon"] = key
        self.save_profile(ctx.author.id, profile)
        await ctx.reply(embed=self.make_embed("Weapon equipped", f"{ctx.author.mention} equipped **{weapon['name']}**."), mention_author=False)

    @commands.command(name="skills")
    async def skills(self, ctx: commands.Context) -> None:
        profile = self.profile(ctx.author.id)
        weapon = WEAPONS[profile["weapon"]]
        unlocked = weapon["ability"] in profile["unlocked"]
        await ctx.reply(embed=self.make_embed("Skill ledger", f"**Skill points:** {profile['points']}\n**Equipped weapon:** {weapon['name']}\n**{weapon['ability_name']}** — {weapon['ability_damage'][0]}–{weapon['ability_damage'][1]} damage\nUnlock with `,unlock {weapon['ability']}` for {weapon['cost']} points.\n**Status:** {'Unlocked' if unlocked else 'Locked'}"), mention_author=False)

    @commands.command(name="unlock")
    async def unlock(self, ctx: commands.Context, *, skill: str) -> None:
        profile = self.profile(ctx.author.id)
        weapon = WEAPONS[profile["weapon"]]
        key = weapon["ability"]
        if skill.lower().strip() != key:
            await ctx.reply(embed=self.make_embed("Unknown skill", f"Your equipped weapon's skill is **{key}**.", discord.Color.orange()), mention_author=False)
            return
        if key in profile["unlocked"]:
            await ctx.reply(embed=self.make_embed("Already unlocked", f"**{weapon['ability_name']}** is already available."), mention_author=False)
            return
        if profile["points"] < weapon["cost"]:
            await ctx.reply(embed=self.make_embed("Not enough skill points", f"You need **{weapon['cost']}** points. You have **{profile['points']}**."), mention_author=False)
            return
        profile["points"] -= weapon["cost"]
        profile["unlocked"].add(key)
        self.save_profile(ctx.author.id, profile)
        await ctx.reply(embed=self.make_embed("Skill unlocked", f"**{weapon['ability_name']}** is now available for **{weapon['name']}**."), mention_author=False)

    @commands.command(name="attack", aliases=["strike", "hit"])
    @commands.guild_only()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def attack(self, ctx: commands.Context, ability: str = None) -> None:
        async with self.lock:
            encounter = self.encounters.get(ctx.guild.id)
            if not encounter:
                await ctx.reply(embed=self.make_embed("No active target", f"Summon a boss with `{ctx.clean_prefix}boss challenge warden`."), mention_author=False)
                return
            if ctx.author.id not in encounter["players"]:
                await ctx.reply(embed=self.make_embed("Not enlisted", f"Use `{ctx.clean_prefix}join` before attacking."), mention_author=False)
                return
            alive = [uid for uid in encounter["turns"] if encounter["players"].get(uid, 0) > 0]
            if not alive:
                del self.encounters[ctx.guild.id]
                await ctx.reply(embed=self.make_embed("Party defeated", "The party has been defeated. The encounter is over.", discord.Color.red()), mention_author=False)
                return
            encounter["turn"] %= len(alive)
            current_id = alive[encounter["turn"]]
            if current_id != ctx.author.id:
                await ctx.reply(embed=self.make_embed("Not your turn", f"It is <@{current_id}>'s turn. Each adventurer acts in order.", discord.Color.orange()), mention_author=False)
                return
            profile = self.profile(ctx.author.id)
            weapon = WEAPONS[profile["weapon"]]
            if ability:
                ability = ability.lower().strip()
                if ability != weapon["ability"] or ability not in profile["unlocked"]:
                    await ctx.reply(embed=self.make_embed("Ability unavailable", f"Equip {weapon['name']} and unlock **{weapon['ability']}** first. Use `,skills`.", discord.Color.orange()), mention_author=False)
                    return
                dealt = random.randint(*weapon["ability_damage"])
                action = weapon["ability_name"]
            else:
                dealt = random.randint(*weapon["damage"])
                action = "Basic attack"
            boss = BOSSES[encounter["key"]]
            dealt = min(dealt, encounter["hp"])
            encounter["hp"] -= dealt
            encounter["damage"][ctx.author.id] += dealt
            if encounter["hp"] <= 0:
                participants = list(encounter["players"])
                results = sorted(encounter["damage"].items(), key=lambda item: item[1], reverse=True)
                for uid in participants:
                    p = self.profile(uid)
                    p["xp"] += 100 + encounter["damage"].get(uid, 0) // 5
                    p["points"] += 1
                    while p["xp"] >= p["level"] * 250:
                        p["xp"] -= p["level"] * 250
                        p["level"] += 1
                    self.save_profile(uid, p)
                del self.encounters[ctx.guild.id]
                defeated = True
                boss_text = ""
            else:
                defeated = False
                # The boss retaliates immediately after the active adventurer's turn.
                incoming = random.randint(*boss["damage"])
                encounter["players"][ctx.author.id] = max(0, encounter["players"][ctx.author.id] - incoming)
                player_hp = encounter["players"][ctx.author.id]
                alive_after = [uid for uid in encounter["turns"] if encounter["players"].get(uid, 0) > 0]
                if alive_after:
                    old_index = encounter["turns"].index(ctx.author.id)
                    next_candidates = encounter["turns"][old_index + 1:] + encounter["turns"][:old_index]
                    next_id = next((uid for uid in next_candidates if encounter["players"].get(uid, 0) > 0), None)
                    encounter["turn"] = alive_after.index(next_id) if next_id else 0
                    next_text = f"\n**Next turn:** <@{next_id}>"
                else:
                    next_text = "\n**The entire party has fallen.**"
                    del self.encounters[ctx.guild.id]
                boss_text = f"\n\n**{boss['name']} retaliates**\n<@{ctx.author.id}> takes **{incoming} damage**. Remaining HP: **{player_hp}/250**.{next_text}"
        if defeated:
            ranking = "\n".join(f"**{i}.** <@{uid}> — {amount:,} damage" for i, (uid, amount) in enumerate(results[:5], 1))
            embed = self.make_embed(f"TARGET ELIMINATED  /  {boss['name']}", f"The party defeated the target. Every participant receives **100+ XP** and **1 skill point**.", discord.Color.green())
            if ranking:
                embed.add_field(name="Damage rankings", value=ranking, inline=False)
        else:
            embed = self.make_embed("Turn resolved", f"{ctx.author.mention} used **{action}** with **{weapon['name']}** for **{dealt:,} damage**.{boss_text}", discord.Color.blurple())
            hp = encounter["hp"] if ctx.guild.id in self.encounters else 0
            maximum = encounter["max_hp"]
            filled = round((hp / maximum) * 16)
            embed.add_field(name="Boss vitality", value=f"`{'█' * filled}{'░' * (16-filled)}`\n**{hp:,} / {maximum:,} HP**", inline=False)
        await ctx.reply(embed=embed, mention_author=False)

    @attack.error
    async def attack_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.reply(embed=self.make_embed("Action cooling down", "You can act once per second.", discord.Color.orange()), mention_author=False)
        else:
            raise error


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Adventure(bot))
