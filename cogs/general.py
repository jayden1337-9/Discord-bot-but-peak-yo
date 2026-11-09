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
        embed.set_footer(text="PEAK  /  POLLS")
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


class General(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    def embed(self, title: str, description: str = "", color: discord.Color = discord.Color.from_rgb(48, 61, 82)) -> discord.Embed:
        result = discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=datetime.now(timezone.utc),
        )
        result.set_footer(text="PEAK  /  SYSTEM")
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
        embed = self.embed("Peak", "A multi-purpose Discord system built for communities, tools and cooperative adventures.")
        embed.add_field(name="Servers", value=f"{len(self.bot.guilds):,}", inline=True)
        embed.add_field(name="Users", value=f"{sum(g.member_count or 0 for g in self.bot.guilds):,}", inline=True)
        embed.add_field(name="Latency", value=f"{round(self.bot.latency * 1000)} ms", inline=True)
        embed.add_field(name="Runtime", value=f"discord.py {discord.__version__}", inline=True)
        embed.add_field(name="Modules", value="General · Community · Adventure", inline=False)
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="help", aliases=["commands", "cmds"])
    async def help_command(self, ctx: commands.Context) -> None:
        p = ctx.clean_prefix
        embed = self.embed("Command index", "A quick reference to the available systems. Arguments in [brackets] are optional.")
        embed.add_field(name="SYSTEM", value=f"`{p}ping` · gateway latency\n`{p}about` · bot information\n`{p}help` · command index", inline=False)
        embed.add_field(name="COMMUNITY", value=f"`{p}userinfo [member]` · member profile\n`{p}serverinfo` · server overview\n`{p}avatar [member]` · avatar viewer\n`{p}roleinfo <role>` · role details\n`{p}poll <question>` · create a reaction poll\n`{p}purge <amount>` · clear messages (moderators)", inline=False)
        embed.add_field(name="TOOLS", value=f"`{p}roll [sides]` · random dice\n`{p}coinflip` · flip a coin\n`{p}choose <a | b | ...>` · random choice\n`{p}8ball <question>` · ask the 8-ball", inline=False)
        embed.add_field(name="ADVENTURE", value=f"`{p}bosses` · boss catalogue\n`{p}boss challenge <name>` · summon a boss\n`{p}boss status` · encounter status\n`{p}join` · join the active fight\n`{p}attack [ability]` · take your turn\n`{p}weapons` · weapon catalogue\n`{p}weapon <name>` · equip a weapon\n`{p}skills` · view your skills\n`{p}unlock <skill>` · unlock a weapon ability", inline=False)
        embed.add_field(name="OWNER", value=f"`{p}reload` · update and restart", inline=False)
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="userinfo", aliases=["whois", "profile"])
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

    @commands.command(name="serverinfo", aliases=["server", "guild"])
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
