"""Compact Discord-native command panel."""
import discord
from discord.ext import commands


class CommandMenu(discord.ui.View):
    def __init__(self, ctx: commands.Context):
        super().__init__(timeout=180)
        self.ctx = ctx
        self.owner_id = ctx.author.id
        self.message = None

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

    @discord.ui.button(label="Wallet", style=discord.ButtonStyle.secondary, row=1)
    async def wallet(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.run(interaction, "wallet")

    @discord.ui.button(label="Guild", style=discord.ButtonStyle.secondary, row=1)
    async def guild(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.run(interaction, "guild")

    @discord.ui.button(label="Market", style=discord.ButtonStyle.secondary, row=1)
    async def market(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.run(interaction, "market")

    @discord.ui.button(label="Bosses", style=discord.ButtonStyle.secondary, row=1)
    async def bosses(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.run(interaction, "bosses")

    async def on_timeout(self) -> None:
        for child in self.children:
            child.disabled = True
        if self.message is not None:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass

    @discord.ui.button(label="Attack", style=discord.ButtonStyle.success, row=2)
    async def attack(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.run(interaction, "attack")

    @discord.ui.button(label="Daily", style=discord.ButtonStyle.secondary, row=2)
    async def daily(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.run(interaction, "daily")

    @discord.ui.button(label="Tower", style=discord.ButtonStyle.secondary, row=2)
    async def tower(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.run(interaction, "tower")

    @discord.ui.button(label="Expedition", style=discord.ButtonStyle.secondary, row=2)
    async def expedition(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.run(interaction, "expedition")

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
                "Your shortcuts for profile, inventory, quests, wallet, community and combat. "
                "Use the buttons below or keep using prefix commands."
            ),
            color=discord.Color.from_rgb(48, 61, 82),
        )
        game = self.bot.get_cog("Adventure")
        if game is not None:
            from cogs.adventure import CHARACTERS, display_number
            profile = game.p(ctx.author.id)
            character = CHARACTERS.get(profile.get("character"), CHARACTERS["sukuna"])[0]
            embed.add_field(
                name="Player",
                value=(
                    f"**{character}** · Level {display_number(profile.get('level', 1))}\n"
                    f"Ascension {int(profile.get('ascension', 0))}/25 · "
                    f"Victories {display_number(profile.get('wins', 0))}"
                ),
                inline=True,
            )
            embed.add_field(
                name="Wallet",
                value=(
                    f"Gold: {display_number(profile.get('gold', 0))}\n"
                    f"Gems: {display_number(profile.get('gems', 0))}"
                ),
                inline=True,
            )
            active = profile.get("attack_mode")
            embed.add_field(name="Last encounter", value=(str(active).replace("_", " ").title() if active else "None"), inline=True)
        embed.set_footer(text=f"Opened by {ctx.author} · Buttons are only usable by you")
        view = CommandMenu(ctx)
        view.message = await ctx.reply(embed=embed, view=view, mention_author=False)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Menu(bot))
