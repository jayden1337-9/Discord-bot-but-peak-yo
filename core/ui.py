import re

import discord


CUSTOM_EMOJIS = {
    "bag": "<:bag1:1569655521953325066>",
    "refresh": "<:refresh1:1569654788973666426>",
    "reward": "<:reward1:1569654864693305404>",
    "boss": "<:boss1:1569655739323129967>",
    "cancel": "<:cancel1:1569655124924698735>",
    "settings": "<:settings1:1569655344739778683>",
    "shield": "<:shield1:1569656398894202931>",
    "chest": "<:chest1:1569656335644102758>",
    "coin": "<:coin1:1569656729640378499>",
    "star": "<:star1:1569656593736405122>",
    "sword": "<:sword1:1569656535775322112>",
    "confirm": "<:confirm1:1569655189110128640>",
    "crown": "<:crown1:1569656669468626974>",
    "tower": "<:tower1:1569655891484221470>",
    "trade": "<:trade1:1569655960673325077>",
    "daily": "<:daily1:1569655584813224088>",
    "down": "<:down:1569655001591316500>",
    "trophy": "<:trophy1:1569656193658392706>",
    "up": "<:up:1569655064719523910>",
    "enemy": "<:enemy1:1569654578738106408>",
    "expedition": "<:expediton1:1569655659555725415>",
    "gem": "<:gem1:1569656792483627018>",
    "guild": "<:guild1:1569656030189584456>",
    "help": "<:help1:1569655259909853195>",
    "info": "<:info1:1569654931730731090>",
    "leaderboard": "<:leaderboard1:1569655422179090542>",
    "lucky": "<:lucky1:1569654706375237662>",
    "market": "<:market1:1569655825759215726>",
    "potion": "<:potion1:1569656462958137364>",
    "quest": "<:quest1:1569656122896552036>",
}


UNICODE_TO_NAME = {
    "🎒": "bag", "🔄": "refresh", "🎉": "reward", "👹": "boss",
    "❌": "cancel", "⚙️": "settings", "🛡️": "shield", "🎁": "chest",
    "💰": "coin", "🪙": "coin", "⭐": "star", "🌟": "star",
    "⚔️": "sword", "🗡️": "sword", "✅": "confirm", "👑": "crown",
    "🏰": "tower", "🤝": "trade", "📅": "daily", "⬇️": "down",
    "🔽": "down", "🏆": "trophy", "⬆️": "up", "🔼": "up",
    "💀": "enemy", "🧭": "expedition", "💎": "gem", "👥": "guild",
    "❓": "help", "ℹ️": "info", "📊": "leaderboard", "🍀": "lucky",
    "🏪": "market", "🧪": "potion", "📜": "quest",
}


def render_text(value: str, emoji_map: dict[str, str] | None = None) -> str:
    if not isinstance(value, str):
        return value
    # Some command strings contain the two literal characters "\\n"
    # instead of a real newline. Normalize those before sending.
    value = value.replace("\\r\\n", "\n").replace("\\n", "\n")
    emojis = emoji_map or CUSTOM_EMOJIS
    for unicode_emoji, name in sorted(
        UNICODE_TO_NAME.items(), key=lambda item: len(item[0]), reverse=True
    ):
        custom_emoji = emojis.get(name)
        if custom_emoji:
            value = value.replace(unicode_emoji, custom_emoji)
    return value


