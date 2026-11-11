import random
from datetime import datetime, timezone
from pathlib import Path

import discord
from core.ui import CUSTOM_EMOJIS, render_embed
from discord.ext import commands

RESTART_FLAG = Path(__file__).resolve().parent.parent / ".restart_requested"


class PollView(discord.ui.View):
    def __init__(self, question: str) -> None:
        super().__init__(timeout=86400)
        self.question = question
        self.votes = {}
        self.message = None
        self.closed = False

    def build_embed(self) -> discord.Embed:
        yes = sum(1 for vote in self.votes.values() if vote)
        no = sum(1 for vote in self.votes.values() if not vote)
        embed = discord.Embed(title="Poll closed" if self.closed else "Community poll", description=self.question, color=discord.Color.blurple())
        embed.add_field(name="Yes", value=str(yes), inline=True)
        embed.add_field(name="No", value=str(no), inline=True)
        embed.add_field(name="Total votes", value=str(len(self.votes)), inline=True)
        return render_embed(embed)

    async def record(self, interaction: discord.Interaction, vote: bool) -> None:
        self.votes[interaction.user.id] = vote
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def on_timeout(self) -> None:
        self.closed = True
        for item in self.children:
            item.disabled = True
        if self.message is not None:
            try:
                await self.message.edit(embed=self.build_embed(), view=self)
            except discord.HTTPException:
                pass

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.success)
    async def yes_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self.record(interaction, True)

    @discord.ui.button(label="No", style=discord.ButtonStyle.danger)
    async def no_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self.record(interaction, False)


COMMAND_DESCRIPTIONS = {
    "help": "Search the command list or open detailed instructions for one command.",
    "ping": "Check the bot's gateway latency and connection status.",
    "about": "View bot statistics, loaded modules and runtime information.",
    "menu": "Open the interactive shortcut panel for the bot's main features.",
    "wallet": "View your current Gold and Gem balances.",
    "inventory": "Browse your owned items, materials and consumables.",
    "profile": "View your character build, level, stats and progression.",
    "daily": "Claim your daily rewards and check your streak.",
    "bosses": "Browse available bosses and inspect their rewards.",
    "boss": "Open the boss command group for challenges, summons and raid status.",
    "boss challenge": "Challenge a boss and create a raid for other players to join.",
    "boss summon": "Spend a boss key to summon a selected boss.",
    "boss status": "Inspect the active raid, boss health and participating players.",
    "join": "Join the active boss raid before the fight begins.",
    "attack": "Take your turn in the active raid using an equipped skill.",
    "skills": "Browse your character's skills, damage and unlock status.",
    "skilltree": "View the universal skill tree and its unlock requirements.",
    "equipskill": "Equip an unlocked skill in a combat category.",
    "unequipskill": "Remove a skill from one of your combat categories.",
    "skillloadout": "Review the skills currently equipped for combat.",
    "character": "Choose which unlocked anime character you want to use.",
    "characters": "Browse the character roster and level requirements.",
    "clans": "Compare clan bonuses and see which clans you can roll.",
    "clan": "Check your current clan or use its subcommands to reroll.",
    "races": "Browse available races and their passive bonuses.",
    "race": "Select an unlocked race for your character.",
    "mastery": "Check your equipped character's mastery tier and progress.",
    "craft": "Craft a weapon or item when you have the required materials.",
    "recipes": "Browse weapon blueprints and the materials each one requires.",
    "chest": "View your chest stock and open chests by tier.",
    "oca": "Open all available chest tiers in one command.",
    "guild": "Manage your guild, membership, donations and guild rankings.",
    "trade": "Create, accept, cancel and review player-to-player trades.",
    "market": "Browse player listings or buy and sell items on the market.",
    "gear": "Inspect your equipped endgame gear and its stat bonuses.",
    "equipgear": "Equip a gear piece you own into its matching slot.",
    "unequipgear": "Remove the gear currently equipped in a slot.",
    "tower": "View and progress through the endgame tower.",
    "forge": "Browse forge options and craft advanced equipment.",
}

