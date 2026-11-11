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
    # Specific matches come first so broad words do not steal an icon.
    rules = [
        (("inventory", "backpack", "bag", "items"), "bag"),
        (("yes", "approve", "vote yes", "success", "accepted"), "confirm"),
        (("no", "reject", "vote no", "cancel", "declin", "invalid", "error", "denied", "unavailable", "missing", "locked", "failed"), "cancel"),
        (("refresh", "reload", "update", "retry"), "refresh"),
        (("reward", "claim", "complete", "cleared", "victory", "prize"), "reward"),
        (("world boss", "boss", "raid", "battle"), "boss"),
        (("enemy", "monster", "opponent", "target", "mob"), "enemy"),
        (("setting", "config", "option", "preference"), "settings"),
        (("shield", "defen", "armor", "protect", "health", "hp"), "shield"),
        (("chest", "vault", "key", "loot", "drop", "treasure"), "chest"),
        (("gold", "wallet", "coin", "balance", "donat", "price", "cost", "paid"), "coin"),
        (("gem", "crystal", "premium"), "gem"),
        (("star", "rarity", "rank s", "character", "mastery"), "star"),
        (("weapon", "sword", "attack", "damage", "skill", "combat", "forge"), "sword"),
        (("king", "leader", "owner", "ascension", "admin"), "crown"),
        (("tower", "floor", "rift"), "tower"),
        (("trade", "offer", "exchange", "deal"), "trade"),
        (("daily", "login", "streak", "weekly"), "daily"),
        (("previous", "back", "retreat", "leave", "older"), "down"),
        (("trophy", "achievement", "record", "best", "win"), "trophy"),
        (("next", "upgrade", "level up", "progress", "forward"), "up"),
        (("expedition", "route", "journey", "companion"), "expedition"),
        (("guild", "clan", "member", "party"), "guild"),
        (("help", "command", "menu", "guide", "usage"), "help"),
        (("info", "status", "profile", "overview", "details", "account"), "info"),
        (("leaderboard", "ranking", "top players", "top guild"), "leaderboard"),
        (("lucky", "luck", "roll", "chance", "random", "reroll"), "lucky"),
        (("market", "listing", "shop", "store", "purchase", "buy", "sell"), "market"),
        (("potion", "elixir", "tonic", "consume", "heal"), "potion"),
        (("quest", "contract", "mission", "objective", "task"), "quest"),
    ]
    for words, key in rules:
        if any(word in text for word in words) and key in emojis:
            return emojis[key]
    return emojis.get("info", "")


def _add_reading_space(value: str) -> str:
    """Separate headings and list rows without damaging paragraphs or code."""
    if not value:
        return value
    # Shorter descriptions benefit from a blank line between every row.
    if len(value) <= 2400 and "```" not in value:
        return re.sub(r"(?<!\n)\n(?!\n)", "\n\n", value)
    value = re.sub(
        r"(?m)(?<!\n)\n(?=(?:\*\*[^*\n]+\*\*|<a?:[A-Za-z0-9_]+:\d+>|[•▸◆▪]|\d+[.)]\s))",
        "\n\n",
        value,
    )
    return value


def render_embed(embed, emoji_map=None):
    """Apply the shared custom-emoji and spacious layout to every embed."""
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
        result.description = _add_reading_space(render_text(result.description, emojis))
    for index, field in enumerate(result.fields):
        name = render_text(field.name, emojis)
        value = _add_reading_space(render_text(field.value, emojis))
        if "<:" not in name:
            icon = _ui_icon_for(name, emojis)
            if icon:
                name = f"{icon}  {name}"
        # One field per row gives stats and descriptions room to breathe.
        result.set_field_at(index, name=name, value=value, inline=False)
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
    """Add matching server emoji to buttons and select options."""
    if view is None:
        return view
    emojis = emoji_map or CUSTOM_EMOJIS
    for item in getattr(view, "children", []):
        if isinstance(item, discord.ui.Button) and item.emoji is None:
            label = (item.label or item.custom_id or "").lower()
            icon = _ui_icon_for(label, emojis)
            if icon:
                try:
                    item.emoji = discord.PartialEmoji.from_str(icon)
                except (TypeError, ValueError):
                    pass
        elif isinstance(item, discord.ui.Select):
            for option in item.options:
                if option.emoji is not None:
                    continue
                icon = _ui_icon_for(option.label, emojis)
                if icon:
                    try:
                        option.emoji = discord.PartialEmoji.from_str(icon)
                    except (TypeError, ValueError):
                        pass
    return view
