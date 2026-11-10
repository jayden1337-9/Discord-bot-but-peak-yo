import asyncio
import logging
import os

import discord
from dotenv import load_dotenv
from discord.ext import commands

from core.config import Settings

# Load Wispbyte environment-file values before reading os.getenv().
load_dotenv("/home/container/.env")

settings = Settings.from_env()

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("discord_bot")

EMOJI_GUILD_ID = 1569387744575103117

# These names are the custom emoji names to add manually in the server.
UNICODE_TO_NAME = {
    "💰": "coin", "🪙": "coin",
    "💎": "gem",
    "⭐": "star", "🌟": "star",
    "👑": "crown",
    "⚔️": "sword", "🗡️": "sword",
    "🛡️": "shield",
    "🧪": "potion",
    "🎁": "chest",
    "🏆": "trophy",
    "📜": "quest",
    "👥": "guild",
    "🤝": "trade",
    "🏪": "market",
    "💀": "boss",
    "🏰": "tower",
    "🧭": "expedition",
    "📅": "daily",
    "🎒": "bag",
    "📊": "leaderboard",
    "⚙️": "settings",
    "❓": "help",
    "✅": "confirm",
    "❌": "cancel",
    "⬆️": "up", "🔼": "up",
    "⬇️": "down", "🔽": "down",
    "ℹ️": "info",
    "🔄": "refresh",
    "🎉": "reward",
    "🍀": "lucky",
    "💀": "enemy",
}


def render_text(value: str, emoji_map: dict[str, str]) -> str:
    for unicode_emoji, name in sorted(UNICODE_TO_NAME.items(), key=lambda item: len(item[0]), reverse=True):
        custom_emoji = emoji_map.get(name)
        if custom_emoji:
            value = value.replace(unicode_emoji, custom_emoji)
    return value


class EmbedPager(discord.ui.View):
    def __init__(self, pages, owner_id):
        super().__init__(timeout=180)
        self.pages = pages
        self.owner_id = owner_id
        self.message = None
        self.index = 0
        self.previous.disabled = True
        self.next.disabled = len(pages) <= 1

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("These controls belong to the person who opened this response.", ephemeral=True)
            return False
        return True

    async def show(self, interaction):
        self.previous.disabled = self.index == 0
        self.next.disabled = self.index >= len(self.pages) - 1
        await interaction.response.edit_message(embed=self.pages[self.index], view=self)

    async def on_timeout(self) -> None:
        for child in self.children:
            child.disabled = True
        if self.message is not None:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.secondary)
    async def previous(self, interaction, button):
        self.index = max(0, self.index - 1)
        await self.show(interaction)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.primary)
    async def next(self, interaction, button):
        self.index = min(len(self.pages) - 1, self.index + 1)
        await self.show(interaction)


def split_text(text, limit=1024):
    """Split text without dropping characters; prefer line and word boundaries."""
    if not text:
        return [""]
    chunks = []
    while len(text) > limit:
        cut = text.rfind("\\n", 0, limit + 1)
        if cut < limit // 2:
            cut = text.rfind(" ", 0, limit + 1)
        if cut < limit // 2:
            cut = limit
        else:
            cut += 1
        chunks.append(text[:cut])
        text = text[cut:]
    if text:
        chunks.append(text)
    return chunks


def paginated_embeds(embed):
    """Convert an oversized embed into valid, lossless 1024-char pages."""
    description_parts = split_text(embed.description or "", 4096)
    fields = []
    for field in embed.fields:
        parts = split_text(field.value, 1024)
        for index, part in enumerate(parts):
            name = field.name if index == 0 else f"{field.name} (continued)"
            fields.append((name[:256], part, False))
    pages = []
    field_index = 0
    desc_index = 0
    while desc_index < len(description_parts) or field_index < len(fields):
        desc = description_parts[desc_index] if desc_index < len(description_parts) else ""
        desc_index += 1 if desc_index < len(description_parts) else 0
        page = discord.Embed(
            title=embed.title,
            description=desc or None,
            color=embed.color or discord.Color.from_rgb(42, 52, 68),
        )
        if embed.url:
            page.url = embed.url
        if embed.author.name:
            page.set_author(name=embed.author.name, url=embed.author.url, icon_url=embed.author.icon_url)
        if embed.thumbnail.url and not pages:
            page.set_thumbnail(url=embed.thumbnail.url)
        if embed.image.url and not pages:
            page.set_image(url=embed.image.url)
        if embed.footer.text:
            page.set_footer(text=embed.footer.text, icon_url=embed.footer.icon_url)
        while field_index < len(fields) and len(page.fields) < 25:
            name, value, inline = fields[field_index]
            current = len(page.description or "") + sum(len(f.name) + len(f.value) for f in page.fields)
            if page.fields and current + len(name) + len(value) > 5600:
                break
            page.add_field(name=name, value=value or "\u200b", inline=inline)
            field_index += 1
        pages.append(page)
    if len(pages) > 1:
        for index, page in enumerate(pages, 1):
            base = embed.title or "Details"
            page.title = f"{base[:220]} · {index}/{len(pages)}"
    return pages


