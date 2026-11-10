"""Server-scoped guilds, direct trades and a player market."""
import asyncio
import time
import discord
from discord.ext import commands
from core.social import award_guild_xp, ensure_social_data, guild_member_limit, next_id, transfer_gold, transfer_item, valid_stack


class TradeOfferView(discord.ui.View):
    def __init__(self, cog, trade_id, server_id, sender_id, recipient_id):
        super().__init__(timeout=86400)
        self.cog = cog
        self.trade_id = trade_id
        self.server_id = server_id
        self.sender_id = sender_id
        self.recipient_id = recipient_id
        self.message = None

    async def finish(self, interaction, title, description):
        for child in self.children:
            child.disabled = True
        embed = self.cog.embed(title, description)
        await interaction.response.edit_message(embed=embed, view=self)

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message is not None:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success)
    async def accept(self, interaction, button):
        if interaction.user.id != self.recipient_id or interaction.guild_id != self.server_id:
            return await interaction.response.send_message("Only the intended recipient can accept this offer in its original server.", ephemeral=True)
        cog = self.cog.game()
        async with self.cog.lock:
            offer = cog.data["trades"].get(self.trade_id)
            if not offer or offer.get("to") != str(self.recipient_id) or int(offer.get("expires", 0)) < int(time.time()):
                for child in self.children:
                    child.disabled = True
                return await interaction.response.edit_message(embed=self.cog.embed("Trade unavailable", "This offer is missing or expired."), view=self)
            try:
                if offer["item"] == "gold":
                    transfer_gold(cog.p(int(offer["from"])), cog.p(self.recipient_id), int(offer["amount"]))
                else:
                    transfer_item(cog.p(int(offer["from"])), cog.p(self.recipient_id), offer["item"], int(offer["amount"]))
            except ValueError as exc:
                del cog.data["trades"][self.trade_id]
                cog.flush()
                for child in self.children:
                    child.disabled = True
                return await interaction.response.edit_message(embed=self.cog.embed("Trade cancelled", f"{exc}. The offer could not be completed."), view=self)
            del cog.data["trades"][self.trade_id]
            cog.flush()
        await self.finish(interaction, "Trade completed", f"Received {offer['amount']:,} × {offer['item'].replace('_', ' ').title()}.")

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.secondary)
    async def decline(self, interaction, button):
        if interaction.user.id != self.recipient_id or interaction.guild_id != self.server_id:
            return await interaction.response.send_message("Only the intended recipient can decline this offer.", ephemeral=True)
        cog = self.cog.game()
        async with self.cog.lock:
            cog.data["trades"].pop(self.trade_id, None)
            cog.flush()
        await self.finish(interaction, "Trade declined", "The offer was declined.")

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction, button):
        if interaction.user.id != self.sender_id or interaction.guild_id != self.server_id:
            return await interaction.response.send_message("Only the sender can cancel this offer.", ephemeral=True)
        cog = self.cog.game()
        async with self.cog.lock:
            cog.data["trades"].pop(self.trade_id, None)
            cog.flush()
        await self.finish(interaction, "Trade cancelled", "The offer was cancelled by its sender.")


class MarketBrowseView(discord.ui.View):
    def __init__(self, cog, server_id, buyer_id, listings):
        super().__init__(timeout=180)
        self.cog = cog
        self.server_id = server_id
        self.buyer_id = buyer_id
        options = []
        for listing in listings[:25]:
            item = listing["item"].replace("_", " ").title()
            label = f"{item} ×{listing['amount']:,}"[:100]
            description = f"{int(listing['price']):,} Gold · Seller {listing['seller']}"[:100]
            options.append(discord.SelectOption(label=label, value=listing["id"], description=description))
        self.select = discord.ui.Select(
            placeholder="Choose a listing to purchase",
            min_values=1,
            max_values=1,
            options=options,
        )
        self.select.callback = self.purchase
        self.add_item(self.select)

    async def interaction_check(self, interaction):
        if interaction.user.id != self.buyer_id or interaction.guild_id != self.server_id:
            await interaction.response.send_message("This market view belongs to the player who opened it in this server.", ephemeral=True)
            return False
        return True

    async def purchase(self, interaction):
        listing_id = self.select.values[0]
        game = self.cog.game()
        async with self.cog.lock:
            listing = game.data["market"].get(listing_id)
            if not listing or listing.get("server_id") != self.server_id:
                return await interaction.response.send_message("That listing is no longer available. Refresh the market.", ephemeral=True)
            buyer = game.p(self.buyer_id)
            seller = game.p(int(listing["seller"]))
            price = int(listing["price"])
            amount = int(listing["amount"])
            item = listing["item"]
            if int(buyer.get("gold", 0)) < price:
                return await interaction.response.send_message("You don't have enough Gold for that listing.", ephemeral=True)
            if int(seller.get("gold", 0)) + price > 10**18:
                return await interaction.response.send_message("The seller's Gold balance is at its limit. The listing cannot be purchased right now.", ephemeral=True)
            if int(buyer["inventory"].get(item, 0)) + amount > 10**18:
                return await interaction.response.send_message("Your item stack would exceed its limit.", ephemeral=True)
            transfer_gold(buyer, seller, price)
            buyer["inventory"][item] = int(buyer["inventory"].get(item, 0)) + amount
            del game.data["market"][listing_id]
            game.flush()
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(
            embed=self.cog.embed("Purchase complete", f"Bought {amount:,} × {item.replace('_', ' ').title()} for {price:,} Gold."),
            view=self,
        )

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True


