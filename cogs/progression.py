from datetime import datetime, timezone
from discord.ext import commands

TITLE_RULES = {
    "rookie": ("Rookie", "Complete your first raid.", lambda p: p.get("wins", 0) >= 1 or p.get("symbolic_rewards", {}).get("wins", 0) > 0),
    "slayer": ("Boss Slayer", "Win 10 raids.", lambda p: p.get("wins", 0) >= 10 or p.get("symbolic_rewards", {}).get("wins", 0) > 0),
    "conqueror": ("Conqueror", "Win 100 raids.", lambda p: p.get("wins", 0) >= 100 or p.get("symbolic_rewards", {}).get("wins", 0) > 0),
    "calamity": ("Calamity", "Deal at least 100,000 total damage.", lambda p: p.get("damage", 0) >= 100000 or p.get("symbolic_rewards", {}).get("damage", 0) > 0),
    "limitless": ("Limitless", "Reach level 50.", lambda p: p.get("level", 1) >= 50),
    "king_of_curses": ("King of Curses", "Unlock the King of Curses race.", lambda p: p.get("sukuna_race_unlocked", False) or p.get("race") == "sukuna"),
}
DAILY_REWARDS = (500, 2)
WEEKLY_REWARDS = (2500, 10)

def utc_day():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")

def utc_week():
    return datetime.now(timezone.utc).strftime("%G-W%V")

