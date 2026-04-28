# src/data/enemies_data.py
# Enemy base stats. Actual stats scale by tier in the generator.

# Each entry:  id, name, hp, touch_dmg, speed, aggro_range, size, color, loot_tier_bonus
# speed in px/s,  touch_dmg per second of contact

ENEMY_TYPES = {
    # ── Universal (can appear anywhere) ──
    "goblin": {
        "name": "Goblin", "hp": 22, "touch_dmg": 8, "speed": 88,
        "aggro": 160, "size": 18, "color": (80, 140, 60), "loot_bonus": 0,
        "biomes": ["plains", "forest", "caves", "hellscape"],
    },
    "skeleton": {
        "name": "Skeleton", "hp": 30, "touch_dmg": 12, "speed": 70,
        "aggro": 180, "size": 20, "color": (210, 200, 180), "loot_bonus": 0,
        "biomes": ["plains", "forest", "caves", "frozen"],
    },
    "zombie": {
        "name": "Zombie", "hp": 45, "touch_dmg": 10, "speed": 55,
        "aggro": 130, "size": 22, "color": (80, 120, 70), "loot_bonus": 0,
        "biomes": ["plains", "forest", "hellscape"],
    },

    # ── Forest ──
    "wolf": {
        "name": "Wolf", "hp": 35, "touch_dmg": 14, "speed": 115,
        "aggro": 200, "size": 20, "color": (80, 80, 100), "loot_bonus": 1,
        "biomes": ["forest"],
    },
    "forest_troll": {
        "name": "Forest Troll", "hp": 75, "touch_dmg": 18, "speed": 60,
        "aggro": 150, "size": 30, "color": (55, 110, 55), "loot_bonus": 1,
        "biomes": ["forest"],
    },

    # ── Desert ──
    "scorpion": {
        "name": "Scorpion", "hp": 28, "touch_dmg": 16, "speed": 95,
        "aggro": 140, "size": 18, "color": (180, 140, 60), "loot_bonus": 0,
        "biomes": ["desert"],
    },
    "sand_wraith": {
        "name": "Sand Wraith", "hp": 55, "touch_dmg": 20, "speed": 75,
        "aggro": 220, "size": 24, "color": (200, 180, 100), "loot_bonus": 1,
        "biomes": ["desert"],
    },

    # ── Caves ──
    "bat": {
        "name": "Bat", "hp": 15, "touch_dmg": 7, "speed": 130,
        "aggro": 180, "size": 14, "color": (60, 40, 80), "loot_bonus": 0,
        "biomes": ["caves"],
    },
    "cave_spider": {
        "name": "Cave Spider", "hp": 40, "touch_dmg": 15, "speed": 105,
        "aggro": 160, "size": 20, "color": (70, 50, 80), "loot_bonus": 1,
        "biomes": ["caves"],
    },
    "stone_golem": {
        "name": "Stone Golem", "hp": 110, "touch_dmg": 22, "speed": 45,
        "aggro": 120, "size": 34, "color": (130, 125, 120), "loot_bonus": 2,
        "biomes": ["caves"],
    },

    # ── Hellscape ──
    "imp": {
        "name": "Imp", "hp": 35, "touch_dmg": 18, "speed": 110,
        "aggro": 190, "size": 18, "color": (200, 70, 50), "loot_bonus": 1,
        "biomes": ["hellscape"],
    },
    "demon": {
        "name": "Demon", "hp": 80, "touch_dmg": 25, "speed": 80,
        "aggro": 200, "size": 28, "color": (180, 45, 35), "loot_bonus": 2,
        "biomes": ["hellscape"],
    },
    "hell_knight": {
        "name": "Hell Knight", "hp": 140, "touch_dmg": 30, "speed": 65,
        "aggro": 220, "size": 32, "color": (160, 30, 20), "loot_bonus": 3,
        "biomes": ["hellscape"],
    },

    # ── Frozen ──
    "frost_wolf": {
        "name": "Frost Wolf", "hp": 50, "touch_dmg": 16, "speed": 100,
        "aggro": 200, "size": 22, "color": (140, 180, 220), "loot_bonus": 1,
        "biomes": ["frozen"],
    },
    "ice_wraith": {
        "name": "Ice Wraith", "hp": 65, "touch_dmg": 20, "speed": 85,
        "aggro": 210, "size": 24, "color": (180, 210, 240), "loot_bonus": 2,
        "biomes": ["frozen"],
    },
    "frost_giant": {
        "name": "Frost Giant", "hp": 160, "touch_dmg": 28, "speed": 50,
        "aggro": 160, "size": 36, "color": (150, 195, 235), "loot_bonus": 3,
        "biomes": ["frozen"],
    },

    # ── Cloud ──
    "harpy": {
        "name": "Harpy", "hp": 38, "touch_dmg": 14, "speed": 120,
        "aggro": 230, "size": 20, "color": (180, 160, 200), "loot_bonus": 1,
        "biomes": ["cloud"],
    },
    "storm_elemental": {
        "name": "Storm Elemental", "hp": 90, "touch_dmg": 24, "speed": 90,
        "aggro": 240, "size": 26, "color": (100, 140, 210), "loot_bonus": 2,
        "biomes": ["cloud"],
    },
}

# Passive/wildlife animals per biome
ANIMAL_TYPES = {
    "cow": {
        "name": "Cow", "hp": 40, "speed": 60, "size": 24,
        "color": (210, 195, 170), "flee_range": 120,
        "drop_chance": 0.7, "drop": "cooked_meat",
        "biomes": ["plains", "forest"],
    },
    "sheep": {
        "name": "Sheep", "hp": 30, "speed": 65, "size": 20,
        "color": (230, 225, 215), "flee_range": 130,
        "drop_chance": 0.6, "drop": "cooked_meat",
        "biomes": ["plains"],
    },
    "deer": {
        "name": "Deer", "hp": 35, "speed": 110, "size": 22,
        "color": (180, 145, 95), "flee_range": 180,
        "drop_chance": 0.65, "drop": "cooked_meat",
        "biomes": ["forest", "plains"],
    },
    "snow_hare": {
        "name": "Snow Hare", "hp": 15, "speed": 130, "size": 14,
        "color": (235, 235, 240), "flee_range": 200,
        "drop_chance": 0.5, "drop": "dried_fish",
        "biomes": ["frozen"],
    },
    "desert_rabbit": {
        "name": "Desert Hare", "hp": 15, "speed": 120, "size": 14,
        "color": (200, 175, 110), "flee_range": 190,
        "drop_chance": 0.4, "drop": "dried_fish",
        "biomes": ["desert"],
    },
}

# Elites are buffed versions of regular enemies
ELITE_MULT = {"hp": 3.0, "touch_dmg": 1.8, "speed": 1.15, "size_add": 8}

# Tier scaling: stats multiply by this per tier above 0
TIER_HP_MULT    = 1.35
TIER_DMG_MULT   = 1.25
TIER_SPEED_MULT = 1.08

def get_enemies_for_biome(biome):
    return {k: v for k, v in ENEMY_TYPES.items() if biome in v["biomes"]}

def get_animals_for_biome(biome):
    return {k: v for k, v in ANIMAL_TYPES.items() if biome in v["biomes"]}
