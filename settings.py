# settings.py — all game-wide constants

SCREEN_WIDTH  = 1280
SCREEN_HEIGHT = 720
TILE_SIZE     = 32
FPS           = 60
TITLE         = "Tavern Looter"

# World dimensions (in tiles)
WORLD_W = 80
WORLD_H = 80

# ---------- Colors ----------
BLACK      = (0,   0,   0)
WHITE      = (255, 255, 255)
GRAY       = (110, 110, 110)
DARK_GRAY  = (45,  45,  45)
RED        = (200, 55,  55)
DARK_RED   = (120, 20,  20)
GREEN      = (60,  180, 60)
DARK_GREEN = (20,  100, 20)
BLUE       = (60,  110, 210)
YELLOW     = (220, 205, 55)
ORANGE     = (220, 135, 30)
BROWN      = (120, 80,  40)
PURPLE     = (150, 55,  210)
CYAN       = (55,  200, 200)
GOLD       = (255, 215, 0)
PINK       = (220, 100, 150)

# UI palette
UI_BG         = (20,  14,  10)
UI_PANEL      = (35,  25,  18)
UI_BORDER     = (80,  60,  40)
UI_HIGHLIGHT  = (100, 75,  50)
UI_TEXT       = (220, 200, 170)
UI_TEXT_DIM   = (130, 110, 85)
TAVERN_BG     = (30,  20,  12)
TAVERN_FLOOR  = (55,  40,  25)
TAVERN_WALL   = (40,  28,  18)

# ---------- Player ----------
PLAYER_SPEED        = 190   # px/s
PLAYER_MAX_HEALTH   = 100
PLAYER_MAX_HUNGER   = 100
HUNGER_DRAIN_WORLD  = 0.55  # per second in world
HUNGER_DRAIN_TAVERN = 0.12  # per second in tavern
STARVATION_DMG      = 6.0   # health/s at 0 hunger
HEALTH_REGEN_RATE   = 3.5   # health/s at max hunger
HEALTH_REGEN_THRESHOLD = 90  # hunger must be >= this to regen

# ---------- Combat ----------
ATTACK_ARC   = 85    # degrees
ATTACK_RANGE = 68    # pixels
SLOW_WHILE_ATTACKING = 0.35   # movement multiplier

# Weapon class modifiers (cooldown s, damage, durability, arc_bonus, range_bonus)
WEAPON_CLASSES = {
    "light":    {"cooldown": 0.30, "dmg_mult": 0.75, "dur": 50,  "arc": 0,  "range": 0},
    "balanced": {"cooldown": 0.50, "dmg_mult": 1.00, "dur": 80,  "arc": 0,  "range": 0},
    "heavy":    {"cooldown": 0.80, "dmg_mult": 1.50, "dur": 110, "arc": 15, "range": 10},
}

# ---------- Inventory ----------
INVENTORY_SIZE  = 24
HOTBAR_SIZE     = 5
EQUIP_SLOTS     = ["head", "chest", "legs", "boots", "weapon"]
STORAGE_SIZES   = [20, 40, 80]  # unlocks at 0/1/2 boss kills

# ---------- Death ----------
DEATH_PILE_TTL  = 60.0   # seconds in-world only

# ---------- Rarity ----------
RARITIES = ["Common", "Good", "Rare", "Epic", "Legendary"]
RARITY_COLORS = {
    "Common":    (175, 175, 175),
    "Good":      (80,  200, 80),
    "Rare":      (55,  130, 230),
    "Epic":      (165, 55,  230),
    "Legendary": (255, 165, 0),
}
RARITY_DMG_MULT   = {"Common": 1.0, "Good": 1.25, "Rare": 1.6,  "Epic": 2.1,  "Legendary": 3.0}
RARITY_DEF_MULT   = {"Common": 1.0, "Good": 1.20, "Rare": 1.5,  "Epic": 2.0,  "Legendary": 2.8}
RARITY_SELL_MULT  = {"Common": 1.0, "Good": 1.5,  "Rare": 3.0,  "Epic": 6.0,  "Legendary": 15.0}
RARITY_WEIGHTS_EARLY  = [55, 28, 12, 4, 1]
RARITY_WEIGHTS_MID    = [35, 30, 20, 12, 3]
RARITY_WEIGHTS_LATE   = [20, 25, 25, 20, 10]

# ---------- Economy ----------
BASE_REPAIR_COST    = 5    # coins per point of durability
SELL_BROKEN_MULT    = 0.05 # fraction of base sell value when broken

# ---------- World generation ----------
TIER_THRESHOLDS = [0, 3, 6, 10, 15]   # completed-world counts → tier 0-4
FOG_VISION_RADIUS = 7   # tiles

# ---------- UI sizes ----------
HUD_H         = 64
SLOT_SIZE     = 48
SLOT_GAP      = 4
FONT_SM       = 13
FONT_MD       = 17
FONT_LG       = 22
FONT_XL       = 30
