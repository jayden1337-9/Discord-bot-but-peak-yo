"""Validated operations for social features."""
from typing import Any

MAX_STACK = 10**18
MAX_GOLD = 10**18


def ensure_social_data(data: dict[str, Any]) -> None:
    data.setdefault("guilds", {})
    data.setdefault("trades", {})
    data.setdefault("market", {})
    data.setdefault("social_sequence", 0)


def valid_stack(profile: dict[str, Any], item: str, amount: int) -> bool:
    inventory = profile.get("inventory", {})
    return 1 <= amount <= MAX_STACK and isinstance(inventory, dict) and int(inventory.get(item, 0)) >= amount


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
