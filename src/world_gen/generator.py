# src/world_gen/generator.py
import random
import math
import pygame
from settings import WORLD_W, WORLD_H, TILE_SIZE, TIER_THRESHOLDS
from src.sprite_factory import get_tile, get_world_object_surface
from src.world_gen.biomes import (BIOMES, ALL_BIOMES, OBJECT_COLORS,
                                   OBJECT_SIZES, OBJECT_BLOCKING)
from src.data.enemies_data import get_enemies_for_biome, get_animals_for_biome


# ─────────────────────────────────────────────
#  Points of Interest definitions
# ─────────────────────────────────────────────
POI_TYPES = {
    "watchtower": {
        "display":    "Abandoned Watchtower",
        "structure":  "tower",
        "enemies":    3,  "elite": True,  "loot_nodes": 1,
        "biomes":     ["plains", "forest", "desert", "frozen"],
    },
    "graveyard": {
        "display":    "Overgrown Graveyard",
        "structure":  "graveyard",
        "enemies":    4,  "elite": False, "loot_nodes": 1,
        "biomes":     ["plains", "forest", "hellscape"],
    },
    "bandit_camp": {
        "display":    "Bandit Camp",
        "structure":  "camp",
        "enemies":    5,  "elite": True,  "loot_nodes": 1,
        "biomes":     ["plains", "forest", "desert"],
    },
    "ruined_shrine": {
        "display":    "Ruined Shrine",
        "structure":  "shrine",
        "enemies":    2,  "elite": True,  "loot_nodes": 2,
        "biomes":     ["plains", "forest", "frozen", "cloud"],
    },
}


# ─────────────────────────────────────────────
#  World data structure (serializable)
# ─────────────────────────────────────────────
class WorldData:
    def __init__(self):
        self.world_id   = random.randint(10000, 99999)
        self.name       = f"World-{self.world_id}"
        self.seed       = random.randint(0, 2**31)
        self.biome      = "plains"
        self.world_type = "resource"
        self.tier       = 0
        self.w          = WORLD_W
        self.h          = WORLD_H
        self.spawn_x    = 0
        self.spawn_y    = 0
        self.portal_x   = 0
        self.portal_y   = 0
        # Fog: 0=hidden, 1=explored, 2=visible (transient)
        self.fog = [[0] * WORLD_H for _ in range(WORLD_W)]
        # Objects: list of {"type", "x", "y", "w", "h", "blocking"}
        self.objects       = []
        self.enemy_spawns  = []
        self.animal_spawns = []
        self.loot_nodes    = []
        # Named points of interest: list of {"name", "x", "y"}
        self.pois          = []
        self.objective     = None
        self.important_kills = []
        self.dropped_items = []
        self.death_pile    = None
        self.revisitable   = True

    def to_dict(self):
        return {
            "world_id": self.world_id, "name": self.name,
            "seed": self.seed, "biome": self.biome,
            "world_type": self.world_type, "tier": self.tier,
            "w": self.w, "h": self.h,
            "spawn_x": self.spawn_x, "spawn_y": self.spawn_y,
            "portal_x": self.portal_x, "portal_y": self.portal_y,
            "fog": self.fog, "objects": self.objects,
            "enemy_spawns": self.enemy_spawns,
            "animal_spawns": self.animal_spawns,
            "loot_nodes": self.loot_nodes,
            "pois": self.pois,
            "objective": self.objective,
            "important_kills": self.important_kills,
            "dropped_items": self.dropped_items,
            "death_pile": self.death_pile,
            "revisitable": self.revisitable,
        }

    @classmethod
    def from_dict(cls, d):
        w = cls()
        for k, v in d.items():
            setattr(w, k, v)
        if not hasattr(w, "pois"):   # backwards compat with old saves
            w.pois = []
        return w


# ─────────────────────────────────────────────
#  Main generator
# ─────────────────────────────────────────────
def get_tier(worlds_cleared, boss_kills):
    base = 0
    for i, thresh in enumerate(TIER_THRESHOLDS):
        if worlds_cleared >= thresh:
            base = i
    return base + boss_kills


