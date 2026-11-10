"""Inventory operations shared by gameplay commands.

Symbolic stacks represent quantities beyond Python's practical materialized
inventory limits. Ordinary stacks are always consumed first.
"""


def has_item(profile, key, amount):
    amount = int(amount)
    if amount < 1:
        return False
    normal = int(profile.get("inventory", {}).get(key, 0))
    if normal >= amount:
        return True
    symbolic = profile.get("symbolic_rewards", {}).get("inventory", {})
    return int(symbolic.get(key, 0)) > 0


def consume_item(profile, key, amount):
    """Consume an item without partial loss when the requested amount is unavailable."""
    amount = int(amount)
    if amount < 1:
        return False

    inventory = profile.setdefault("inventory", {})
    normal = max(0, int(inventory.get(key, 0)))
    take_normal = min(normal, amount)
    remaining = amount - take_normal

    symbolic_rewards = profile.setdefault("symbolic_rewards", {})
    symbolic_inventory = symbolic_rewards.setdefault("inventory", {})
    symbolic_spent = symbolic_rewards.setdefault("inventory_spent", {})
    has_symbolic_stack = int(symbolic_inventory.get(key, 0)) > 0

    # Validate the entire transaction before changing either balance.
    if remaining and not has_symbolic_stack:
        return False

    new_normal = normal - take_normal
    if new_normal:
        inventory[key] = new_normal
    else:
        inventory.pop(key, None)

    if remaining:
        symbolic_spent[key] = int(symbolic_spent.get(key, 0)) + remaining
    return True
