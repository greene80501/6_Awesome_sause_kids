import math
import random
from pathlib import Path

import pygame

from settings import TILE_SIZE, RARITY_COLORS


ASSET_ROOT = Path(__file__).resolve().parent.parent / "assets"

_RAW_IMAGE_CACHE = {}
_FITTED_IMAGE_CACHE = {}
TILE_SURFACES = {}


WORLD_OBJECT_ASSETS = {
    "campfire": "world/interactive/campfire.png",
    "puddle": "world/decoration/puddle.png",
    "ice_rock": "world/frozen/ice_rock.png",
    "skull_pile": "world/hellscape/bone_pile.png",
    "fire_rock": "world/hellscape/flaming_rock.png",
    "lava_crack": "world/hellscape/lava_fissure.png",
    "rock_large": "world/rocks/large_rock.png",
    "rock_med": "world/rocks/medium_rock.png",
    "rock_small": "world/rocks/small_rock.png",
    "stalagmite": "world/rocks/stalagmite.png",
    "bush": "world/vegetation/bush.png",
    "cactus": "world/vegetation/cactus.png",
    "log": "world/vegetation/log.png",
}

ANIMAL_ASSETS = {
    "cow": ["animals/cows/cow_brown.png", "animals/cows/cow_white.png"],
    "sheep": "animals/sheep/sheep.png",
    "deer": "animals/deer/deer.png",
    "snow_hare": ["animals/rabbits/snow_hare.png", "animals/rabbits/snow_hare_alt.png"],
    "desert_rabbit": "animals/rabbits/snow_hare_alt.png",
}

ITEM_ASSETS = {
    "berries": "items/food/apples.png",
    "apples": "items/food/apples.png",
    "bananas": "items/food/bananas.png",
    "beer": "items/food/beer.png",
    "bell_pepper": "items/food/bell_pepper.png",
    "bread": "items/food/bread.png",
    "bread_slice": "items/food/bread_slice.png",
    "cabbage": "items/food/cabbage.png",
    "candy_canes": "items/food/candy_canes.png",
    "cheese": "items/food/cheese.png",
    "cherry_pie": "items/food/cherry_pie.png",
    "chicken": "items/food/chicken.png",
    "chili_pepper": "items/food/chili_pepper.png",
    "chips": "items/food/chips.png",
    "coffee_mug": "items/food/coffee_mug.png",
    "cooked_meat": "items/food/meat.png",
    "cupcake": "items/food/cupcake.png",
    "dried_fish": "items/food/canned_fish.png",
    "donut": "items/food/donut.png",
    "fried_egg": "items/food/fried_egg.png",
    "hamburger": "items/food/hamburger.png",
    "hot_dog": "items/food/hot_dog.png",
    "lollipop": "items/food/lollipop.png",
    "milk": "items/food/milk.png",
    "stew": "items/food/bowl_of_rice.png",
    "feast_ration": "items/food/sandwich.png",
    "pizza": "items/food/pizza.png",
    "popcorn": "items/food/popcorn.png",
    "salt": "items/food/salt.png",
    "soda_can": "items/food/soda_can.png",
    "taco": "items/food/taco.png",
    "leather_hood": "items/armor/hood.png",
    "iron_helm": "items/armor/iron_helmet.png",
    "chain_coif": "items/armor/chainmail_coif.png",
    "war_helm": "items/armor/iron_helmet.png",
    "dread_crown": "items/armor/dread_crown.png",
    "infernal_crown": "items/armor/dread_crown.png",
    "leather_vest": "items/armor/leather_vest.png",
    "chain_mail": "items/armor/leather_vest.png",
    "plate_chest": "items/armor/leather_vest.png",
    "war_plate": "items/armor/leather_vest.png",
    "warden_plate": "items/armor/leather_vest.png",
    "watermelon": "items/food/watermelon.png",
    "wrapped_sweet": "items/food/wrapped_sweet.png",
    "mushrooms": "items/food/mushrooms.png",
    "honey": "items/food/honey.png",
}

