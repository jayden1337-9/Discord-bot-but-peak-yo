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
log = logging.getLogger("peakbot")


class EmbedPager(discord.ui.View):
    def __init__(self, pages):
        super().__init__(timeout=180)
        self.pages = pages
        self.index = 0
        self.previous.disabled = True
        self.next.disabled = len(pages) <= 1

    async def show(self, interaction):
        self.previous.disabled = self.index == 0
        self.next.disabled = self.index >= len(self.pages) - 1
        await interaction.response.edit_message(embed=self.pages[self.index], view=self)

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
    description_parts = split_text(embed.description or "", 1024)
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


class PeakContext(commands.Context):
    async def send(self, content=None, **kwargs):
        embed = kwargs.get("embed")
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
            kwargs["view"] = EmbedPager(pages)
            return await super().send(content, **kwargs)
        return await super().send(content, **kwargs)


class PeakBot(commands.Bot):
    async def setup_hook(self) -> None:
        await self.load_extension("cogs.general")
        await self.load_extension("cogs.adventure")
        await self.load_extension("cogs.progression")
        await self.load_extension("cogs.endgame")
        await self.load_extension("cogs.expeditions")
        await self.load_extension("cogs.ascension")
        log.info("Extensions loaded")

    async def on_ready(self) -> None:
        log.info("Logged in as %s (ID: %s)", self.user, self.user.id)

    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        if isinstance(error, commands.CommandNotFound):
            return
        if isinstance(error, commands.MissingRequiredArgument):
            message = f"Missing argument: `{error.param.name}`. Use `{ctx.clean_prefix}help` for usage."
        elif isinstance(error, commands.BadArgument):
            message = "That argument could not be understood. Check the command usage with the help command."
        elif isinstance(error, commands.NoPrivateMessage):
            message = "This command can only be used inside a server."
        elif isinstance(error, commands.CommandOnCooldown):
            message = f"Try again in {error.retry_after:.1f} seconds."
        else:
            log.error("Command failed", exc_info=(type(error), error, error.__traceback__))
            message = "Something went wrong while running that command."
        embed = discord.Embed(title="Something went wrong", description=message, color=discord.Color.from_rgb(190, 62, 72))
        await ctx.reply(embed=embed, mention_author=False)

    async def is_owner(self, user: discord.User | discord.Member) -> bool:
        return settings.owner_id is not None and user.id == settings.owner_id


async def main() -> None:
    token = settings.require_token()

    intents = discord.Intents.default()
    intents.message_content = True
    bot = PeakBot(
        command_prefix=settings.prefix,
        intents=intents,
        help_command=None,
        context=PeakContext,
    )
    try:
        await bot.start(token)
    finally:
        if not bot.is_closed():
            await bot.close()


if __name__ == "__main__":
    asyncio.run(main())
