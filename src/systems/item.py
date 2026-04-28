# src/systems/item.py
import copy
from settings import (RARITIES, RARITY_DMG_MULT, RARITY_DEF_MULT,
                       RARITY_SELL_MULT, WEAPON_CLASSES, SELL_BROKEN_MULT)


class Item:
    """Represents a single item instance (weapon, armor, food, junk)."""

    def __init__(self, itype, data, rarity="Common", quantity=1):
        """
        itype    : "weapon" | "armor" | "food" | "boss" | "junk"
        data     : dict from items_data matching the base definition
        rarity   : one of RARITIES
        quantity : for stackable items
        """
        self.itype    = itype
        self.id       = data["id"]
        self.name     = data["name"]
        self.rarity   = rarity
        self.quantity = quantity
        self.color    = data.get("color", (180, 180, 180))
        self.desc     = data.get("desc", "")
        self.tier     = data.get("tier", 0)
        self.stackable = data.get("stack", False)
        self.broken   = False

        # ── Weapon fields ──
        self.weapon_class  = data.get("class")
        self.base_dmg      = 0
        self.damage        = 0
        self.cooldown      = 0.5
        self.max_durability = 80
        self.durability    = 80

        # ── Armor fields ──
        self.slot          = data.get("slot")
        self.base_def      = 0
        self.defense       = 0
        self.speed_bonus   = data.get("speed_bonus", 0)

        # ── Food fields ──
        self.hunger_restore = 0

        self._apply_stats(data, rarity)

    def _apply_stats(self, data, rarity):
        if self.itype == "weapon":
            wc = WEAPON_CLASSES.get(self.weapon_class, WEAPON_CLASSES["balanced"])
            self.base_dmg       = data["base_dmg"]
            self.damage         = round(self.base_dmg * RARITY_DMG_MULT[rarity] * wc["dmg_mult"])
            self.cooldown       = wc["cooldown"]
            self.max_durability = wc["dur"]
            self.durability     = self.max_durability

        elif self.itype == "armor":
            self.base_def      = data["base_def"]
            self.defense       = round(self.base_def * RARITY_DEF_MULT[rarity])
            self.max_durability = 100
            self.durability    = 100

        elif self.itype == "food":
            self.hunger_restore = data["hunger"]

        elif self.itype == "boss":
            # Boss items use explicit rarity from data
            self.rarity = data.get("rarity", rarity)
            if data.get("type") == "weapon":
                self.weapon_class   = data.get("class", "balanced")
                wc = WEAPON_CLASSES.get(self.weapon_class, WEAPON_CLASSES["balanced"])
                self.base_dmg       = data["base_dmg"]
                self.damage         = self.base_dmg
                self.cooldown       = wc["cooldown"]
                self.max_durability = wc["dur"]
                self.durability     = self.max_durability
            elif data.get("type") == "armor":
                self.slot          = data["slot"]
                self.base_def      = data["base_def"]
                self.defense       = self.base_def
                self.max_durability = 100
                self.durability    = 100

    # ── Durability helpers ──
    def take_durability(self, amount):
        if self.stackable:
            return
        self.durability = max(0, self.durability - amount)
        if self.durability == 0:
            self.broken = True

    def repair(self, amount):
        if self.broken:
            self.broken = False
            self.durability = max(1, amount)
        else:
            self.durability = min(self.max_durability, self.durability + amount)

    @property
    def dur_pct(self):
        if self.max_durability == 0:
            return 1.0
        return self.durability / self.max_durability

    # ── Economy helpers ──
    @property
    def sell_value(self):
        base = self._base_sell()
        if self.broken:
            return max(1, round(base * SELL_BROKEN_MULT))
        dur_mult = 0.3 + 0.7 * self.dur_pct
        return max(1, round(base * dur_mult))

    @property
    def buy_value(self):
        return max(1, round(self._base_sell() * 2.2))

    def _base_sell(self):
        mult = RARITY_SELL_MULT.get(self.rarity, 1.0)
        if self.itype == "weapon":
            return round(self.base_dmg * 1.8 * mult)
        elif self.itype == "armor":
            return round(self.base_def * 1.5 * mult)
        elif self.itype == "food":
            return max(1, round(self.hunger_restore * 0.4))
        elif self.itype == "boss":
            return round(150 * mult)
        return 1

    def repair_cost(self, coins_per_point=5):
        missing = self.max_durability - self.durability
        mult = RARITY_SELL_MULT.get(self.rarity, 1.0)
        return max(1, round(missing * coins_per_point * mult * 0.5))

    # ── Display helpers ──
    @property
    def display_name(self):
        if self.rarity == "Common":
            return self.name
        return f"{self.rarity} {self.name}"

    def stat_line(self):
        if self.itype == "weapon":
            return f"DMG {self.damage}  |  {self.weapon_class.title()}  |  {self.durability}/{self.max_durability} DUR"
        elif self.itype == "armor":
            line = f"DEF {self.defense}  |  {self.slot.title()}  |  {self.durability}/{self.max_durability} DUR"
            if self.speed_bonus:
                line += f"  |  +{self.speed_bonus} SPD"
            return line
        elif self.itype == "food":
            return f"Restores {self.hunger_restore} Hunger  (x{self.quantity})"
        return ""

    # ── Serialization ──
    def to_dict(self):
        return {
            "itype": self.itype, "id": self.id, "rarity": self.rarity,
            "quantity": self.quantity, "durability": self.durability, "broken": self.broken,
        }

    @classmethod
    def from_dict(cls, d):
        from src.data.items_data import (WEAPONS_BY_ID, ARMOR_BY_ID,
                                          FOOD_BY_ID, BOSS_BY_ID)
        itype = d["itype"]
        iid   = d["id"]
        if itype == "weapon":
            data = WEAPONS_BY_ID[iid]
        elif itype == "armor":
            data = ARMOR_BY_ID[iid]
        elif itype == "food":
            data = FOOD_BY_ID[iid]
        elif itype == "boss":
            data = BOSS_BY_ID[iid]
        else:
            return None
        item = cls(itype, data, rarity=d["rarity"], quantity=d["quantity"])
        item.durability = d["durability"]
        item.broken     = d["broken"]
        return item

    def clone(self):
        return copy.deepcopy(self)
