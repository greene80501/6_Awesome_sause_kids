# src/systems/inventory.py
from settings import INVENTORY_SIZE, HOTBAR_SIZE, EQUIP_SLOTS, STORAGE_SIZES


class Inventory:
    """24-slot main inventory + 5-slot hotbar + equipment slots."""

    def __init__(self):
        self.slots  = [None] * INVENTORY_SIZE   # main inv
        self.hotbar = [None] * HOTBAR_SIZE
        self.equip  = {s: None for s in EQUIP_SLOTS}  # head/chest/legs/boots/weapon

    # ── Add item ──
    def add_item(self, item):
        """Returns True if item was fully added, False if no space."""
        if item.stackable:
            # Try to stack with existing
            for slot_list in (self.hotbar, self.slots):
                for i, s in enumerate(slot_list):
                    if s and s.id == item.id and s.itype == item.itype:
                        s.quantity += item.quantity
                        return True
        # Find empty slot (hotbar first)
        for slot_list in (self.hotbar, self.slots):
            for i, s in enumerate(slot_list):
                if s is None:
                    slot_list[i] = item
                    return True
        return False

    def add_item_to_main(self, item):
        """Add only to main inventory (not hotbar)."""
        if item.stackable:
            for i, s in enumerate(self.slots):
                if s and s.id == item.id:
                    s.quantity += item.quantity
                    return True
        for i, s in enumerate(self.slots):
            if s is None:
                self.slots[i] = item
                return True
        return False

    # ── Remove helpers ──
    def remove_slot(self, idx):
        item = self.slots[idx]
        self.slots[idx] = None
        return item

    def remove_hotbar(self, idx):
        item = self.hotbar[idx]
        self.hotbar[idx] = None
        return item

    def remove_equip(self, slot):
        item = self.equip.get(slot)
        self.equip[slot] = None
        return item

    # ── Equip / unequip ──
    def equip_item(self, item):
        """Equip an item, returning displaced item or None."""
        slot = None
        if item.itype == "weapon":
            slot = "weapon"
        elif item.itype == "armor":
            slot = item.slot
        elif item.itype == "boss":
            if item.weapon_class:
                slot = "weapon"
            elif item.slot:
                slot = item.slot
        if slot is None:
            return None
        displaced = self.equip.get(slot)
        self.equip[slot] = item
        return displaced

    def unequip_slot(self, slot):
        item = self.equip.get(slot)
        if item is None:
            return False
        if self.add_item(item):
            self.equip[slot] = None
            return True
        return False  # no inventory space

    # ── Consume food ──
    def consume_hotbar(self, idx):
        """Consume one food item from hotbar. Returns hunger_restore or 0."""
        item = self.hotbar[idx]
        if item is None or item.itype != "food":
            return 0
        restore = item.hunger_restore
        item.quantity -= 1
        if item.quantity <= 0:
            self.hotbar[idx] = None
        return restore

    # ── Queries ──
    def is_full(self):
        return all(s is not None for s in self.slots) and all(s is not None for s in self.hotbar)

    def total_items(self):
        return sum(1 for s in self.slots if s) + sum(1 for s in self.hotbar if s)

    def all_items(self):
        """Yield (location, index_or_slot, item) for all held items."""
        for i, s in enumerate(self.slots):
            if s: yield ("inv", i, s)
        for i, s in enumerate(self.hotbar):
            if s: yield ("hot", i, s)
        for k, v in self.equip.items():
            if v: yield ("eq", k, v)

    def drop_all(self):
        """Remove and return every carried item (for death drop)."""
        items = []
        for i in range(len(self.slots)):
            if self.slots[i]:
                items.append(self.slots[i])
                self.slots[i] = None
        for i in range(len(self.hotbar)):
            if self.hotbar[i]:
                items.append(self.hotbar[i])
                self.hotbar[i] = None
        for k in list(self.equip.keys()):
            if self.equip[k]:
                items.append(self.equip[k])
                self.equip[k] = None
        return items

    @property
    def equipped_weapon(self):
        return self.equip.get("weapon")

    @property
    def total_defense(self):
        total = 0
        for slot in ["head", "chest", "legs", "boots"]:
            item = self.equip.get(slot)
            if item and not item.broken:
                total += item.defense
        return total

    @property
    def speed_bonus(self):
        boots = self.equip.get("boots")
        if boots and not boots.broken:
            return boots.speed_bonus
        return 0

    # ── Serialization ──
    def to_dict(self):
        def ser(item):
            return item.to_dict() if item else None
        return {
            "slots":  [ser(s) for s in self.slots],
            "hotbar": [ser(s) for s in self.hotbar],
            "equip":  {k: ser(v) for k, v in self.equip.items()},
        }

    @classmethod
    def from_dict(cls, d):
        from src.systems.item import Item
        inv = cls()
        for i, sd in enumerate(d.get("slots", [])[:len(inv.slots)]):
            inv.slots[i] = Item.from_dict(sd) if sd else None
        for i, sd in enumerate(d.get("hotbar", [])[:len(inv.hotbar)]):
            inv.hotbar[i] = Item.from_dict(sd) if sd else None
        for k, sd in d.get("equip", {}).items():
            if k in inv.equip:
                inv.equip[k] = Item.from_dict(sd) if sd else None
        return inv


class TavernStorage:
    """Permanent tavern storage; size expands with boss kills."""

    def __init__(self, boss_kills=0):
        self._boss_kills = boss_kills
        size = STORAGE_SIZES[min(boss_kills, len(STORAGE_SIZES)-1)]
        self.slots = [None] * size

    def update_size(self, boss_kills):
        new_size = STORAGE_SIZES[min(boss_kills, len(STORAGE_SIZES)-1)]
        if new_size > len(self.slots):
            self.slots.extend([None] * (new_size - len(self.slots)))

    def add_item(self, item):
        if item.stackable:
            for i, s in enumerate(self.slots):
                if s and s.id == item.id:
                    s.quantity += item.quantity
                    return True
        for i, s in enumerate(self.slots):
            if s is None:
                self.slots[i] = item
                return True
        return False

    def remove_slot(self, idx):
        item = self.slots[idx]
        self.slots[idx] = None
        return item

    def is_full(self):
        return all(s is not None for s in self.slots)

    def to_dict(self):
        return {"slots": [s.to_dict() if s else None for s in self.slots]}

    @classmethod
    def from_dict(cls, d, boss_kills=0):
        from src.systems.item import Item
        st = cls(boss_kills)
        saved = d.get("slots", [])
        for i, sd in enumerate(saved):
            if i < len(st.slots):
                st.slots[i] = Item.from_dict(sd) if sd else None
        return st
