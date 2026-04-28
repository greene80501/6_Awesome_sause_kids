# src/data/items_data.py
# Base definitions for all item types in the game.
# Stats are for Common rarity; multipliers applied at generation time.

WEAPONS = [
    # ── Light weapons ──
    {"id": "dagger",      "name": "Dagger",        "class": "light",    "base_dmg": 10, "tier": 0,
     "desc": "Fast but fragile. Good for kiting.",  "color": (180, 180, 200)},
    {"id": "short_sword", "name": "Short Sword",   "class": "light",    "base_dmg": 12, "tier": 0,
     "desc": "Quick cuts, low commitment.",          "color": (200, 200, 220)},
    {"id": "sickle",      "name": "Sickle",         "class": "light",    "base_dmg": 11, "tier": 1,
     "desc": "Curved blade for fast sweeps.",        "color": (160, 180, 160)},
    {"id": "rapier",      "name": "Rapier",          "class": "light",    "base_dmg": 14, "tier": 2,
     "desc": "Precision strike, narrow arc.",        "color": (210, 210, 230)},
    {"id": "twin_blades", "name": "Twin Blades",    "class": "light",    "base_dmg": 16, "tier": 3,
     "desc": "Two blades, twice the speed.",         "color": (200, 160, 120)},

    # ── Balanced weapons ──
    {"id": "sword",        "name": "Sword",          "class": "balanced", "base_dmg": 18, "tier": 0,
     "desc": "Reliable all-rounder.",                "color": (190, 190, 210)},
    {"id": "hatchet",      "name": "Hatchet",        "class": "balanced", "base_dmg": 20, "tier": 1,
     "desc": "Solid damage, decent speed.",          "color": (160, 140, 100)},
    {"id": "broadsword",   "name": "Broadsword",     "class": "balanced", "base_dmg": 22, "tier": 1,
     "desc": "Standard combat blade.",               "color": (200, 195, 220)},
    {"id": "scimitar",     "name": "Scimitar",       "class": "balanced", "base_dmg": 24, "tier": 2,
     "desc": "Curved for sweeping blows.",           "color": (220, 190, 120)},
    {"id": "war_sword",    "name": "War Sword",      "class": "balanced", "base_dmg": 26, "tier": 3,
     "desc": "Battle-tested long blade.",            "color": (180, 185, 210)},

    # ── Heavy weapons ──
    {"id": "club",         "name": "Club",           "class": "heavy",    "base_dmg": 28, "tier": 0,
     "desc": "Slow but punishing.",                  "color": (140, 100, 60)},
    {"id": "battle_axe",   "name": "Battle Axe",     "class": "heavy",    "base_dmg": 34, "tier": 1,
     "desc": "Big arc, big commitment.",             "color": (170, 140, 90)},
    {"id": "war_hammer",   "name": "War Hammer",     "class": "heavy",    "base_dmg": 38, "tier": 2,
     "desc": "Each hit costs resources.",            "color": (150, 150, 170)},
    {"id": "great_sword",  "name": "Greatsword",     "class": "heavy",    "base_dmg": 44, "tier": 3,
     "desc": "Maximum damage, minimum mobility.",   "color": (200, 205, 225)},
    {"id": "executioner",  "name": "Executioner Axe","class": "heavy",    "base_dmg": 52, "tier": 4,
     "desc": "Endgame devastation.",                 "color": (220, 100, 80)},
]

