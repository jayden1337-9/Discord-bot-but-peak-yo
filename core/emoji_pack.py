"""Server custom emoji pack and lightweight renderer."""
from __future__ import annotations

import io
import logging
from PIL import Image, ImageDraw, ImageFont

log = logging.getLogger("discord_bot.emojis")

# name: (two-character glyph, foreground, background)
EMOJI_DESIGNS = {
    "coin": ("$", "#ffd45a", "#80531b"),
    "gold": ("G", "#ffe078", "#80531b"),
    "gem": ("◆", "#65d8ff", "#164a91"),
    "crystal": ("✦", "#c58aff", "#53228b"),
    "star": ("★", "#ffe36b", "#80551b"),
    "crown": ("♛", "#ffdc65", "#81531a"),
    "sword": ("⚔", "#e8efff", "#354b76"),
    "shield": ("⬟", "#82caff", "#22548a"),
    "potion": ("!", "#b58cff", "#56328c"),
    "chest": ("▣", "#ffc36c", "#74401c"),
    "trophy": ("♜", "#ffe16a", "#80551b"),
    "quest": ("≡", "#ffe0a0", "#80552b"),
    "guild": ("♟", "#8bbcff", "#244b91"),
    "trade": ("⇄", "#ffca8b", "#74431f"),
    "market": ("▤", "#ff9d82", "#853c30"),
    "boss": ("☠", "#ff8585", "#702d3b"),
    "tower": ("▥", "#c4c9ff", "#424a85"),
    "expedition": ("➤", "#8fe5d4", "#246b68"),
    "daily": ("7", "#ff9d9d", "#843b4b"),
    "inventory": ("▣", "#d4b18d", "#67452f"),
    "leaderboard": ("▥", "#9bd2ff", "#27578c"),
    "settings": ("⚙", "#c4c9d8", "#4c5368"),
    "help": ("?", "#9bd5ff", "#245d9d"),
    "success": ("✓", "#9effb0", "#236d45"),
    "error": ("×", "#ff9ca4", "#812d43"),
    "info": ("i", "#a6d8ff", "#245d9d"),
    "warning": ("!", "#ffe38c", "#805b20"),
    "reward": ("+", "#ffe3a1", "#80511f"),
    "enemy": ("☠", "#ffaaaa", "#692c37"),
    "armor": ("⬟", "#d3ddff", "#3e4e83"),
}

# Unicode fallback characters are converted only when this server's emoji exists.
UNICODE_TO_NAME = {
    "💰": "coin", "🪙": "coin", "💎": "gem", "🔮": "crystal",
    "⭐": "star", "🌟": "star", "👑": "crown", "⚔️": "sword",
    "🗡️": "sword", "🛡️": "shield", "🧪": "potion", "🎁": "chest",
    "🏆": "trophy", "📜": "quest", "👥": "guild", "🤝": "trade",
    "🏪": "market", "💀": "boss", "🏰": "tower", "🧭": "expedition",
    "📅": "daily", "🎒": "inventory", "📊": "leaderboard", "⚙️": "settings",
    "❓": "help", "✅": "success", "❌": "error", "ℹ️": "info",
    "⚠️": "warning", "🎉": "reward", "👾": "enemy", "🛡": "armor",
}


def _font(size: int):
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
    except OSError:
        return ImageFont.load_default()


def render_emoji(name: str) -> bytes:
    """Create a compact, transparent 96px icon using Pillow primitives."""
    glyph, foreground, background = EMOJI_DESIGNS[name]
    image = Image.new("RGBA", (96, 96), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse((5, 5, 91, 91), fill=background, outline="#d9c7ff", width=4)
    draw.ellipse((12, 12, 84, 84), outline="#ffffff55", width=2)
    font = _font(54 if len(glyph) == 1 else 48)
    box = draw.textbbox((0, 0), glyph, font=font, stroke_width=1)
    x = (96 - (box[2] - box[0])) / 2 - box[0]
    y = (96 - (box[3] - box[1])) / 2 - box[1] - 2
    draw.text((x, y), glyph, font=font, fill=foreground, stroke_width=1, stroke_fill="#171322")
    out = io.BytesIO()
    image.save(out, format="PNG", optimize=True)
    return out.getvalue()


async def sync_emoji_pack(bot, guild_id: int = 1569387744575103117) -> dict[str, str]:
    """Create missing emoji in the target server and return usable mention strings."""
    guild = bot.get_guild(guild_id)
    if guild is None:
        log.warning("Emoji sync skipped: target server %s is not in the bot cache", guild_id)
        return {}
    me = guild.me
    if me is None or not me.guild_permissions.manage_emojis_and_stickers:
        log.warning("Emoji sync skipped: bot needs Manage Expressions in %s", guild.name)
        return {}
    existing = {emoji.name: emoji for emoji in guild.emojis}
    result = {}
    for name in EMOJI_DESIGNS:
        emoji = existing.get(name)
        if emoji is None:
            try:
                emoji = await guild.create_custom_emoji(
                    name=name, image=render_emoji(name),
                    reason="Install the bot's custom emoji pack",
                )
                log.info("Created custom emoji :%s: in %s", name, guild.name)
            except Exception:
                log.exception("Could not create custom emoji :%s:", name)
                continue
        result[name] = str(emoji)
    log.info("Custom emoji pack ready: %s/%s in %s", len(result), len(EMOJI_DESIGNS), guild.name)
    return result


def render_text(value: str, emoji_map: dict[str, str]) -> str:
    for unicode_emoji, name in sorted(UNICODE_TO_NAME.items(), key=lambda item: len(item[0]), reverse=True):
        if name in emoji_map:
            value = value.replace(unicode_emoji, emoji_map[name])
    return value
