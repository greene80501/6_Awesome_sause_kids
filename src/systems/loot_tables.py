# src/systems/loot_tables.py
import random
from settings import (RARITIES, RARITY_WEIGHTS_EARLY,
                       RARITY_WEIGHTS_MID, RARITY_WEIGHTS_LATE)
from src.data.items_data import (get_weapons_for_tier, get_armor_for_tier,
                                   get_food_for_tier, BOSS_LOOT)
from src.systems.item import Item


def _rarity_weights(tier):
    if tier <= 1:
        return RARITY_WEIGHTS_EARLY
    elif tier <= 3:
        return RARITY_WEIGHTS_MID
    else:
        return RARITY_WEIGHTS_LATE


def roll_rarity(tier):
    return random.choices(RARITIES, weights=_rarity_weights(tier), k=1)[0]


def make_weapon(tier, rarity=None):
    pool = get_weapons_for_tier(min(tier, 4))
    if not pool:
        pool = get_weapons_for_tier(0)
    data = random.choice(pool)
    r = rarity or roll_rarity(tier)
    return Item("weapon", data, rarity=r)


def make_armor(tier, rarity=None, slot=None):
    pool = get_armor_for_tier(min(tier, 4))
    if slot:
        pool = [a for a in pool if a["slot"] == slot]
    if not pool:
        pool = get_armor_for_tier(0)
    data = random.choice(pool)
    r = rarity or roll_rarity(tier)
    return Item("armor", data, rarity=r)


def make_food(tier, qty=1):
    pool = get_food_for_tier(min(tier, 3))
    data = random.choice(pool)
    item = Item("food", data)
    item.quantity = qty
    return item


def make_boss_loot(boss_id):
    """Returns 2-3 items from the boss loot table for the given boss."""
    if boss_id == 1:
        pool = [b for b in BOSS_LOOT if b["id"] in ("warden_blade", "warden_plate")]
    else:
        pool = [b for b in BOSS_LOOT if b["id"] in ("hellborn_edge", "infernal_crown")]
    items = []
    for data in pool:
        items.append(Item("boss", data))
    return items


def roll_enemy_drop(loot_bonus, tier):
    """
    Returns a list of Items from an enemy kill.
    loot_bonus: int 0-3 from enemy definition
    """
    drops = []
    # Coin drop handled separately (returns int)
    # Gear drop chance scales with tier and loot_bonus
    gear_chance = 0.08 + 0.04 * loot_bonus + 0.02 * tier
    if random.random() < gear_chance:
        if random.random() < 0.5:
            drops.append(make_weapon(tier))
        else:
            drops.append(make_armor(tier))

    # Food drop chance
    food_chance = 0.15 + 0.05 * loot_bonus
    if random.random() < food_chance:
        drops.append(make_food(tier, qty=random.randint(1, 2)))

    return drops


def roll_enemy_coins(loot_bonus, tier):
    base = random.randint(1, 4) + loot_bonus
    tier_bonus = random.randint(0, tier * 2)
    return base + tier_bonus


def roll_animal_drop(animal_data):
    if random.random() < animal_data["drop_chance"]:
        from src.data.items_data import FOOD_BY_ID
        food_id = animal_data["drop"]
        data = FOOD_BY_ID.get(food_id)
        if data:
            item = Item("food", data)
            item.quantity = random.randint(1, 2)
            return item
    return None


def roll_loot_node(tier):
    """Placed loot chest / node in the world."""
    items = []
    num = random.randint(1, 2)
    for _ in range(num):
        r = random.random()
        if r < 0.45:
            items.append(make_weapon(tier))
        elif r < 0.85:
            items.append(make_armor(tier))
        else:
            items.append(make_food(tier, qty=random.randint(1, 3)))
    return items


def roll_objective_reward(tier):
    """High-value reward for completing a world objective."""
    rarity = roll_rarity(tier + 1)   # bump tier for better loot
    items = []
    items.append(make_weapon(tier + 1, rarity=rarity))
    items.append(make_armor(tier + 1, rarity=rarity))
    items.append(make_food(tier, qty=random.randint(2, 4)))
    coins = random.randint(20 + tier * 8, 40 + tier * 15)
    return items, coins