ARMOR = [
    # (slot, name, base_defense per slot: head 8, chest 18, legs 10, boots 6)
    # boots get small speed bonus
    {"id": "leather_hood",   "name": "Leather Hood",    "slot": "head",  "base_def": 8,  "tier": 0,
     "desc": "Basic head protection.", "color": (140, 100, 60)},
    {"id": "iron_helm",      "name": "Iron Helm",       "slot": "head",  "base_def": 12, "tier": 1,
     "desc": "Solid iron headpiece.", "color": (160, 165, 175)},
    {"id": "chain_coif",     "name": "Chain Coif",      "slot": "head",  "base_def": 16, "tier": 2,
     "desc": "Flexible chain protection.", "color": (140, 145, 155)},
    {"id": "war_helm",       "name": "War Helm",        "slot": "head",  "base_def": 22, "tier": 3,
     "desc": "Heavy combat helm.", "color": (130, 135, 150)},
    {"id": "dread_crown",    "name": "Dread Crown",     "slot": "head",  "base_def": 30, "tier": 4,
     "desc": "Forged in hellfire.", "color": (180, 60, 60)},

    {"id": "leather_vest",   "name": "Leather Vest",    "slot": "chest", "base_def": 18, "tier": 0,
     "desc": "Light torso armor.", "color": (130, 90, 55)},
    {"id": "chain_mail",     "name": "Chain Mail",      "slot": "chest", "base_def": 26, "tier": 1,
     "desc": "Interlocked rings.", "color": (150, 155, 165)},
    {"id": "plate_chest",    "name": "Plate Chest",     "slot": "chest", "base_def": 36, "tier": 2,
     "desc": "Heavy solid plate.", "color": (145, 148, 165)},
    {"id": "war_plate",      "name": "War Plate",       "slot": "chest", "base_def": 48, "tier": 3,
     "desc": "Battle-grade protection.", "color": (130, 133, 155)},
    {"id": "infernal_plate", "name": "Infernal Plate",  "slot": "chest", "base_def": 65, "tier": 4,
     "desc": "Grants near-immunity.", "color": (170, 55, 55)},

    {"id": "leather_legs",   "name": "Leather Leggings","slot": "legs",  "base_def": 10, "tier": 0,
     "desc": "Basic leg coverage.", "color": (120, 85, 50)},
    {"id": "iron_greaves",   "name": "Iron Greaves",    "slot": "legs",  "base_def": 15, "tier": 1,
     "desc": "Iron leg armor.", "color": (155, 158, 168)},
    {"id": "chain_legs",     "name": "Chain Leggings",  "slot": "legs",  "base_def": 20, "tier": 2,
     "desc": "Flexible chain legs.", "color": (138, 142, 152)},
    {"id": "plate_legs",     "name": "Plate Leggings",  "slot": "legs",  "base_def": 28, "tier": 3,
     "desc": "Full plate leg armor.", "color": (128, 132, 150)},
    {"id": "dread_legs",     "name": "Dread Legs",      "slot": "legs",  "base_def": 38, "tier": 4,
     "desc": "Hellforged legs.", "color": (165, 50, 50)},

    {"id": "worn_boots",     "name": "Worn Boots",      "slot": "boots", "base_def": 5,  "tier": 0,
     "speed_bonus": 0,   "desc": "Barely holding together.", "color": (110, 78, 45)},
    {"id": "leather_boots",  "name": "Leather Boots",   "slot": "boots", "base_def": 8,  "tier": 1,
     "speed_bonus": 5,   "desc": "Light and comfortable.", "color": (130, 92, 58)},
    {"id": "iron_boots",     "name": "Iron Boots",      "slot": "boots", "base_def": 12, "tier": 2,
     "speed_bonus": 0,   "desc": "Heavy but protective.", "color": (148, 152, 162)},
    {"id": "swift_boots",    "name": "Swift Boots",     "slot": "boots", "base_def": 10, "tier": 3,
     "speed_bonus": 18,  "desc": "Enchanted for speed.", "color": (70, 140, 200)},
    {"id": "dread_boots",    "name": "Dread Boots",     "slot": "boots", "base_def": 20, "tier": 4,
     "speed_bonus": 10,  "desc": "Infernal-forged stompers.", "color": (160, 45, 45)},
]

