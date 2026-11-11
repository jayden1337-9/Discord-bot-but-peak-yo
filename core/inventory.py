"""Finite inventory operations with all-or-nothing item consumption."""


def has_item(profile, key, amount):
    amount = int(amount)
    if amount < 1:
        return False
    return int(profile.get("inventory", {}).get(key, 0)) >= amount


def consume_item(profile, key, amount):
    """Consume an item without partial loss when the requested amount is unavailable."""
    amount = int(amount)
    if amount < 1:
        return False
    inventory = profile.setdefault("inventory", {})
    current = max(0, int(inventory.get(key, 0)))
    if current < amount:
        return False
    remaining = current - amount
    if remaining:
        inventory[key] = remaining
    else:
        inventory.pop(key, None)
    return True
