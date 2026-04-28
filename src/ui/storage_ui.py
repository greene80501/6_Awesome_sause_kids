# src/ui/storage_ui.py
import pygame
from settings import (SCREEN_WIDTH, SCREEN_HEIGHT, SLOT_SIZE, SLOT_GAP,
                       RARITY_COLORS, UI_BG, UI_PANEL, UI_BORDER,
                       UI_TEXT, UI_TEXT_DIM, FONT_SM, FONT_MD, FONT_LG)
from src.sprite_factory import loot_drop_sprite, item_slot_bg


class StorageUI:
    """Tavern storage chest UI — move items between inventory and storage."""

    COLS = 8

    def __init__(self, font_sm, font_md, font_lg):
        self.font_sm = font_sm
        self.font_md = font_md
        self.font_lg = font_lg
        self.visible  = False
        self.selected = None   # ("inv"|"hot"|"st", index)
        self.hovered  = None
        self.panel_w  = 660
        self.panel_h  = 460
        self.panel_x  = SCREEN_WIDTH  // 2 - self.panel_w // 2
        self.panel_y  = SCREEN_HEIGHT // 2 - self.panel_h // 2

    def open(self):
        self.visible  = True
        self.selected = None

    def close(self):
        self.visible  = False
        self.selected = None

    def handle_event(self, event, player_data):
        if not self.visible:
            return False
        inv     = player_data["inventory"]
        storage = player_data["storage"]

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_e):
                self.close(); return True

        if event.type == pygame.MOUSEMOTION:
            self.hovered = self._hit(event.pos, inv, storage)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            close_r = pygame.Rect(self.panel_x + self.panel_w - 30, self.panel_y + 8, 22, 22)
            if close_r.collidepoint(event.pos):
                self.close(); return True

            hit = self._hit(event.pos, inv, storage)
            if hit is None: return True

            if self.selected is None:
                item = self._get(hit, inv, storage)
                if item: self.selected = hit
            else:
                self._do_move(self.selected, hit, inv, storage)
                self.selected = None
            return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            hit = self._hit(event.pos, inv, storage)
            if hit:
                item = self._get(hit, inv, storage)
                if item:
                    # Quick-transfer
                    ltype = hit[0]
                    if ltype == "st":
                        inv.add_item(item)
                        storage.remove_slot(hit[1])
                    else:
                        storage.add_item(item)
                        self._remove(hit, inv, storage)
            return True

        return self.visible

    def _hit(self, pos, inv, storage):
        for i, r in enumerate(self._inv_rects(inv)):
            if r.collidepoint(pos): return ("inv", i)
        for i, r in enumerate(self._hot_rects()):
            if r.collidepoint(pos): return ("hot", i)
        for i, r in enumerate(self._st_rects(storage)):
            if r.collidepoint(pos): return ("st", i)
        return None

    def _get(self, loc, inv, storage):
        t, i = loc
        if t == "inv":  return inv.slots[i]
        if t == "hot":  return inv.hotbar[i]
        if t == "st":   return storage.slots[i]
        return None

    def _remove(self, loc, inv, storage):
        t, i = loc
        if t == "inv":  inv.slots[i] = None
        elif t == "hot": inv.hotbar[i] = None
        elif t == "st":  storage.slots[i] = None

    def _do_move(self, src, dst, inv, storage):
        src_item = self._get(src, inv, storage)
        dst_item = self._get(dst, inv, storage) if dst[1] is not None else None

        # Find empty dst slot if dst idx is None
        if dst[0] == "st" and dst[1] is None:
            storage.add_item(src_item)
            self._remove(src, inv, storage)
            return
        if dst[1] is None:
            inv.add_item(src_item)
            self._remove(src, inv, storage)
            return

        # Swap
        t, i = src
        dt, di = dst
        self._set(src, dst_item, inv, storage)
        self._set(dst, src_item, inv, storage)

    def _set(self, loc, item, inv, storage):
        t, i = loc
        if t == "inv":  inv.slots[i] = item
        elif t == "hot": inv.hotbar[i] = item
        elif t == "st":  storage.slots[i] = item

    # ── Geometry ──
    def _inv_rects(self, inv):
        rects = []
        ox = self.panel_x + 20; oy = self.panel_y + 50
        total = len(inv.slots)
        cols = 6
        for i in range(total):
            col = i % cols; row = i // cols
            rects.append(pygame.Rect(ox + col*(SLOT_SIZE+SLOT_GAP),
                                     oy + row*(SLOT_SIZE+SLOT_GAP), SLOT_SIZE, SLOT_SIZE))
        return rects

    def _hot_rects(self):
        rects = []
        ox = self.panel_x + 20; oy = self.panel_y + 50 + 4*(SLOT_SIZE+SLOT_GAP) + 8
        for i in range(5):
            rects.append(pygame.Rect(ox + i*(SLOT_SIZE+SLOT_GAP), oy, SLOT_SIZE, SLOT_SIZE))
        return rects

    def _st_rects(self, storage):
        rects = []
        ox = self.panel_x + 6*(SLOT_SIZE+SLOT_GAP) + 36
        oy = self.panel_y + 50
        cols = self.COLS - 6
        cols = max(2, cols)
        for i in range(len(storage.slots)):
            col = i % 2; row = i // 2
            rects.append(pygame.Rect(ox + col*(SLOT_SIZE+SLOT_GAP),
                                     oy + row*(SLOT_SIZE+SLOT_GAP), SLOT_SIZE, SLOT_SIZE))
        return rects

    def draw(self, surface, player_data):
        if not self.visible: return
        inv = player_data["inventory"]; storage = player_data["storage"]

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 155))
        surface.blit(overlay, (0, 0))

        pygame.draw.rect(surface, UI_PANEL,  (self.panel_x, self.panel_y, self.panel_w, self.panel_h), 0, 8)
        pygame.draw.rect(surface, UI_BORDER, (self.panel_x, self.panel_y, self.panel_w, self.panel_h), 2, 8)

        ttl = self.font_lg.render("STORAGE", True, UI_TEXT)
        surface.blit(ttl, (self.panel_x + 20, self.panel_y + 12))

        close_r = pygame.Rect(self.panel_x + self.panel_w - 30, self.panel_y + 8, 22, 22)
        pygame.draw.rect(surface, (120, 40, 40), close_r, 0, 4)
        xt = self.font_md.render("X", True, UI_TEXT)
        surface.blit(xt, (close_r.x + 5, close_r.y + 2))

        # Inv label
        il = self.font_sm.render("Inventory", True, UI_TEXT_DIM)
        surface.blit(il, (self.panel_x + 20, self.panel_y + 34))

        # Storage label
        st_rects = self._st_rects(storage)
        if st_rects:
            sl = self.font_sm.render(f"Storage ({len([s for s in storage.slots if s])}/{len(storage.slots)})",
                                     True, UI_TEXT_DIM)
            surface.blit(sl, (st_rects[0].x, self.panel_y + 34))

        for i, r in enumerate(self._inv_rects(inv)):
            bg = item_slot_bg(SLOT_SIZE, self.hovered==("inv",i), self.selected==("inv",i))
            surface.blit(bg, r)
            item = inv.slots[i]
            if item: self._draw_item(surface, r, item)

        for i, r in enumerate(self._hot_rects()):
            bg = item_slot_bg(SLOT_SIZE, self.hovered==("hot",i), self.selected==("hot",i))
            surface.blit(bg, r)
            item = inv.hotbar[i]
            if item: self._draw_item(surface, r, item)

        for i, r in enumerate(st_rects):
            bg = item_slot_bg(SLOT_SIZE, self.hovered==("st",i), self.selected==("st",i))
            surface.blit(bg, r)
            item = storage.slots[i] if i < len(storage.slots) else None
            if item: self._draw_item(surface, r, item)

        inst = self.font_sm.render("Right-click to quick-transfer  |  Left-click to swap  |  E to close",
                                   True, UI_TEXT_DIM)
        surface.blit(inst, (self.panel_x + 20, self.panel_y + self.panel_h - 18))

    def _draw_item(self, surface, r, item):
        spr = loot_drop_sprite(item, SLOT_SIZE - 8)
        surface.blit(spr, (r.x + 4, r.y + 4))
        if item.stackable and item.quantity > 1:
            qt = self.font_sm.render(str(item.quantity), True, (255, 255, 200))
            surface.blit(qt, (r.x + SLOT_SIZE - 18, r.y + SLOT_SIZE - 16))
