import random
from datetime import datetime, timedelta, timezone

import discord
from core.ui import render_embed
from discord.ext import commands

from core.locking import serialized

from cogs.adventure import (
    CHARACTERS, CLANS, CHARACTER_ATTACK_TYPES, RACES, SKILL_TREE,
    apply_level_ups, display_number, mastery_tier, AttackCategoryView,
)

PETS = {
    "cursed_wolf": {"name": "Cursed Wolf", "attack": 0.08, "defense": 0.03, "rarity": "Rare", "lore": "A loyal hound born from residual cursed energy."},
    "chakra_fox": {"name": "Chakra Fox", "attack": 0.06, "defense": 0.06, "rarity": "Epic", "lore": "A fox that converts chakra into a protective aura."},
    "soul_moth": {"name": "Soul Moth", "attack": 0.05, "defense": 0.12, "rarity": "Epic", "lore": "A quiet spirit that shields its partner."},
    "dragonling": {"name": "Dragonling", "attack": 0.12, "defense": 0.02, "rarity": "Legendary", "lore": "A young dragon with an explosive fighting instinct."},
    "void_sprite": {"name": "Void Sprite", "attack": 999.99, "defense": 999.99, "rarity": "Mythic", "lore": "A fragment of a world that no longer exists."},
}

ROUTES = {
    "cursed_realm": {
        "name": "Cursed Realm Descent", "level": 1, "description": "A three-stage hunt through a nest of cursed spirits.",
        "stages": [
            ("Cursed Scout", 520, (12, 19), "cursed_ash"),
            ("Transfigured Brute", 850, (17, 25), "transfigured_soul"),
            ("Disaster Curse", 1350, (22, 32), "soul_fragment"),
        ],
        "xp": 550, "bonus": "cursed_fingers",
    },
    "shinobi_frontier": {
        "name": "Shinobi Frontier", "level": 10, "description": "A dangerous route guarded by rogue ninja and forbidden techniques.",
        "stages": [
            ("Rogue Jonin", 1100, (19, 28), "chakra_crystal"),
            ("Susanoo Echo", 1650, (25, 36), "uchiha_relic"),
            ("Forbidden Shinobi", 2350, (31, 44), "six_paths_essence"),
        ],
        "xp": 1100, "bonus": "dimensional_eye",
    },
    "grand_line": {
        "name": "Grand Line Gauntlet", "level": 20, "description": "A voyage through a brutal stretch of the New World.",
        "stages": [
            ("New World Captain", 1850, (27, 39), "devil_fruit_shard"),
            ("Tyrant Commander", 2550, (34, 48), "starsteel"),
            ("Emperor's Vanguard", 3400, (42, 58), "dragon_scale"),
        ],
        "xp": 1800, "bonus": "kingly_aura",
    },
    "riftfall": {
        "name": "Riftfall: End of Worlds", "level": 40, "description": "An endgame gauntlet where reality itself fights back.",
        "stages": [
            ("Rift Executioner", 3200, (39, 55), "time_rift_fragment"),
            ("World Breaker", 4400, (48, 66), "ancient_core"),
            ("The Final Calamity", 6200, (58, 82), "spiral_core"),
        ],
        "xp": 3200, "bonus": "mythic_token",
    },
}


def expedition_scale(level):
    return 1.0 + min(50, max(0, int(level) - 1)) * 0.035


def daily_login_reward(streak):
    day = ((max(1, int(streak)) - 1) % 7) + 1
    return {"xp": 150 + day * 50, "points": 1 if day < 7 else 3, "token": day == 7}


