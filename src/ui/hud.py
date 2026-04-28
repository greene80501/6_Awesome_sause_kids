# src/ui/hud.py
import pygame
from settings import (SCREEN_WIDTH, SCREEN_HEIGHT, HUD_H, SLOT_SIZE, SLOT_GAP,
                       RARITY_COLORS, UI_BG, UI_PANEL, UI_BORDER, UI_TEXT,
                       UI_TEXT_DIM, FONT_SM, FONT_MD, FONT_LG)
from src.sprite_factory import loot_drop_sprite, item_slot_bg


class HUD:
    def __init__(self, font_sm, font_md, font_lg):
        self.font_sm = font_sm
        self.font_md = font_md
        self.font_lg = font_lg
        self.y = SCREEN_HEIGHT - HUD_H
        self._bar_w = 180
        self._bar_h = 14

    def draw(self, surface, player, active_hotbar=0, notification=None, notif_timer=0):
        # Panel background
        pygame.draw.rect(surface, UI_BG, (0, self.y, SCREEN_WIDTH, HUD_H))
        pygame.draw.line(surface, UI_BORDER, (0, self.y), (SCREEN_WIDTH, self.y), 2)

        x = 12
        y = self.y + 6

        # ── Health bar ──
        self._draw_bar(surface, x, y,      self._bar_w, self._bar_h,
                       player.health, player.data["max_health"],
                       (200, 50, 50), (80, 20, 20), "HP")

        # ── Hunger bar ──
        self._draw_bar(surface, x, y + 20, self._bar_w, self._bar_h,
                       player.hunger, player.data["max_hunger"],
                       (200, 160, 50), (80, 60, 20), "HN")

        # ── Coins ──
        coin_x = x + self._bar_w + 16
        pygame.draw.circle(surface, (255, 215, 0), (coin_x + 7, y + 5), 7)
        coins_txt = self.font_md.render(str(player.data["coins"]), True, (255, 215, 0))
        surface.blit(coins_txt, (coin_x + 18, y))

        # ── Equipped weapon info ──
        weap = player.inventory.equip.get("weapon")
        if weap:
            name_col = RARITY_COLORS.get(weap.rarity, (180, 180, 180))
            nt = self.font_sm.render(weap.display_name, True, name_col)
            surface.blit(nt, (coin_x, y + 22))
            # Durability
            dur_pct = weap.dur_pct
            dur_col = (200, 50, 50) if dur_pct < 0.25 else (200, 180, 60) if dur_pct < 0.6 else (80, 180, 80)
            dt = self.font_sm.render(f"DUR {weap.durability}/{weap.max_durability}", True, dur_col)
            surface.blit(dt, (coin_x + nt.get_width() + 8, y + 22))

        # ── Hotbar ──
        hb_total = (SLOT_SIZE + SLOT_GAP) * 5 - SLOT_GAP
        hb_x = SCREEN_WIDTH // 2 - hb_total // 2
        hb_y = self.y + (HUD_H - SLOT_SIZE) // 2

        for i, item in enumerate(player.inventory.hotbar):
            sx = hb_x + i * (SLOT_SIZE + SLOT_GAP)
            highlighted = (i == active_hotbar)
            bg = item_slot_bg(SLOT_SIZE, highlighted)
            surface.blit(bg, (sx, hb_y))

            if item:
                spr = loot_drop_sprite(item, SLOT_SIZE - 8)
                surface.blit(spr, (sx + 4, hb_y + 4))
                if item.stackable and item.quantity > 1:
                    qt = self.font_sm.render(str(item.quantity), True, UI_TEXT)
                    surface.blit(qt, (sx + SLOT_SIZE - 18, hb_y + SLOT_SIZE - 16))

            # Slot number
            num_t = self.font_sm.render(str(i + 1), True, UI_TEXT_DIM)
            surface.blit(num_t, (sx + 3, hb_y + 2))

            # Active border
            if highlighted:
                pygame.draw.rect(surface, (255, 215, 0), (sx, hb_y, SLOT_SIZE, SLOT_SIZE), 2)

        # ── Minimap ──
        self._draw_minimap(surface, player)

        # ── Notification ──
        if notification and notif_timer > 0:
            alpha = min(255, int(notif_timer * 500))
            nt = self.font_md.render(notification, True, (255, 230, 100))
            nt.set_alpha(alpha)
            nx = SCREEN_WIDTH // 2 - nt.get_width() // 2
            surface.blit(nt, (nx, self.y - 30))

        # ── Objective indicator ──
        # (passed from world state if active)

    def _draw_bar(self, surface, x, y, w, h, val, maxval, col, bg_col, label):
        pct = max(0, min(1, val / maxval)) if maxval > 0 else 0
        pygame.draw.rect(surface, bg_col, (x, y, w, h), 0, 3)
        if pct > 0:
            pygame.draw.rect(surface, col, (x, y, int(w * pct), h), 0, 3)
        pygame.draw.rect(surface, UI_BORDER, (x, y, w, h), 1, 3)
        lbl = self.font_sm.render(f"{label} {int(val)}/{int(maxval)}", True, UI_TEXT)
        surface.blit(lbl, (x + 3, y))

    def _draw_minimap(self, surface, player):
        mm_size = 80
        mm_x = SCREEN_WIDTH - mm_size - 10
        mm_y = self.y + (HUD_H - mm_size) // 2

        from settings import WORLD_W, WORLD_H, TILE_SIZE
        # Background
        pygame.draw.rect(surface, (20, 15, 10), (mm_x, mm_y, mm_size, mm_size))
        pygame.draw.rect(surface, UI_BORDER, (mm_x, mm_y, mm_size, mm_size), 1)

        # Player dot
        px = player.pos.x / (WORLD_W * TILE_SIZE) * mm_size
        py = player.pos.y / (WORLD_H * TILE_SIZE) * mm_size
        pygame.draw.circle(surface, (80, 200, 80),
                           (mm_x + int(px), mm_y + int(py)), 3)
