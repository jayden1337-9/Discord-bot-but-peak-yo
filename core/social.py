"""Validated operations for social features."""
from typing import Any

MAX_STACK = 10**18
MAX_GOLD = 10**18


def ensure_social_data(data: dict[str, Any]) -> None:
    for key in ("guilds", "trades", "market"):
        data.setdefault(key, {})
        if not isinstance(data[key], dict):
            raise ValueError(f"Social database collection '{key}' is invalid")
    data.setdefault("social_sequence", 0)
    try:
        data["social_sequence"] = max(0, int(data["social_sequence"]))
    except (TypeError, ValueError) as exc:
        raise ValueError("Social sequence counter is invalid") from exc


def valid_stack(profile: dict[str, Any], item: str, amount: int) -> bool:
    inventory = profile.get("inventory", {})
    if not 1 <= amount <= MAX_STACK or not isinstance(inventory, dict):
        return False
    try:
        return int(inventory.get(item, 0)) >= amount
    except (TypeError, ValueError):
        return False


def next_id(data: dict[str, Any], prefix: str) -> str:
    data["social_sequence"] = int(data.get("social_sequence", 0)) + 1
    return f"{prefix}{data['social_sequence']:06d}"


def transfer_item(source: dict[str, Any], target: dict[str, Any], item: str, amount: int) -> None:
    if not valid_stack(source, item, amount):
        raise ValueError("Insufficient transferable items")
    target_inventory = target.setdefault("inventory", {})
    if int(target_inventory.get(item, 0)) + amount > MAX_STACK:
        raise ValueError("Recipient stack limit would be exceeded")
    source["inventory"][item] -= amount
    if source["inventory"][item] == 0:
        del source["inventory"][item]
    target_inventory[item] = int(target_inventory.get(item, 0)) + amount


def transfer_gold(source: dict[str, Any], target: dict[str, Any], amount: int) -> None:
    if amount < 1 or amount > MAX_GOLD or int(source.get("gold", 0)) < amount:
        raise ValueError("Insufficient Gold")
    if int(target.get("gold", 0)) + amount > MAX_GOLD:
        raise ValueError("Recipient Gold limit would be exceeded")
    source["gold"] = int(source.get("gold", 0)) - amount
    target["gold"] = int(target.get("gold", 0)) + amount


def award_guild_xp(data: dict[str, Any], server_id: int, user_id: int, amount: int) -> tuple[int, int] | None:
    """Award guild XP to the member's guild; return (new level, levels gained)."""
    if amount <= 0:
        return None
    for guild in data.get("guilds", {}).values():
        if guild.get("server_id") != server_id or str(user_id) not in guild.get("members", []):
            continue
        old_level = max(1, min(20, int(guild.get("level", 1))))
        guild["level"] = old_level
        guild["xp"] = max(0, int(guild.get("xp", 0))) + int(amount)
        while int(guild["level"]) < 20 and guild["xp"] >= int(guild["level"]) * 500:
            guild["xp"] -= int(guild["level"]) * 500
            guild["level"] += 1
        return int(guild["level"]), int(guild["level"]) - old_level
    return None


def guild_member_limit(guild: dict[str, Any]) -> int:
    """Guilds start with 10 slots and unlock up to 20 through levels."""
    return min(20, 10 + max(1, int(guild.get("level", 1))) // 2)
