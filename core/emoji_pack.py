"""Illustrated server emoji pack, generated with Pillow vector artwork."""
from __future__ import annotations

import io
import logging
from PIL import Image, ImageDraw

log = logging.getLogger("discord_bot.emojis")

# Each icon has its own silhouette and color treatment; no text glyphs are used.
PALETTE = {
    "coin": ("#ffd45a", "#8b5b18"), "gold": ("#ffe078", "#80531b"),
    "gem": ("#75e2ff", "#164a91"), "crystal": ("#d2a0ff", "#53228b"),
    "star": ("#ffe36b", "#80551b"), "crown": ("#ffdc65", "#81531a"),
    "sword": ("#e8efff", "#354b76"), "shield": ("#82caff", "#22548a"),
    "potion": ("#d1a4ff", "#56328c"), "chest": ("#ffc36c", "#74401c"),
    "trophy": ("#ffe16a", "#80551b"), "quest": ("#ffe0a0", "#80552b"),
    "guild": ("#8bbcff", "#244b91"), "trade": ("#ffca8b", "#74431f"),
    "market": ("#ffad91", "#853c30"), "boss": ("#ff9999", "#702d3b"),
    "tower": ("#c4c9ff", "#424a85"), "expedition": ("#8fe5d4", "#246b68"),
    "daily": ("#ffaaaa", "#843b4b"), "inventory": ("#d4b18d", "#67452f"),
    "leaderboard": ("#9bd2ff", "#27578c"), "settings": ("#c4c9d8", "#4c5368"),
    "help": ("#9bd5ff", "#245d9d"), "success": ("#9effb0", "#236d45"),
    "error": ("#ff9ca4", "#812d43"), "info": ("#a6d8ff", "#245d9d"),
    "warning": ("#ffe38c", "#805b20"), "reward": ("#ffe3a1", "#80511f"),
    "enemy": ("#ffaaaa", "#692c37"), "armor": ("#d3ddff", "#3e4e83"),
}
EMOJI_DESIGNS = tuple(PALETTE)

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


