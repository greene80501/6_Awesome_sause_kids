# src/systems/economy.py
import random
from src.systems.loot_tables import make_weapon, make_armor, make_food
from src.data.items_data import get_food_for_tier


def build_shop_stock(boss_kills, tier):
    """
    Returns a list of Items available in the bartender's shop.
    Quality is gated by boss kills (0 = basic, 1 = mid, 2 = good).
    """
    stock = []
    shop_tier = min(boss_kills, 2)

    # Always: some food
    food_pool = get_food_for_tier(min(shop_tier + 1, 3))
    random.shuffle(food_pool)
    for food_data in food_pool[:4 + shop_tier * 2]:
        from src.systems.item import Item
        item = Item("food", food_data)
        item.quantity = random.randint(3, 8)
        stock.append(item)

    # Always: 1-2 basic weapons
    num_weapons = 2 + shop_tier
    rarities_pool = ["Common", "Common", "Good"] if shop_tier == 0 else \
                    ["Common", "Good", "Good", "Rare"] if shop_tier == 1 else \
                    ["Good", "Rare", "Rare", "Epic"]
    for _ in range(num_weapons):
        r = random.choice(rarities_pool)
        stock.append(make_weapon(min(shop_tier * 2, 4), rarity=r))

    # Always: 2-3 armor pieces
    num_armor = 2 + shop_tier
    for _ in range(num_armor):
        r = random.choice(rarities_pool)
        stock.append(make_armor(min(shop_tier * 2, 4), rarity=r))

    return stock


def sell_price(item):
    return item.sell_value


def buy_price(item):
    return item.buy_value


def repair_price(item):
    return item.repair_cost()


def can_afford(player_data, cost):
    return player_data["coins"] >= cost


def deduct_coins(player_data, cost):
    player_data["coins"] = max(0, player_data["coins"] - cost)


def add_coins(player_data, amount):
    player_data["coins"] += amount
