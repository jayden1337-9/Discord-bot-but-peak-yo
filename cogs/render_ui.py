from io import BytesIO
from math import ceil, floor, log10
from PIL import Image, ImageDraw, ImageFont

BG = (10, 14, 24)
PANEL = (19, 27, 42)
CARD = (25, 36, 54)
BORDER = (53, 72, 98)
TEXT = (238, 243, 251)
MUTED = (139, 157, 182)
ACCENT = (119, 177, 255)
GOLD = (245, 197, 104)
GREEN = (117, 211, 164)
PURPLE = (180, 145, 255)
CYAN = (105, 208, 222)


def _font(size, bold=False, emoji=False):
    candidates = []
    if emoji:
        candidates += [
            "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
            "/usr/share/fonts/truetype/noto/NotoEmoji-Regular.ttf",
            "/usr/share/fonts/truetype/ancient-scripts/Symbola_hint.ttf",
        ]
    candidates += [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            pass
    return ImageFont.load_default()


def _fit(draw, text, font, width):
    text = str(text)
    while text and draw.textbbox((0, 0), text, font=font)[2] > width:
        text = text[:-2] + "…"
    return text


def _number(value):
    try:
        value = int(value)
        if value.bit_length() > 256:
            exponent = floor(log10(value))
            mantissa = 10 ** (log10(value) - exponent)
            return f"{mantissa:.2f}e{exponent}"
        return f"{value:,}"
    except (TypeError, ValueError, OverflowError):
        return str(value)


def _category(key):
    if key.startswith("boss_chest_") or key.endswith("_key") or key in {"jjk_key", "jojo_key", "naruto_key"}:
        return "CHESTS & KEYS", PURPLE
    if any(word in key for word in ("potion", "tonic", "elixir", "feather", "token")):
        return "CONSUMABLES", GREEN
    if key in {"six_eyes", "cursed_fingers", "black_flash_residue", "sukuna_relic", "limitless_core"} or any(word in key for word in ("seal", "relic", "core", "essence", "shard")):
        return "RARE DROPS", GOLD
    return "MATERIALS", CYAN


def _finish(image):
    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    output.seek(0)
    return output


def inventory_image(profile, items, page=1, icons=None, page_size=12):
    icons = icons or {}
    normal = [(key, value, False) for key, value in profile.get("inventory", {}).items() if value > 0]
    symbolic = [(key, value, True) for key, value in profile.get("symbolic_rewards", {}).get("inventory", {}).items() if value > 0]
    entries = sorted(normal + symbolic, key=lambda item: (_category(item[0])[0], item[0]))
    total_pages = max(1, ceil(len(entries) / page_size))
    page = max(1, min(int(page), total_pages))
    selected = entries[(page - 1) * page_size:page * page_size]

    width, card_w, card_h, gap = 1000, 466, 104, 14
    columns = 2
    rows = max(1, ceil(len(selected) / columns))
    header_h, footer_h = 228, 78
    height = header_h + rows * (card_h + gap) + footer_h
    image = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(image)
    title, subtitle = _font(35, True), _font(15)
    body, small, tiny, emoji = _font(19, True), _font(13), _font(11, True), _font(29, emoji=True)

    draw.rounded_rectangle((22, 20, width - 22, 190), 24, fill=PANEL, outline=BORDER, width=2)
    draw.text((50, 43), "INVENTORY", font=title, fill=TEXT)
    draw.text((52, 96), "YOUR ITEMS  /  MATERIALS  /  RARE DROPS", font=subtitle, fill=MUTED)
    draw.text((52, 133), f"{len(entries)} item stacks     PAGE {page}/{total_pages}", font=small, fill=ACCENT)

    wallets = [
        (24, 204, 480, 272, "🪙", "GOLD", _number(profile.get("gold", 0)), GOLD),
        (504, 204, 960, 272, "💎", "GEMS", _number(profile.get("gems", 0)), PURPLE),
    ]
    for x1, y1, x2, y2, symbol, label, value, color in wallets:
        draw.rounded_rectangle((x1, y1, x2, y2), 16, fill=CARD, outline=BORDER, width=2)
        try:
            draw.text((x1 + 18, y1 + 15), symbol, font=emoji, embedded_color=True)
        except (TypeError, ValueError):
            draw.text((x1 + 18, y1 + 15), label[0], font=body, fill=color)
        draw.text((x1 + 70, y1 + 10), label, font=tiny, fill=MUTED)
        draw.text((x1 + 70, y1 + 30), value, font=body, fill=color)

    if not selected:
        draw.rounded_rectangle((24, header_h, width - 24, header_h + 135), 18, fill=PANEL, outline=BORDER, width=2)
        draw.text((55, header_h + 45), "Your inventory is empty.", font=body, fill=MUTED)

    for index, (key, amount, is_symbolic) in enumerate(selected):
        col, row = index % columns, index // columns
        x = 24 + col * (card_w + gap)
        y = header_h + row * (card_h + gap)
        category, accent = _category(key)
        draw.rounded_rectangle((x, y, x + card_w, y + card_h), 17, fill=CARD, outline=BORDER, width=2)
        draw.rounded_rectangle((x + 14, y + 17, x + 66, y + 69), 13, fill=(37, 52, 76), outline=accent, width=2)
        icon = icons.get(key, "📦")
        try:
            draw.text((x + 24, y + 24), icon, font=emoji, embedded_color=True)
        except (TypeError, ValueError):
            initials = "".join(part[0] for part in key.split("_")[:2]).upper()
            draw.text((x + 25, y + 32), initials[:2], font=body, fill=accent)
        name = items.get(key, key.replace("_", " ").title())
        draw.text((x + 82, y + 14), _fit(draw, name, body, card_w - 100), font=body, fill=TEXT)
        amount_text = f"{_number(amount)} × 10^(10^100)" if is_symbolic else f"x{_number(amount)}"
        draw.text((x + 84, y + 47), _fit(draw, amount_text, small, card_w - 105), font=small, fill=GOLD if is_symbolic else GREEN)
        draw.text((x + 84, y + 76), category, font=tiny, fill=accent)

    footer_y = height - footer_h + 8
    draw.line((28, footer_y, width - 28, footer_y), fill=BORDER, width=2)
    draw.text((42, footer_y + 20), "PEAK RPG  /  ITEM STORAGE", font=tiny, fill=MUTED)
    draw.text((width - 250, footer_y + 18), "Use ,inventory <page>", font=small, fill=ACCENT)
    return _finish(image)


def gear_image(profile, gear):
    width, height = 900, 520
    image = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(image)
    title, body, small = _font(32, True), _font(20, True), _font(15)
    draw.rounded_rectangle((24, 24, width - 24, height - 24), 22, fill=PANEL, outline=BORDER, width=2)
    draw.text((52, 48), "EQUIPMENT LOADOUT", font=title, fill=TEXT)
    equipped = profile.get("gear_equipped", {})
    slots = [("armor", "🛡️ ARMOR"), ("relic", "💠 RELIC"), ("core", "⚙️ CORE")]
    for i, (slot, label) in enumerate(slots):
        y = 125 + i * 105
        key = equipped.get(slot)
        item = gear.get(key, {}) if key else {}
        draw.rounded_rectangle((52, y, width - 52, y + 82), 15, fill=CARD, outline=BORDER, width=2)
        draw.text((74, y + 14), label, font=small, fill=ACCENT)
        draw.text((230, y + 12), item.get("name", "Empty"), font=body, fill=TEXT)
        stats = f"ATK +{item['attack']}   DEF +{int(item['defense'] * 100)}%   HP +{item['hp']}" if item else "No equipment assigned"
        draw.text((230, y + 46), stats, font=small, fill=GOLD if item else MUTED)
    owned = len(profile.get("gear_owned", []))
    draw.text((54, 465), f"RELICS OWNED  {owned}/{len(gear)}", font=small, fill=MUTED)
    return _finish(image)