class Progression(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def profile(self, user_id):
        cog = self.bot.get_cog("Adventure")
        if cog is None:
            raise RuntimeError("Adventure module is not loaded")
        p = cog.p(user_id)
        p.setdefault("quests", {})
        p.setdefault("unlocked_titles", [])
        p.setdefault("equipped_title", None)
        return cog, p

    def ensure_quest(self, p, kind):
        state = p["quests"]
        key = utc_day() if kind == "daily" else utc_week()
        if state.get(f"{kind}_period") != key:
            state[f"{kind}_period"] = key
            state[f"{kind}_claimed"] = False
            state[f"{kind}_baseline_wins"] = int(p.get("wins", 0))
            state[f"{kind}_baseline_damage"] = int(p.get("damage", 0))
            sr = p.get("symbolic_rewards", {})
            state[f"{kind}_baseline_symbolic_wins"] = int(sr.get("wins", 0))
            state[f"{kind}_baseline_symbolic_damage"] = int(sr.get("damage", 0))
            if kind == "daily":
                state["daily_objective"] = "damage" if int(p.get("wins", 0)) % 2 == 0 else "wins"
        return state

    def quest_progress(self, p, kind):
        state = self.ensure_quest(p, kind)
        wins = max(0, int(p.get("wins", 0)) - state[f"{kind}_baseline_wins"])
        damage = max(0, int(p.get("damage", 0)) - state[f"{kind}_baseline_damage"])
        sr = p.get("symbolic_rewards", {})
        wins += max(0, int(sr.get("wins", 0)) - state[f"{kind}_baseline_symbolic_wins"])
        damage += max(0, int(sr.get("damage", 0)) - state[f"{kind}_baseline_symbolic_damage"])
        if kind == "daily":
            if state.get("daily_objective") == "wins":
                return wins, 1, "Win a boss raid"
            return damage, 1000, "Deal 1,000 damage"
        return wins, 3, "Win 3 boss raids"

    def grant_titles(self, p):
        unlocked = set(p.get("unlocked_titles", []))
        new_titles = []
        for key, (_, _, check) in TITLE_RULES.items():
            if key not in unlocked and check(p):
                unlocked.add(key)
                new_titles.append(key)
        p["unlocked_titles"] = sorted(unlocked)
        return new_titles

    @commands.command(name="daily")
    async def daily(self, ctx):
        cog, p = self.profile(ctx.author.id)
        self.ensure_quest(p, "daily")
        progress, target, objective = self.quest_progress(p, "daily")
        state = p["quests"]
        cog.flush()
        status = "READY TO CLAIM" if progress >= target and not state["daily_claimed"] else ("CLAIMED" if state["daily_claimed"] else "IN PROGRESS")
        embed = cog.embed("DAILY CONTRACT", f"**Objective:** {objective}\n**Progress:** {min(progress, target):,}/{target:,}\n**Status:** {status}\n**Reward:** {DAILY_REWARDS[0]:,} XP and {DAILY_REWARDS[1]} skill points\n\nClaim with ,claim daily once complete.")
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="weekly")
    async def weekly(self, ctx):
        cog, p = self.profile(ctx.author.id)
        self.ensure_quest(p, "weekly")
        progress, target, objective = self.quest_progress(p, "weekly")
        state = p["quests"]
        cog.flush()
        status = "READY TO CLAIM" if progress >= target and not state["weekly_claimed"] else ("CLAIMED" if state["weekly_claimed"] else "IN PROGRESS")
        embed = cog.embed("WEEKLY CONTRACT", f"**Objective:** {objective}\n**Progress:** {min(progress, target):,}/{target:,}\n**Status:** {status}\n**Reward:** {WEEKLY_REWARDS[0]:,} XP and {WEEKLY_REWARDS[1]} skill points\n\nClaim with ,claim weekly once complete.")
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="quests")
    async def quests(self, ctx):
        cog, p = self.profile(ctx.author.id)
        lines = []
        for kind in ("daily", "weekly"):
            self.ensure_quest(p, kind)
            progress, target, objective = self.quest_progress(p, kind)
            claimed = p["quests"].get(f"{kind}_claimed", False)
            status = "Claimed" if claimed else ("Ready" if progress >= target else "In progress")
            lines.append(f"**{kind.title()}** · {objective}\n{min(progress, target):,}/{target:,} · {status}")
        cog.flush()
        await ctx.reply(embed=cog.embed("CONTRACT BOARD", "\n\n".join(lines)), mention_author=False)

    @commands.command(name="claim")
    async def claim(self, ctx, kind: str):
        kind = kind.lower().strip()
        if kind not in {"daily", "weekly"}:
            await ctx.reply("Choose daily or weekly.")
            return
        cog, p = self.profile(ctx.author.id)
        self.ensure_quest(p, kind)
        progress, target, objective = self.quest_progress(p, kind)
        state = p["quests"]
        claimed_key = f"{kind}_claimed"
        if state.get(claimed_key):
            await ctx.reply(embed=cog.embed("ALREADY CLAIMED", f"Your {kind} contract has already been claimed for this period."))
            return
        if progress < target:
            await ctx.reply(embed=cog.embed("CONTRACT INCOMPLETE", f"{objective}\nProgress: {min(progress, target):,}/{target:,}."))
            return
        xp, points = DAILY_REWARDS if kind == "daily" else WEEKLY_REWARDS
        p["xp"] = int(p.get("xp", 0)) + xp
        p["points"] = int(p.get("points", 0)) + points
        from cogs.adventure import apply_level_ups
        levels = apply_level_ups(p)
        state[claimed_key] = True
        new_titles = self.grant_titles(p)
        cog.flush()
        extra = f"\nLevels gained: {levels}" if levels else ""
        if new_titles:
            extra += "\nNew titles: " + ", ".join(TITLE_RULES[k][0] for k in new_titles)
        await ctx.reply(embed=cog.embed(f"{kind.upper()} REWARD CLAIMED", f"Received {xp:,} XP and {points} skill points.{extra}"), mention_author=False)

    @commands.command(name="achievements", aliases=["achieve"])
    async def achievements(self, ctx):
        cog, p = self.profile(ctx.author.id)
        new_titles = self.grant_titles(p)
        cog.flush()
        unlocked = set(p["unlocked_titles"])
        lines = [f"**{name}** · {'UNLOCKED' if key in unlocked else 'LOCKED'}\n{requirement}" for key, (name, requirement, _) in TITLE_RULES.items()]
        await ctx.reply(embed=cog.embed("ACHIEVEMENT ARCHIVE", "\n\n".join(lines)), mention_author=False)

    @commands.command(name="titles")
    async def titles(self, ctx):
        cog, p = self.profile(ctx.author.id)
        self.grant_titles(p)
        cog.flush()
        equipped = p.get("equipped_title")
        available = [TITLE_RULES[k][0] for k in p["unlocked_titles"] if k in TITLE_RULES]
        listing = "\n".join(available) if available else "No titles unlocked yet. Complete achievements to earn titles."
        current = TITLE_RULES[equipped][0] if equipped in TITLE_RULES else "None"
        await ctx.reply(embed=cog.embed("TITLE COLLECTION", f"**Equipped:** {current}\n\n{listing}\n\nEquip with ,title <key> or clear with ,title off."), mention_author=False)

    @commands.command(name="title")
    async def title(self, ctx, *, key: str):
        cog, p = self.profile(ctx.author.id)
        key = key.lower().strip().replace(" ", "_")
        self.grant_titles(p)
        if key in {"off", "none", "clear"}:
            p["equipped_title"] = None
            cog.flush()
            await ctx.reply(embed=cog.embed("TITLE CLEARED", "Your profile title has been removed."), mention_author=False)
            return
        if key not in TITLE_RULES or key not in p.get("unlocked_titles", []):
            await ctx.reply(embed=cog.embed("TITLE LOCKED", "That title is unavailable. Check achievements and titles."), mention_author=False)
            return
        p["equipped_title"] = key
        cog.flush()
        await ctx.reply(embed=cog.embed("TITLE EQUIPPED", f"Your title is now **{TITLE_RULES[key][0]}**."), mention_author=False)

async def setup(bot):
    await bot.add_cog(Progression(bot))
