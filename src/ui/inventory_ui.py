# src/ui/inventory_ui.py
import pygame
from settings import (SCREEN_WIDTH, SCREEN_HEIGHT, SLOT_SIZE, SLOT_GAP,
                       RARITY_COLORS, UI_BG, UI_PANEL, UI_BORDER,
                       UI_TEXT, UI_TEXT_DIM, UI_HIGHLIGHT, FONT_SM, FONT_MD, FONT_LG)
from src.sprite_factory import loot_drop_sprite, item_slot_bg


class InventoryUI:
    """Full inventory screen: 24-slot grid + equipment panel + tooltip."""

    COLS = 6
    ROWS = 4   # 24 slots

    def __init__(self, font_sm, font_md, font_lg):
        self.font_sm = font_sm
        self.font_md = font_md
        self.font_lg = font_lg

        self.visible = False
        self.selected = None    # ("inv"|"hot"|"eq", index_or_slot)
        self.hovered  = None

        # Panel geometry
        self.panel_w = 580
        self.panel_h = 440
        self.panel_x = SCREEN_WIDTH  // 2 - self.panel_w // 2
        self.panel_y = SCREEN_HEIGHT // 2 - self.panel_h // 2

        # Slot rects (inv)
        self._inv_rects  = []
        self._hot_rects  = []
        self._eq_rects   = {}
        self._build_rects()

    def _build_rects(self):
        ox = self.panel_x + 20
        oy = self.panel_y + 50

        # Main inventory grid
        for row in range(self.ROWS):
            for col in range(self.COLS):
                x = ox + col * (SLOT_SIZE + SLOT_GAP)
                y = oy + row * (SLOT_SIZE + SLOT_GAP)
                self._inv_rects.append(pygame.Rect(x, y, SLOT_SIZE, SLOT_SIZE))

        # Hotbar row
        hy = oy + self.ROWS * (SLOT_SIZE + SLOT_GAP) + 10
        for i in range(5):
            x = ox + i * (SLOT_SIZE + SLOT_GAP)
            self._hot_rects.append(pygame.Rect(x, hy, SLOT_SIZE, SLOT_SIZE))

        # Equipment panel (right side)
        eq_x = ox + self.COLS * (SLOT_SIZE + SLOT_GAP) + 20
        eq_y = oy
        slots_order = [("weapon", "Weapon"), ("head", "Head"),
                       ("chest", "Chest"), ("legs", "Legs"), ("boots", "Boots")]
        for i, (slot, _label) in enumerate(slots_order):
            self._eq_rects[slot] = pygame.Rect(eq_x, eq_y + i * (SLOT_SIZE + SLOT_GAP + 4),
                                                SLOT_SIZE, SLOT_SIZE)

    def toggle(self):
        self.visible = not self.visible
        self.selected = None

    def handle_event(self, event, inventory):
        """Returns action dict or None."""
        if not self.visible:
            return None

        if event.type == pygame.MOUSEMOTION:
            self.hovered = self._hit_test(event.pos)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            hit = self._hit_test(event.pos)
            if hit is None:
                self.visible = False
                self.selected = None
                return None

            if self.selected is None:
                # Select a slot
                item = self._get_item(inventory, hit)
                if item:
                    self.selected = hit
            else:
                # Move item
                action = self._move_item(inventory, self.selected, hit)
                self.selected = None
                return action

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            # Right-click: equip/unequip or use food
            hit = self._hit_test(event.pos)
            if hit:
                return self._right_click(inventory, hit)

        elif event.type == pygame.KEYDOWN and event.key == pygame.K_e:
            self.visible = False
            self.selected = None

        return None

    def _hit_test(self, pos):
        for i, r in enumerate(self._inv_rects):
            if r.collidepoint(pos):
                return ("inv", i)
        for i, r in enumerate(self._hot_rects):
            if r.collidepoint(pos):
                return ("hot", i)
        for slot, r in self._eq_rects.items():
            if r.collidepoint(pos):
                return ("eq", slot)
        return None

    def _get_item(self, inv, loc):
        ltype, idx = loc
        if ltype == "inv":  return inv.slots[idx]
        if ltype == "hot":  return inv.hotbar[idx]
        if ltype == "eq":   return inv.equip.get(idx)
        return None

    def _set_item(self, inv, loc, item):
        ltype, idx = loc
        if ltype == "inv":   inv.slots[idx] = item
        elif ltype == "hot": inv.hotbar[idx] = item
        elif ltype == "eq":  inv.equip[idx] = item

    def _move_item(self, inv, src, dst):
        """Swap src and dst items."""
        src_item = self._get_item(inv, src)
        dst_item = self._get_item(inv, dst)

        # If equipping to equipment slot, validate slot
        if dst[0] == "eq":
            slot = dst[1]
            if src_item:
                valid = (slot == "weapon" and src_item.itype in ("weapon", "boss") and
                         (src_item.weapon_class is not None)) or \
                        (slot in ("head","chest","legs","boots") and
                         src_item.itype in ("armor", "boss") and
                         src_item.slot == slot)
                if not valid:
                    return {"action": "error", "msg": "Wrong slot!"}

        self._set_item(inv, src, dst_item)
        self._set_item(inv, dst, src_item)
        return {"action": "swap", "src": src, "dst": dst}

    def _right_click(self, inv, loc):
        item = self._get_item(inv, loc)
        if not item:
            return None
        if item.itype == "food":
            return {"action": "eat", "loc": loc}
        if item.itype in ("weapon", "armor", "boss") and loc[0] != "eq":
            displaced = inv.equip_item(item)
            self._set_item(inv, loc, displaced)
            return {"action": "equip", "item": item}
        if loc[0] == "eq":
            # Unequip
            if inv.unequip_slot(loc[1]):
                inv.equip[loc[1]] = None
                return {"action": "unequip"}
        return None

    def draw(self, surface, inventory):
        if not self.visible:
            return

        # Dim background
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))

        # Panel
        pygame.draw.rect(surface, UI_PANEL,  (self.panel_x, self.panel_y, self.panel_w, self.panel_h), 0, 8)
        pygame.draw.rect(surface, UI_BORDER, (self.panel_x, self.panel_y, self.panel_w, self.panel_h), 2, 8)

        # Title
        ttl = self.font_lg.render("INVENTORY", True, UI_TEXT)
        surface.blit(ttl, (self.panel_x + 20, self.panel_y + 12))

        # ── Main inventory ──
        for i, r in enumerate(self._inv_rects):
            selected = (self.selected == ("inv", i))
            hovered  = (self.hovered  == ("inv", i))
            bg = item_slot_bg(SLOT_SIZE, hovered, selected)
            surface.blit(bg, r)
            item = inventory.slots[i]
            self._draw_slot_item(surface, r, item, selected)

        # ── Hotbar ──
        ht = self.font_sm.render("Hotbar", True, UI_TEXT_DIM)
        surface.blit(ht, (self._hot_rects[0].x, self._hot_rects[0].y - 16))
        for i, r in enumerate(self._hot_rects):
            selected = (self.selected == ("hot", i))
            hovered  = (self.hovered  == ("hot", i))
            bg = item_slot_bg(SLOT_SIZE, hovered, selected)
            surface.blit(bg, r)
            item = inventory.hotbar[i]
            self._draw_slot_item(surface, r, item, selected)

        # ── Equipment slots ──
        eq_label_x = list(self._eq_rects.values())[0].x
        eql = self.font_sm.render("Equipment", True, UI_TEXT_DIM)
        surface.blit(eql, (eq_label_x, self.panel_y + 32))

        slot_labels = {"weapon": "WPN", "head": "HEAD", "chest": "CHEST",
                       "legs": "LEGS", "boots": "BOOT"}
        for slot, r in self._eq_rects.items():
            selected = (self.selected == ("eq", slot))
            hovered  = (self.hovered  == ("eq", slot))
            bg = item_slot_bg(SLOT_SIZE, hovered, True)
            surface.blit(bg, r)
            item = inventory.equip.get(slot)
            self._draw_slot_item(surface, r, item, selected)
            # Slot label if empty
            if not item:
                lbl = self.font_sm.render(slot_labels.get(slot, slot[:3].upper()), True, UI_TEXT_DIM)
                surface.blit(lbl, (r.x + 2, r.y + r.h - 14))

        # ── Stats summary ──
        sx = self._eq_rects["weapon"].x
        sy = self._eq_rects["boots"].bottom + 12
        def_t = self.font_sm.render(f"Defense: {inventory.total_defense}", True, (100, 160, 220))
        surface.blit(def_t, (sx, sy))
        spd_t = self.font_sm.render(f"Speed +{inventory.speed_bonus}", True, (100, 220, 160))
        surface.blit(spd_t, (sx, sy + 16))

        # ── Tooltip ──
        if self.hovered:
            item = self._get_item(inventory, self.hovered)
            if item:
                self._draw_tooltip(surface, item)

        # ── Instructions ──
        inst = self.font_sm.render("E / Click outside to close   |   Right-click to equip/eat",
                                   True, UI_TEXT_DIM)
        surface.blit(inst, (self.panel_x + 20, self.panel_y + self.panel_h - 20))

    def _draw_slot_item(self, surface, r, item, selected):
        if not item:
            return
        spr = loot_drop_sprite(item, SLOT_SIZE - 8)
        surface.blit(spr, (r.x + 4, r.y + 4))
        if item.stackable and item.quantity > 1:
            qt = self.font_sm.render(str(item.quantity), True, (255, 255, 200))
            surface.blit(qt, (r.x + SLOT_SIZE - 18, r.y + SLOT_SIZE - 16))
        if item.broken:
            bt = self.font_sm.render("!", True, (220, 50, 50))
            surface.blit(bt, (r.x + 2, r.y + 2))
        if selected:
            pygame.draw.rect(surface, (255, 215, 0), r, 2)

    def _draw_tooltip(self, surface, item):
        lines = [
            item.display_name,
            item.stat_line(),
            item.desc,
            f"Sell: {item.sell_value}g",
        ]
        if item.broken:
            lines.insert(1, "*** BROKEN ***")

        tw = 240
        th = len(lines) * 18 + 16
        mx, my = pygame.mouse.get_pos()
        tx = min(mx + 12, SCREEN_WIDTH  - tw - 4)
        ty = min(my + 12, SCREEN_HEIGHT - th - 4)

        pygame.draw.rect(surface, UI_BG,    (tx, ty, tw, th), 0, 6)
        pygame.draw.rect(surface, RARITY_COLORS.get(item.rarity, UI_BORDER),
                         (tx, ty, tw, th), 1, 6)

        for i, line in enumerate(lines):
            col = RARITY_COLORS.get(item.rarity, UI_TEXT) if i == 0 else UI_TEXT
            if "BROKEN" in line:
                col = (220, 50, 50)
            t = self.font_sm.render(line, True, col)
            surface.blit(t, (tx + 8, ty + 8 + i * 18))
