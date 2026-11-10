import random
from discord.ext import commands

from cogs.adventure import CHARACTERS, ITEMS, display_number, AttackCategoryView

GEAR = {
    "cursed_mantle": {"name": "Cursed Mantle", "slot": "armor", "level": 8, "attack": 12, "defense": 0.08, "hp": 35, "materials": {"cursed_ash": 12, "transfigured_soul": 4}},
    "six_eyes_lens": {"name": "Six Eyes Lens", "slot": "relic", "level": 15, "attack": 24, "defense": 0.02, "hp": 0, "materials": {"six_eyes": 1, "limitless_core": 5, "blue_orb": 5}},
    "shinobi_vest": {"name": "Shinobi War Vest", "slot": "armor", "level": 18, "attack": 18, "defense": 0.12, "hp": 55, "materials": {"chakra_crystal": 10, "uchiha_relic": 4}},
    "conqueror_medallion": {"name": "Conqueror Medallion", "slot": "relic", "level": 24, "attack": 38, "defense": 0.03, "hp": 20, "materials": {"kingly_aura": 5, "celestial_blood": 3}},
    "dragon_scale_mail": {"name": "Dragon Scale Mail", "slot": "armor", "level": 30, "attack": 35, "defense": 0.18, "hp": 100, "materials": {"dragon_scale": 12, "dragon_ball": 6, "cosmic_core": 5}},
    "soul_reaper_badge": {"name": "Soul Reaper Badge", "slot": "relic", "level": 34, "attack": 55, "defense": 0.05, "hp": 30, "materials": {"ether_core": 10, "soul_fragment": 15, "spirit_silk": 8}},
    "void_core": {"name": "Void Core", "slot": "core", "level": 42, "attack": 85, "defense": 0.08, "hp": 60, "materials": {"void_ore": 18, "ancient_core": 5, "celestial_dust": 12}},
    "reality_anchor": {"name": "Reality Anchor", "slot": "core", "level": 55, "attack": 140, "defense": 0.12, "hp": 100, "materials": {"time_rift_fragment": 20, "dimension_key": 3, "ancient_core": 12}},
}

TOWER_BOSSES = [
    "Cursed Warden", "String Tyrant", "Phantom Shinobi", "Demon Sovereign",
    "Abyssal Reaper", "Celestial Executioner", "Void Colossus",
    "Rift Devourer", "World Breaker", "The Last Calamity",
]

TOWER_LOOT = [
    ("cursed_ash", 2, 4), ("string_core", 2, 4), ("chakra_crystal", 2, 4),
    ("demon_blood", 2, 4), ("ether_core", 2, 4), ("cosmic_core", 2, 4),
    ("void_ore", 2, 4), ("ancient_core", 2, 4), ("time_rift_fragment", 2, 4),
    ("dimension_key", 1, 2),
]