def pick_world_type():
    return random.choices(["resource", "combat", "objective"],
                          weights=[40, 40, 20])[0]


def generate_world(worlds_cleared=0, boss_kills=0, biome=None):
    from src.config import get_config
    config = get_config()
    wc = config.get("world", {})

    wd  = WorldData()
    rng = random.Random(wd.seed)

    wd.tier       = get_tier(worlds_cleared, boss_kills) + wc.get("loot_tier_bonus", 0)
    wd.biome      = biome or rng.choice(ALL_BIOMES)
    wd.world_type = pick_world_type()

    bdata = BIOMES[wd.biome]

    # ── Portal + spawn ──
    margin = 4
    wd.portal_x = rng.randint(margin, margin + 4) * TILE_SIZE + TILE_SIZE // 2
    wd.portal_y = rng.randint(wd.h // 2 - 4, wd.h // 2 + 4) * TILE_SIZE + TILE_SIZE // 2
    wd.spawn_x  = wd.portal_x + TILE_SIZE * 2
    wd.spawn_y  = wd.portal_y

    spawn_col = wd.spawn_x // TILE_SIZE
    spawn_row = wd.spawn_y // TILE_SIZE

    # ── Scatter blocking/decorative objects ──
    density   = bdata["obstacle_density"]
    obj_types = bdata["scatter_objects"]
    num_objs  = int(wd.w * wd.h * density)

    blocked_positions = set()
    for _ in range(num_objs):
        otype = rng.choice(obj_types)
        col   = rng.randint(0, wd.w - 1)
        row   = rng.randint(0, wd.h - 1)
        if abs(col - spawn_col) < 5 and abs(row - spawn_row) < 5:
            continue
        obj_w, obj_h = OBJECT_SIZES.get(otype, (24, 24))
        cx = col * TILE_SIZE + TILE_SIZE // 2
        cy = row * TILE_SIZE + TILE_SIZE // 2
        blocking = OBJECT_BLOCKING.get(otype, False)
        wd.objects.append({"type": otype, "x": cx, "y": cy,
                            "w": obj_w, "h": obj_h, "blocking": blocking})
        if blocking:
            blocked_positions.add((col, row))

    # ── New world features ──
    _place_ruins(wd, rng, blocked_positions, spawn_col, config)
    _place_enemy_camps(wd, rng, blocked_positions, spawn_col, config)
    _place_decorative_scatter(wd, rng, bdata, spawn_col, spawn_row, config)
    _place_pois(wd, rng, blocked_positions, spawn_col, config)

    # ── Enemy spawns ──
    enemy_pool = get_enemies_for_biome(wd.biome)
    if enemy_pool:
        base_count       = 5 + wd.tier * 3
        type_mult        = {"resource": 0.6, "combat": 1.5, "objective": 1.2}
        biome_mult       = bdata["threat_budget_mult"]
        enemy_count_mult = wc.get("enemy_count_mult", 1.0)
        num_enemies      = int(base_count * type_mult[wd.world_type]
                               * biome_mult * enemy_count_mult)
        num_elites    = max(0, num_enemies // 6)
        spawn_col_min = 8
        etypes        = list(enemy_pool.keys())

        for i in range(num_enemies):
            etype = rng.choice(etypes)
            col   = rng.randint(spawn_col_min, wd.w - 2)
            row   = rng.randint(2, wd.h - 2)
            if (col, row) in blocked_positions:
                continue
            wd.enemy_spawns.append({
                "etype": etype,
                "x": col * TILE_SIZE + TILE_SIZE // 2,
                "y": row * TILE_SIZE + TILE_SIZE // 2,
                "elite": i < num_elites,
            })

    # ── Animal spawns (herds) ──
    animal_pool   = get_animals_for_biome(wd.biome)
    animal_budget = int(bdata["animal_budget"] * wc.get("animal_count_mult", 1.0))
    if animal_pool and wd.world_type != "combat":
        atypes  = list(animal_pool.keys())
        spawned = 0
        while spawned < animal_budget:
            atype     = rng.choice(atypes)
            herd_size = rng.randint(2, 4)
            hcol      = rng.randint(2, wd.w - 2)
            hrow      = rng.randint(2, wd.h - 2)
            for _ in range(herd_size):
                col = max(2, min(wd.w - 2, hcol + rng.randint(-3, 3)))
                row = max(2, min(wd.h - 2, hrow + rng.randint(-3, 3)))
                wd.animal_spawns.append({
                    "atype": atype,
                    "x": col * TILE_SIZE + TILE_SIZE // 2,
                    "y": row * TILE_SIZE + TILE_SIZE // 2,
                })
                spawned += 1
                if spawned >= animal_budget:
                    break

    # ── Loot nodes ──
    density_map   = {"none": 0, "low": 1, "medium": 3, "high": 5}
    num_loot      = density_map.get(bdata["loot_density"], 2)
    if wd.world_type == "objective":
        num_loot += 2
    num_loot      = max(1, int(num_loot * wc.get("loot_node_count_mult", 1.0)))
    spawn_col_min = 8
    for _ in range(num_loot):
        col = rng.randint(spawn_col_min, wd.w - 3)
        row = rng.randint(3, wd.h - 3)
        wd.loot_nodes.append({
            "x": col * TILE_SIZE + TILE_SIZE // 2,
            "y": row * TILE_SIZE + TILE_SIZE // 2,
            "looted": False,
        })

    # ── Objective ──
    if wd.world_type == "objective":
        obj_type = rng.choice(["kill_elite", "clear_world", "carry_item"])
        wd.objective = {"type": obj_type, "target_id": None, "done": False}
        if obj_type == "kill_elite":
            for sp in wd.enemy_spawns:
                if sp["elite"]:
                    wd.objective["target_id"] = f'{sp["x"]}_{sp["y"]}'
                    break
            if wd.objective["target_id"] is None:
                if wd.enemy_spawns:
                    sp = rng.choice(wd.enemy_spawns)
                    sp["elite"] = True
                    wd.objective["target_id"] = f'{sp["x"]}_{sp["y"]}'

    return wd


# ─────────────────────────────────────────────
#  World feature placement helpers
# ─────────────────────────────────────────────
def _ruin_offsets(shape):
    """Tile (dx, dy) offsets for each ruin shape."""
    if shape == "L":
        return [(i, 0) for i in range(4)] + [(0, j) for j in range(1, 4)]
    elif shape == "U":
        return ([(0, j) for j in range(3)]
                + [(3, j) for j in range(3)]
                + [(i, 0) for i in range(1, 3)])
    elif shape == "line":
        pts = [(i, 0) for i in range(5)]
        pts.pop(2)   # gap in the middle
        return pts
    else:  # broken_ring
        return [(-1,-1),(0,-1),(1,-1),(2,-1),
                (-1, 0),              (2, 0),
                (-1, 1),              (2, 1),
                (0, 2),(1, 2)]


def _place_ruins(wd, rng, blocked_positions, spawn_col, config):
    wc    = config.get("world", {})
    count = rng.randint(wc.get("ruin_count_min", 1), wc.get("ruin_count_max", 3))

    for _ in range(count):
        col, row = spawn_col + 10, wd.h // 2
        for _a in range(20):
            tc = rng.randint(10, wd.w - 8)
            tr = rng.randint(4,  wd.h - 4)
            if abs(tc - spawn_col) >= 8:
                col, row = tc, tr
                break

        cx    = col * TILE_SIZE + TILE_SIZE // 2
        cy    = row * TILE_SIZE + TILE_SIZE // 2
        shape = rng.choice(["L", "U", "line", "broken_ring"])

        for dx, dy in _ruin_offsets(shape):
            ox    = cx + dx * TILE_SIZE
            oy    = cy + dy * TILE_SIZE
            otype = rng.choice(["rock_large", "rock_med"])
            ow, oh = OBJECT_SIZES.get(otype, (30, 24))
            wd.objects.append({"type": otype, "x": ox, "y": oy,
                                "w": ow, "h": oh, "blocking": True})
            blocked_positions.add((int(ox // TILE_SIZE), int(oy // TILE_SIZE)))

        # Guaranteed chest near ruins
        lx = cx + rng.randint(-2, 2) * TILE_SIZE
        ly = cy + rng.randint(-2, 2) * TILE_SIZE
        wd.loot_nodes.append({"x": lx, "y": ly, "looted": False})


def _place_enemy_camps(wd, rng, blocked_positions, spawn_col, config):
    wc    = config.get("world", {})
    count = rng.randint(wc.get("enemy_camp_count_min", 1),
                        wc.get("enemy_camp_count_max", 2))

    enemy_pool = get_enemies_for_biome(wd.biome)
    if not enemy_pool:
        return
    etypes = list(enemy_pool.keys())

    for _ in range(count):
        col, row = spawn_col + 12, wd.h // 2
        for _a in range(20):
            tc = rng.randint(12, wd.w - 6)
            tr = rng.randint(4,  wd.h - 4)
            if abs(tc - spawn_col) >= 10:
                col, row = tc, tr
                break

        cx = col * TILE_SIZE + TILE_SIZE // 2
        cy = row * TILE_SIZE + TILE_SIZE // 2

        # Campfire centre (non-blocking)
        wd.objects.append({"type": "campfire", "x": cx, "y": cy,
                            "w": 16, "h": 16, "blocking": False})
        # Decorative rocks ringing the fire
        for dx, dy in [(-1,-1),(1,-1),(-1,1),(1,1)]:
            rx = cx + dx * (TILE_SIZE // 2 + 4)
            ry = cy + dy * (TILE_SIZE // 2 + 4)
            wd.objects.append({"type": "rock_small", "x": rx, "y": ry,
                                "w": 14, "h": 12, "blocking": False})

        # Enemies clustered around camp — first one is an elite
        num_camp_enemies = rng.randint(3, 5)
        for i in range(num_camp_enemies):
            etype = rng.choice(etypes)
            ex = cx + rng.randint(-3, 3) * TILE_SIZE
            ey = cy + rng.randint(-3, 3) * TILE_SIZE
            wd.enemy_spawns.append({
                "etype": etype, "x": ex, "y": ey, "elite": (i == 0),
            })

        # Guaranteed loot at camp
        wd.loot_nodes.append({"x": cx + TILE_SIZE, "y": cy, "looted": False})


def _place_decorative_scatter(wd, rng, bdata, spawn_col, spawn_row, config):
    """Add non-blocking visual variety objects (flowers, grass, puddles)."""
    wc   = config.get("world", {})
    mult = wc.get("decorative_scatter_mult", 1.0)

    decor_map = {
        "plains": ["flower", "tall_grass", "puddle"],
        "forest": ["flower", "tall_grass"],
    }
    types = decor_map.get(wd.biome, [])
    if not types:
        return

    base_count = int(wd.w * wd.h * 0.04 * mult)
    for _ in range(base_count):
        dtype = rng.choice(types)
        col   = rng.randint(0, wd.w - 1)
        row   = rng.randint(0, wd.h - 1)
        if abs(col - spawn_col) < 4 and abs(row - spawn_row) < 4:
            continue
        ow, oh = OBJECT_SIZES.get(dtype, (10, 10))
        cx = col * TILE_SIZE + TILE_SIZE // 2
        cy = row * TILE_SIZE + TILE_SIZE // 2
        wd.objects.append({"type": dtype, "x": cx, "y": cy,
                            "w": ow, "h": oh, "blocking": False})


def _place_pois(wd, rng, blocked_positions, spawn_col, config):
    wc    = config.get("world", {})
    count = wc.get("poi_count", 1)

    enemy_pool = get_enemies_for_biome(wd.biome)
    etypes     = list(enemy_pool.keys()) if enemy_pool else []

    available = [p for p in POI_TYPES.values() if wd.biome in p["biomes"]]
    if not available:
        available = list(POI_TYPES.values())

    placed_centers = []
    for _ in range(count):
        poi = rng.choice(available)
        col, row = spawn_col + 15, wd.h // 2
        for _a in range(30):
            tc = rng.randint(15, wd.w - 8)
            tr = rng.randint(5,  wd.h - 5)
            if abs(tc - spawn_col) < 12:
                continue
            if any(abs(tc - pc) < 10 and abs(tr - pr) < 10
                   for pc, pr in placed_centers):
                continue
            col, row = tc, tr
            break

        placed_centers.append((col, row))
        cx = col * TILE_SIZE + TILE_SIZE // 2
        cy = row * TILE_SIZE + TILE_SIZE // 2

        _build_poi_structure(wd, rng, cx, cy, poi, blocked_positions)

        for i in range(poi["enemies"]):
            if not etypes:
                break
            etype = rng.choice(etypes)
            ex = cx + rng.randint(-4, 4) * TILE_SIZE
            ey = cy + rng.randint(-4, 4) * TILE_SIZE
            wd.enemy_spawns.append({
                "etype": etype, "x": ex, "y": ey,
                "elite": (i == 0 and poi["elite"]),
            })

        for _ in range(poi["loot_nodes"]):
            lx = cx + rng.randint(-2, 2) * TILE_SIZE
            ly = cy + rng.randint(-2, 2) * TILE_SIZE
            wd.loot_nodes.append({"x": lx, "y": ly, "looted": False})

        wd.pois.append({"name": poi["display"], "x": cx, "y": cy})


def _build_poi_structure(wd, rng, cx, cy, poi, blocked_positions):
    stype = poi["structure"]

    if stype == "tower":
        # Hollow 5×5 ring of rocks
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                if abs(dx) == 2 or abs(dy) == 2:
                    ox, oy = cx + dx * TILE_SIZE, cy + dy * TILE_SIZE
                    otype  = "rock_large"
                    ow, oh = OBJECT_SIZES[otype]
                    wd.objects.append({"type": otype, "x": ox, "y": oy,
                                       "w": ow, "h": oh, "blocking": True})
                    blocked_positions.add((int(ox // TILE_SIZE), int(oy // TILE_SIZE)))

    elif stype == "graveyard":
        # Skull piles / headstones in a grid
        for i in range(3):
            for j in range(2):
                ox = cx + (i - 1) * TILE_SIZE * 2
                oy = cy + (j - 1) * TILE_SIZE * 2
                dtype    = "skull_pile" if rng.random() < 0.6 else "rock_small"
                ow, oh   = OBJECT_SIZES.get(dtype, (20, 14))
                blocking = OBJECT_BLOCKING.get(dtype, False)
                wd.objects.append({"type": dtype, "x": ox, "y": oy,
                                   "w": ow, "h": oh, "blocking": blocking})
                if blocking:
                    blocked_positions.add((int(ox // TILE_SIZE), int(oy // TILE_SIZE)))
        # Broken perimeter wall
        for dx in [-3, 3]:
            for dy in range(-2, 3):
                if rng.random() < 0.6:
                    ox, oy = cx + dx * TILE_SIZE, cy + dy * TILE_SIZE
                    otype  = "rock_med"
                    ow, oh = OBJECT_SIZES[otype]
                    wd.objects.append({"type": otype, "x": ox, "y": oy,
                                       "w": ow, "h": oh, "blocking": True})
                    blocked_positions.add((int(ox // TILE_SIZE), int(oy // TILE_SIZE)))

    elif stype == "camp":
        wd.objects.append({"type": "campfire", "x": cx, "y": cy,
                            "w": 16, "h": 16, "blocking": False})
        for dx, dy in [(-2,0),(2,0),(0,-2),(0,2),(-2,-2),(2,-2),(-2,2),(2,2)]:
            if rng.random() < 0.7:
                ox, oy = cx + dx * TILE_SIZE, cy + dy * TILE_SIZE
                otype  = "rock_med"
                ow, oh = OBJECT_SIZES[otype]
                wd.objects.append({"type": otype, "x": ox, "y": oy,
                                   "w": ow, "h": oh, "blocking": True})
                blocked_positions.add((int(ox // TILE_SIZE), int(oy // TILE_SIZE)))

    elif stype == "shrine":
        otype  = "rock_large"
        ow, oh = OBJECT_SIZES[otype]
        for dx, dy in [(0,0),(-2,0),(2,0),(0,-2),(0,2),
                       (-3,-3),(3,-3),(-3,3),(3,3)]:
            ox, oy = cx + dx * TILE_SIZE, cy + dy * TILE_SIZE
            wd.objects.append({"type": otype, "x": ox, "y": oy,
                               "w": ow, "h": oh, "blocking": True})
            blocked_positions.add((int(ox // TILE_SIZE), int(oy // TILE_SIZE)))


# ─────────────────────────────────────────────
#  Rendering helpers
# ─────────────────────────────────────────────
def _grass_lean(seed_x, offset):
    """Deterministic grass blade lean so it looks the same every frame."""
    return int(math.sin(seed_x * 0.07 + offset) * 3)


def draw_world_base(world_data):
    """Creates and returns the static world surface (terrain + objects, no fog)."""
    w_px = world_data.w * TILE_SIZE
    h_px = world_data.h * TILE_SIZE
    surf = pygame.Surface((w_px, h_px))

    bdata  = BIOMES[world_data.biome]
    tile = get_tile(bdata["floor_tile"])
    for col in range(world_data.w):
        for row in range(world_data.h):
            surf.blit(tile, (col * TILE_SIZE, row * TILE_SIZE))

    for obj in world_data.objects:
        color = OBJECT_COLORS.get(obj["type"], (100, 100, 100))
        ow, oh = obj["w"], obj["h"]
        ox = int(obj["x"]) - ow // 2
        oy = int(obj["y"]) - oh // 2
        otype = obj["type"]
        art = get_world_object_surface(otype, ow, oh)

        if art is not None:
            surf.blit(art, (ox, oy))
            continue

        if otype == "campfire":
            # Stone ring
            pygame.draw.circle(surf, (75, 60, 42),
                               (ox + ow//2, oy + oh//2), ow//2 + 2)
            # Embers
            pygame.draw.circle(surf, (180, 75, 18),
                               (ox + ow//2, oy + oh//2), ow//3)
            # Flame layers
            pygame.draw.circle(surf, (235, 155, 25),
                               (ox + ow//2, oy + oh//2 - 2), ow//4)
            pygame.draw.circle(surf, (255, 225, 75),
                               (ox + ow//2, oy + oh//2 - 4), max(1, ow//6))

        elif otype == "flower":
            stem_col = (55, 115, 38)
            pygame.draw.line(surf, stem_col,
                             (ox + ow//2, oy + oh),
                             (ox + ow//2, oy + oh//2), 1)
            pygame.draw.circle(surf, color, (ox + ow//2, oy + oh//2), max(1, ow//2))
            pygame.draw.circle(surf, (255, 240, 100),
                               (ox + ow//2, oy + oh//2), max(1, ow//4))

        elif otype == "tall_grass":
            step = max(1, ow // 3)
            for i, gx in enumerate(range(0, ow, step)):
                lean = _grass_lean(int(obj["x"]), i)
                pygame.draw.line(surf, color,
                                 (ox + gx, oy + oh),
                                 (ox + gx + lean, oy), 1)

        elif otype == "puddle":
            pygame.draw.ellipse(surf, color, (ox, oy, ow, oh))
            lighter = tuple(min(255, c + 45) for c in color)
            pygame.draw.ellipse(surf, lighter,
                                (ox + 3, oy + 2, max(2, ow//2), max(2, oh//2)))

        elif obj["blocking"]:
            pygame.draw.rect(surf, color, (ox, oy, ow, oh), 0, 4)
            highlight = tuple(min(255, c + 25) for c in color)
            pygame.draw.rect(surf, highlight, (ox, oy, ow, oh), 1, 4)

        else:
            pygame.draw.ellipse(surf, color, (ox, oy, ow, oh))

    return surf


def get_collision_rects(world_data):
    """Returns list of pygame.Rects for blocking objects."""
    rects = []
    for obj in world_data.objects:
        if obj["blocking"]:
            ow, oh = obj["w"], obj["h"]
            rects.append(pygame.Rect(
                int(obj["x"]) - ow // 2,
                int(obj["y"]) - oh // 2, ow, oh))
    return rects
