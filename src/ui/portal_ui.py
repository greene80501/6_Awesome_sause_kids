# src/ui/portal_ui.py
import pygame
from settings import (SCREEN_WIDTH, SCREEN_HEIGHT, UI_BG, UI_PANEL, UI_BORDER,
                       UI_TEXT, UI_TEXT_DIM, FONT_SM, FONT_MD, FONT_LG, FONT_XL)
from src.world_gen.biomes import BIOMES


class PortalUI:
    """World selection screen shown when using the portal."""

    def __init__(self, font_sm, font_md, font_lg, font_xl):
        self.font_sm = font_sm
        self.font_md = font_md
        self.font_lg = font_lg
        self.font_xl = font_xl

        self.visible      = False
        self.has_saved    = False
        self.saved_name   = ""
        self.saved_biome  = ""
        self.saved_type   = ""
        self.preview_data = None   # WorldData for preview

        self.pw = 560
        self.ph = 380
        self.px = SCREEN_WIDTH  // 2 - self.pw // 2
        self.py = SCREEN_HEIGHT // 2 - self.ph // 2

        # Buttons
        self.btn_revisit = pygame.Rect(self.px + 40, self.py + 100, 220, 60)
        self.btn_new     = pygame.Rect(self.px + 40, self.py + 180, 220, 60)
        self.btn_boss1   = pygame.Rect(self.px + 300, self.py + 100, 220, 60)
        self.btn_boss2   = pygame.Rect(self.px + 300, self.py + 180, 220, 60)
        self.btn_cancel  = pygame.Rect(self.px + self.pw//2 - 80, self.py + self.ph - 60, 160, 40)

        self.result = None

    def open(self, has_saved, saved_world=None, boss_kills=0):
        self.has_saved  = has_saved
        self.visible    = True
        self.result     = None
        self.boss_kills = boss_kills
        if saved_world:
            self.saved_name  = saved_world.get("name", "Unknown World")
            self.saved_biome = saved_world.get("biome", "")
            self.saved_type  = saved_world.get("world_type", "")
        else:
            self.saved_name = ""

    def close(self):
        self.visible = False
        self.result  = None

    def handle_event(self, event):
        if not self.visible:
            return None

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.close()
            return "cancel"

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos

            if self.btn_cancel.collidepoint(pos):
                self.close()
                return "cancel"

            if self.has_saved and self.btn_revisit.collidepoint(pos):
                self.close()
                return "revisit"

            if self.btn_new.collidepoint(pos):
                self.close()
                return "new"

            if self.boss_kills >= 0 and self.btn_boss1.collidepoint(pos):
                self.close()
                return "boss1"

            if self.boss_kills >= 1 and self.btn_boss2.collidepoint(pos):
                self.close()
                return "boss2"

        return None

    def draw(self, surface, boss_kills):
        if not self.visible:
            return

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        pygame.draw.rect(surface, UI_PANEL,  (self.px, self.py, self.pw, self.ph), 0, 10)
        pygame.draw.rect(surface, UI_BORDER, (self.px, self.py, self.pw, self.ph), 2, 10)

        # Title
        ttl = self.font_xl.render("THE PORTAL", True, (140, 100, 255))
        surface.blit(ttl, (self.px + self.pw//2 - ttl.get_width()//2, self.py + 14))
        sub = self.font_sm.render("Choose your destination", True, UI_TEXT_DIM)
        surface.blit(sub, (self.px + self.pw//2 - sub.get_width()//2, self.py + 52))

        # ── Re-enter saved world ──
        if self.has_saved:
            self._btn(surface, self.btn_revisit, (50, 80, 50),
                      f"Re-enter:", f"{self.saved_name}")
        else:
            self._btn_disabled(surface, self.btn_revisit, "No saved world")

        # ── Generate new world ──
        self._btn(surface, self.btn_new, (40, 50, 90),
                  "Generate New World", "Replaces saved slot")

        # ── Boss 1 ──
        b1_locked = False
        b1_done   = boss_kills >= 1
        self._btn(surface, self.btn_boss1,
                  (60, 20, 20) if not b1_done else (20, 60, 20),
                  "Boss 1: The Warden",
                  "Defeated ✓" if b1_done else "Always available",
                  done=b1_done)

        # ── Boss 2 ──
        b2_locked = boss_kills < 1
        b2_done   = boss_kills >= 2
        self._btn(surface, self.btn_boss2,
                  (40, 10, 10) if not b2_locked else (30, 30, 30),
                  "Boss 2: The Hellborn",
                  "Defeated ✓" if b2_done else ("Locked — defeat Boss 1 first" if b2_locked else "Unlocked"),
                  locked=b2_locked, done=b2_done)

        # Cancel button
        pygame.draw.rect(surface, (60, 40, 30), self.btn_cancel, 0, 6)
        pygame.draw.rect(surface, UI_BORDER, self.btn_cancel, 1, 6)
        ct = self.font_md.render("Cancel (Esc)", True, UI_TEXT)
        surface.blit(ct, (self.btn_cancel.centerx - ct.get_width()//2,
                           self.btn_cancel.centery - ct.get_height()//2))

    def _btn(self, surface, r, col, line1, line2, locked=False, done=False):
        c = (30, 30, 30) if locked else col
        pygame.draw.rect(surface, c, r, 0, 6)
        border_col = (80, 80, 80) if locked else ((50, 160, 50) if done else UI_BORDER)
        pygame.draw.rect(surface, border_col, r, 2, 6)
        text_col = UI_TEXT_DIM if locked else UI_TEXT
        l1 = self.font_md.render(line1, True, text_col)
        l2 = self.font_sm.render(line2, True, UI_TEXT_DIM)
        surface.blit(l1, (r.x + 10, r.y + 10))
        surface.blit(l2, (r.x + 10, r.y + 32))

    def _btn_disabled(self, surface, r, label):
        pygame.draw.rect(surface, (30, 30, 30), r, 0, 6)
        pygame.draw.rect(surface, (50, 50, 50), r, 1, 6)
        t = self.font_md.render(label, True, UI_TEXT_DIM)
        surface.blit(t, (r.centerx - t.get_width()//2, r.centery - t.get_height()//2))


# ─────────────────────────────────────────────
#  Ground items panel
# ─────────────────────────────────────────────
class GroundPanel:
    """Shows nearby loot when inventory is open."""

    def __init__(self, font_sm, font_md):
        self.font_sm = font_sm
        self.font_md = font_md
        self.items   = []    # list of LootDrop / CoinDrop nearby

    def update(self, nearby_drops):
        self.items = list(nearby_drops)[:8]

    def draw(self, surface):
        if not self.items:
            return
        from settings import SLOT_SIZE, SLOT_GAP, UI_PANEL, UI_BORDER, UI_TEXT
        from src.sprite_factory import loot_drop_sprite
        num = len(self.items)
        panel_w = num * (SLOT_SIZE + SLOT_GAP) + 20
        panel_h = SLOT_SIZE + 30
        px = SCREEN_WIDTH  // 2 - panel_w // 2
        py = 10

        pygame.draw.rect(surface, UI_PANEL,  (px, py, panel_w, panel_h), 0, 6)
        pygame.draw.rect(surface, UI_BORDER, (px, py, panel_w, panel_h), 1, 6)
        lbl = self.font_sm.render("Nearby items (F to pick up)", True, UI_TEXT)
        surface.blit(lbl, (px + 8, py + 4))

        for i, drop in enumerate(self.items):
            sx = px + 10 + i * (SLOT_SIZE + SLOT_GAP)
            sy = py + 18
            from src.sprite_factory import item_slot_bg
            bg = item_slot_bg(SLOT_SIZE)
            surface.blit(bg, (sx, sy))
            if hasattr(drop, "item"):
                spr = loot_drop_sprite(drop.item, SLOT_SIZE - 8)
                surface.blit(spr, (sx + 4, sy + 4))