STATIC_ASSETS = {
    "chest_closed": "world/interactive/closed_loot_chest.png",
    "chest_opened": "world/interactive/opened_loot_chest.png",
    "campfire": "world/interactive/campfire.png",
    "death_pile": "world/hellscape/bone_pile.png",
}

WEAPON_ASSET_BASES = {
    "dagger": "weapons/light/dagger/dagger",
    "short_sword": "weapons/light/mini_sword/mini_sword",
    "sickle": "weapons/light/sickle/sickle",
    "rapier": "weapons/light/rapier/rapier",
    "twin_blades": "weapons/light/twinblades/twinblades",
    "sword": "weapons/balanced/sword/sword",
    "hatchet": "weapons/balanced/hatchet/hatchet",
    "broadsword": "weapons/balanced/broadsword/broadsword",
    "scimitar": "weapons/balanced/scimitar/scimitar",
    "war_sword": "weapons/balanced/war_sword/war_sword",
    "club": "weapons/heavy/club/club",
    "battle_axe": "weapons/heavy/battle_axe/battle_axe",
    "war_hammer": "weapons/heavy/war_hammer/war_hammer",
    "great_sword": "weapons/heavy/greatsword/greatsword",
    "executioner": "weapons/heavy/executioner_axe/executioner_axe",
}

WEAPON_BOSS_ASSETS = {
    "warden_blade": "weapons/boss/warden_blade/warden_blade.png",
    "hellborn_edge": "weapons/boss/hellborn_edge/hellborn_edge.png",
}

WEAPON_MATERIAL_BY_TIER = {
    0: "wood",
    1: "iron",
    2: "stone",
    3: "diamond",
    4: "diamond",
}


def _surf(w, h, alpha=True):
    surf = pygame.Surface((w, h), pygame.SRCALPHA if alpha else 0)
    surf.fill((0, 0, 0, 0) if alpha else (0, 0, 0))
    return surf


def _load_raw_image(rel_path):
    if rel_path is None:
        return None
    key = rel_path.replace("\\", "/")
    if key in _RAW_IMAGE_CACHE:
        return _RAW_IMAGE_CACHE[key]

    path = ASSET_ROOT / key
    if not path.exists():
        _RAW_IMAGE_CACHE[key] = None
        return None

    image = pygame.image.load(str(path))
    if pygame.display.get_init() and pygame.display.get_surface():
        image = image.convert_alpha()
    _RAW_IMAGE_CACHE[key] = image
    return image


def _fit_image(rel_path, width, height, pad=0, valign="center"):
    key = (rel_path, width, height, pad, valign)
    if key in _FITTED_IMAGE_CACHE:
        return _FITTED_IMAGE_CACHE[key]

    raw = _load_raw_image(rel_path)
    if raw is None:
        return None

    canvas = _surf(width, height)
    avail_w = max(1, width - pad * 2)
    avail_h = max(1, height - pad * 2)
    scale = min(avail_w / raw.get_width(), avail_h / raw.get_height())
    scaled_w = max(1, int(round(raw.get_width() * scale)))
    scaled_h = max(1, int(round(raw.get_height() * scale)))
    scaled = pygame.transform.scale(raw, (scaled_w, scaled_h))

    x = (width - scaled_w) // 2
    if valign == "bottom":
        y = height - scaled_h - pad
    elif valign == "top":
        y = pad
    else:
        y = (height - scaled_h) // 2

    canvas.blit(scaled, (x, y))
    _FITTED_IMAGE_CACHE[key] = canvas
    return canvas


def _static_asset(name, width, height, pad=0, valign="bottom"):
    return _fit_image(STATIC_ASSETS.get(name), width, height, pad=pad, valign=valign)


def get_world_object_surface(otype, width, height=None):
    if height is None:
        height = width
    valign = "center" if otype in {"puddle", "lava_crack"} else "bottom"
    return _fit_image(WORLD_OBJECT_ASSETS.get(otype), width, height, pad=1, valign=valign)