class Endgame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def services(self, ctx):
        cog = self.bot.get_cog("Adventure")
        if cog is None:
            raise RuntimeError("Adventure module is not loaded")
        p = cog.p(ctx.author.id)
        p.setdefault("gear_owned", [])
        p.setdefault("gear_equipped", {"armor": None, "relic": None, "core": None})
        p.setdefault("tower", None)
        p.setdefault("best_tower", 0)
        return cog, p

    def gear_stats(self, p):
        result = {"attack": 0, "defense": 0.0, "hp": 0}
        owned = set(p.get("gear_owned", []))
        equipped = p.get("gear_equipped", {})
        for slot, key in equipped.items():
            if key in owned and key in GEAR:
                item = GEAR[key]
                for stat in result:
                    result[stat] += item[stat]
        return result

    def embed(self, cog, title, description=""):
        return cog.embed(title, description)

    @commands.group(name="forge", invoke_without_command=True)
    async def forge(self, ctx):
        await ctx.invoke(self.forge_list)

    @forge.command(name="list")
    async def forge_list(self, ctx):
        cog, p = self.services(ctx)
        embed = self.embed(cog, "RELIC FORGE", "Permanent equipment. Craft with ,forge craft <key>.")
        stats = self.gear_stats(p)
        for key, item in GEAR.items():
            materials = ", ".join(f"{ITEMS.get(k, k)} x{v}" for k, v in item["materials"].items())
            status = "OWNED" if key in p["gear_owned"] else f"Level {item['level']}"
            embed.add_field(
                name=f"{item['name']} / {key} · {status}",
                value=f"Slot: {item['slot'].title()} | ATK +{item['attack']} | DEF +{int(item['defense'] * 100)}% | HP +{item['hp']}\nMaterials: {materials}",
                inline=False,
            )
        await ctx.reply(embed=embed, mention_author=False)

    @forge.command(name="craft")
    async def forge_craft(self, ctx, *, key: str):
        key = key.lower().strip().replace(" ", "_")
        cog, p = self.services(ctx)
        item = GEAR.get(key)
        if item is None:
            await ctx.reply(embed=self.embed(cog, "BLUEPRINT NOT FOUND", "Use ,forge list."), mention_author=False)
            return
        if key in p["gear_owned"]:
            await ctx.reply(embed=self.embed(cog, "ALREADY CRAFTED", "You already own this relic."), mention_author=False)
            return
        missing = [f"{ITEMS.get(k, k)} x{amount - int(p['inventory'].get(k, 0))}" for k, amount in item["materials"].items() if not cog.has_item(p, k, amount)]
        if int(p["level"]) < item["level"] or missing:
            await ctx.reply(embed=self.embed(cog, "FORGE REQUIREMENTS", f"Required level: {item['level']}\nMissing materials: {', '.join(missing) if missing else 'None'}"), mention_author=False)
            return
        for material, amount in item["materials"].items():
            if not cog.consume_item(p, material, amount):
                await ctx.reply(embed=self.embed(cog, "MATERIAL ERROR", "A material could not be consumed. No gear was crafted."), mention_author=False)
                return
        p["gear_owned"].append(key)
        p["gear_equipped"][item["slot"]] = key
        cog.flush()
        await ctx.reply(embed=self.embed(cog, "RELIC FORGED", f"Crafted and equipped **{item['name']}** in the {item['slot']} slot."), mention_author=False)

    @commands.command(name="gear")
    async def gear(self, ctx):
        cog, p = self.services(ctx)
        stats = self.gear_stats(p)
        lines = [f"**{slot.title()}:** {GEAR[key]['name'] if key in GEAR else 'Empty'}" for slot, key in p["gear_equipped"].items()]
        lines.append(f"\n**Total bonuses**\nATK +{stats['attack']} · DEF {int(stats['defense'] * 100)}% · HP +{stats['hp']}")
        lines.append(f"\nOwned relics: {len(p['gear_owned'])}/{len(GEAR)}")
        from cogs.render_ui import gear_image
        image = gear_image(p, GEAR)
        file = __import__("discord").File(image, filename="equipment.png")
        embed = self.embed(cog, "EQUIPMENT LOADOUT", "\n".join(lines))
        embed.set_image(url="attachment://equipment.png")
        await ctx.reply(embed=embed, file=file, mention_author=False)

    @commands.command(name="equipgear")
    async def equipgear(self, ctx, *, key: str):
        key = key.lower().strip().replace(" ", "_")
        cog, p = self.services(ctx)
        if key in {"off", "none", "clear"}:
            await ctx.reply(embed=self.embed(cog, "UNEQUIP REQUIRES SLOT", "Use ,unequipgear <armor|relic|core>."), mention_author=False)
            return
        if key not in p["gear_owned"] or key not in GEAR:
            await ctx.reply(embed=self.embed(cog, "GEAR LOCKED", "Craft it first with ,forge craft <key>."), mention_author=False)
            return
        slot = GEAR[key]["slot"]
        p["gear_equipped"][slot] = key
        cog.flush()
        await ctx.reply(embed=self.embed(cog, "GEAR EQUIPPED", f"{GEAR[key]['name']} equipped in {slot}."), mention_author=False)

    @commands.command(name="unequipgear")
    async def unequipgear(self, ctx, slot: str):
        cog, p = self.services(ctx)
        slot = slot.lower().strip()
        if slot not in {"armor", "relic", "core"}:
            await ctx.reply(embed=self.embed(cog, "INVALID SLOT", "Choose armor, relic or core."), mention_author=False)
            return
        p["gear_equipped"][slot] = None
        cog.flush()
        await ctx.reply(embed=self.embed(cog, "GEAR UNEQUIPPED", f"{slot.title()} slot is now empty."), mention_author=False)

    def tower_enemy(self, floor):
        base_name = TOWER_BOSSES[(floor - 1) % len(TOWER_BOSSES)]
        name = base_name if floor <= len(TOWER_BOSSES) else f"{base_name} · Ascended Floor {floor}"
        hp = 650 * floor * floor
        return {"name": name, "max_hp": hp, "hp": hp, "damage": (22 + floor * 13, 38 + floor * 18)}

    @commands.group(name="tower", invoke_without_command=True)
    async def tower(self, ctx):
        cog, p = self.services(ctx)
        state = p.get("tower")
        if not state:
            await ctx.reply(embed=self.embed(cog, "RIFT TOWER", f"Endless floors. Scaling bosses. A permanent record.\nBest floor cleared: {p.get('best_tower', 0)}\nStart with ,tower start, then use ,attack."), mention_author=False)
            return
        enemy = state["enemy"]
        await ctx.reply(embed=self.embed(cog, "RIFT TOWER STATUS", f"Floor {state['floor']}\n{enemy['name']}: {enemy['hp']:,}/{enemy['max_hp']:,} HP\nYour HP: {state['hp']}/{state['max_hp']}\nDamage dealt: {state['damage']:,}\nUse ,attack."), mention_author=False)

    @tower.command(name="start")
    async def tower_start(self, ctx):
        cog, p = self.services(ctx)
        if p.get("tower"):
            await ctx.reply(embed=self.embed(cog, "RUN ALREADY ACTIVE", "Use ,tower to check your current floor."), mention_author=False)
            return
        gear = self.gear_stats(p)
        hp = 300 + min(100, int(p["level"])) * 2 + gear["hp"]
        enemy = self.tower_enemy(1)
        p["tower"] = {"floor": 1, "hp": hp, "max_hp": hp, "enemy": enemy, "damage": 0, "started": True}
        p["attack_mode"] = "tower"
        cog.flush()
        await ctx.reply(embed=self.embed(cog, "RIFT TOWER ENTERED", f"Floor 1: **{enemy['name']}**\nEnemy HP: {enemy['hp']:,}\nYour HP: {hp}\nThe run ends if you are defeated. Progress is saved."), mention_author=False)

    @tower.command(name="attack")
    @commands.cooldown(1, 1.0, commands.BucketType.user)
    async def tower_attack(self, ctx, *, ability: str = None):
        cog, p = self.services(ctx)
        state = p.get("tower")
        if not state:
            await ctx.reply(embed=self.embed(cog, "NO ACTIVE RUN", "Start with ,tower start."), mention_author=False)
            return
        if ability is None:
            categories = cog.attack_skill_options(ctx.author.id)
            if not categories:
                await ctx.reply(embed=self.embed(cog, "NO EQUIPPED SKILLS", "Equip an unlocked skill with ,equipskill <melee|sword|magic> <skill>."), mention_author=False)
                return
            await ctx.reply(embed=self.embed(cog, "CHOOSE WEAPON TYPE", "Choose a category, then choose one equipped skill. No attack happens until you select it."), view=AttackCategoryView(cog, ctx, categories, self.tower_attack, self), mention_author=False)
            return
        gear = self.gear_stats(p)
        character = CHARACTERS[p["character"]]
        weapon_key = p.get("weapon")
        custom_weapons = cog.data.get("custom_weapons", {})
        weapon = custom_weapons.get(weapon_key) if weapon_key else None
        override = p.get("weapon_damage_override")

        from cogs.adventure import (
            RACES, CLANS, CHARACTER_ATTACK_TYPES, DIMENSIONS, SKILL_TREE,
            PETS, mastery_tier,
        )
        key = ability.lower().strip().replace(" ", "_")
        options = cog.attack_skill_options(ctx.author.id)
        selected_category = next((kind for kind, skills in options.items() if any(skill_key == key for skill_key, _ in skills)), None)
        if selected_category is None:
            await ctx.reply(embed=self.embed(cog, "SKILL NOT EQUIPPED", "That skill is not equipped in your combat loadout."), mention_author=False)
            return
        if weapon and key == weapon["ability_key"]:
            damage = random.randint(*weapon["ability_damage"])
            override = p.get("weapon_damage_override")
            if override == "googolplex":
                damage = state["enemy"]["hp"]
            elif override is not None:
                damage = int(override)
        elif key == character[5]:
            if key not in p.get("unlocked", []) and not (p["race"] == "vessel" and p["character"] == "sukuna"):
                await ctx.reply(embed=self.embed(cog, "SKILL LOCKED", f"Unlock it with ,unlock {key}."), mention_author=False)
                return
            damage = random.randint(*character[6])
        elif key in p.get("unlocked_skills", []) and key in SKILL_TREE:
            damage = int(random.randint(*character[3]) * SKILL_TREE[key]["multiplier"])
        else:
            await ctx.reply(embed=self.embed(cog, "SKILL LOCKED", "That ability is not unlocked."), mention_author=False)
            return
        race = RACES[p["race"]]
        clan = CLANS.get(p.get("clan"))
        attack_type = selected_category
        clan_mult = 1 + (clan.get(attack_type, 0) if clan else 0)
        level_mult = 1 + min(35, max(0, int(p["level"]) - 1)) * 0.01
        mastery_xp = int(p.setdefault("mastery", {}).get(p["character"], 0))
        mastery_mult = 1 + 0.02 * mastery_tier(mastery_xp)
        pet = PETS.get(p.get("pet_equipped"))
        pet_mult = 1 + (pet["attack"] if pet else 0)
        if p.get("damage_boosts", 0) > 0:
            damage = int(damage * 1.5)
            p["damage_boosts"] -= 1
        if p.get("focus_boosts", 0) > 0:
            damage *= 2
            p["focus_boosts"] -= 1
        dimension_mult = DIMENSIONS.get(p.get("active_dimension"), DIMENSIONS["earth"])["bonus"]
        damage = max(1, int((damage + gear["attack"]) * race[1] * clan_mult * level_mult * mastery_mult * pet_mult * dimension_mult * (1 + 0.02 * min(25, max(0, int(p.get("ascension", 0)))))))
        damage = min(state["enemy"]["hp"], damage)
        state["enemy"]["hp"] = max(0, state["enemy"]["hp"] - damage)
        state["damage"] += damage
        if state["enemy"]["hp"] <= 0:
            floor = state["floor"]
            p["xp"] += floor * 350
            p["points"] += 1 if floor % 2 == 0 else 0
            material, low, high = TOWER_LOOT[(floor - 1) % len(TOWER_LOOT)]
            amount = random.randint(low, high) + floor // 10
            cog.item(p, material, amount)
            from cogs.adventure import apply_level_ups
            levels = apply_level_ups(p)
            p["best_tower"] = max(int(p.get("best_tower", 0)), floor)
            next_floor = floor + 1
            enemy = self.tower_enemy(next_floor)
            state.update({"floor": next_floor, "enemy": enemy})
            cog.flush()
            await ctx.reply(embed=self.embed(cog, f"FLOOR {floor} CLEARED", f"Defeated {TOWER_BOSSES[(floor - 1) % len(TOWER_BOSSES)]}.\nRewards: {floor * 350:,} XP, {amount} {ITEMS.get(material, material)}.\nNext: Floor {next_floor} — {enemy['name']} ({enemy['hp']:,} HP).\nYour HP carries over: {state['hp']}/{state['max_hp']}."), mention_author=False)
            return
        enemy = state["enemy"]
        incoming = random.randint(*enemy["damage"])
        race_reduction = RACES[p["race"]][2]
        pet_reduction = pet["defense"] if pet else 0
        reduction = min(0.75, max(-0.10, self.gear_stats(p)["defense"] + race_reduction + pet_reduction))
        incoming = max(1, int(incoming * (1 - reduction)))
        state["hp"] = max(0, state["hp"] - incoming)
        if state["hp"] <= 0:
            floor = state["floor"]
            p["best_tower"] = max(int(p.get("best_tower", 0)), floor - 1)
            p["tower"] = None
            cog.flush()
            await ctx.reply(embed=self.embed(cog, "TOWER RUN ENDED", f"You reached floor {floor} and cleared {floor - 1} floors.\nDamage dealt: {state['damage']:,}\nYour best record is now floor {p['best_tower']}.\nRewards from completed floors are kept."), mention_author=False)
            return
        cog.flush()
        await ctx.reply(embed=self.embed(cog, "TOWER TURN", f"You dealt {damage:,} damage to {enemy['name']}.\nThe boss retaliated for {incoming} damage.\nYour HP: {state['hp']}/{state['max_hp']}\nEnemy HP: {enemy['hp']:,}/{enemy['max_hp']:,}."), mention_author=False)

    @tower.command(name="retreat")
    async def tower_retreat(self, ctx):
        cog, p = self.services(ctx)
        state = p.get("tower")
        if not state:
            await ctx.reply(embed=self.embed(cog, "NO ACTIVE RUN", "There is no tower run to retreat from."), mention_author=False)
            return
        floor = state["floor"]
        p["best_tower"] = max(int(p.get("best_tower", 0)), floor - 1)
        p["tower"] = None
        cog.flush()
        await ctx.reply(embed=self.embed(cog, "TOWER RETREAT", f"Run ended at floor {floor}. Rewards from cleared floors are kept."), mention_author=False)


async def setup(bot):
    await bot.add_cog(Endgame(bot))