FOOD = [
    {"id": "berries",     "name": "Berries",      "hunger": 15, "stack": True, "tier": 0,
     "desc": "Small snack. Better than nothing.", "color": (160, 80, 140)},
    {"id": "apples",      "name": "Apples",       "hunger": 16, "stack": True, "tier": 0,
     "desc": "Fresh fruit for the road.",         "color": (190, 80, 60)},
    {"id": "bananas",     "name": "Bananas",      "hunger": 18, "stack": True, "tier": 0,
     "desc": "Easy to carry and quick to eat.",   "color": (220, 200, 80)},
    {"id": "bread",       "name": "Bread",        "hunger": 25, "stack": True, "tier": 0,
     "desc": "Standard ration.",                  "color": (200, 160, 90)},
    {"id": "bread_slice", "name": "Bread Slice",  "hunger": 12, "stack": True, "tier": 0,
     "desc": "Not much, but it helps.",           "color": (210, 175, 100)},
    {"id": "chips",       "name": "Chips",        "hunger": 14, "stack": True, "tier": 0,
     "desc": "Salty tavern snack.",               "color": (220, 185, 90)},
    {"id": "milk",        "name": "Milk",         "hunger": 15, "stack": True, "tier": 0,
     "desc": "Simple, filling, and cheap.",       "color": (220, 220, 215)},
    {"id": "cabbage",     "name": "Cabbage",      "hunger": 20, "stack": True, "tier": 0,
     "desc": "Rough field food.",                 "color": (120, 180, 100)},
    {"id": "cooked_meat", "name": "Cooked Meat",  "hunger": 40, "stack": True, "tier": 1,
     "desc": "Hearty and filling.",               "color": (185, 100, 60)},
    {"id": "dried_fish",  "name": "Dried Fish",   "hunger": 30, "stack": True, "tier": 1,
     "desc": "Preserved and portable.",           "color": (150, 140, 100)},
    {"id": "beer",        "name": "Beer",         "hunger": 12, "stack": True, "tier": 1,
     "desc": "Liquid courage and calories.",      "color": (190, 140, 55)},
    {"id": "cheese",      "name": "Cheese",       "hunger": 24, "stack": True, "tier": 1,
     "desc": "Dense and dependable.",             "color": (230, 210, 100)},
    {"id": "chicken",     "name": "Chicken",      "hunger": 34, "stack": True, "tier": 1,
     "desc": "A better meal than jerky.",         "color": (205, 150, 85)},
    {"id": "coffee_mug",  "name": "Coffee Mug",   "hunger": 10, "stack": True, "tier": 1,
     "desc": "Not food, but it keeps you sharp.", "color": (120, 90, 65)},
    {"id": "mushrooms",   "name": "Mushrooms",    "hunger": 22, "stack": True, "tier": 1,
     "desc": "Forest-picked and surprisingly good.","color": (170, 135, 95)},
    {"id": "stew",        "name": "Stew Bowl",    "hunger": 55, "stack": True, "tier": 2,
     "desc": "Thick and nourishing.",             "color": (170, 120, 70)},
    {"id": "bell_pepper", "name": "Bell Pepper",  "hunger": 18, "stack": True, "tier": 2,
     "desc": "Bright, crisp travel produce.",     "color": (220, 70, 60)},
    {"id": "chili_pepper","name": "Chili Pepper", "hunger": 12, "stack": True, "tier": 2,
     "desc": "Hot enough to wake the dead.",      "color": (215, 60, 40)},
    {"id": "fried_egg",   "name": "Fried Egg",    "hunger": 20, "stack": True, "tier": 2,
     "desc": "Light but efficient.",              "color": (245, 220, 120)},
    {"id": "honey",       "name": "Honey",        "hunger": 22, "stack": True, "tier": 2,
     "desc": "Sticky energy in a jar.",           "color": (210, 155, 70)},
    {"id": "hot_dog",     "name": "Hot Dog",      "hunger": 32, "stack": True, "tier": 2,
     "desc": "Fast hot meal.",                    "color": (200, 120, 70)},
    {"id": "pizza",       "name": "Pizza",        "hunger": 44, "stack": True, "tier": 2,
     "desc": "Suspiciously fancy field rations.", "color": (220, 150, 90)},
    {"id": "taco",        "name": "Taco",         "hunger": 28, "stack": True, "tier": 2,
     "desc": "Portable and satisfying.",          "color": (210, 165, 80)},
    {"id": "watermelon",  "name": "Watermelon",   "hunger": 26, "stack": True, "tier": 2,
     "desc": "Heavy, refreshing, and messy.",     "color": (90, 180, 90)},
    {"id": "feast_ration","name": "Feast Ration", "hunger": 75, "stack": True, "tier": 3,
     "desc": "High-quality traveler's meal.",     "color": (220, 180, 100)},
    {"id": "candy_canes", "name": "Candy Canes",  "hunger": 18, "stack": True, "tier": 3,
     "desc": "Pure sugar and bad judgment.",      "color": (220, 80, 80)},
    {"id": "cherry_pie",  "name": "Cherry Pie",   "hunger": 48, "stack": True, "tier": 3,
     "desc": "A rare comfort in harsh places.",   "color": (190, 80, 90)},
    {"id": "cupcake",     "name": "Cupcake",      "hunger": 24, "stack": True, "tier": 3,
     "desc": "Small, sweet, and expensive.",      "color": (220, 150, 170)},
    {"id": "donut",       "name": "Donut",        "hunger": 22, "stack": True, "tier": 3,
     "desc": "Dense sugar ring.",                 "color": (190, 130, 90)},
    {"id": "hamburger",   "name": "Hamburger",    "hunger": 52, "stack": True, "tier": 3,
     "desc": "A full meal in one hand.",          "color": (175, 120, 75)},
    {"id": "lollipop",    "name": "Lollipop",     "hunger": 10, "stack": True, "tier": 3,
     "desc": "Mostly morale, barely nutrition.",  "color": (210, 90, 150)},
    {"id": "popcorn",     "name": "Popcorn",      "hunger": 16, "stack": True, "tier": 3,
     "desc": "Light, salty, and oddly lucky.",    "color": (230, 210, 150)},
    {"id": "salt",        "name": "Salt",         "hunger": 4,  "stack": True, "tier": 3,
     "desc": "Technically edible. Barely.",       "color": (215, 215, 215)},
    {"id": "soda_can",    "name": "Soda Can",     "hunger": 12, "stack": True, "tier": 3,
     "desc": "All fizz, no discipline.",          "color": (180, 70, 70)},
    {"id": "wrapped_sweet","name": "Wrapped Sweet","hunger": 14, "stack": True, "tier": 3,
     "desc": "Pocket sugar for desperate runs.",  "color": (200, 120, 180)},
]

