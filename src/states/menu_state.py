# src/states/menu_state.py
import pygame
import math
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, UI_TEXT, UI_TEXT_DIM, UI_BG
from src.states.base_state import BaseState
from src.save_system import has_save


class MenuState(BaseState):

    def __init__(self, game):
        super().__init__(game)
        self.font_sm, self.font_md, self.font_lg, self.font_xl = self._make_fonts()
        self._t = 0.0

        self._btn_new     = pygame.Rect(SCREEN_WIDTH//2 - 130, SCREEN_HEIGHT//2 - 20, 260, 52)
        self._btn_continue = pygame.Rect(SCREEN_WIDTH//2 - 130, SCREEN_HEIGHT//2 + 50, 260, 52)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    if has_save():
                        self.next = "load"
                    else:
                        self.next = "tavern_new"
                    self.done = True

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos
                if self._btn_new.collidepoint(pos):
                    self.next = "tavern_new"
                    self.done = True
                elif self._btn_continue.collidepoint(pos) and has_save():
                    self.next = "load"
                    self.done = True

    def update(self, dt):
        self._t += dt

    def draw(self, surface):
        # Background gradient
        surface.fill((12, 8, 5))

        # Animated stars
        import random
        rng = random.Random(42)
        for _ in range(80):
            sx = rng.randint(0, SCREEN_WIDTH)
            sy = rng.randint(0, SCREEN_HEIGHT - 120)
            pulse = 0.5 + 0.5 * math.sin(self._t * 0.8 + sx * 0.05)
            pygame.draw.circle(surface, (int(100*pulse), int(90*pulse), int(120*pulse)),
                               (sx, sy), 1)

        # Title
        title_col = (
            int(180 + 60 * math.sin(self._t * 0.5)),
            int(120 + 40 * math.sin(self._t * 0.3)),
            int(200 + 55 * math.sin(self._t * 0.7)),
        )
        ttl = self.font_xl.render("TAVERN LOOTER", True, title_col)
        surface.blit(ttl, (SCREEN_WIDTH//2 - ttl.get_width()//2, 120))

        sub = self.font_md.render("A dark-fantasy survival looter", True, UI_TEXT_DIM)
        surface.blit(sub, (SCREEN_WIDTH//2 - sub.get_width()//2, 175))

        # Portal glow
        glow_r = int(55 + 15 * math.sin(self._t * 1.2))
        glow_surf = pygame.Surface((glow_r*2+4, glow_r*2+4), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (100, 60, 200, 60), (glow_r+2, glow_r+2), glow_r)
        surface.blit(glow_surf, (SCREEN_WIDTH//2 - glow_r - 2, 280 - glow_r - 2))
        pygame.draw.circle(surface, (80, 40, 180), (SCREEN_WIDTH//2, 280), 30)
        pygame.draw.circle(surface, (140, 100, 255), (SCREEN_WIDTH//2, 280), 30, 3)

        # Buttons
        save_exists = has_save()
        mx, my = pygame.mouse.get_pos()

        self._draw_btn(surface, self._btn_new,
                       "New Game", mx, my, always_enabled=True)
        self._draw_btn(surface, self._btn_continue,
                       "Continue" if save_exists else "Continue (no save)",
                       mx, my, always_enabled=save_exists)

        # Controls hint
        ctrl_lines = [
            "WASD — Move     Mouse — Aim     LMB — Attack",
            "E — Inventory   F — Interact    1-5 — Hotbar",
            "ESC — Exit world",
        ]
        for i, line in enumerate(ctrl_lines):
            t = self.font_sm.render(line, True, UI_TEXT_DIM)
            surface.blit(t, (SCREEN_WIDTH//2 - t.get_width()//2,
                              SCREEN_HEIGHT - 80 + i * 18))

    def _draw_btn(self, surface, r, label, mx, my, always_enabled=True):
        hovered = r.collidepoint(mx, my) and always_enabled
        col = (70, 55, 38) if not always_enabled else \
              (90, 70, 50) if hovered else (55, 40, 28)
        border = (140, 110, 70) if hovered else (80, 60, 40)
        pygame.draw.rect(surface, col, r, 0, 8)
        pygame.draw.rect(surface, border, r, 2, 8)
        text_col = (140, 120, 90) if not always_enabled else \
                   (255, 230, 180) if hovered else (200, 175, 130)
        t = self.font_lg.render(label, True, text_col)
        surface.blit(t, (r.centerx - t.get_width()//2, r.centery - t.get_height()//2))
