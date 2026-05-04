# src/states/tavern_state.py
import pygame
import math
from settings import (SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE, HUD_H,
                       HUNGER_DRAIN_TAVERN, UI_TEXT, UI_TEXT_DIM,
                       TAVERN_BG, TAVERN_FLOOR, TAVERN_WALL)
from src.states.base_state import BaseState
from src.entities.player import Player
from src.sprite_factory import (portal_sprite, chest_sprite, bartender_sprite,
                                  get_tile)
from src.ui.hud import HUD
from src.ui.inventory_ui import InventoryUI
from src.ui.shop_ui import ShopUI
from src.ui.storage_ui import StorageUI
from src.ui.portal_ui import PortalUI
from src.systems.economy import build_shop_stock
from src.save_system import save_player, save_world


# ── Tavern layout constants ──
TAVERN_W = 25   # tiles
TAVERN_H = 18
SPAWN_X  = 6 * TILE_SIZE + TILE_SIZE // 2
SPAWN_Y  = 9 * TILE_SIZE + TILE_SIZE // 2


class TavernState(BaseState):

    def __init__(self, game):
        super().__init__(game)
        self.font_sm, self.font_md, self.font_lg, self.font_xl = self._make_fonts()

        self.player   = None
        self.hud      = HUD(self.font_sm, self.font_md, self.font_lg)
        self.inv_ui   = InventoryUI(self.font_sm, self.font_md, self.font_lg)
        self.shop_ui  = ShopUI(self.font_sm, self.font_md, self.font_lg)
        self.stor_ui  = StorageUI(self.font_sm, self.font_md, self.font_lg)
        self.portal_ui = PortalUI(self.font_sm, self.font_md, self.font_lg, self.font_xl)

        self._shop_stock = []
        self._build_map()

        # Notification system
        self.notif_text  = ""
        self.notif_timer = 0.0

        # Active hotbar index
        self.hotbar_idx = 0

        # Camera offset for tavern scroll (center on player)
        self._cam_x = 0
        self._cam_y = 0

        self._portal_pulse = 0.0

    def _build_map(self):
        """Build the fixed tavern tilemap and interactables."""
        W, H  = TAVERN_W, TAVERN_H
        self.tiles = []   # (x_px, y_px, type)

        # Floor everywhere
        for row in range(H):
            for col in range(W):
                is_wall = (row == 0 or row == H-1 or col == 0 or col == W-1)
                self.tiles.append((col * TILE_SIZE, row * TILE_SIZE,
                                   "tavern_wall" if is_wall else "tavern_floor"))

        # Interior walls (bar area top-center)
        self._wall_rects = []
        for col in range(W):
            for row in [0, H-1]:
                self._wall_rects.append(pygame.Rect(col*TILE_SIZE, row*TILE_SIZE,
                                                    TILE_SIZE, TILE_SIZE))
        for row in range(H):
            for col in [0, W-1]:
                if pygame.Rect(col*TILE_SIZE, row*TILE_SIZE, TILE_SIZE, TILE_SIZE) \
                        not in self._wall_rects:
                    self._wall_rects.append(pygame.Rect(col*TILE_SIZE, row*TILE_SIZE,
                                                         TILE_SIZE, TILE_SIZE))
        # Bar counter (row 3, cols 8-14)
        for col in range(8, 15):
            r = pygame.Rect(col*TILE_SIZE, 3*TILE_SIZE, TILE_SIZE, TILE_SIZE)
            self._wall_rects.append(r)

        # Interactables
        self.bartender_pos = (11 * TILE_SIZE + TILE_SIZE//2, 2 * TILE_SIZE + TILE_SIZE//2)
        self.storage_pos   = (3  * TILE_SIZE + TILE_SIZE//2, 4 * TILE_SIZE + TILE_SIZE//2)
        self.portal_pos    = (21 * TILE_SIZE + TILE_SIZE//2, 9 * TILE_SIZE + TILE_SIZE//2)

        # Pre-render static world surface
        total_w = TAVERN_W * TILE_SIZE
        total_h = TAVERN_H * TILE_SIZE
        self._world_surf = pygame.Surface((total_w, total_h))
        self._world_surf.fill(TAVERN_BG)
        floor_t = get_tile("tavern_floor")
        wall_t  = get_tile("tavern_wall")
        for col in range(TAVERN_W):
            for row in range(TAVERN_H):
                is_wall = (row == 0 or row == TAVERN_H-1 or
                           col == 0 or col == TAVERN_W-1)
                surf = wall_t if is_wall else floor_t
                self._world_surf.blit(surf, (col*TILE_SIZE, row*TILE_SIZE))

        # Bar counter
        for col in range(8, 15):
            pygame.draw.rect(self._world_surf, (90, 55, 25),
                             (col*TILE_SIZE, 3*TILE_SIZE, TILE_SIZE, TILE_SIZE))
            pygame.draw.rect(self._world_surf, (110, 70, 35),
                             (col*TILE_SIZE, 3*TILE_SIZE, TILE_SIZE, TILE_SIZE), 2)

        # Decorative elements
        # Torches on walls
        for tx in [3*TILE_SIZE, 18*TILE_SIZE]:
            for ty in [2*TILE_SIZE, 15*TILE_SIZE]:
                pygame.draw.circle(self._world_surf, (255, 180, 50), (tx, ty), 6)
                pygame.draw.circle(self._world_surf, (255, 120, 20), (tx, ty), 4)

        # Sprites
        self._bartender_spr = bartender_sprite(32)
        self._chest_spr     = chest_sprite(32)
        self._portal_spr    = portal_sprite(56)

    def on_enter(self, prev_state=None):
        pd = self.game.player_data
        revived = False

        # Recover broken or old saves that enter the tavern with no survivable state.
        if pd.get("health", 0) <= 0:
            pd["health"] = max(1, pd.get("max_health", 100) * 0.3)
            revived = True
        if pd.get("hunger", 0) <= 0:
            pd["hunger"] = max(25, pd.get("max_hunger", 100) * 0.25)
            revived = True

        # Heal/restore slightly when entering tavern after a successful run
        if prev_state == "world":
            self._notify("Run complete! Welcome back.")
        elif revived:
            self._notify("Recovered you in the tavern to prevent a dead save.")

        self.player = Player(SPAWN_X, SPAWN_Y, pd)

        # Refresh shop stock on each visit
        boss_kills = pd.get("boss_kills", 0)
        tier       = pd.get("highest_tier", 0)
        self._shop_stock = build_shop_stock(boss_kills, tier)

        # Auto-save
        save_player(pd)

    def handle_events(self, events):
        pd = self.game.player_data
        any_menu = self.inv_ui.visible or self.shop_ui.visible or \
                   self.stor_ui.visible or self.portal_ui.visible

        for event in events:
            # Portal UI
            if self.portal_ui.visible:
                result = self.portal_ui.handle_event(event)
                if result == "new":
                    self.next = "world_new"
                    self.done = True
                elif result == "revisit":
                    self.next = "world_revisit"
                    self.done = True
                elif result == "boss1":
                    self.next = "boss1"
                    self.done = True
                elif result == "boss2":
                    self.next = "boss2"
                    self.done = True
                continue

            # Shop UI
            if self.shop_ui.handle_event(event, pd):
                continue

            # Storage UI
            if self.stor_ui.handle_event(event, pd):
                continue

            # Inventory UI
            inv_was_open = self.inv_ui.visible
            action = self.inv_ui.handle_event(event, pd["inventory"])
            if action and action.get("action") == "eat":
                loc = action["loc"]
                ltype, idx = loc
                if ltype == "hot":
                    self.player.eat(idx)
                continue
            if inv_was_open:
                continue

            if event.type == pygame.KEYDOWN:
                k = event.key
                if k == pygame.K_e:
                    self.inv_ui.toggle()
                elif k in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5):
                    self.hotbar_idx = k - pygame.K_1
                elif k == pygame.K_f:
                    self._interact()

            if event.type == pygame.MOUSEWHEEL:
                self.hotbar_idx = (self.hotbar_idx - event.y) % 5

    def _interact(self):
        px, py = self.player.rect.centerx, self.player.rect.centery
        pd = self.game.player_data

        # Bartender
        bx, by = self.bartender_pos
        if math.hypot(px - bx, py - by) < 80:
            self.shop_ui.open(self._shop_stock)
            return

        # Storage
        sx, sy = self.storage_pos
        if math.hypot(px - sx, py - sy) < 80:
            self.stor_ui.open()
            return

        # Portal
        ppx, ppy = self.portal_pos
        if math.hypot(px - ppx, py - ppy) < 80:
            saved = self.game.player_data.get("saved_world")
            self.portal_ui.open(
                has_saved=saved is not None,
                saved_world=saved,
                boss_kills=pd.get("boss_kills", 0),
            )
            return

    def update(self, dt):
        if self.done:
            return
        pd = self.game.player_data
        menu_open = (self.inv_ui.visible or self.shop_ui.visible or
                     self.stor_ui.visible or self.portal_ui.visible)

        keys = pygame.key.get_pressed()
        mouse = pygame.mouse.get_pos()
        world_rect = pygame.Rect(0, 0, TAVERN_W * TILE_SIZE, TAVERN_H * TILE_SIZE)

        # Translate mouse to world coords for aiming
        mx = mouse[0] + self._cam_x
        my = mouse[1] + self._cam_y

        self.player.update(dt, keys, (mx, my), world_rect,
                           in_tavern=True, menu_open=menu_open,
                           collision_rects=self._wall_rects)

        # Portal pulse
        self._portal_pulse += dt

        # Notification
        if self.notif_timer > 0:
            self.notif_timer -= dt

        # Shop update
        self.shop_ui.update(dt)

        # Camera follow
        view_w = SCREEN_WIDTH
        view_h = SCREEN_HEIGHT - HUD_H
        self._cam_x = max(0, min(self.player.pos.x - view_w // 2,
                                  TAVERN_W * TILE_SIZE - view_w))
        self._cam_y = max(0, min(self.player.pos.y - view_h // 2,
                                  TAVERN_H * TILE_SIZE - view_h))

        # Proximity hints
        px, py = self.player.rect.centerx, self.player.rect.centery
        if math.hypot(px - self.portal_pos[0], py - self.portal_pos[1]) < 80:
            self._hint = "Press F — Enter portal"
        elif math.hypot(px - self.bartender_pos[0], py - self.bartender_pos[1]) < 80:
            self._hint = "Press F — Talk to Bartender"
        elif math.hypot(px - self.storage_pos[0], py - self.storage_pos[1]) < 80:
            self._hint = "Press F — Open Storage"
        else:
            self._hint = ""

    def draw(self, surface):
        surface.fill(TAVERN_BG)
        cx, cy = int(self._cam_x), int(self._cam_y)

        # World
        surface.blit(self._world_surf, (-cx, -cy))

        # Portal (animated)
        pulse = abs(math.sin(self._portal_pulse * 1.5))
        pp = self._portal_spr.copy()
        pp.set_alpha(int(180 + 75 * pulse))
        px_scr = self.portal_pos[0] - cx - 28
        py_scr = self.portal_pos[1] - cy - 28
        surface.blit(pp, (px_scr, py_scr))
        plab = self.font_sm.render("PORTAL", True, (160, 120, 255))
        surface.blit(plab, (px_scr + 8, py_scr + 58))

        # Storage chest
        scx = self.storage_pos[0] - cx - 16
        scy = self.storage_pos[1] - cy - 16
        surface.blit(self._chest_spr, (scx, scy))
        boss_kills = self.game.player_data.get("boss_kills", 0)
        from settings import STORAGE_SIZES
        cap = STORAGE_SIZES[min(boss_kills, len(STORAGE_SIZES)-1)]
        used = len([s for s in self.game.player_data["storage"].slots if s])
        slab = self.font_sm.render(f"Storage {used}/{cap}", True, (180, 150, 100))
        surface.blit(slab, (scx - 12, scy + 34))

        # Bartender
        bx = self.bartender_pos[0] - cx - 16
        by = self.bartender_pos[1] - cy - 16
        surface.blit(self._bartender_spr, (bx, by))
        blab = self.font_sm.render("Bartender", True, (200, 170, 120))
        surface.blit(blab, (bx - 10, by + 34))

        # Player
        p_scr_x = self.player.rect.x - cx
        p_scr_y = self.player.rect.y - cy
        from src.sprite_factory import player_sprite
        surface.blit(self.player.image, (p_scr_x, p_scr_y))

        # Proximity hint
        if hasattr(self, "_hint") and self._hint:
            ht = self.font_md.render(self._hint, True, (255, 230, 100))
            surface.blit(ht, (SCREEN_WIDTH//2 - ht.get_width()//2, SCREEN_HEIGHT - HUD_H - 40))

        # HUD
        self.hud.draw(surface, self.player, self.hotbar_idx,
                      self.notif_text, self.notif_timer)

        # UI overlays
        self.inv_ui.draw(surface, self.game.player_data["inventory"])
        self.shop_ui.draw(surface, self.game.player_data)
        self.stor_ui.draw(surface, self.game.player_data)
        self.portal_ui.draw(surface, self.game.player_data.get("boss_kills", 0))

        # Game title + info strip (top-left when no menu)
        if not (self.inv_ui.visible or self.shop_ui.visible or self.stor_ui.visible):
            info = self.font_sm.render(
                f"Boss kills: {self.game.player_data.get('boss_kills',0)}  |  "
                f"Worlds cleared: {self.game.player_data.get('worlds_cleared',0)}",
                True, UI_TEXT_DIM)
            surface.blit(info, (8, 4))

    def _notify(self, text):
        self.notif_text  = text
        self.notif_timer = 3.0
