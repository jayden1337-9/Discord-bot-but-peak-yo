"""Compact Discord-native command panel."""
import discord
from discord.ext import commands


class CommandMenu(discord.ui.View):
    def __init__(self, ctx: commands.Context):
        super().__init__(timeout=180)
        self.ctx = ctx
        self.owner_id = ctx.author.id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "This menu belongs to the person who opened it.", ephemeral=True
            )
            return False
        return True

    async def run(self, interaction: discord.Interaction, command_name: str) -> None:
        command = self.ctx.bot.get_command(command_name)
        if command is None:
            await interaction.response.send_message(
                "That command is currently unavailable.", ephemeral=True
            )
            return
        await interaction.response.defer()
        await self.ctx.invoke(command)

    @discord.ui.button(label="Profile", style=discord.ButtonStyle.primary)
    async def profile(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.run(interaction, "stats")

    @discord.ui.button(label="Inventory", style=discord.ButtonStyle.secondary)
    async def inventory(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.run(interaction, "inventory")

    @discord.ui.button(label="Quests", style=discord.ButtonStyle.secondary)
    async def quests(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.run(interaction, "quests")

    @discord.ui.button(label="Leaderboard", style=discord.ButtonStyle.secondary)
    async def leaderboard(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.run(interaction, "leaderboard")

    @discord.ui.button(label="Help", style=discord.ButtonStyle.secondary)
    async def help(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.run(interaction, "help")

    @discord.ui.button(label="Close", style=discord.ButtonStyle.danger)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(
            embed=discord.Embed(
                title="Menu closed",
                description="Run `,menu` whenever you need it again.",
                color=discord.Color.from_rgb(48, 61, 82),
            ),
            view=self,
        )


class Menu(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="menu", aliases=["panel", "start"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def menu(self, ctx: commands.Context) -> None:
        embed = discord.Embed(
            title="Quick menu",
            description=(
                "Use the buttons to open your profile, inventory, quests, "
                "leaderboard or command help. You can still use every command normally."
            ),
            color=discord.Color.from_rgb(48, 61, 82),
        )
        embed.set_footer(text=f"Opened by {ctx.author}")
        await ctx.reply(embed=embed, view=CommandMenu(ctx), mention_author=False)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Menu(bot))
