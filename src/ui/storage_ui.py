import math
import pygame
from settings import (SCREEN_WIDTH, SCREEN_HEIGHT, SLOT_SIZE, SLOT_GAP,
                       UI_PANEL, UI_BORDER, UI_TEXT, UI_TEXT_DIM)
from src.sprite_factory import loot_drop_sprite, item_slot_bg


class StorageUI:
    """Tavern storage chest UI: move items between inventory and storage."""

    INV_COLS = 6

    def __init__(self, font_sm, font_md, font_lg):
        self.font_sm = font_sm
        self.font_md = font_md
        self.font_lg = font_lg
        self.visible = False
        self.selected = None   # ("inv"|"hot"|"st", index)
        self.hovered = None
        self.panel_w = 660
        self.panel_h = 460
        self.panel_x = SCREEN_WIDTH // 2 - self.panel_w // 2
        self.panel_y = SCREEN_HEIGHT // 2 - self.panel_h // 2
        self.storage_page = 0
        self.message = ""

    def open(self):
        self.visible = True
        self.selected = None
        self.hovered = None
        self.storage_page = 0
        self.message = ""

    def close(self):
        self.visible = False
        self.selected = None
        self.hovered = None

    def handle_event(self, event, player_data):
        if not self.visible:
            return False

        inv = player_data["inventory"]
        storage = player_data["storage"]
        page_count = self._storage_page_count(storage)

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_e):
                self.close()
                return True
            if event.key == pygame.K_LEFT and page_count > 1:
                self._change_page(-1, storage)
                return True
            if event.key == pygame.K_RIGHT and page_count > 1:
                self._change_page(1, storage)
                return True

        if event.type == pygame.MOUSEWHEEL and page_count > 1:
            self._change_page(-event.y, storage)
            return True

        if event.type == pygame.MOUSEMOTION:
            self.hovered = self._hit(event.pos, inv, storage)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            close_r = pygame.Rect(self.panel_x + self.panel_w - 30, self.panel_y + 8, 22, 22)
            if close_r.collidepoint(event.pos):
                self.close()
                return True

            prev_r, next_r = self._page_button_rects(storage)
            if prev_r and prev_r.collidepoint(event.pos):
                self._change_page(-1, storage)
                return True
            if next_r and next_r.collidepoint(event.pos):
                self._change_page(1, storage)
                return True

            hit = self._hit(event.pos, inv, storage)
            if hit is None:
                return True

            if self.selected is None:
                item = self._get(hit, inv, storage)
                if item:
                    self.selected = hit
            else:
                self._do_move(self.selected, hit, inv, storage)
                self.selected = None
            return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            hit = self._hit(event.pos, inv, storage)
            if hit:
                self._quick_transfer(hit, inv, storage)
            return True

        return self.visible

    def _change_page(self, delta, storage):
        page_count = self._storage_page_count(storage)
        if page_count <= 1:
            self.storage_page = 0
            return
        self.storage_page = max(0, min(self.storage_page + delta, page_count - 1))
        if self.selected and self.selected[0] == "st":
            start, end = self._storage_page_bounds(storage)
            if not (start <= self.selected[1] < end):
                self.selected = None
        self.hovered = None

    def _quick_transfer(self, loc, inv, storage):
        item = self._get(loc, inv, storage)
        if not item:
            return

        ltype = loc[0]
        if ltype == "st":
            if inv.add_item(item):
                storage.remove_slot(loc[1])
                self.message = "Moved item to inventory."
            else:
                self.message = "Inventory full."
            return

        if storage.add_item(item):
            self._remove(loc, inv, storage)
            self.message = "Stored item."
        else:
            self.message = "Storage full."

    def _hit(self, pos, inv, storage):
        for i, r in enumerate(self._inv_rects(inv)):
            if r.collidepoint(pos):
                return ("inv", i)
        for i, r in enumerate(self._hot_rects()):
            if r.collidepoint(pos):
                return ("hot", i)
        for idx, r in self._st_rects(storage):
            if r.collidepoint(pos):
                return ("st", idx)
        return None

    def _get(self, loc, inv, storage):
        t, i = loc
        if t == "inv":
            return inv.slots[i]
        if t == "hot":
            return inv.hotbar[i]
        if t == "st":
            return storage.slots[i]
        return None

    def _remove(self, loc, inv, storage):
        t, i = loc
        if t == "inv":
            inv.slots[i] = None
        elif t == "hot":
            inv.hotbar[i] = None
        elif t == "st":
            storage.slots[i] = None

    def _do_move(self, src, dst, inv, storage):
        src_item = self._get(src, inv, storage)
        dst_item = self._get(dst, inv, storage)
        if src_item is None:
            return

        self._set(src, dst_item, inv, storage)
        self._set(dst, src_item, inv, storage)
        self.message = "Items moved."

    def _set(self, loc, item, inv, storage):
        t, i = loc
        if t == "inv":
            inv.slots[i] = item
        elif t == "hot":
            inv.hotbar[i] = item
        elif t == "st":
            storage.slots[i] = item

    def _storage_layout(self):
        inv_left = self.panel_x + 20
        inv_w = self.INV_COLS * (SLOT_SIZE + SLOT_GAP) - SLOT_GAP
        st_x = inv_left + inv_w + 36
        st_y = self.panel_y + 50
        usable_w = self.panel_x + self.panel_w - 20 - st_x
        usable_h = self.panel_y + self.panel_h - 54 - st_y
        cols = max(2, usable_w // (SLOT_SIZE + SLOT_GAP))
        rows = max(1, usable_h // (SLOT_SIZE + SLOT_GAP))
        return st_x, st_y, cols, rows

    def _storage_page_size(self):
        _x, _y, cols, rows = self._storage_layout()
        return cols * rows

    def _storage_page_count(self, storage):
        return max(1, math.ceil(len(storage.slots) / self._storage_page_size()))

    def _storage_page_bounds(self, storage):
        per_page = self._storage_page_size()
        start = self.storage_page * per_page
        end = min(len(storage.slots), start + per_page)
        return start, end

    def _inv_rects(self, inv):
        rects = []
        ox = self.panel_x + 20
        oy = self.panel_y + 50
        for i in range(len(inv.slots)):
            col = i % self.INV_COLS
            row = i // self.INV_COLS
            rects.append(pygame.Rect(
                ox + col * (SLOT_SIZE + SLOT_GAP),
                oy + row * (SLOT_SIZE + SLOT_GAP),
                SLOT_SIZE,
                SLOT_SIZE,
            ))
        return rects

    def _hot_rects(self):
        rects = []
        ox = self.panel_x + 20
        oy = self.panel_y + 50 + 4 * (SLOT_SIZE + SLOT_GAP) + 8
        for i in range(5):
            rects.append(pygame.Rect(ox + i * (SLOT_SIZE + SLOT_GAP), oy, SLOT_SIZE, SLOT_SIZE))
        return rects

    def _st_rects(self, storage):
        rects = []
        st_x, st_y, cols, _rows = self._storage_layout()
        start, end = self._storage_page_bounds(storage)
        for draw_idx, slot_idx in enumerate(range(start, end)):
            col = draw_idx % cols
            row = draw_idx // cols
            rect = pygame.Rect(
                st_x + col * (SLOT_SIZE + SLOT_GAP),
                st_y + row * (SLOT_SIZE + SLOT_GAP),
                SLOT_SIZE,
                SLOT_SIZE,
            )
            rects.append((slot_idx, rect))
        return rects

    def _page_button_rects(self, storage):
        page_count = self._storage_page_count(storage)
        if page_count <= 1:
            return None, None
        st_x, _st_y, cols, _rows = self._storage_layout()
        label_x = st_x + cols * (SLOT_SIZE + SLOT_GAP) - SLOT_GAP
        prev_r = pygame.Rect(label_x - 72, self.panel_y + 32, 28, 18)
        next_r = pygame.Rect(label_x - 36, self.panel_y + 32, 28, 18)
        return prev_r, next_r

    def draw(self, surface, player_data):
        if not self.visible:
            return

        inv = player_data["inventory"]
        storage = player_data["storage"]
        st_rects = self._st_rects(storage)
        page_count = self._storage_page_count(storage)

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 155))
        surface.blit(overlay, (0, 0))

        pygame.draw.rect(surface, UI_PANEL, (self.panel_x, self.panel_y, self.panel_w, self.panel_h), 0, 8)
        pygame.draw.rect(surface, UI_BORDER, (self.panel_x, self.panel_y, self.panel_w, self.panel_h), 2, 8)

        ttl = self.font_lg.render("STORAGE", True, UI_TEXT)
        surface.blit(ttl, (self.panel_x + 20, self.panel_y + 12))

        close_r = pygame.Rect(self.panel_x + self.panel_w - 30, self.panel_y + 8, 22, 22)
        pygame.draw.rect(surface, (120, 40, 40), close_r, 0, 4)
        xt = self.font_md.render("X", True, UI_TEXT)
        surface.blit(xt, (close_r.x + 5, close_r.y + 2))

        il = self.font_sm.render("Inventory", True, UI_TEXT_DIM)
        surface.blit(il, (self.panel_x + 20, self.panel_y + 34))

        if st_rects:
            st_label = self.font_sm.render(
                f"Storage ({len([s for s in storage.slots if s])}/{len(storage.slots)})",
                True,
                UI_TEXT_DIM,
            )
            surface.blit(st_label, (st_rects[0][1].x, self.panel_y + 34))

        prev_r, next_r = self._page_button_rects(storage)
        if prev_r and next_r:
            for rect, label, enabled in (
                (prev_r, "<", self.storage_page > 0),
                (next_r, ">", self.storage_page < page_count - 1),
            ):
                fill = (75, 60, 45) if enabled else (45, 38, 30)
                border = UI_BORDER if enabled else UI_TEXT_DIM
                pygame.draw.rect(surface, fill, rect, 0, 4)
                pygame.draw.rect(surface, border, rect, 1, 4)
                text = self.font_sm.render(label, True, UI_TEXT if enabled else UI_TEXT_DIM)
                surface.blit(text, (rect.centerx - text.get_width() // 2,
                                    rect.centery - text.get_height() // 2))

            page_t = self.font_sm.render(
                f"Page {self.storage_page + 1}/{page_count}",
                True,
                UI_TEXT_DIM,
            )
            surface.blit(page_t, (prev_r.x - page_t.get_width() - 8, self.panel_y + 34))

        for i, r in enumerate(self._inv_rects(inv)):
            bg = item_slot_bg(SLOT_SIZE, self.hovered == ("inv", i), self.selected == ("inv", i))
            surface.blit(bg, r)
            item = inv.slots[i]
            if item:
                self._draw_item(surface, r, item)

        for i, r in enumerate(self._hot_rects()):
            bg = item_slot_bg(SLOT_SIZE, self.hovered == ("hot", i), self.selected == ("hot", i))
            surface.blit(bg, r)
            item = inv.hotbar[i]
            if item:
                self._draw_item(surface, r, item)

        for idx, r in st_rects:
            bg = item_slot_bg(SLOT_SIZE, self.hovered == ("st", idx), self.selected == ("st", idx))
            surface.blit(bg, r)
            item = storage.slots[idx]
            if item:
                self._draw_item(surface, r, item)

        if self.message:
            msg = self.font_sm.render(self.message, True, (255, 220, 80))
            surface.blit(msg, (self.panel_x + 20, self.panel_y + self.panel_h - 36))

        inst = self.font_sm.render(
            "Right-click to quick-transfer  |  Left-click to swap  |  Wheel or arrows to page  |  E to close",
            True,
            UI_TEXT_DIM,
        )
        surface.blit(inst, (self.panel_x + 20, self.panel_y + self.panel_h - 18))

    def _draw_item(self, surface, r, item):
        spr = loot_drop_sprite(item, SLOT_SIZE - 8)
        surface.blit(spr, (r.x + 4, r.y + 4))
        if item.stackable and item.quantity > 1:
            qt = self.font_sm.render(str(item.quantity), True, (255, 255, 200))
            surface.blit(qt, (r.x + SLOT_SIZE - 18, r.y + SLOT_SIZE - 16))