def get_item_art_surface(item_id, width, height=None):
    if height is None:
        height = width
    return _fit_image(ITEM_ASSETS.get(item_id), width, height, pad=2, valign="center")


def _resolve_item_icon(item):
    direct = ITEM_ASSETS.get(item.id)
    if direct:
        return direct
    weapon_asset = _resolve_weapon_icon(item)
    if weapon_asset:
        return weapon_asset
    if item.itype == "armor":
        if item.slot == "head":
            if item.tier >= 4:
                return ITEM_ASSETS["dread_crown"]
            if item.tier >= 2:
                return ITEM_ASSETS["chain_coif"]
            if item.tier >= 1:
                return ITEM_ASSETS["iron_helm"]
            return ITEM_ASSETS["leather_hood"]
        if item.slot == "chest":
            return ITEM_ASSETS["leather_vest"]
    if item.itype == "boss" and item.slot == "head":
        return ITEM_ASSETS["infernal_crown"]
    if item.itype == "boss" and item.slot == "chest":
        return ITEM_ASSETS["warden_plate"]
    return None


def _resolve_weapon_icon(item):
    if item.id in WEAPON_BOSS_ASSETS:
        return WEAPON_BOSS_ASSETS[item.id]
    base = WEAPON_ASSET_BASES.get(item.id)
    if base is None:
        return None
    material = WEAPON_MATERIAL_BY_TIER.get(min(item.tier, 4), "diamond")
    return f"{base}_{material}.png"


# Terrain tiles
def tile_plains(size=TILE_SIZE):
    surf = _surf(size, size, False)
    surf.fill((75, 110, 55))
    for _ in range(6):
        x = random.randint(0, size - 3)
        y = random.randint(0, size - 3)
        color = (
            65 + random.randint(-5, 5),
            100 + random.randint(-5, 5),
            48 + random.randint(-5, 5),
        )
        pygame.draw.rect(surf, color, (x, y, 2, 2))
    return surf


def tile_forest(size=TILE_SIZE):
    surf = _surf(size, size, False)
    surf.fill((45, 80, 35))
    return surf


def tile_desert(size=TILE_SIZE):
    surf = _surf(size, size, False)
    surf.fill((190, 165, 100))
    return surf


def tile_cave(size=TILE_SIZE):
    surf = _surf(size, size, False)
    surf.fill((50, 45, 40))
    return surf


def tile_hellscape(size=TILE_SIZE):
    surf = _surf(size, size, False)
    surf.fill((80, 30, 20))
    return surf


def tile_frozen(size=TILE_SIZE):
    surf = _surf(size, size, False)
    surf.fill((175, 200, 220))
    return surf


def tile_cloud(size=TILE_SIZE):
    surf = _surf(size, size, False)
    surf.fill((200, 215, 235))
    return surf


def tile_wall(biome="plains", size=TILE_SIZE):
    colors = {
        "plains": (50, 70, 40),
        "forest": (35, 55, 25),
        "desert": (155, 130, 70),
        "caves": (35, 30, 28),
        "hellscape": (60, 20, 12),
        "frozen": (130, 155, 180),
        "cloud": (160, 175, 200),
    }
    surf = _surf(size, size, False)
    color = colors.get(biome, (60, 60, 60))
    surf.fill(color)
    pygame.draw.line(surf, tuple(min(255, v + 30) for v in color), (0, 0), (size - 1, 0), 2)
    pygame.draw.line(surf, tuple(min(255, v + 30) for v in color), (0, 0), (0, size - 1), 2)
    return surf


def tile_tavern_floor(size=TILE_SIZE):
    surf = _surf(size, size, False)
    surf.fill((55, 40, 25))
    pygame.draw.line(surf, (40, 30, 18), (0, size - 1), (size - 1, size - 1), 1)
    pygame.draw.line(surf, (40, 30, 18), (size - 1, 0), (size - 1, size - 1), 1)
    return surf


def tile_tavern_wall(size=TILE_SIZE):
    surf = _surf(size, size, False)
    surf.fill((35, 25, 15))
    return surf


