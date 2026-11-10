import random
from discord.ext import commands

from core.locking import serialized

from cogs.adventure import (
    CHARACTERS, CLANS, DIMENSIONS, PETS, RACES, SKILL_TREE,
    AttackCategoryView, apply_level_ups, display_number, mastery_tier,
)

MAX_ASCENSIONS = 25
ASCENSION_BONUS = 0.02
WORLD_BOSSES = {
    "world_eater": {"name": "The World Eater", "hp": 120_000, "damage": (90, 140), "drops": ["rift_crystal", "mythic_token", "abyssal_pearl"]},
    "celestial_dragon": {"name": "The Celestial Dragon", "hp": 400_000, "damage": (150, 220), "drops": ["dragon_scale", "phoenix_ash", "mythic_token"]},
    "void_emperor": {"name": "The Void Emperor", "hp": 1_200_000, "damage": (240, 340), "drops": ["abyssal_pearl", "spiral_core", "rift_crystal"]},
}


def ascension_damage_multiplier(profile):
    rank = max(0, min(MAX_ASCENSIONS, int(profile.get("ascension", 0))))
    return 1.0 + rank * ASCENSION_BONUS


def ascension_cost(rank):
    rank = max(0, int(rank))
    return {"rift_crystal": 5 + rank * 2, "mythic_token": 1 + rank // 3, "time_rift_fragment": 10 + rank * 5}


def worldboss_reward_tier(damage, max_hp, rank):
    share = max(0, int(damage)) / max(1, int(max_hp))
    if rank == 1 or share >= 0.20:
        return "mythic"
    if rank <= 3 or share >= 0.08:
        return "ruby"
    if share >= 0.02:
        return "diamond"
    return "rare"


class Ascension(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def services(self, ctx):
        game = self.bot.get_cog("Adventure")
        if game is None:
            raise RuntimeError("Adventure module is not loaded")
        return game, game.p(ctx.author.id)

    def attack_skill_options(self, uid, category=None):
        game = self.bot.get_cog("Adventure")
        return game.attack_skill_options(uid, category) if game else {}

    def embed(self, game_or_title, title_or_description="", description="", color=None):
        if isinstance(game_or_title, str):
            game = self.bot.get_cog("Adventure")
            title = game_or_title
            description = title_or_description
        else:
            game = game_or_title
            title = title_or_description
        return game.embed(title, description, color)

    @commands.command(name="ascension", aliases=["ascendinfo"])
    async def ascension(self, ctx):
        game, p = self.services(ctx)
        rank = max(0, int(p.get("ascension", 0)))
        cost = ascension_cost(rank)
        missing = [f"{key.replace('_', ' ').title()} ×{amount}" for key, amount in cost.items() if not game.has_item(p, key, amount)]
        ready = int(p.get("level", 1)) >= 55 and int(p.get("best_tower", 0)) >= 10 and not missing and rank < MAX_ASCENSIONS
        description = (
            f"**Ascension:** {rank}/{MAX_ASCENSIONS}\n"
            f"**Permanent damage bonus:** +{rank * 2}%\n"
            f"**Level:** {display_number(p.get('level', 1))} (requires 55)\n"
            f"**Best Rift Tower floor:** {p.get('best_tower', 0)} (requires 10)\n\n"
            "**Next trial cost**\n"
            + "\n".join(f"• {key.replace('_', ' ').title()} ×{amount}" for key, amount in cost.items())
            + "\n\n"
            + ("All requirements met. Use ,ascend." if ready else ("Maximum ascension reached." if rank >= MAX_ASCENSIONS else "Missing: " + (", ".join(missing) if missing else "Reach level 55 and clear Rift Tower floor 10.")))
            + "\n\nYour level, XP, inventory, equipment, weapons and existing progress are never reset."
        )
        await ctx.reply(embed=self.embed(game, "ASCENSION ARCHIVE", description), mention_author=False)

    @commands.command(name="ascend")
    @serialized
    async def ascend(self, ctx):
        game, p = self.services(ctx)
        rank = max(0, int(p.get("ascension", 0)))
        if rank >= MAX_ASCENSIONS:
            await ctx.reply(embed=self.embed(game, "ASCENSION COMPLETE", f"You have reached the maximum rank of {MAX_ASCENSIONS}."), mention_author=False)
            return
        cost = ascension_cost(rank)
        if int(p.get("level", 1)) < 55 or int(p.get("best_tower", 0)) < 10:
            await ctx.reply(embed=self.embed(game, "TRIAL REQUIREMENTS", "Reach level 55 and clear at least floor 10 of the Rift Tower. Your progress is not reset when you ascend."), mention_author=False)
            return
        missing = [f"{key.replace('_', ' ').title()} ×{amount - int(p['inventory'].get(key, 0))}" for key, amount in cost.items() if int(p["inventory"].get(key, 0)) < amount]
        if missing:
            await ctx.reply(embed=self.embed(game, "MATERIALS REQUIRED", "\n".join(missing) + "\nCheck ,ascension for the full requirements."), mention_author=False)
            return
        for key, amount in cost.items():
            if not game.consume_item(p, key, amount):
                await ctx.reply(embed=self.embed(game, "MATERIAL ERROR", "A required material could not be consumed. No ascension was applied."), mention_author=False)
                return
        p["ascension"] = rank + 1
        p["points"] = int(p.get("points", 0)) + 5
        p["xp"] = int(p.get("xp", 0)) + 2500
        levels = apply_level_ups(p)
        game.flush()
        await ctx.reply(embed=self.embed(game, "ASCENSION SUCCESSFUL", f"**Ascension {rank + 1}/{MAX_ASCENSIONS}**\nPermanent damage bonus: **+{(rank + 1) * 2}%**\nBonus: 5 skill points and 2,500 XP ({levels} levels gained).\n\nYour level, items, weapons, equipment, skills and other progress were preserved."), mention_author=False)

    @commands.group(name="worldboss", aliases=["wb"], invoke_without_command=True)
    async def worldboss(self, ctx):
        game, _ = self.services(ctx)
        state = game.data.get("world_boss")
        if not state:
            description = "No world boss is currently active. The bot owner can open an event with ,worldboss summon <key>."
        else:
            status = "ACTIVE" if state.get("active") else "DEFEATED — rewards available"
            rows = sorted(state.get("players", {}).items(), key=lambda row: row[1].get("damage", 0), reverse=True)[:5]
            board = "\n".join(f"<@{uid}> · {display_number(data.get('damage', 0))}" for uid, data in rows) or "No contributors yet."
            description = (
                f"**{state['name']}** · {status}\n"
                f"HP: {display_number(state.get('hp', 0))}/{display_number(state.get('max_hp', 0))}\n"
                f"Contributors: {len(state.get('players', {}))}\n\n**Top damage**\n{board}\n\n"
                + ("Join with ,worldboss join, then use ,attack." if state.get("active") else "Claim your reward with ,worldboss claim.")
            )
        await ctx.reply(embed=self.embed(game, "GLOBAL WORLD BOSS", description), mention_author=False)

    @worldboss.command(name="summon")
    @commands.guild_only()
    @commands.is_owner()
    async def worldboss_summon(self, ctx, *, key: str):
        game, _ = self.services(ctx)
        key = key.lower().strip().replace(" ", "_")
        boss = WORLD_BOSSES.get(key)
        if boss is None:
            await ctx.reply(embed=self.embed(game, "UNKNOWN WORLD BOSS", "Choose: world_eater, celestial_dragon, or void_emperor."), mention_author=False)
            return
        async with game.lock:
            old = game.data.get("world_boss")
            if old and old.get("active"):
                await ctx.reply(embed=self.embed(game, "EVENT ALREADY ACTIVE", f"{old['name']} still has {display_number(old['hp'])} HP remaining. Close it with ,worldboss close first."), mention_author=False)
                return
            if old and old.get("defeated"):
                pending = [uid for uid, data in old.get("players", {}).items() if int(data.get("damage", 0)) > 0 and uid not in old.get("claimed", [])]
                if pending:
                    await ctx.reply(embed=self.embed(game, "REWARDS STILL UNCLAIMED", f"{len(pending)} contributors still have rewards waiting. Ask them to use ,worldboss claim, or close the old event with ,worldboss close."), mention_author=False)
                    return
            event_id = int(game.data.get("world_boss_counter", 0)) + 1
            game.data["world_boss_counter"] = event_id
            game.data["world_boss"] = {
                "id": event_id, "key": key, "name": boss["name"],
                "hp": boss["hp"], "max_hp": boss["hp"], "active": True,
                "players": {}, "claimed": [], "drops": boss["drops"],
            }
            game.flush()
        await ctx.reply(embed=self.embed(game, "WORLD BOSS SUMMONED", f"**{boss['name']}** has appeared across every server.\nHealth: {display_number(boss['hp'])}\nJoin with ,worldboss join and fight with ,attack. Rewards are based on your contribution."), mention_author=False)

    @worldboss.command(name="join")
    async def worldboss_join(self, ctx):
        game, p = self.services(ctx)
        async with game.lock:
            state = game.data.get("world_boss")
            if not state or not state.get("active"):
                await ctx.reply(embed=self.embed(game, "NO ACTIVE EVENT", "There is no world boss to join right now."), mention_author=False)
                return
            uid = str(ctx.author.id)
            state.setdefault("players", {}).setdefault(uid, {"damage": 0, "attacks": 0})
            p["attack_mode"] = "worldboss"
            game.flush()
            name = state["name"]
        await ctx.reply(embed=self.embed(game, "WORLD BOSS PARTY", f"You joined **{name}**. Use ,attack to choose an equipped skill."), mention_author=False)

    @worldboss.command(name="attack")
    @commands.cooldown(1, 3.0, commands.BucketType.user)
    async def worldboss_attack(self, ctx, *, ability: str = None):
        game, p = self.services(ctx)
        state = game.data.get("world_boss")
        uid = str(ctx.author.id)
        if not state or not state.get("active"):
            await ctx.reply(embed=self.embed(game, "NO ACTIVE EVENT", "There is no active world boss."), mention_author=False)
            return
        if uid not in state.get("players", {}):
            await ctx.reply(embed=self.embed(game, "NOT IN EVENT", "Join first with ,worldboss join."), mention_author=False)
            return
        if ability is None:
            categories = game.attack_skill_options(ctx.author.id)
            if not categories:
                await ctx.reply(embed=self.embed(game, "NO EQUIPPED SKILLS", "Equip an unlocked skill first with ,equipskill <melee|sword|magic> <skill>."), mention_author=False)
                return
            await ctx.reply(embed=self.embed(game, "CHOOSE WEAPON TYPE", "Choose a category, then choose an equipped skill. No damage is dealt until you select it."), view=AttackCategoryView(self, ctx, categories, self.worldboss_attack, self), mention_author=False)
            return
        async with game.lock:
            state = game.data.get("world_boss")
            if not state or not state.get("active"):
                await ctx.reply(embed=self.embed(game, "EVENT ENDED", "The world boss is no longer active."), mention_author=False)
                return
            if uid not in state.get("players", {}):
                await ctx.reply(embed=self.embed(game, "NOT IN EVENT", "Join first with ,worldboss join."), mention_author=False)
                return
            char = CHARACTERS[p["character"]]
            custom = game.data.get("custom_weapons", {}).get(p.get("weapon"))
            key = ability.lower().strip().replace(" ", "_")
            options = game.attack_skill_options(ctx.author.id)
            category = next((kind for kind, skills in options.items() if any(skill_key == key for skill_key, _ in skills)), None)
            if category is None:
                await ctx.reply(embed=self.embed(game, "SKILL NOT EQUIPPED", "That skill is not equipped in your loadout."), mention_author=False)
                return
            if custom and key == custom.get("ability_key"):
                damage = random.randint(*custom["ability_damage"])
                action = custom["ability"]
                override = p.get("weapon_damage_override")
                if override == "googolplex":
                    damage = state["hp"]
                elif override is not None:
                    damage = int(override)
            elif key == char[5]:
                if key not in p.get("unlocked", []) and not (p["race"] == "vessel" and p["character"] == "sukuna"):
                    await ctx.reply(embed=self.embed(game, "SKILL LOCKED", f"Unlock it with ,unlock {key}."), mention_author=False)
                    return
                damage = random.randint(*char[6])
                action = char[4]
            elif key in p.get("unlocked_skills", []) and key in SKILL_TREE:
                skill = SKILL_TREE[key]
                damage = int(random.randint(*char[3]) * skill["multiplier"])
                action = skill["name"]
            else:
                await ctx.reply(embed=self.embed(game, "SKILL LOCKED", "That ability is not unlocked."), mention_author=False)
                return
            race = RACES[p["race"]]
            clan = CLANS.get(p.get("clan"))
            clan_mult = 1 + (clan.get(category, 0) if clan else 0)
            level_mult = 1 + min(35, max(0, int(p.get("level", 1)) - 1)) * 0.01
            mastery_xp = int(p.setdefault("mastery", {}).get(p["character"], 0))
            mastery_mult = 1 + 0.02 * mastery_tier(mastery_xp)
            gear_attack = 0
            try:
                from cogs.endgame import GEAR
                gear_attack = sum(GEAR[k]["attack"] for k in p.get("gear_equipped", {}).values() if k in GEAR)
            except ImportError:
                pass
            pet = PETS.get(p.get("pet_equipped"))
            pet_mult = 1 + (pet["attack"] if pet else 0)
            if p.get("damage_boosts", 0) > 0:
                damage = int(damage * 1.5)
                p["damage_boosts"] -= 1
            if p.get("focus_boosts", 0) > 0:
                damage *= 2
                p["focus_boosts"] -= 1
            dimension_mult = DIMENSIONS.get(p.get("active_dimension"), DIMENSIONS["earth"])["bonus"]
            damage = int((damage + gear_attack) * race[1] * clan_mult * level_mult * mastery_mult * pet_mult * dimension_mult * ascension_damage_multiplier(p))
            damage = min(int(state["hp"]), max(1, damage))
            state["hp"] = max(0, int(state["hp"]) - damage)
            entry = state["players"][uid]
            entry["damage"] = min(int(state["max_hp"]), int(entry.get("damage", 0)) + damage)
            entry["attacks"] = int(entry.get("attacks", 0)) + 1
            p["damage"] = int(p.get("damage", 0)) + damage
            p.setdefault("mastery", {})[p["character"]] = mastery_xp + damage
            defeated = state["hp"] <= 0
            if defeated:
                state["active"] = False
                state["defeated"] = True
                state["winner"] = uid
            game.flush()
            remaining = int(state["hp"])
            boss_name = state["name"]
            max_hp = int(state["max_hp"])
        result = f"You used **{action}** for **{display_number(damage)}** damage.\n{boss_name} HP: {display_number(remaining)}/{display_number(max_hp)}."
        if defeated:
            result += "\n\n**WORLD BOSS DEFEATED.** Contributors can claim rewards with ,worldboss claim."
        await ctx.reply(embed=self.embed(game, "WORLD BOSS TURN", result), mention_author=False)

    @worldboss.command(name="leaderboard", aliases=["top"])
    async def worldboss_leaderboard(self, ctx):
        game, _ = self.services(ctx)
        state = game.data.get("world_boss")
        if not state:
            await ctx.reply(embed=self.embed(game, "WORLD BOSS LEADERBOARD", "No event has been recorded yet."), mention_author=False)
            return
        rows = sorted(state.get("players", {}).items(), key=lambda row: row[1].get("damage", 0), reverse=True)[:10]
        description = "\n".join(f"**{i}.** <@{uid}> · {display_number(data.get('damage', 0))} damage · {data.get('attacks', 0)} attacks" for i, (uid, data) in enumerate(rows, 1)) or "No damage recorded."
        await ctx.reply(embed=self.embed(game, "WORLD BOSS LEADERBOARD", description), mention_author=False)

    @worldboss.command(name="claim")
    async def worldboss_claim(self, ctx):
        game, p = self.services(ctx)
        uid = str(ctx.author.id)
        async with game.lock:
            state = game.data.get("world_boss")
            if not state or not state.get("defeated"):
                await ctx.reply(embed=self.embed(game, "REWARDS NOT READY", "Defeat the active world boss before claiming rewards."), mention_author=False)
                return
            entry = state.get("players", {}).get(uid)
            if not entry or int(entry.get("damage", 0)) <= 0:
                await ctx.reply(embed=self.embed(game, "NO CONTRIBUTION", "You must deal damage during the event to claim a reward."), mention_author=False)
                return
            if uid in state.setdefault("claimed", []):
                await ctx.reply(embed=self.embed(game, "ALREADY CLAIMED", "You have already claimed this event's reward."), mention_author=False)
                return
            ranked = sorted(state["players"].items(), key=lambda row: row[1].get("damage", 0), reverse=True)
            rank = next(i for i, (player_id, _) in enumerate(ranked, 1) if player_id == uid)
            tier = worldboss_reward_tier(entry["damage"], state["max_hp"], rank)
            xp = 5000 + min(50000, int(entry["damage"]) // 100)
            gold = 2500 + min(100000, int(entry["damage"]) // 50)
            gems = 5 + min(20, int(entry["damage"]) // 250000)
            chest = f"{tier}_chest"
            drop = random.choice(state.get("drops", ["rift_crystal"]))
            p["xp"] = int(p.get("xp", 0)) + xp
            p["gold"] = int(p.get("gold", 0)) + gold
            p["gems"] = int(p.get("gems", 0)) + gems
            game.item(p, chest, 1)
            game.item(p, drop, 1)
            levels = apply_level_ups(p)
            state["claimed"].append(uid)
            game.flush()
        await ctx.reply(embed=self.embed(game, "WORLD BOSS REWARD", f"Rank: **#{rank}**\nDamage: {display_number(entry['damage'])}\nRewards: {xp:,} XP ({levels} levels), {gold:,} Gold, {gems} Gems, {chest.replace('_', ' ').title()} ×1 and {drop.replace('_', ' ').title()} ×1."), mention_author=False)

    @worldboss.command(name="close")
    @commands.is_owner()
    async def worldboss_close(self, ctx):
        game, _ = self.services(ctx)
        async with game.lock:
            state = game.data.get("world_boss")
            if not state:
                await ctx.reply(embed=self.embed(game, "NO EVENT", "There is no world boss event to close."), mention_author=False)
                return
            game.data["world_boss"] = None
            game.flush()
        await ctx.reply(embed=self.embed(game, "WORLD BOSS CLOSED", "The event was closed. Any unclaimed rewards from it are no longer available."), mention_author=False)


async def setup(bot):
    await bot.add_cog(Ascension(bot))