def render_emoji(name: str) -> bytes:
    """Render a distinct 96px illustrated icon with transparent outer corners."""
    if name not in PALETTE:
        raise KeyError(name)
    fg, bg = PALETTE[name]
    im = Image.new("RGBA", (96, 96), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((4, 4, 92, 92), fill=bg, outline="#e7dcff", width=3)
    d.ellipse((10, 10, 86, 86), outline="#ffffff55", width=2)

    def poly(points, fill=fg, outline="#28243a"):
        d.polygon(points, fill=fill, outline=outline)
    def line(points, fill=fg, width=6):
        d.line(points, fill=fill, width=width, joint="curve")
    def ell(box, fill=fg, outline="#28243a", width=2):
        d.ellipse(box, fill=fill, outline=outline, width=width)
    def rr(box, radius=6, fill=fg, outline="#28243a", width=2):
        d.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)

    if name in ("coin", "gold"):
        for y in (53, 43, 33):
            d.ellipse((25, y, 71, y+17), fill="#b87920", outline="#382a24", width=2)
        d.ellipse((25, 24, 71, 43), fill=fg, outline="#382a24", width=3)
        d.ellipse((32, 28, 64, 39), outline="#fff0a8", width=2)
    elif name == "gem":
        poly([(48,17),(72,35),(62,70),(48,81),(34,70),(24,35)])
        line([(48,17),(48,80)], "#e8fbff", 3)
        line([(24,35),(72,35)], "#e8fbff", 3)
        poly([(48,19),(35,35),(48,35)], "#eaffff", "#eaffff")
    elif name == "crystal":
        poly([(48,14),(66,34),(61,68),(48,82),(35,68),(30,34)])
        poly([(48,14),(48,82),(35,68),(30,34)], "#f0ddff")
        line([(48,14),(48,82)], "#ffffff", 3)
    elif name == "star":
        import math
        pts=[]
        for i in range(10):
            a=-math.pi/2+i*math.pi/5
            rad=31 if i%2==0 else 14
            pts.append((48+rad*math.cos(a),48+rad*math.sin(a)))
        poly(pts)
    elif name == "crown":
        poly([(19,34),(34,48),(47,22),(62,48),(77,34),(70,70),(26,70)])
        line([(27,77),(69,77)], "#fff0a8", 4)
        for x,y in ((19,31),(47,18),(77,31)): ell((x-5,y-5,x+5,y+5),"#fff1a8")
    elif name == "sword":
        poly([(48,13),(58,42),(52,59),(44,59),(38,42)])
        line([(48,55),(48,79)], "#f4c78a", 7)
        line([(33,58),(63,58)], "#f4c78a", 6)
        ell((42,73,54,85),"#d69b62")
    elif name in ("shield", "armor"):
        poly([(22,22),(48,14),(74,22),(71,55),(48,80),(25,55)])
        line([(48,20),(48,71),"#f3f5ff",3)
        if name == "armor":
            line([(30,39),(66,39)], "#f3f5ff", 3)
            ell((42,30,54,43),"#f3f5ff")
    elif name == "potion":
        rr((39,17,57,31),4,"#eadbff")
        poly([(39,29),(57,29),(64,43),(66,68),(59,77),(37,77),(30,68),(32,43)],"#d9b2ff")
        d.rectangle((34,53,62,68),fill="#a86bfa")
        line([(37,44),(43,38)],"#ffffff",3)
    elif name == "chest":
        rr((20,36,76,72),7,"#b87535")
        d.rectangle((20,35,76,51),fill="#e6a34e",outline="#382a24",width=2)
        line([(20,51),(76,51)],"#ffe0a0",4)
        rr((43,44,53,60),3,"#ffdf76")
        line([(27,30),(69,30)],"#ffd58c",5)
    elif name == "trophy":
        poly([(27,20),(69,20),(65,48),(56,59),(40,59),(31,48)])
        line([(27,27),(16,27),(18,43),(34,49)],fg,6)
        line([(69,27),(80,27),(78,43),(62,49)],fg,6)
        rr((43,57,53,72),3,"#ffe6a0")
        rr((31,72,65,79),3,"#e9b64b")
    elif name == "quest":
        rr((25,15,70,81),5,"#f5d9a0")
        for y,w in ((34,27),(46,33),(58,25)):
            line([(34,y),(34+w,y)],"#916d48",3)
        poly([(58,64),(65,71),(78,54),(73,49)])
    elif name == "guild":
        ell((38,21,58,42)); ell((17,33,36,52)); ell((60,33,79,52))
        d.rounded_rectangle((30,45,66,74),radius=12,fill=fg,outline="#28243a",width=2)
        d.rounded_rectangle((12,53,38,73),radius=9,fill="#b7d7ff",outline="#28243a",width=2)
        d.rounded_rectangle((58,53,84,73),radius=9,fill="#b7d7ff",outline="#28243a",width=2)
    elif name == "trade":
        line([(20,34),(70,34)],fg,8); poly([(62,23),(77,34),(62,45)])
        line([(76,62),(26,62)],"#ffd8a9",8); poly([(34,51),(19,62),(34,73)],"#ffd8a9")
    elif name == "market":
        rr((23,39,73,76),5,"#e8b18b")
        poly([(18,39),(27,20),(69,20),(78,39)],"#ffcf9f")
        line([(18,40),(78,40)],"#fff0d7",4)
        rr((43,52,59,76),3,"#8d5b4c")
        for x in (29,61): line([(x,47),(x,58)],"#fff0d7",3)
    elif name in ("boss", "enemy"):
        # Friendly game-monster mask, not a realistic skull.
        ell((22,23,74,75), "#e9d9d5")
        ell((32,42,43,55), "#30263b"); ell((53,42,64,55), "#30263b")
        poly([(48,54),(42,64),(54,64)],"#9d5260")
        if name == "enemy":
            poly([(22,33),(13,18),(36,27)]); poly([(74,33),(83,18),(60,27)])
        else:
            poly([(29,31),(18,13),(42,26)]); poly([(67,31),(78,13),(54,26)])
    elif name == "tower":
        poly([(22,78),(22,36),(33,36),(33,25),(42,25),(42,36),(54,36),(54,25),(64,25),(64,36),(74,36),(74,78)])
        d.rectangle((42,55,55,78),fill=bg,outline="#28243a",width=2)
        for x in (30,49,66): d.rectangle((x,44,x+5,51),fill="#28243a")
    elif name == "expedition":
        ell((17,17,79,79),None,fg,4)
        line([(48,70),(48,29)],fg,4); poly([(48,17),(38,37),(48,32),(58,37)])
        line([(48,48),(68,62)],"#fff0b0",4)
    elif name == "daily":
        rr((23,23,73,76),6,"#ffe5e5")
        line([(23,39),(73,39)],"#a74e62",5)
        line([(35,17),(35,30)],"#fff0f0",5); line([(61,17),(61,30)],"#fff0f0",5)
        for x,y in ((36,50),(51,50),(36,64),(51,64)): ell((x-3,y-3,x+3,y+3),"#d66b80")
    elif name == "inventory":
        rr((24,29,72,77),7,"#c99b70")
        rr((35,19,61,38),6,"#e6c49b")
        line([(24,45),(72,45)],"#f3d4a8",4)
        ell((43,48,53,58),"#7a503d")
    elif name == "leaderboard":
        rr((22,48,36,75),3,"#9bcfff")
        rr((41,31,55,75),3,"#d7eaff")
        rr((60,18,74,75),3,"#78b7f0")
        line([(20,78),(77,78)],"#eaf5ff",3)
    elif name == "settings":
        ell((29,29,67,67),fg)
        ell((41,41,55,55),bg)
        import math
        for i in range(8):
            a=i*math.pi/4
            x,y=48+27*math.cos(a),48+27*math.sin(a)
            d.rounded_rectangle((x-5,y-5,x+5,y+5),radius=2,fill=fg,outline="#28243a")
    elif name == "help":
        ell((19,19,77,77),None,fg,6)
        ell((43,31,53,41),fg)
        line([(48,42),(48,56)],fg,6); ell((44,64,52,72),fg)
    elif name == "success":
        line([(23,49),(41,66),(74,29)],fg,10)
    elif name == "error":
        line([(29,29),(67,67)],fg,10); line([(67,29),(29,67)],fg,10)
    elif name == "info":
        ell((19,19,77,77),None,fg,5)
        ell((44,30,52,38),fg); line([(48,44),(48,66)],fg,6)
    elif name == "warning":
        poly([(48,15),(82,76),(14,76)],fg)
        line([(48,36),(48,55)],"#543f20",6); ell((44,62,52,70),"#543f20")
    elif name == "reward":
        rr((23,37,73,75),6,"#f3bd65")
        poly([(23,37),(48,49),(73,37),(73,28),(23,28)],"#ffe8a8")
        line([(48,29),(48,74)],"#fff4d2",4)
        line([(48,28),(37,17),(31,22),(39,34)],"#ffdf83",5)
        line([(48,28),(59,17),(65,22),(57,34)],"#ffdf83",5)

    out=io.BytesIO()
    im.save(out,format="PNG",optimize=True)
    return out.getvalue()


async def sync_emoji_pack(bot, guild_id: int = 1569387744575103117) -> dict[str, str]:
    """Create missing icons and replace earlier placeholder versions in the target server."""
    guild=bot.get_guild(guild_id)
    if guild is None:
        log.warning("Emoji sync skipped: target server %s is not in the bot cache",guild_id)
        return {}
    me=guild.me
    if me is None or not me.guild_permissions.manage_emojis_and_stickers:
        log.warning("Emoji sync skipped: bot needs Manage Expressions in %s",guild.name)
        return {}
    existing={emoji.name:emoji for emoji in guild.emojis}
    result={}
    for name in EMOJI_DESIGNS:
        try:
            artwork=render_emoji(name)
            emoji=existing.get(name)
            if emoji is None:
                emoji=await guild.create_custom_emoji(name=name,image=artwork,reason="Install illustrated custom emoji pack")
            else:
                emoji=await emoji.edit(image=artwork,reason="Replace placeholder emoji with illustrated artwork")
            result[name]=str(emoji)
        except Exception:
            log.exception("Could not sync custom emoji :%s:",name)
    log.info("Illustrated emoji pack ready: %s/%s in %s",len(result),len(EMOJI_DESIGNS),guild.name)
    return result


def render_text(value: str, emoji_map: dict[str, str]) -> str:
    for unicode_emoji,name in sorted(UNICODE_TO_NAME.items(),key=lambda item:len(item[0]),reverse=True):
        if name in emoji_map:
            value=value.replace(unicode_emoji,emoji_map[name])
    return value