class Expeditions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def services(self):
        return self.bot.get_cog("Adventure")

    def embed(self, title, description="", color=None):
        return render_embed(discord.Embed(
            title=title, description=description,
            color=color or discord.Color.from_rgb(35, 45, 64),
        ))

    def profile(self, ctx):
        game = self.services()
        if game is None:
            raise RuntimeError("Adventure system is not loaded")
        p = game.p(ctx.author.id)
        p.setdefault("expedition", None)
        p.setdefault("pets", [])
        p.setdefault("pet_equipped", None)
        p.setdefault("expedition_clears", 0)
        p.setdefault("login_streak", 0)
        p.setdefault("last_login", None)
        return game, p

    def pet_bonus(self, p):
        pet = PETS.get(p.get("pet_equipped"))
        return (pet["attack"], pet["defense"]) if pet else (0.0, 0.0)

    def gear_stats(self, p):
        attack = defense = hp = 0
        try:
            from cogs.endgame import GEAR
            for key in p.get("gear_equipped", {}).values():
                if key in GEAR:
                    item = GEAR[key]
                    attack += item["attack"]
                    defense += item["defense"]
                    hp += item["hp"]
        except ImportError:
            pass
        return attack, defense, hp

    @commands.group(name="expedition", invoke_without_command=True)
    @commands.guild_only()
    async def expedition(self, ctx):
        game, p = self.profile(ctx)
        state = p.get("expedition")
        if state:
            await self.expedition_status(ctx)
            return
        lines = []
        for key, route in ROUTES.items():
            lock = f"Level {route['level']} required" if int(p["level"]) < route["level"] else "Available"
            lines.append(f"**{route['name']}** — {lock}\n`,expedition start {key}`")
        await ctx.reply(embed=self.embed("EXPEDITION BOARD", "\n\n".join(lines) + "\n\nEach route has three stages. Progress and HP are saved between turns."), mention_author=False)

    @expedition.command(name="start")
    @commands.guild_only()
    @serialized
    async def expedition_start(self, ctx, *, route: str):
        game, p = self.profile(ctx)
        key = route.lower().strip().replace(" ", "_")
        if key not in ROUTES:
            await ctx.reply(embed=self.embed("UNKNOWN EXPEDITION", "Use `,expedition` to view the route board."), mention_author=False)
            return
        if p.get("expedition"):
            await ctx.reply(embed=self.embed("RUN ALREADY ACTIVE", "Finish or retreat from your current expedition first."), mention_author=False)
            return
        data = ROUTES[key]
        if int(p["level"]) < data["level"]:
            await ctx.reply(embed=self.embed("ROUTE LOCKED", f"This route requires level {data['level']}."), mention_author=False)
            return
        scale = expedition_scale(p["level"])
        first = data["stages"][0]
        gear_attack, _, gear_hp = self.gear_stats(p)
        max_hp = 250 + min(100, int(p["level"])) * 5 + gear_hp
        p["expedition"] = {
            "route": key, "stage": 0, "enemy_hp": int(first[1] * scale),
            "enemy_max_hp": int(first[1] * scale), "player_hp": max_hp,
            "player_max_hp": max_hp, "started_at": datetime.now(timezone.utc).isoformat(),
        }
        p["attack_mode"] = "expedition"
        game.flush()
        await ctx.reply(embed=self.embed("EXPEDITION STARTED", f"**{data['name']}**\n{data['description']}\n\nFirst target: **{first[0]}**\nEnemy HP: {display_number(p['expedition']['enemy_hp'])}\nYour HP: {max_hp}/{max_hp}\n\nUse `,attack` to take your turn."), mention_author=False)

    @expedition.command(name="status", aliases=["info"])
    @commands.guild_only()
    async def expedition_status(self, ctx):
        game, p = self.profile(ctx)
        state = p.get("expedition")
        if not state:
            await ctx.reply(embed=self.embed("NO ACTIVE EXPEDITION", "Choose a route with `,expedition start <route>`."), mention_author=False)
            return
        route = ROUTES[state["route"]]
        stage = route["stages"][state["stage"]]
        e = self.embed("EXPEDITION STATUS", f"**{route['name']}**\nStage {state['stage'] + 1}/3 — {stage[0]}\nEnemy HP: {display_number(state['enemy_hp'])}/{display_number(state['enemy_max_hp'])}\nYour HP: {display_number(state['player_hp'])}/{display_number(state['player_max_hp'])}")
        await ctx.reply(embed=e, mention_author=False)

    @expedition.command(name="attack")
    @commands.guild_only()
    @commands.cooldown(1, 1.0, commands.BucketType.user)
    async def expedition_attack(self, ctx, *, ability: str = None):
        game, p = self.profile(ctx)
        async with game.lock:
            state = p.get("expedition")
            if not state:
                await ctx.reply(embed=self.embed("NO ACTIVE EXPEDITION", "Start one with `,expedition start <route>`, then use `,attack`."), mention_author=False)
                return
            if ability is None:
                categories = game.attack_skill_options(ctx.author.id)
                if not categories:
                    await ctx.reply(embed=self.embed("NO EQUIPPED SKILLS", "Equip an unlocked skill with ,equipskill <melee|sword|magic> <skill>."), mention_author=False)
                    return
                view = AttackCategoryView(game, ctx, categories, self.expedition_attack, self)
                view.message = await ctx.reply(embed=self.embed("CHOOSE WEAPON TYPE", "Choose a category, then choose one equipped skill. No attack happens until you select it."), view=view, mention_author=False)
                return
            route = ROUTES[state["route"]]
            stage = route["stages"][state["stage"]]
            char = CHARACTERS[p["character"]]
            custom = game.data.get("custom_weapons", {}).get(p.get("weapon"))
            gear_attack, gear_defense, _ = self.gear_stats(p)
            pet_attack, pet_defense = self.pet_bonus(p)
            key = ability.lower().strip().replace(" ", "_")
            options = game.attack_skill_options(ctx.author.id)
            selected_category = next((kind for kind, skills in options.items() if any(skill_key == key for skill_key, _ in skills)), None)
            if selected_category is None:
                await ctx.reply(embed=self.embed("SKILL NOT EQUIPPED", "That skill is not equipped in your combat loadout."), mention_author=False)
                return
            if custom and key == custom["ability_key"]:
                damage = random.randint(*custom["ability_damage"])
                action = custom["ability"]
                override = p.get("weapon_damage_override")
                if override == "googolplex":
                    damage = state["enemy_hp"]
                elif override is not None:
                    damage = int(override)
            elif key == char[5]:
                if key not in p.get("unlocked", []) and not (p["race"] == "vessel" and p["character"] == "sukuna"):
                    await ctx.reply(embed=self.embed("SKILL LOCKED", f"Unlock it with ,unlock {key}."), mention_author=False)
                    return
                damage = random.randint(*char[6])
                action = char[4]
            elif key in p.get("unlocked_skills", []) and key in SKILL_TREE:
                skill = SKILL_TREE[key]
                damage = int(random.randint(*char[3]) * skill["multiplier"])
                action = skill["name"]
            else:
                await ctx.reply(embed=self.embed("SKILL LOCKED", "That ability is not unlocked on your profile."), mention_author=False)
                return
            race = RACES[p["race"]]
            clan = CLANS.get(p.get("clan"))
            attack_type = selected_category
            clan_mult = 1 + (clan.get(attack_type, 0) if clan else 0)
            level_mult = 1 + min(35, max(0, int(p["level"]) - 1)) * 0.01
            mastery_xp = int(p.setdefault("mastery", {}).get(p["character"], 0))
            mastery_mult = 1 + 0.02 * mastery_tier(mastery_xp)
            if p.get("damage_boosts", 0) > 0:
                damage = int(damage * 1.5)
                p["damage_boosts"] -= 1
            if p.get("focus_boosts", 0) > 0:
                damage *= 2
                p["focus_boosts"] -= 1
            dimension = game.data.get("dimensions", {})
            dimension_mult = 1.0
            try:
                from cogs.adventure import DIMENSIONS
                dimension_mult = DIMENSIONS.get(p.get("active_dimension"), DIMENSIONS["earth"])["bonus"]
            except (ImportError, KeyError):
                pass
            damage += gear_attack
            damage = max(1, int(damage * race[1] * clan_mult * level_mult * mastery_mult * dimension_mult * (1 + pet_attack) * (1 + 0.02 * min(25, max(0, int(p.get("ascension", 0)))))))
            dealt = min(state["enemy_hp"], damage)
            state["enemy_hp"] -= dealt
            p.setdefault("mastery", {})[p["character"]] = mastery_xp + dealt
            stage_line = ""
            reward_line = ""
            if state["enemy_hp"] <= 0:
                game.item(p, stage[3], 1 + state["stage"])
                stage_xp = 80 + (state["stage"] + 1) * 45
                p["xp"] += stage_xp
                apply_level_ups(p)
                if state["stage"] == 2:
                    bonus = route["bonus"]
                    game.item(p, bonus, 1)
                    p["expedition_clears"] = p.get("expedition_clears", 0) + 1
                    pet_found = None
                    pity = p["expedition_clears"] % 5 == 0
                    if pity or random.random() < 0.20:
                        available = [key for key in PETS if key not in p.setdefault("pets", [])]
                        if available:
                            pet_found = random.choice(available)
                            p["pets"].append(pet_found)
                    total_xp = route["xp"]
                    p["xp"] += total_xp
                    apply_level_ups(p)
                    reward_line = f"\nRoute clear reward: {display_number(total_xp)} XP, {bonus.replace('_', ' ').title()} x1"
                    if pet_found:
                        reward_line += f"\nNew companion discovered: **{PETS[pet_found]['name']}**. Equip it with `,pet equip {pet_found}`."
                    state_name = route["name"]
                    p["expedition"] = None
                    game.flush()
                    await ctx.reply(embed=self.embed("EXPEDITION CLEARED", f"You defeated **{stage[0]}** with **{display_number(dealt)}** damage.\n\n**{state_name}** is complete.\n{stage[3].replace('_', ' ').title()} x{1 + 2}\n{reward_line}\n\nUse `,pets` to manage companions."), mention_author=False)
                    return
                next_index = state["stage"] + 1
                next_stage = route["stages"][next_index]
                scale = expedition_scale(p["level"])
                state["stage"] = next_index
                state["enemy_hp"] = int(next_stage[1] * scale)
                state["enemy_max_hp"] = state["enemy_hp"]
                stage_line = f"\nStage cleared. Next target: **{next_stage[0]}** ({display_number(state['enemy_hp'])} HP)."
            else:
                incoming = random.randint(*stage[2])
                reduction = min(0.75, max(-0.10, race[2] + pet_defense + gear_defense))
                incoming = max(1, int(incoming * (1 - reduction)))
                state["player_hp"] = max(0, state["player_hp"] - incoming)
                if state["player_hp"] <= 0:
                    p["expedition"] = None
                    game.flush()
                    await ctx.reply(embed=self.embed("EXPEDITION FAILED", f"**{stage[0]}** defeated your party.\nDamage dealt: {display_number(dealt)}\nNo route-clear reward was earned. You can prepare and try again."), mention_author=False)
                    return
                stage_line = f"\n{stage[0]} counterattacked for {incoming}. Your HP: {state['player_hp']}/{state['player_max_hp']}."
            game.flush()
        await ctx.reply(embed=self.embed("EXPEDITION TURN", f"You used **{action}** for **{display_number(dealt)}** damage.\nTarget HP: {display_number(state['enemy_hp'])}/{display_number(state['enemy_max_hp'])}{stage_line}{reward_line}"), mention_author=False)

    @expedition.command(name="retreat")
    @commands.guild_only()
    @serialized
    async def expedition_retreat(self, ctx):
        game, p = self.profile(ctx)
        if not p.get("expedition"):
            await ctx.reply(embed=self.embed("NO ACTIVE EXPEDITION", "There is no run to retreat from."), mention_author=False)
            return
        p["expedition"] = None
        game.flush()
        await ctx.reply(embed=self.embed("RETREATED", "Your expedition was ended. Materials already collected remain in your inventory."), mention_author=False)

    @commands.command(name="pets", aliases=["companions"])
    @commands.guild_only()
    async def pets(self, ctx):
        game, p = self.profile(ctx)
        owned = p.setdefault("pets", [])
        equipped = p.get("pet_equipped")
        if not owned:
            description = "You have no companions yet. Clear expeditions to discover one."
        else:
            rows = []
            for key in owned:
                pet = PETS.get(key)
                if not pet:
                    continue
                marker = " [EQUIPPED]" if key == equipped else ""
                rows.append(f"**{pet['name']}**{marker} — {pet['rarity']}\nAttack +{pet['attack']*100:.0f}% · Defense +{pet['defense']*100:.0f}%\n`,pet equip {key}`")
            description = "\n\n".join(rows)
        await ctx.reply(embed=self.embed("COMPANION ARCHIVE", description), mention_author=False)

    @commands.group(name="pet", invoke_without_command=True)
    @commands.guild_only()
    async def pet(self, ctx):
        await self.pets(ctx)

    @pet.command(name="equip")
    @commands.guild_only()
    @serialized
    async def pet_equip(self, ctx, *, key: str):
        game, p = self.profile(ctx)
        key = key.lower().strip().replace(" ", "_")
        if key not in p.setdefault("pets", []) or key not in PETS:
            await ctx.reply(embed=self.embed("COMPANION NOT OWNED", "Clear expeditions to discover companions."), mention_author=False)
            return
        p["pet_equipped"] = key
        game.flush()
        pet = PETS[key]
        await ctx.reply(embed=self.embed("COMPANION EQUIPPED", f"**{pet['name']}**\nAttack +{pet['attack']*100:.0f}% · Defense +{pet['defense']*100:.0f}%"), mention_author=False)

    @pet.command(name="off")
    @commands.guild_only()
    @serialized
    async def pet_off(self, ctx):
        game, p = self.profile(ctx)
        p["pet_equipped"] = None
        game.flush()
        await ctx.reply(embed=self.embed("COMPANION UNEQUIPPED", "Your companion bonuses are inactive."), mention_author=False)

    @commands.command(name="login", aliases=["dailylogin"])
    @commands.guild_only()
    @serialized
    async def login(self, ctx):
        game, p = self.profile(ctx)
        today = datetime.now(timezone.utc).date()
        last = p.get("last_login")
        if last == today.isoformat():
            await ctx.reply(embed=self.embed("DAILY LOGIN CLAIMED", f"Your current streak is **{p.get('login_streak', 1)} days**. Come back after the UTC day changes."), mention_author=False)
            return
        yesterday = (today - timedelta(days=1)).isoformat()
        streak = int(p.get("login_streak", 0)) + 1 if last == yesterday else 1
        reward = daily_login_reward(streak)
        p["login_streak"] = streak
        p["last_login"] = today.isoformat()
        p["xp"] += reward["xp"]
        p["points"] += reward["points"]
        apply_level_ups(p)
        if reward["token"]:
            game.item(p, "mythic_token", 1)
        game.flush()
        extra = "\n7-day bonus: Mythic Token x1" if reward["token"] else ""
        await ctx.reply(embed=self.embed("DAILY LOGIN REWARD", f"Day **{((streak - 1) % 7) + 1}/7** · Current streak: **{streak} days**\nXP: +{display_number(reward['xp'])}\nSkill points: +{reward['points']}{extra}"), mention_author=False)


async def setup(bot):
    await bot.add_cog(Expeditions(bot))