def command_description(command):
    """Return useful help text, never a circular 'use help' placeholder."""
    if command.help:
        return command.help.strip()
    if command.short_doc:
        return command.short_doc.strip()
    callback_doc = getattr(command.callback, "__doc__", None)
    if callback_doc and callback_doc.strip():
        return callback_doc.strip()
    qualified = command.qualified_name.lower()
    if qualified in COMMAND_DESCRIPTIONS:
        return COMMAND_DESCRIPTIONS[qualified]
    if command.name.lower() in COMMAND_DESCRIPTIONS:
        return COMMAND_DESCRIPTIONS[command.name.lower()]
    words = command.name.replace("_", " ").replace("-", " ")
    if isinstance(command, commands.Group):
        return f"Open the {words} command group. Use its listed subcommands to perform specific actions."
    return f"Run the {words} command."

class HelpView(discord.ui.View):
    def __init__(self, author_id: int, prefix: str, bot: commands.Bot) -> None:
        super().__init__(timeout=180)
        self.author_id = author_id
        self.prefix = prefix
        self.bot = bot
        self.page = 0
        self.pages = self.build_pages()
        self.message = None
        self.refresh_buttons()

    def build_pages(self) -> list[tuple[str, str]]:
        grouped = {}
        for command in self.bot.walk_commands():
            if command.hidden:
                continue
            category = command.cog.qualified_name if command.cog else "OTHER"
            suffix = f" {command.signature}" if command.signature else ""
            description = command_description(command)
            grouped.setdefault(category.upper(), []).append(f"`{self.prefix}{command.qualified_name}{suffix}`\n{description}")
        pages = []
        for category, entries in sorted(grouped.items()):
            for offset in range(0, len(entries), 10):
                page_entries = entries[offset:offset + 10]
                page_number = offset // 10 + 1
                page_total = (len(entries) + 9) // 10
                title = category if page_total == 1 else f"{category} · {page_number}/{page_total}"
                pages.append((title, "\n\n".join(page_entries)[:4000]))
        return pages or [("COMMANDS", "No public commands are currently loaded.")]

    def build_embed(self) -> discord.Embed:
        title, description = self.pages[self.page]
        embed = discord.Embed(
            title=f"{title}  /  COMMAND INDEX",
            description=description,
            color=discord.Color.from_rgb(35, 45, 64),
        )
        return render_embed(embed)

    def refresh_buttons(self) -> None:
        self.previous_button.disabled = self.page == 0
        self.next_button.disabled = self.page >= len(self.pages) - 1

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("These help controls belong to the person who opened the menu.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.secondary)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.page = max(0, self.page - 1)
        self.refresh_buttons()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.page = min(len(self.pages) - 1, self.page + 1)
        self.refresh_buttons()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True
        if self.message is not None:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass


class General(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    def embed(self, title: str, description: str = "", color: discord.Color = discord.Color.from_rgb(48, 61, 82)) -> discord.Embed:
        result = discord.Embed(
            title=title,
            description=description,
            color=color,
        )
        return render_embed(result)

    @commands.command(name="ping", aliases=["latency"])
    async def ping(self, ctx: commands.Context) -> None:
        ms = round(self.bot.latency * 1000)
        color = discord.Color.green() if ms < 150 else discord.Color.orange() if ms < 300 else discord.Color.red()
        embed = self.embed("Network diagnostics", f"**{ms} ms**\nGateway response time", color)
        embed.add_field(name="Status", value="Operational" if ms < 300 else "High latency", inline=True)
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="about", aliases=["botinfo"])
    async def about(self, ctx: commands.Context) -> None:
        embed = self.embed("Bot information", "A multi-purpose Discord bot for community tools and cooperative RPG features.")
        embed.add_field(name="Servers", value=f"{len(self.bot.guilds):,}", inline=True)
        embed.add_field(name="Users", value=f"{sum(g.member_count or 0 for g in self.bot.guilds):,}", inline=True)
        embed.add_field(name="Latency", value=f"{round(self.bot.latency * 1000)} ms", inline=True)
        embed.add_field(name="Runtime", value=f"discord.py {discord.__version__}", inline=True)
        embed.add_field(name="Modules", value="General · Community · Adventure · Progression · Endgame · Expeditions · Social", inline=False)
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="help", aliases=["commands", "cmds"])
    async def help_command(self, ctx: commands.Context, *, command_name: str = None) -> None:
        if command_name:
            query = command_name.strip().lower()
            all_commands = list(self.bot.walk_commands())
            exact = next((c for c in all_commands if c.qualified_name.lower() == query), None)
            if exact is None:
                exact = next((c for c in all_commands if c.name.lower() == query or query in [alias.lower() for alias in c.aliases]), None)
            if exact is None:
                matches = [c for c in all_commands if query in c.qualified_name.lower() or query in c.name.lower() or any(query in alias.lower() for alias in c.aliases)]
                if matches:
                    lines = []
                    for c in matches[:20]:
                        suffix = f" {c.signature}" if c.signature else ""
                        lines.append(f"`{ctx.clean_prefix}{c.qualified_name}{suffix}` — {command_description(c)}")
                    embed = self.embed(f"Command search · {len(matches)} match(es)", "I couldn't find an exact match. Closest commands:\n\n" + "\n".join(lines), discord.Color.blurple())
                else:
                    embed = self.embed("No matching command", f"No command or alias matches **{command_name}**. Try a shorter keyword, or use `{ctx.clean_prefix}help` to browse.", discord.Color.orange())
                await ctx.reply(embed=embed, mention_author=False)
                return
            suffix = f" {exact.signature}" if exact.signature else ""
            usage = f"`{ctx.clean_prefix}{exact.qualified_name}{suffix}`"
            description = command_description(exact)
            embed = self.embed(f"{CUSTOM_EMOJIS['help']}  COMMAND · {exact.qualified_name}", description)
            embed.add_field(name="EXACT USAGE", value=usage, inline=False)
            if exact.aliases:
                embed.add_field(name="ALIASES", value=", ".join(f"`{alias}`" for alias in exact.aliases), inline=False)
            if isinstance(exact, commands.Group) and exact.commands:
                lines = []
                for child in exact.commands:
                    child_suffix = f" {child.signature}" if child.signature else ""
                    lines.append(f"`{ctx.clean_prefix}{child.qualified_name}{child_suffix}`\n{child.short_doc or 'No description yet.'}")
                embed.add_field(name="SUBCOMMANDS · USE `,help <subcommand>` FOR DETAILS", value="\n\n".join(lines)[:1024], inline=False)
            if exact.parent is not None:
                embed.add_field(name="COMMAND GROUP", value=f"`{ctx.clean_prefix}help {exact.parent.qualified_name}`", inline=False)
            await ctx.reply(embed=embed, mention_author=False)
            return
        view = HelpView(ctx.author.id, ctx.clean_prefix, self.bot)
        view.message = await ctx.reply(embed=view.build_embed(), view=view, mention_author=False)

    @commands.command(name="userinfo", aliases=["whois"])
    async def userinfo(self, ctx: commands.Context, member: discord.Member = None) -> None:
        member = member or ctx.author
        embed = self.embed(f"Member dossier  /  {member}", color=discord.Color.blurple())
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="User ID", value=f"`{member.id}`", inline=False)
        embed.add_field(name="Created", value=discord.utils.format_dt(member.created_at, style="D"), inline=True)
        if isinstance(member, discord.Member):
            embed.add_field(name="Joined", value=discord.utils.format_dt(member.joined_at, style="D") if member.joined_at else "Unknown", inline=True)
            embed.add_field(name="Highest role", value=member.top_role.mention if member.top_role else "None", inline=True)
            embed.add_field(name="Account status", value="Bot account" if member.bot else "User account", inline=True)
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="serverinfo", aliases=["server"])
    @commands.guild_only()
    async def serverinfo(self, ctx: commands.Context) -> None:
        guild = ctx.guild
        embed = self.embed(f"Server overview  /  {guild.name}", color=discord.Color.blurple())
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        embed.add_field(name="Members", value=f"{guild.member_count or 0:,}", inline=True)
        embed.add_field(name="Channels", value=f"{len(guild.channels):,}", inline=True)
        embed.add_field(name="Roles", value=f"{len(guild.roles):,}", inline=True)
        embed.add_field(name="Owner", value=guild.owner.mention if guild.owner else "Unavailable", inline=True)
        embed.add_field(name="Created", value=discord.utils.format_dt(guild.created_at, style="D"), inline=True)
        embed.add_field(name="Boost level", value=f"Level {guild.premium_tier} · {guild.premium_subscription_count} boosts", inline=True)
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="avatar", aliases=["pfp"])
    async def avatar(self, ctx: commands.Context, member: discord.Member = None) -> None:
        member = member or ctx.author
        embed = self.embed(f"Avatar viewer  /  {member}", color=discord.Color.blurple())
        embed.set_image(url=member.display_avatar.url)
        embed.add_field(name="Image link", value=f"[Open original]({member.display_avatar.url})", inline=False)
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="roleinfo", aliases=["role"])
    @commands.guild_only()
    async def roleinfo(self, ctx: commands.Context, *, role: discord.Role) -> None:
        embed = self.embed(f"Role dossier  /  {role.name}", color=role.color if role.color.value else discord.Color.blurple())
        embed.add_field(name="Role ID", value=f"`{role.id}`", inline=False)
        embed.add_field(name="Members", value=f"{len(role.members):,}", inline=True)
        embed.add_field(name="Position", value=str(role.position), inline=True)
        embed.add_field(name="Mentionable", value="Yes" if role.mentionable else "No", inline=True)
        embed.add_field(name="Hoisted", value="Yes" if role.hoist else "No", inline=True)
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="roll", aliases=["dice"])
    async def roll(self, ctx: commands.Context, sides: int = 6) -> None:
        if not 2 <= sides <= 1000000:
            await ctx.reply(embed=self.embed("Invalid input", "Choose a number of sides between 2 and 1,000,000.", discord.Color.orange()), mention_author=False)
            return
        value = random.randint(1, sides)
        await ctx.reply(embed=self.embed("Dice result", f"{ctx.author.mention} rolled **{value}** on a **{sides}**-sided die.", discord.Color.blurple()), mention_author=False)

    @commands.command(name="coinflip", aliases=["flip"])
    async def coinflip(self, ctx: commands.Context) -> None:
        result = random.choice(["Heads", "Tails"])
        await ctx.reply(embed=self.embed("Coin toss", f"The result is **{result}**.", discord.Color.blurple()), mention_author=False)

    @commands.command(name="choose", aliases=["pick"])
    async def choose(self, ctx: commands.Context, *, options: str) -> None:
        choices = [part.strip() for part in options.split("|") if part.strip()]
        if not 2 <= len(choices) <= 20:
            await ctx.reply(embed=self.embed("Invalid options", "Provide between 2 and 20 choices, separated with `|`.", discord.Color.orange()), mention_author=False)
            return
        await ctx.reply(embed=self.embed("Selection", f"Selected: **{random.choice(choices)}**", discord.Color.blurple()), mention_author=False)

    @commands.command(name="8ball")
    async def eight_ball(self, ctx: commands.Context, *, question: str) -> None:
        answers = ["Yes.", "No.", "Probably.", "Unlikely.", "Ask again later.", "The outlook is favourable.", "There is not enough information."]
        await ctx.reply(embed=self.embed("The 8-ball", f"**Question**\n{question}\n\n**Answer**\n{random.choice(answers)}", discord.Color.blurple()), mention_author=False)

    @commands.command(name="poll", aliases=["vote"])
    @commands.guild_only()
    async def poll(self, ctx: commands.Context, *, question: str) -> None:
        if len(question) > 250:
            await ctx.reply(embed=self.embed("Poll too long", "Keep the question under 250 characters.", discord.Color.orange()), mention_author=False)
            return
        view = PollView(question)
        view.message = await ctx.send(embed=view.build_embed(), view=view)

    @commands.command(name="purge", aliases=["clear"])
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True, read_message_history=True)
    async def purge(self, ctx: commands.Context, amount: int) -> None:
        if not 1 <= amount <= 100:
            await ctx.reply(embed=self.embed("Invalid amount", "Choose between 1 and 100 messages.", discord.Color.orange()), mention_author=False)
            return
        deleted = await ctx.channel.purge(limit=amount + 1)
        notice = await ctx.send(embed=self.embed("Channel cleaned", f"Removed **{len(deleted) - 1}** messages."))
        await notice.delete(delay=5)

    @commands.command(name="reload")
    @commands.is_owner()
    async def reload_bot(self, ctx: commands.Context) -> None:
        await ctx.reply(embed=self.embed("Update queued", "The supervisor will pull the latest GitHub version and restart the bot."))
        RESTART_FLAG.touch()
        await self.bot.close()

    @reload_bot.error
    async def reload_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        if isinstance(error, commands.NotOwner):
            await ctx.reply(embed=self.embed("Access denied", "This operation is restricted to the bot owner.", discord.Color.red()), mention_author=False)
        else:
            raise error

    @purge.error
    async def purge_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        if isinstance(error, commands.MissingPermissions):
            message = "You need the Manage Messages permission to use this command."
        elif isinstance(error, commands.BotMissingPermissions):
            message = "I need Manage Messages and Read Message History permissions."
        else:
            raise error
        await ctx.reply(embed=self.embed("Permission required", message, discord.Color.red()), mention_author=False)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(General(bot))