class Social(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        game = bot.get_cog("Adventure")
        self.lock = game.lock if game is not None else asyncio.Lock()
        self.activity_cooldowns = {}

    def game(self):
        cog = self.bot.get_cog("Adventure")
        if cog is None:
            raise RuntimeError("Adventure system is unavailable")
        ensure_social_data(cog.data)
        return cog

    def embed(self, title, description=""):
        return discord.Embed(title=title, description=description, color=discord.Color.from_rgb(48, 61, 82))

    def find_guild(self, data, server_id, user_id):
        for key, guild in data["guilds"].items():
            if guild.get("server_id") == server_id and str(user_id) in guild.get("members", []):
                return key, guild
        return None, None

    @commands.guild_only()
    @commands.group(name="guild", invoke_without_command=True)
    async def guild(self, ctx):
        p = ctx.clean_prefix
        await ctx.send(embed=self.embed("Guild commands", f"{p}guild create <name> (10,000 Gold)\n{p}guild join <name>\n{p}guild leave\n{p}guild info\n{p}guild members\n{p}guild kick @member\n{p}guild top\n{p}guild donate <gold>"))

    @guild.command(name="create")
    async def guild_create(self, ctx, *, name: str):
        name = " ".join(name.split())[:32]
        if len(name) < 3:
            return await ctx.reply("Guild names must be 3–32 characters.", mention_author=False)
        cog = self.game()
        data = cog.data
        async with self.lock:
            if self.find_guild(data, ctx.guild.id, ctx.author.id)[1]:
                return await ctx.reply("You're already in a guild.", mention_author=False)
            key = name.lower().replace(" ", "_")
            if any(g.get("server_id") == ctx.guild.id and g.get("key") == key for g in data["guilds"].values()):
                return await ctx.reply("That guild name is already taken in this server.", mention_author=False)
            profile = cog.p(ctx.author.id)
            if int(profile.get("gold", 0)) < 10000:
                return await ctx.reply("Creating a guild costs 10,000 Gold.", mention_author=False)
            profile["gold"] -= 10000
            gid = next_id(data, "G")
            data["guilds"][gid] = {"key": key, "name": name, "server_id": ctx.guild.id, "leader": str(ctx.author.id), "members": [str(ctx.author.id)], "level": 1, "xp": 0, "created": int(time.time())}
            cog.flush()
        await ctx.reply(embed=self.embed("Guild created", f"{name} is now registered. You're the leader."), mention_author=False)

    @guild.command(name="join")
    async def guild_join(self, ctx, *, name: str):
        cog = self.game()
        data = cog.data
        async with self.lock:
            if self.find_guild(data, ctx.guild.id, ctx.author.id)[1]:
                return await ctx.reply("Leave your current guild first.", mention_author=False)
            found = next(((k, g) for k, g in data["guilds"].items() if g.get("server_id") == ctx.guild.id and g.get("key") == name.lower().replace(" ", "_")), None)
            if not found:
                return await ctx.reply("No guild with that name exists in this server.", mention_author=False)
            _, guild = found
            limit = guild_member_limit(guild)
            if len(guild["members"]) >= limit:
                return await ctx.reply(f"That guild is full ({limit} members). Level up the guild to unlock more slots.", mention_author=False)
            guild["members"].append(str(ctx.author.id))
            cog.flush()
        await ctx.reply(embed=self.embed("Guild joined", f"You joined {guild['name']}."), mention_author=False)

    @guild.command(name="leave")
    async def guild_leave(self, ctx):
        cog = self.game()
        data = cog.data
        async with self.lock:
            gid, guild = self.find_guild(data, ctx.guild.id, ctx.author.id)
            if not guild:
                return await ctx.reply("You're not in a guild.", mention_author=False)
            if guild["leader"] == str(ctx.author.id) and len(guild["members"]) > 1:
                return await ctx.reply("Transfer leadership before leaving.", mention_author=False)
            guild["members"].remove(str(ctx.author.id))
            if not guild["members"]:
                del data["guilds"][gid]
            cog.flush()
        await ctx.reply("You left your guild.", mention_author=False)

    @guild.command(name="transfer")
    async def guild_transfer(self, ctx, member: discord.Member):
        cog = self.game()
        async with self.lock:
            _, guild = self.find_guild(cog.data, ctx.guild.id, ctx.author.id)
            if not guild or guild["leader"] != str(ctx.author.id):
                return await ctx.reply("Only the guild leader can transfer leadership.", mention_author=False)
            if str(member.id) not in guild["members"]:
                return await ctx.reply("That member isn't in your guild.", mention_author=False)
            guild["leader"] = str(member.id)
            cog.flush()
        await ctx.reply(f"Leadership transferred to {member.mention}.", mention_author=False)

    @guild.command(name="donate")
    async def guild_donate(self, ctx, amount: int):
        if amount < 100 or amount > 10**18:
            return await ctx.reply("Donate between 100 and 10^18 Gold. Every 100 Gold adds 1 Guild XP.", mention_author=False)
        cog = self.game()
        async with self.lock:
            _, guild = self.find_guild(cog.data, ctx.guild.id, ctx.author.id)
            if not guild:
                return await ctx.reply("Join a guild before donating.", mention_author=False)
            profile = cog.p(ctx.author.id)
            if int(profile.get("gold", 0)) < amount:
                return await ctx.reply("Insufficient Gold.", mention_author=False)
            xp = amount // 100
            profile["gold"] -= amount
            old_level = int(guild.get("level", 1))
            award_guild_xp(cog.data, ctx.guild.id, ctx.author.id, xp)
            new_level = int(guild.get("level", 1))
            cog.flush()
        note = f" The guild reached level {new_level} and unlocked more member slots." if new_level > old_level else ""
        await ctx.reply(embed=self.embed("Guild donation", f"Donated {amount:,} Gold for {xp:,} Guild XP.{note}"), mention_author=False)

    @guild.command(name="info")
    async def guild_info(self, ctx):
        cog = self.game()
        _, guild = self.find_guild(cog.data, ctx.guild.id, ctx.author.id)
        if not guild:
            return await ctx.reply("You're not in a guild.", mention_author=False)
        leader = ctx.guild.get_member(int(guild["leader"]))
        progress = "MAX LEVEL" if int(guild["level"]) >= 20 else f"Guild XP: {int(guild['xp']):,}/{int(guild['level']) * 500:,}"
        await ctx.reply(embed=self.embed(guild["name"], f"Leader: {leader.mention if leader else 'Unknown'}\nMembers: {len(guild['members'])}/{guild_member_limit(guild)}\nLevel: {guild['level']}/20\n{progress}\nLeveling unlocks more member slots."), mention_author=False)

    @guild.command(name="kick")
    async def guild_kick(self, ctx, member: discord.Member):
        cog = self.game()
        async with self.lock:
            _, guild = self.find_guild(cog.data, ctx.guild.id, ctx.author.id)
            if not guild or guild["leader"] != str(ctx.author.id):
                return await ctx.reply("Only the guild leader can remove members.", mention_author=False)
            if member.id == ctx.author.id or str(member.id) not in guild["members"]:
                return await ctx.reply("Choose another member of your guild.", mention_author=False)
            guild["members"].remove(str(member.id))
            cog.flush()
        await ctx.reply(embed=self.embed("Guild member removed", f"{member.mention} was removed from {guild['name']}."), mention_author=False)

    @guild.command(name="top")
    async def guild_top(self, ctx):
        cog = self.game()
        guilds = [g for g in cog.data["guilds"].values() if g.get("server_id") == ctx.guild.id]
        guilds.sort(key=lambda g: (int(g.get("level", 1)), int(g.get("xp", 0)), len(g.get("members", []))), reverse=True)
        if not guilds:
            return await ctx.reply("There are no guilds in this server yet.", mention_author=False)
        lines = [f"**{i}. {g['name']}** · Level {g['level']} · {len(g['members'])}/{guild_member_limit(g)} members" for i, g in enumerate(guilds[:10], 1)]
        await ctx.reply(embed=self.embed("Guild rankings", "\n".join(lines)), mention_author=False)

    @guild.command(name="members")
    async def guild_members(self, ctx):
        cog = self.game()
        _, guild = self.find_guild(cog.data, ctx.guild.id, ctx.author.id)
        if not guild:
            return await ctx.reply("You're not in a guild.", mention_author=False)
        lines = []
        for uid in guild["members"]:
            member = ctx.guild.get_member(int(uid))
            lines.append(("★ " if uid == guild["leader"] else "") + (member.mention if member else f"<@{uid}>"))
        await ctx.reply(embed=self.embed(f"{guild['name']} members", "\n".join(lines)), mention_author=False)

    @commands.guild_only()
    @commands.group(name="trade", invoke_without_command=True)
    async def trade(self, ctx):
        p = ctx.clean_prefix
        await ctx.send(embed=self.embed("Trade commands", f"{p}trade offer @member <item> <amount>\n{p}trade accept <id>\n{p}trade cancel <id>\n{p}trade pending\nTrade regular items or Gold."))

    @trade.command(name="pending")
    async def trade_pending(self, ctx):
        cog = self.game()
        now = int(time.time())
        offers = [
            offer for offer in cog.data["trades"].values()
            if offer.get("server_id") == ctx.guild.id
            and str(ctx.author.id) in {offer.get("from"), offer.get("to")}
            and int(offer.get("expires", 0)) >= now
        ]
        if not offers:
            return await ctx.reply("You have no active trade offers in this server.", mention_author=False)
        offers.sort(key=lambda offer: int(offer.get("expires", 0)))
        lines = []
        for offer in offers[:20]:
            direction = "Incoming" if offer["to"] == str(ctx.author.id) else "Outgoing"
            item = "Gold" if offer["item"] == "gold" else offer["item"].replace("_", " ").title()
            lines.append(f"`{offer['id']}` · {direction} · {offer['amount']:,} × {item} · <@{offer['from']}> → <@{offer['to']}>")
        await ctx.reply(embed=self.embed("Active trade offers", "\n".join(lines)), mention_author=False)

    @trade.command(name="offer")
    async def trade_offer(self, ctx, member: discord.Member, item: str, amount: int):
        if member.bot or member.id == ctx.author.id:
            return await ctx.reply("Choose another player.", mention_author=False)
        cog = self.game()
        data = cog.data
        item = item.lower().replace(" ", "_")
        async with self.lock:
            profile = cog.p(ctx.author.id)
            if item == "gold":
                if amount < 1 or amount > 10**18 or int(profile.get("gold", 0)) < amount:
                    return await ctx.reply("You do not have that much transferable Gold.", mention_author=False)
            elif not valid_stack(profile, item, amount):
                return await ctx.reply("You do not have that many transferable items.", mention_author=False)
            tid = next_id(data, "T")
            data["trades"][tid] = {"from": str(ctx.author.id), "to": str(member.id), "server_id": ctx.guild.id, "item": item, "amount": amount, "expires": int(time.time()) + 86400}
            cog.flush()
        embed = self.embed(f"Trade offer {tid}", f"{ctx.author.mention} offers {amount:,} × {item.replace('_', ' ').title()} to {member.mention}.\nThe recipient can accept or decline below. This offer expires in 24 hours.")
        view = TradeOfferView(self, tid, ctx.guild.id, ctx.author.id, member.id)
        view.message = await ctx.reply(embed=embed, view=view, mention_author=False)

    @trade.command(name="accept")
    async def trade_accept(self, ctx, trade_id: str):
        cog = self.game()
        data = cog.data
        key = trade_id.upper()
        async with self.lock:
            offer = data["trades"].get(key)
            if not offer or offer["to"] != str(ctx.author.id) or offer["server_id"] != ctx.guild.id or offer["expires"] < int(time.time()):
                return await ctx.reply("That offer is missing, expired or not addressed to you.", mention_author=False)
            try:
                if offer["item"] == "gold":
                    transfer_gold(cog.p(int(offer["from"])), cog.p(ctx.author.id), int(offer["amount"]))
                else:
                    transfer_item(cog.p(int(offer["from"])), cog.p(ctx.author.id), offer["item"], int(offer["amount"]))
            except ValueError as exc:
                del data["trades"][key]
                cog.flush()
                return await ctx.reply(f"{exc}. The offer was cancelled.", mention_author=False)
            del data["trades"][key]
            cog.flush()
        await ctx.reply(embed=self.embed("Trade completed", f"Received {offer['amount']:,} × {offer['item'].replace('_', ' ').title()}."), mention_author=False)

    @trade.command(name="cancel")
    async def trade_cancel(self, ctx, trade_id: str):
        cog = self.game()
        data = cog.data
        key = trade_id.upper()
        async with self.lock:
            offer = data["trades"].get(key)
            if not offer or offer["from"] != str(ctx.author.id) or offer["server_id"] != ctx.guild.id:
                return await ctx.reply("You don't own that active offer.", mention_author=False)
            del data["trades"][key]
            cog.flush()
        await ctx.reply("Trade offer cancelled.", mention_author=False)

    @commands.guild_only()
    @commands.group(name="market", invoke_without_command=True)
    async def market(self, ctx):
        p = ctx.clean_prefix
        await ctx.send(embed=self.embed("Player market", f"{p}market browse\n{p}market my\n{p}market list <item> <amount> <price>\n{p}market buy <id>\n{p}market cancel <id>"))

    @market.command(name="browse")
    async def market_browse(self, ctx):
        cog = self.game()
        listings = [x for x in cog.data["market"].values() if x["server_id"] == ctx.guild.id and x["seller"] != str(ctx.author.id)]
        listings.sort(key=lambda x: (int(x["price"]), int(x["created"])))
        if not listings:
            return await ctx.reply("No listings are available.", mention_author=False)
        shown = listings[:25]
        body = "\n".join(f"`{x['id']}` · {x['amount']:,} × {x['item'].replace('_', ' ').title()} · {x['price']:,} Gold · <@{x['seller']}>" for x in shown)
        view = MarketBrowseView(self, ctx.guild.id, ctx.author.id, shown)
        await ctx.reply(embed=self.embed("Player market", body + "\n\nSelect a listing below to buy it."), view=view, mention_author=False)

    @market.command(name="list")
    async def market_list(self, ctx, item: str, amount: int, price: int):
        if not 1 <= amount <= 10**18 or not 1 <= price <= 10**18:
            return await ctx.reply("Amount and price must be between 1 and 10^18.", mention_author=False)
        cog = self.game()
        data = cog.data
        item = item.lower().replace(" ", "_")
        async with self.lock:
            profile = cog.p(ctx.author.id)
            if sum(1 for x in data["market"].values() if x["seller"] == str(ctx.author.id)) >= 10:
                return await ctx.reply("You can have at most 10 active listings.", mention_author=False)
            if not valid_stack(profile, item, amount):
                return await ctx.reply("You don't have that many transferable items.", mention_author=False)
            profile["inventory"][item] -= amount
            if not profile["inventory"][item]:
                del profile["inventory"][item]
            lid = next_id(data, "M")
            data["market"][lid] = {"id": lid, "seller": str(ctx.author.id), "server_id": ctx.guild.id, "item": item, "amount": amount, "price": price, "created": int(time.time())}
            cog.flush()
        await ctx.reply(embed=self.embed("Listing created", f"{lid}: {amount:,} × {item.replace('_', ' ').title()} for {price:,} Gold. Your items are held until sale or cancellation."), mention_author=False)

    @market.command(name="my")
    async def market_my(self, ctx):
        cog = self.game()
        listings = [x for x in cog.data["market"].values() if x["server_id"] == ctx.guild.id and x["seller"] == str(ctx.author.id)]
        listings.sort(key=lambda x: x["created"])
        if not listings:
            return await ctx.reply("You have no active listings in this server.", mention_author=False)
        lines = [f"`{x['id']}` · {x['amount']:,} × {x['item'].replace('_', ' ').title()} · {x['price']:,} Gold" for x in listings]
        await ctx.reply(embed=self.embed("Your market listings", "\n".join(lines)), mention_author=False)

    @market.command(name="buy")
    async def market_buy(self, ctx, listing_id: str):
        cog = self.game()
        data = cog.data
        key = listing_id.upper()
        async with self.lock:
            listing = data["market"].get(key)
            if not listing or listing["server_id"] != ctx.guild.id:
                return await ctx.reply("That listing is unavailable.", mention_author=False)
            if listing["seller"] == str(ctx.author.id):
                return await ctx.reply("You can't buy your own listing.", mention_author=False)
            buyer = cog.p(ctx.author.id)
            seller = cog.p(int(listing["seller"]))
            if int(buyer.get("gold", 0)) < listing["price"]:
                return await ctx.reply("You don't have enough Gold.", mention_author=False)
            if int(seller.get("gold", 0)) + listing["price"] > 10**18:
                return await ctx.reply("Seller's Gold balance is at its limit.", mention_author=False)
            if int(buyer["inventory"].get(listing["item"], 0)) + int(listing["amount"]) > 10**18:
                return await ctx.reply("Your item stack would exceed its limit.", mention_author=False)
            try:
                transfer_gold(buyer, seller, int(listing["price"]))
                buyer["inventory"][listing["item"]] = int(buyer["inventory"].get(listing["item"], 0)) + int(listing["amount"])
            except ValueError as exc:
                return await ctx.reply(str(exc), mention_author=False)
            del data["market"][key]
            cog.flush()
        await ctx.reply(embed=self.embed("Purchase complete", f"Bought {listing['amount']:,} × {listing['item'].replace('_', ' ').title()} for {listing['price']:,} Gold."), mention_author=False)

    @market.command(name="cancel")
    async def market_cancel(self, ctx, listing_id: str):
        cog = self.game()
        data = cog.data
        key = listing_id.upper()
        async with self.lock:
            listing = data["market"].get(key)
            if not listing or listing["seller"] != str(ctx.author.id) or listing["server_id"] != ctx.guild.id:
                return await ctx.reply("You don't own that listing.", mention_author=False)
            profile = cog.p(ctx.author.id)
            returned_total = int(profile["inventory"].get(listing["item"], 0)) + int(listing["amount"])
            if returned_total > 10**18:
                return await ctx.reply("Your inventory stack is at its limit. Free some space before cancelling this listing.", mention_author=False)
            profile["inventory"][listing["item"]] = returned_total
            del data["market"][key]
            cog.flush()
        await ctx.reply("Listing cancelled and items returned.", mention_author=False)

    @commands.Cog.listener()
    async def on_guild_activity(self, server_id, user_id, amount):
        cog = self.bot.get_cog("Adventure")
        if cog is None:
            return
        async with self.lock:
            ensure_social_data(cog.data)
            result = award_guild_xp(cog.data, int(server_id), int(user_id), int(amount))
            if result is not None:
                cog.flush()

    @commands.Cog.listener()
    async def on_message(self, message):
        # Guild activity progression is deliberately slow and rate-limited:
        # commands, bots, DMs and one-word spam do not grant guild XP.
        if message.guild is None or message.author.bot:
            return
        content = (message.content or "").strip()
        if len(content) < 8 or content.startswith((",", "!", ".", "?")):
            return
        key = (message.guild.id, message.author.id)
        now = time.monotonic()
        if now - self.activity_cooldowns.get(key, 0.0) < 60:
            return
        self.activity_cooldowns[key] = now
        # Bound the cache so a busy server cannot grow it indefinitely.
        if len(self.activity_cooldowns) > 10000:
            cutoff = now - 3600
            self.activity_cooldowns = {
                user: stamp for user, stamp in self.activity_cooldowns.items()
                if stamp >= cutoff
            }
        cog = self.bot.get_cog("Adventure")
        if cog is None:
            return
        async with self.lock:
            ensure_social_data(cog.data)
            result = award_guild_xp(cog.data, message.guild.id, message.author.id, 5)
            if result is not None:
                cog.flush()

    @commands.Cog.listener()
    async def on_ready(self):
        cog = self.bot.get_cog("Adventure")
        if cog:
            async with self.lock:
                ensure_social_data(cog.data)
                now = int(time.time())
                expired = [key for key, offer in cog.data["trades"].items() if int(offer.get("expires", 0)) < now]
                for key in expired:
                    del cog.data["trades"][key]
                if expired:
                    cog.flush()


async def setup(bot):
    await bot.add_cog(Social(bot))