BOSS_LOOT = [
    {"id": "warden_blade",  "name": "Warden Blade",   "type": "weapon", "class": "balanced",
     "base_dmg": 55, "rarity": "Legendary", "tier": 5,
     "desc": "The Warden's own weapon. Formidable.",  "color": (80, 200, 180)},
    {"id": "warden_plate",  "name": "Warden Plate",   "type": "armor",  "slot": "chest",
     "base_def": 80, "rarity": "Legendary", "tier": 5,
     "desc": "Heavy armor of the dungeon guardian.", "color": (90, 190, 170)},
    {"id": "hellborn_edge", "name": "Hellborn Edge",  "type": "weapon", "class": "heavy",
     "base_dmg": 72, "rarity": "Legendary", "tier": 5,
     "desc": "Blazing blade of the Hellborn.",       "color": (255, 100, 50)},
    {"id": "infernal_crown","name": "Infernal Crown", "type": "armor",  "slot": "head",
     "base_def": 42, "rarity": "Legendary", "tier": 5,
     "desc": "Crown forged in hellfire.",             "color": (255, 80, 30)},
]

# Build lookup dicts
WEAPONS_BY_ID = {w["id"]: w for w in WEAPONS}
ARMOR_BY_ID   = {a["id"]: a for a in ARMOR}
FOOD_BY_ID    = {f["id"]: f for f in FOOD}
BOSS_BY_ID    = {b["id"]: b for b in BOSS_LOOT}

def get_weapons_for_tier(max_tier):
    return [w for w in WEAPONS if w["tier"] <= max_tier]

def get_armor_for_tier(max_tier):
    return [a for a in ARMOR if a["tier"] <= max_tier]

def get_food_for_tier(max_tier):
    return [f for f in FOOD if f["tier"] <= max_tier]