def get_tile(name, size=TILE_SIZE):
    key = (name, size)
    if key not in TILE_SURFACES:
        fn = {
            "plains": tile_plains,
            "forest": tile_forest,
            "desert": tile_desert,
            "caves": tile_cave,
            "hellscape": tile_hellscape,
            "frozen": tile_frozen,
            "cloud": tile_cloud,
            "tavern_floor": tile_tavern_floor,
            "tavern_wall": tile_tavern_wall,
        }.get(name, tile_plains)
        TILE_SURFACES[key] = fn(size)
    return TILE_SURFACES[key]


# Entities
def player_sprite(size=24):
    surf = _surf(size, size)
    radius = size // 2
    pygame.draw.circle(surf, (180, 140, 90), (radius, radius), radius - 1)
    pygame.draw.circle(surf, (210, 170, 120), (radius - 2, radius - 3), max(1, radius // 3))
    pygame.draw.circle(surf, (100, 70, 40), (radius, radius), radius - 1, 2)
    return surf


def enemy_sprite(color, size):
    surf = _surf(size, size)
    radius = size // 2
    pygame.draw.circle(surf, color, (radius, radius), radius - 1)
    eye_y = radius - 2
    pygame.draw.circle(surf, (255, 50, 50), (radius - 4, eye_y), 2)
    pygame.draw.circle(surf, (255, 50, 50), (radius + 2, eye_y), 2)
    pygame.draw.circle(surf, (80, 20, 20), (radius, radius), radius - 1, 2)
    return surf


def elite_sprite(color, size):
    surf = enemy_sprite(color, size)
    radius = size // 2
    pygame.draw.polygon(
        surf,
        (255, 215, 0),
        [(radius - 6, 4), (radius, 0), (radius + 6, 4), (radius + 8, 8), (radius - 8, 8)],
    )
    return surf


def animal_sprite(color, size, atype=None, variant_seed=0):
    rel_path = ANIMAL_ASSETS.get(atype)
    if isinstance(rel_path, list):
        rel_path = rel_path[variant_seed % len(rel_path)]
    asset = _fit_image(rel_path, size, size, pad=1, valign="bottom")
    if asset is not None:
        return asset

    surf = _surf(size, size)
    radius = size // 2
    pygame.draw.ellipse(surf, color, (2, radius // 2, size - 4, size // 2))
    pygame.draw.circle(surf, color, (radius, radius // 2 + 2), max(1, radius // 3))
    pygame.draw.ellipse(
        surf,
        tuple(min(255, c + 20) for c in color),
        (2, radius // 2, size - 4, size // 2),
        2,
    )
    return surf


def portal_sprite(size=48):
    surf = _surf(size, size)
    cx, cy = size // 2, size // 2
    for i in range(4):
        radius = size // 2 - i * 2
        color = (100, 60, 200)
        ring = _surf(size, size)
        pygame.draw.circle(ring, color, (cx, cy), max(1, radius), 2)
        surf.blit(ring, (0, 0))
    pygame.draw.circle(surf, (60, 20, 160), (cx, cy), size // 4)
    pygame.draw.circle(surf, (140, 100, 255), (cx, cy), size // 4, 2)
    return surf


def chest_sprite(size=32, opened=False):
    name = "chest_opened" if opened else "chest_closed"
    asset = _static_asset(name, size, size)
    if asset is not None:
        return asset

    surf = _surf(size, size)
    pygame.draw.rect(surf, (140, 90, 40), (2, size // 3, size - 4, size * 2 // 3 - 2))
    pygame.draw.rect(surf, (160, 110, 55), (2, 4, size - 4, size // 3 - 2))
    pygame.draw.rect(surf, (200, 170, 60), (size // 2 - 3, size // 2 - 2, 6, 7))
    pygame.draw.rect(surf, (80, 50, 20), (2, 4, size - 4, size - 6), 2)
    return surf


def bartender_sprite(size=32):
    surf = _surf(size, size)
    pygame.draw.rect(surf, (90, 60, 35), (size // 4, size // 3, size // 2, size * 2 // 3 - 2))
    pygame.draw.circle(surf, (210, 170, 120), (size // 2, size // 4), size // 4)
    pygame.draw.rect(surf, (40, 25, 12), (size // 2 - size // 5, 2, size * 2 // 5, size // 6))
    pygame.draw.rect(surf, (40, 25, 12), (size // 2 - size // 4, size // 6, size // 2, size // 10))
    return surf


def death_pile_sprite(size=28):
    asset = _static_asset("death_pile", size, size, pad=1)
    if asset is not None:
        return asset

    surf = _surf(size, size)
    pygame.draw.polygon(surf, (200, 50, 50), [(size // 2, 2), (size - 2, size - 2), (2, size - 2)])
    pygame.draw.polygon(surf, (255, 100, 100), [(size // 2, 2), (size - 2, size - 2), (2, size - 2)], 2)
    cx, cy = size // 2, size * 3 // 5
    pygame.draw.circle(surf, (240, 230, 210), (cx, cy), size // 5)
    pygame.draw.circle(surf, (40, 20, 20), (cx - 3, cy - 1), 2)
    pygame.draw.circle(surf, (40, 20, 20), (cx + 3, cy - 1), 2)
    return surf


def _fallback_weapon_sprite(item, size):
    surf = _surf(size, size)
    pygame.draw.line(surf, item.color, (size // 2, 2), (size // 2, size - 4), 3)
    pygame.draw.line(surf, item.color, (3, size // 2 - 2), (size - 3, size // 2 - 2), 2)
    return surf


def _fallback_armor_sprite(item, size):
    surf = _surf(size, size)
    pygame.draw.rect(surf, item.color, (3, 3, size - 6, size - 6), 0, 3)
    pygame.draw.rect(surf, (30, 20, 12), (3, 3, size - 6, size - 6), 1, 3)
    return surf


def _fallback_food_sprite(item, size):
    surf = _surf(size, size)
    pygame.draw.circle(surf, item.color, (size // 2, size // 2), size // 2 - 2)
    return surf


def loot_drop_sprite(item, size=20):
    surf = _surf(size, size)
    rarity_color = RARITY_COLORS.get(item.rarity, (180, 180, 180))

    icon = _fit_image(_resolve_item_icon(item), size, size, pad=2, valign="center")

    if icon is not None:
        surf.blit(icon, (0, 0))
    elif item.itype == "weapon" or (item.itype == "boss" and item.weapon_class):
        surf.blit(_fallback_weapon_sprite(item, size), (0, 0))
    elif item.itype == "armor" or (item.itype == "boss" and item.slot):
        surf.blit(_fallback_armor_sprite(item, size), (0, 0))
    elif item.itype == "food":
        surf.blit(_fallback_food_sprite(item, size), (0, 0))
    else:
        pygame.draw.rect(surf, item.color, (2, 2, size - 4, size - 4))

    pygame.draw.rect(surf, rarity_color, (0, 0, size, size), 1)
    return surf


def attack_arc_surface(arc_deg, radius, color=(255, 220, 80, 80)):
    size = radius * 2 + 4
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = size // 2, size // 2
    points = [(cx, cy)]
    half = math.radians(arc_deg / 2)
    steps = 20
    for i in range(steps + 1):
        angle = -half + (2 * half * i / steps)
        px = cx + math.cos(angle) * radius
        py = cy + math.sin(angle) * radius
        points.append((px, py))
    if len(points) >= 3:
        pygame.draw.polygon(surf, color, points)
    return surf


def item_slot_bg(size=48, highlighted=False, equipped=False):
    surf = _surf(size, size)
    bg = (60, 45, 30) if equipped else (40, 30, 20)
    border = (140, 110, 70) if highlighted else (70, 55, 38)
    surf.fill(bg)
    pygame.draw.rect(surf, border, (0, 0, size, size), 2)
    return surf