class BotContext(commands.Context):
    async def send(self, content=None, **kwargs):
        emoji_map = getattr(self.bot, "emoji_map", {})
        if isinstance(content, str):
            content = render_text(content, emoji_map)
        embed = kwargs.get("embed")
        if embed is not None and emoji_map:
            embed = embed.copy()
            if embed.title:
                embed.title = render_text(embed.title, emoji_map)
            if embed.description:
                embed.description = render_text(embed.description, emoji_map)
            for index, field in enumerate(embed.fields):
                embed.set_field_at(index, name=render_text(field.name, emoji_map), value=render_text(field.value, emoji_map), inline=field.inline)
            kwargs["embed"] = embed
        embeds = kwargs.get("embeds")
        if embed is not None:
            pages = paginated_embeds(embed)
            oversized = len(pages) > 1
        elif embeds:
            pages = []
            for item in embeds:
                pages.extend(paginated_embeds(item))
            oversized = len(pages) > len(embeds)
        else:
            oversized = False
            pages = []
        if oversized:
            kwargs.pop("embed", None)
            kwargs.pop("embeds", None)
            kwargs["embed"] = pages[0]
            view = EmbedPager(pages, self.author.id)
            kwargs["view"] = view
            message = await super().send(content, **kwargs)
            view.message = message
            return message
        return await super().send(content, **kwargs)


class DiscordBot(commands.Bot):
    async def setup_hook(self) -> None:
        await self.load_extension("cogs.general")
        await self.load_extension("cogs.adventure")
        await self.load_extension("cogs.progression")
        await self.load_extension("cogs.endgame")
        await self.load_extension("cogs.expeditions")
        await self.load_extension("cogs.ascension")
        await self.load_extension("cogs.social")
        await self.load_extension("cogs.menu")
        log.info("Extensions loaded")

    async def on_ready(self) -> None:
        log.info("Logged in as %s (ID: %s)", self.user, self.user.id)
        guild = self.get_guild(EMOJI_GUILD_ID)
        self.emoji_map = {
            emoji.name: str(emoji)
            for emoji in guild.emojis
        } if guild else {}
        log.info("Loaded %s manually added custom emojis", len(self.emoji_map))

    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        # Keep one ordered chain so CommandNotFound is not overwritten by fallback handling.
        if isinstance(error, commands.CommandNotFound):
            from difflib import get_close_matches
            names = [command.qualified_name for command in self.walk_commands()]
            matches = get_close_matches(ctx.invoked_with or "", names, n=1, cutoff=0.6)
            suggestion = f" Did you mean `{ctx.clean_prefix}{matches[0]}`?" if matches else ""
            message = f"Unknown command `{ctx.invoked_with}`.{suggestion} Use `{ctx.clean_prefix}help` to see available commands."
        elif isinstance(error, commands.MissingRequiredArgument):
            usage = f"{ctx.clean_prefix}{ctx.command.qualified_name} {ctx.command.signature}".strip()
            message = f"Missing argument: `{error.param.name}`. Usage: `{usage}`"
        elif isinstance(error, commands.BadArgument):
            usage = f"{ctx.clean_prefix}{ctx.command.qualified_name} {ctx.command.signature}".strip()
            message = f"That argument could not be understood. Usage: `{usage}`"
        elif isinstance(error, commands.MissingPermissions):
            message = "You do not have permission to use that command."
        elif isinstance(error, commands.BotMissingPermissions):
            message = "I am missing a permission required to run that command."
        elif isinstance(error, commands.NotOwner):
            message = "This command is restricted to the bot owner."
        elif isinstance(error, commands.NoPrivateMessage):
            message = "This command can only be used inside a server."
        elif isinstance(error, commands.CommandOnCooldown):
            message = f"Try again in {error.retry_after:.1f} seconds."
        elif isinstance(error, commands.CheckFailure):
            message = "You cannot use that command here or with your current permissions."
        elif isinstance(error, commands.CommandInvokeError):
            original = error.original
            log.error("Command failed: %s", original, exc_info=(type(original), original, original.__traceback__))
            message = "Something went wrong while running that command. The error has been logged."
        else:
            log.error("Command failed", exc_info=(type(error), error, error.__traceback__))
            message = "Something went wrong while running that command."
        if isinstance(error, commands.CommandNotFound):
            title = "Command not found"
        elif isinstance(error, commands.CommandOnCooldown):
            title = "Slow down"
        elif isinstance(error, (commands.MissingRequiredArgument, commands.BadArgument)):
            title = "Invalid command input"
        elif isinstance(error, (commands.MissingPermissions, commands.BotMissingPermissions, commands.NotOwner, commands.NoPrivateMessage, commands.CheckFailure)):
            title = "Permission denied"
        else:
            title = "Something went wrong"
        embed = discord.Embed(title=title, description=message, color=discord.Color.from_rgb(190, 62, 72))
        await ctx.reply(embed=embed, mention_author=False)


async def main() -> None:
    token = settings.require_token()

    intents = discord.Intents.default()
    intents.message_content = True
    bot = DiscordBot(
        command_prefix=settings.prefix,
        intents=intents,
        help_command=None,
        context=BotContext,
    )
    try:
        await bot.start(token)
    finally:
        if not bot.is_closed():
            await bot.close()


if __name__ == "__main__":
    asyncio.run(main())
