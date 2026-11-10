import random
from datetime import datetime, timezone
from pathlib import Path

import discord
from discord.ext import commands

RESTART_FLAG = Path(__file__).resolve().parent.parent / ".restart_requested"


class PollView(discord.ui.View):
    def __init__(self, question: str) -> None:
        super().__init__(timeout=86400)
        self.question = question
        self.votes = {}

    def build_embed(self) -> discord.Embed:
        yes = sum(1 for vote in self.votes.values() if vote)
        no = sum(1 for vote in self.votes.values() if not vote)
        embed = discord.Embed(title="Community poll", description=self.question, color=discord.Color.blurple())
        embed.add_field(name="Yes", value=str(yes), inline=True)
        embed.add_field(name="No", value=str(no), inline=True)
        embed.add_field(name="Total votes", value=str(len(self.votes)), inline=True)
        return embed

    async def record(self, interaction: discord.Interaction, vote: bool) -> None:
        self.votes[interaction.user.id] = vote
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.success)
    async def yes_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self.record(interaction, True)

    @discord.ui.button(label="No", style=discord.ButtonStyle.danger)
    async def no_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self.record(interaction, False)


class HelpView(discord.ui.View):
    def __init__(self, author_id: int, prefix: str) -> None:
        super().__init__(timeout=180)
        self.author_id = author_id
        self.prefix = prefix
        self.page = 0
        self.pages = self.build_pages()
        self.message = None
        self.refresh_buttons()

    def build_pages(self) -> list[tuple[str, str]]:
        p = self.prefix
        return [
            ("SYSTEM", f"`{p}menu` / `{p}panel` · interactive quick menu\n`{p}ping` · gateway latency\n`{p}about` · bot information\n`{p}help` · command index"),
            ("COMMUNITY", f"`{p}guild` · guilds, message activity XP, donations, member management and rankings\n`{p}trade` · trade items or Gold; `{p}trade pending` lists active offers\n`{p}market` · browse, list, buy and manage your listings\n`{p}userinfo [member]` · member profile\n`{p}serverinfo` · server overview\n`{p}avatar [member]` · avatar viewer\n`{p}roleinfo <role>` · role details\n`{p}poll <question>` · create a poll\n`{p}purge <amount>` · clear messages (moderators)"),
            ("TOOLS", f"`{p}roll [sides]` · random dice\n`{p}coinflip` · flip a coin\n`{p}choose <a | b | ...>` · random choice\n`{p}8ball <question>` · ask the 8-ball"),
            ("ADVENTURE", f"`{p}bosses` · anime raid register\n`{p}boss challenge <name>` · start a raid\n`{p}boss status` · battlefield status\n`{p}boss leave` · leave the party\n`{p}boss abandon` · close your raid\n`{p}boss summon <key> <count>` · summon a boss swarm (owner)\n`{p}join` · join the active fight\n`{p}attack` · attack your current raid, tower, expedition or joined world boss\n`{p}equipskill <type> <skill>` / `{p}unequipskill <type> <skill>` · manage combat loadout\n`{p}skillloadout` · view equipped skills\n`{p}use <item>` · use consumables\n`{p}weapon list` / `{p}weapon equip <key>` · custom weapons\n`{p}characters` / `{p}character <name>` · character roster and selection\n`{p}skills` / `{p}skilltree` / `{p}unlock <skill>` · combat skills\n`{p}recipes` / `{p}craft <key>` · forge weapons\n`{p}dimension list` / `{p}dimension enter <key>` · travel between anime worlds and view their boss rosters\n`{p}chest` / `{p}chest open <common|rare|diamond|ruby|mythic>` · view and open five chest tiers\n`{p}wallet` / `{p}shop` / `{p}buy <item> [amount]` · manage Gold and Gems\n`{p}mastery` · character progression\n`{p}forge list` / `{p}forge craft <key>` · craft relic equipment\n`{p}gear` / `{p}equipgear <key>` / `{p}unequipgear <slot>` · manage equipment\n`{p}tower` / `{p}tower start` / `{p}tower retreat` · solo endgame (attack with `{p}attack`)\n`{p}races` / `{p}race <name>` · race passives and selection\n`{p}clans` / `{p}clan roll` / `{p}clan set <key>` · clan bonuses and owner selection\n`{p}bosskey use <jjk|jojo|naruto>` · open anime boss keys\n`{p}craft item <key>` / `{p}craft i <key>` · craft keys and rerolls\n`{p}inventory` · collected items\n`{p}eat <item>` · awaken bloodlines\n`{p}profile` / `{p}stats [member]` · RPG player profile\n`{p}leaderboard` · top adventurers\n`{p}expedition` / `{p}expedition start <route>` / `{p}expedition retreat` · three-stage solo runs (attack with `{p}attack`)\n`{p}pets` / `{p}pet equip <key>` / `{p}pet off` · companion collection and bonuses\n`{p}login` · daily streak rewards\n`{p}ascension` / `{p}ascend` · permanent endgame progression\n`{p}worldboss` / `{p}worldboss join` / `{p}worldboss claim` · global cooperative boss event (attack with `{p}attack`)\n`{p}worldboss leaderboard` · event damage rankings"),
            ("PROGRESSION & OWNER", f"`{p}daily` / `{p}weekly` · contracts\n`{p}quests` · contract board\n`{p}claim <daily|weekly>` · collect rewards\n`{p}achievements` · achievement archive\n`{p}titles` / `{p}title <key>` · title collection\n\n**OWNER ONLY**\n`{p}reload` · update and restart\n`{p}giveitem <member> <item> [amount]` · grant unlimited loot\n`{p}addclanrolls <member> <amount>` · grant clan rerolls\n`{p}addxp <member> <amount>` · grant XP\n`{p}setlevel <member> <level>` · set level\n`{p}addpoints <member> <amount>` · grant skill points\n`{p}setcharacter <member> <character>` · set character\n`{p}setrace <member> <race>` · set race\n`{p}resetprofile <member>` · reset profile\n`{p}gamedb` · database status\n`{p}createweapon` · custom weapon builder\n`{p}setdamage <amount|googolplex|off>` · damage override"),
        ]

    def build_embed(self) -> discord.Embed:
        title, description = self.pages[self.page]
        embed = discord.Embed(
            title=f"{title}  /  COMMAND INDEX",
            description=description,
            color=discord.Color.from_rgb(35, 45, 64),
        )
        return embed

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
        return result

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
            command = self.bot.get_command(command_name.strip())
            if command is None:
                await ctx.reply(embed=self.embed("Command not found", f"No command named `{command_name}` exists. Use `{ctx.clean_prefix}help` to browse the command index.", discord.Color.orange()), mention_author=False)
                return
            usage = f"`{ctx.clean_prefix}{command.qualified_name} {command.signature}`".strip()
            description = command.help or command.short_doc or "No additional description is available."
            embed = self.embed(f"Command help / {command.qualified_name}", description)
            embed.add_field(name="Usage", value=usage, inline=False)
            if command.aliases:
                embed.add_field(name="Aliases", value=", ".join(f"`{alias}`" for alias in command.aliases), inline=False)
            if isinstance(command, commands.Group) and command.commands:
                lines = [f"`{ctx.clean_prefix}{child.qualified_name} {child.signature}`".strip() for child in command.commands]
                embed.add_field(name="Subcommands", value="\n".join(lines)[:1024], inline=False)
            await ctx.reply(embed=embed, mention_author=False)
            return
        view = HelpView(ctx.author.id, ctx.clean_prefix)
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
        await ctx.send(embed=view.build_embed(), view=view)

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
