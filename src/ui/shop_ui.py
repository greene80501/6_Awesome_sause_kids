# src/ui/shop_ui.py
import pygame
from settings import (SCREEN_WIDTH, SCREEN_HEIGHT, SLOT_SIZE, SLOT_GAP,
                       RARITY_COLORS, UI_BG, UI_PANEL, UI_BORDER,
                       UI_TEXT, UI_TEXT_DIM, UI_HIGHLIGHT, FONT_SM, FONT_MD, FONT_LG)
from src.sprite_factory import loot_drop_sprite, item_slot_bg


class ShopUI:
    """Bartender shop: Buy stock, sell from inventory, repair gear."""

    TABS = ["Buy", "Sell", "Repair"]

    def __init__(self, font_sm, font_md, font_lg):
        self.font_sm = font_sm
        self.font_md = font_md
        self.font_lg = font_lg

        self.visible  = False
        self.tab      = 0       # 0=buy 1=sell 2=repair
        self.hovered  = None
        self.selected = None
        self.stock    = []      # list of Items
        self.message  = ""
        self.msg_timer = 0.0

        self.panel_w = 640
        self.panel_h = 460
        self.panel_x = SCREEN_WIDTH  // 2 - self.panel_w // 2
        self.panel_y = SCREEN_HEIGHT // 2 - self.panel_h // 2

    def open(self, stock):
        self.stock   = list(stock)
        self.visible = True
        self.tab     = 0
        self.selected = None

    def close(self):
        self.visible  = False
        self.selected = None

    def update(self, dt):
        if self.msg_timer > 0:
            self.msg_timer -= dt

    def handle_event(self, event, player_data):
        if not self.visible:
            return False
        inventory = player_data["inventory"]

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_e):
                self.close()
                return True
            if event.key == pygame.K_TAB:
                self.tab = (self.tab + 1) % 3
                self.selected = None
                return True

        if event.type == pygame.MOUSEMOTION:
            self.hovered = self._hit_item(event.pos, inventory)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Check tab clicks
            for i, label in enumerate(self.TABS):
                tr = self._tab_rect(i)
                if tr.collidepoint(event.pos):
                    self.tab = i
                    self.selected = None
                    return True

            idx = self._hit_item(event.pos, inventory)
            if idx is not None:
                self._execute(idx, player_data)
                return True

            # Close button
            close_r = pygame.Rect(self.panel_x + self.panel_w - 30, self.panel_y + 8, 22, 22)
            if close_r.collidepoint(event.pos):
                self.close()
                return True

        return self.visible

    def _execute(self, idx, player_data):
        inventory = player_data["inventory"]
        coins = player_data["coins"]

        if self.tab == 0:  # Buy
            if idx >= len(self.stock):
                return
            item = self.stock[idx]
            cost = item.buy_value
            if coins < cost:
                self._msg("Not enough coins!")
                return
            added = inventory.add_item(item.clone())
            if not added:
                self._msg("Inventory full!")
                return
            player_data["coins"] -= cost
            self.stock.pop(idx)
            self._msg(f"Bought {item.display_name} for {cost}g")

        elif self.tab == 1:  # Sell
            all_items = self._get_sell_items(inventory)
            if idx >= len(all_items):
                return
            loc, item = all_items[idx]
            sv = item.sell_value
            # Remove from inventory
            ltype, lidx = loc
            if ltype == "inv":   inventory.slots[lidx] = None
            elif ltype == "hot": inventory.hotbar[lidx] = None
            elif ltype == "eq":  inventory.equip[lidx]  = None
            player_data["coins"] += sv
            self._msg(f"Sold {item.display_name} for {sv}g")

        elif self.tab == 2:  # Repair
            all_gear = self._get_repair_items(inventory)
            if idx >= len(all_gear):
                return
            loc, item = all_gear[idx]
            cost = item.repair_cost()
            if coins < cost:
                self._msg("Not enough coins!")
                return
            player_data["coins"] -= cost
            item.repair(item.max_durability)
            self._msg(f"Repaired {item.display_name} for {cost}g")

    def _msg(self, text):
        self.message   = text
        self.msg_timer = 2.5

    def _get_sell_items(self, inv):
        items = []
        for i, s in enumerate(inv.slots):
            if s: items.append((("inv", i), s))
        for i, s in enumerate(inv.hotbar):
            if s: items.append((("hot", i), s))
        for k, v in inv.equip.items():
            if v: items.append((("eq", k), v))
        return items

    def _get_repair_items(self, inv):
        items = []
        for i, s in enumerate(inv.slots):
            if s and hasattr(s, "max_durability") and s.durability < s.max_durability:
                items.append((("inv", i), s))
        for k, v in inv.equip.items():
            if v and hasattr(v, "max_durability") and v.durability < v.max_durability:
                items.append((("eq", k), v))
        return items

    def _hit_item(self, pos, inventory):
        rects = self._item_rects(inventory)
        for i, r in enumerate(rects):
            if r.collidepoint(pos):
                return i
        return None

    def _item_rects(self, inventory):
        rects = []
        cols = 5
        ox = self.panel_x + 20
        oy = self.panel_y + 80
        items = self._current_items(inventory)
        for i in range(len(items)):
            col = i % cols
            row = i // cols
            rects.append(pygame.Rect(ox + col * (SLOT_SIZE + SLOT_GAP),
                                     oy + row * (SLOT_SIZE + SLOT_GAP),
                                     SLOT_SIZE, SLOT_SIZE))
        return rects

    def _current_items(self, inventory):
        if self.tab == 0: return [(None, s) for s in self.stock]
        if self.tab == 1: return self._get_sell_items(inventory)
        if self.tab == 2: return self._get_repair_items(inventory)
        return []

    def _tab_rect(self, i):
        tw = 100
        return pygame.Rect(self.panel_x + 20 + i * (tw + 8),
                           self.panel_y + 46, tw, 26)

    def draw(self, surface, player_data):
        if not self.visible:
            return

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        surface.blit(overlay, (0, 0))

        pygame.draw.rect(surface, UI_PANEL,  (self.panel_x, self.panel_y, self.panel_w, self.panel_h), 0, 8)
        pygame.draw.rect(surface, UI_BORDER, (self.panel_x, self.panel_y, self.panel_w, self.panel_h), 2, 8)

        ttl = self.font_lg.render("BARTENDER", True, (220, 180, 100))
        surface.blit(ttl, (self.panel_x + 20, self.panel_y + 10))

        # Coins
        coins_t = self.font_md.render(f"Your coins: {player_data['coins']}g",
                                       True, (255, 215, 0))
        surface.blit(coins_t, (self.panel_x + self.panel_w - coins_t.get_width() - 40,
                                self.panel_y + 14))

        # Close button
        close_r = pygame.Rect(self.panel_x + self.panel_w - 30, self.panel_y + 8, 22, 22)
        pygame.draw.rect(surface, (120, 40, 40), close_r, 0, 4)
        xt = self.font_md.render("X", True, UI_TEXT)
        surface.blit(xt, (close_r.x + 5, close_r.y + 2))

        # Tabs
        for i, label in enumerate(self.TABS):
            r = self._tab_rect(i)
            col = UI_HIGHLIGHT if i == self.tab else UI_PANEL
            pygame.draw.rect(surface, col, r, 0, 4)
            pygame.draw.rect(surface, UI_BORDER, r, 1, 4)
            lt = self.font_md.render(label, True, UI_TEXT)
            surface.blit(lt, (r.x + r.w//2 - lt.get_width()//2, r.y + 4))

        # Items grid
        inventory = player_data["inventory"]
        items    = self._current_items(inventory)
        rects    = self._item_rects(inventory)

        for i, (loc, item) in enumerate(items):
            if i >= len(rects):
                break
            r   = rects[i]
            hov = (self.hovered == i)
            bg  = item_slot_bg(SLOT_SIZE, hov)
            surface.blit(bg, r)
            spr = loot_drop_sprite(item, SLOT_SIZE - 8)
            surface.blit(spr, (r.x + 4, r.y + 4))
            if item.stackable and item.quantity > 1:
                qt = self.font_sm.render(str(item.quantity), True, (255, 255, 200))
                surface.blit(qt, (r.x + SLOT_SIZE - 18, r.y + SLOT_SIZE - 16))
            if item.broken:
                bt = self.font_sm.render("!", True, (220, 50, 50))
                surface.blit(bt, (r.x + 2, r.y + 2))

        # Tooltip on hover
        if self.hovered is not None and self.hovered < len(items):
            _, item = items[self.hovered]
            self._draw_tooltip(surface, item, player_data["coins"])

        # Message
        if self.message and self.msg_timer > 0:
            mt = self.font_md.render(self.message, True, (255, 220, 80))
            surface.blit(mt, (self.panel_x + 20, self.panel_y + self.panel_h - 36))

        # Tab-specific hint
        hints = {
            0: "Click item to BUY",
            1: "Click item to SELL",
            2: "Click item to REPAIR (restores full durability)",
        }
        ht = self.font_sm.render(hints[self.tab], True, UI_TEXT_DIM)
        surface.blit(ht, (self.panel_x + 20, self.panel_y + self.panel_h - 18))

    def _draw_tooltip(self, surface, item, player_coins):
        extra = ""
        if self.tab == 0:
            extra = f"Cost: {item.buy_value}g"
            if item.buy_value > player_coins:
                extra += "  (can't afford)"
        elif self.tab == 1:
            extra = f"Sell value: {item.sell_value}g"
        elif self.tab == 2:
            extra = f"Repair cost: {item.repair_cost()}g"

        lines = [item.display_name, item.stat_line(), item.desc, extra]
        if item.broken:
            lines.insert(1, "*** BROKEN ***")

        tw = 260
        th = len(lines) * 18 + 16
        mx, my = pygame.mouse.get_pos()
        tx = min(mx + 14, SCREEN_WIDTH  - tw - 4)
        ty = min(my + 14, SCREEN_HEIGHT - th - 4)

        pygame.draw.rect(surface, UI_BG, (tx, ty, tw, th), 0, 6)
        pygame.draw.rect(surface, RARITY_COLORS.get(item.rarity, UI_BORDER),
                         (tx, ty, tw, th), 1, 6)
        for i, line in enumerate(lines):
            col = RARITY_COLORS.get(item.rarity, UI_TEXT) if i == 0 else UI_TEXT
            if "BROKEN" in line: col = (220, 50, 50)
            t = self.font_sm.render(line, True, col)
            surface.blit(t, (tx + 8, ty + 8 + i * 18))