def _ui_icon_for(value: str, emoji_map=None) -> str:
    text = str(value or "").lower()
    emojis = emoji_map or CUSTOM_EMOJIS
    rules = [
        (("inventory", "backpack", "bag"), "bag"),
        (("yes", "approve", "vote yes"), "confirm"),
        (("no", "reject", "vote no"), "cancel"),
        (("refresh", "reload", "update"), "refresh"),
        (("reward", "claim", "complete", "cleared", "victory", "success"), "reward"),
        (("boss", "raid", "world boss", "enemy"), "boss"),
        (("cancel", "declin", "invalid", "error", "denied", "unavailable", "missing", "locked", "failed"), "cancel"),
        (("setting", "config", "option"), "settings"),
        (("shield", "defen", "armor", "protect"), "shield"),
        (("chest", "vault", "key", "loot", "drop"), "chest"),
        (("gold", "wallet", "coin", "donat", "price", "cost"), "coin"),
        (("star", "rarity", "rank s"), "star"),
        (("weapon", "sword", "attack", "damage", "skill", "combat"), "sword"),
        (("confirm", "accept", "equip", "join", "created", "selected", "purchase"), "confirm"),
        (("king", "leader", "owner", "ascension"), "crown"),
        (("tower", "floor", "rift"), "tower"),
        (("trade", "offer", "exchange"), "trade"),
        (("daily", "login", "streak"), "daily"),
        (("down", "previous", "back", "retreat", "leave"), "down"),
        (("trophy", "achievement", "record", "best"), "trophy"),
        (("up", "next", "upgrade", "level up", "progress"), "up"),
        (("enemy", "monster", "opponent", "target"), "enemy"),
        (("expedition", "route", "journey", "companion"), "expedition"),
        (("gem", "crystal", "premium"), "gem"),
        (("guild", "clan", "member"), "guild"),
        (("help", "command", "menu", "guide"), "help"),
        (("info", "status", "profile", "overview", "details"), "info"),
        (("leaderboard", "ranking", "top players", "top guild"), "leaderboard"),
        (("lucky", "roll", "chance", "random"), "lucky"),
        (("market", "listing", "shop", "store"), "market"),
        (("potion", "elixir", "tonic", "consume", "heal"), "potion"),
        (("quest", "contract", "mission", "objective"), "quest"),
    ]
    for words, key in rules:
        if any(word in text for word in words) and key in emojis:
            return emojis[key]
    return emojis.get("info", "")


def render_embed(embed, emoji_map=None):
    """Apply the shared custom-emoji and spacing style to any Discord embed."""
    if embed is None:
        return None
    emojis = emoji_map or CUSTOM_EMOJIS
    result = embed.copy()
    if result.title:
        title = render_text(result.title, emojis)
        if "<:" not in title:
            icon = _ui_icon_for(title, emojis)
            if icon:
                title = f"{icon}  {title}"
        result.title = title
    if result.description:
        description = render_text(result.description, emojis)
        # Give section headings and bullet groups breathing room without
        # changing compact stat lines or existing paragraph breaks.
        description = re.sub(
            r"(?m)(?<!\n)\n(?=(?:\*\*[^*\n]+\*\*|[•▸◆])\s*)",
            "\n\n",
            description,
        )
        result.description = description
    for index, field in enumerate(result.fields):
        name = render_text(field.name, emojis)
        value = render_text(field.value, emojis)
        if "<:" not in name:
            icon = _ui_icon_for(name, emojis)
            if icon:
                name = f"{icon}  {name}"
        result.set_field_at(index, name=name, value=value, inline=field.inline)
    if result.author.name:
        result.set_author(
            name=render_text(result.author.name, emojis),
            url=result.author.url,
            icon_url=result.author.icon_url,
        )
    if result.footer.text:
        result.set_footer(
            text=render_text(result.footer.text, emojis),
            icon_url=result.footer.icon_url,
        )
    return result


def style_view(view, emoji_map=None):
    """Add matching server emoji to Discord buttons while preserving labels."""
    if view is None:
        return view
    emojis = emoji_map or CUSTOM_EMOJIS
    for item in getattr(view, "children", []):
        if not isinstance(item, discord.ui.Button) or item.emoji is not None:
            continue
        label = (item.label or item.custom_id or "").lower()
        icon = _ui_icon_for(label, emojis)
        if icon:
            try:
                item.emoji = discord.PartialEmoji.from_str(icon)
            except (TypeError, ValueError):
                pass
    return view

