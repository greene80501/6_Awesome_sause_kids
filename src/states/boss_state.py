# src/states/boss_state.py
import pygame
import math
import random
from settings import (SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE, HUD_H,
                       UI_TEXT, UI_TEXT_DIM, UI_BG, UI_PANEL, UI_BORDER,
                       RARITY_COLORS)
from src.states.base_state import BaseState
from src.entities.player import Player
from src.entities.enemy import Enemy
from src.entities.loot_drop import LootDrop, CoinDrop
from src.sprite_factory import portal_sprite
from src.camera import Camera
from src.ui.hud import HUD
from src.ui.inventory_ui import InventoryUI
from src.systems.loot_tables import make_boss_loot
from src.save_system import save_player


# Boss arena dimensions
ARENA_W = 40
ARENA_H = 30


class BossData:
    """Defines the two bosses."""

    BOSS1 = {
        "id": 1, "name": "The Warden",
        "hp": 600, "touch_dmg": 18, "speed": 85, "size": 52,
        "color": (80, 160, 140), "aggro": 500,
        "phase2_hp": 0.45,   # fraction of max HP where phase 2 starts
        "arena_bg": (30, 50, 45),
        "wall_col": (40, 65, 55),
        "loot_bonus": 5,
        "description": "Guardian of the dungeon threshold.",
        "phase2_msg": "The Warden enrages!",
    }
    BOSS2 = {
        "id": 2, "name": "The Hellborn",
        "hp": 1100, "touch_dmg": 28, "speed": 95, "size": 60,
        "color": (200, 55, 30), "aggro": 500,
        "phase2_hp": 0.40,
        "arena_bg": (45, 12, 8),
        "wall_col": (60, 18, 10),
        "loot_bonus": 8,
        "description": "Ancient evil sealed in hellfire.",
        "phase2_msg": "The Hellborn erupts in hellfire!",
    }


class BossEnemy:
    """Special boss entity with phases and patterns."""

    def __init__(self, bdata, arena_cx, arena_cy):
        self.bdata     = bdata
        self.name      = bdata["name"]
        self.max_hp    = bdata["hp"]
        self.hp        = self.max_hp
        self.touch_dmg = bdata["touch_dmg"]
        self.base_speed = bdata["speed"]
        self.speed     = self.base_speed
        self.size      = bdata["size"]
        self.color     = bdata["color"]
        self.aggro     = bdata["aggro"]
        self.loot_bonus = bdata["loot_bonus"]
        self.alive     = True
        self.phase2    = False
        self._uid      = id(self)

        self.pos  = pygame.math.Vector2(arena_cx, arena_cy)
        self.rect = pygame.Rect(arena_cx - self.size//2,
                                arena_cy - self.size//2,
                                self.size, self.size)

        self.dmg_cooldown = 0.0
        self.pattern_timer = 0.0
        self.pattern_phase = 0

        # Minion spawn timer (phase 2)
        self.minion_timer = 0.0

    def update(self, dt, player, world_rect):
        if not self.alive:
            return

        # Phase 2 trigger
        if not self.phase2 and self.hp / self.max_hp < self.bdata["phase2_hp"]:
            self.phase2 = True
            self.speed  = self.base_speed * 1.4
            self.touch_dmg *= 1.5

        # Movement: chase + pattern
        px, py = player.pos.x, player.pos.y
        dx = px - self.pos.x
        dy = py - self.pos.y
        dist = math.hypot(dx, dy)

        self.pattern_timer += dt
        charge_period = 4.0 if not self.phase2 else 2.5

        if self.pattern_timer >= charge_period:
            # Charge: fast rush then slow
            charge_spd = self.speed * 2.2
            self.pattern_timer = 0.0
        else:
            charge_spd = self.speed

        if dist > 1:
            move = pygame.math.Vector2(dx, dy).normalize() * charge_spd * dt
            new_x = max(world_rect.left + self.size//2,
                        min(self.pos.x + move.x, world_rect.right  - self.size//2))
            new_y = max(world_rect.top  + self.size//2,
                        min(self.pos.y + move.y, world_rect.bottom - self.size//2))
            self.pos.x = new_x
            self.pos.y = new_y

        self.rect.center = (round(self.pos.x), round(self.pos.y))

        # Touch damage
        if self.dmg_cooldown > 0:
            self.dmg_cooldown -= dt
        if self.dmg_cooldown <= 0 and self.rect.colliderect(player.rect):
            actual = player.take_damage(self.touch_dmg)
            if actual > 0:
                self.dmg_cooldown = 0.6

        # Minion spawn timer (phase 2 only)
        if self.phase2:
            self.minion_timer -= dt

    def should_spawn_minion(self):
        """Returns True if it's time to spawn a minion."""
        if self.phase2 and self.minion_timer <= 0:
            self.minion_timer = 8.0
            return True
        return False

    def take_hit(self, damage):
        self.hp -= damage
        if self.hp <= 0:
            self.hp    = 0
            self.alive = False
        return not self.alive

    def draw(self, surface, camera):
        scr = camera.apply(self.rect)

        # Glow aura (phase 2)
        if self.phase2:
            glow_r = self.size // 2 + 10
            glow_surf = pygame.Surface((glow_r*2+4, glow_r*2+4), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*self.color[:3], 60),
                               (glow_r+2, glow_r+2), glow_r)
            surface.blit(glow_surf,
                         (scr.centerx - glow_r - 2, scr.centery - glow_r - 2))

        # Body
        pygame.draw.circle(surface, self.color, scr.center, self.size // 2)
        # Inner detail
        inner = tuple(min(255, c + 30) for c in self.color)
        pygame.draw.circle(surface, inner, scr.center, self.size // 3)
        # Outline
        pygame.draw.circle(surface, (255, 255, 255), scr.center, self.size // 2, 2)

        # Health bar (big)
        bar_w = 220
        bar_h = 16
        bar_x = SCREEN_WIDTH // 2 - bar_w // 2
        bar_y = 40
        pct   = self.hp / self.max_hp
        pygame.draw.rect(surface, (60, 20, 20), (bar_x - 2, bar_y - 2, bar_w + 4, bar_h + 4), 0, 4)
        col = (200, 80, 80) if not self.phase2 else (220, 120, 30)
        pygame.draw.rect(surface, col, (bar_x, bar_y, int(bar_w * pct), bar_h), 0, 3)
        pygame.draw.rect(surface, (180, 180, 180), (bar_x, bar_y, bar_w, bar_h), 1, 3)

    @property
    def uid(self):
        return self._uid


class BossState(BaseState):

    def __init__(self, game, boss_id=1):
        super().__init__(game)
        self.boss_id = boss_id
        self.font_sm, self.font_md, self.font_lg, self.font_xl = self._make_fonts()

        self.camera   = Camera()
        self.hud      = HUD(self.font_sm, self.font_md, self.font_lg)
        self.inv_ui   = InventoryUI(self.font_sm, self.font_md, self.font_lg)

        self.boss     = None
        self.player   = None
        self.minions  = []
        self.loot_drops = []
        self.coin_drops = []

        self.world_surf = None
        self._portal_spr = portal_sprite(56)
        self._portal_pulse = 0.0

        self.arena_w = ARENA_W * TILE_SIZE
        self.arena_h = ARENA_H * TILE_SIZE
        self._portal_pos = (3 * TILE_SIZE + TILE_SIZE//2, ARENA_H//2 * TILE_SIZE)
        self._portal_rect = pygame.Rect(self._portal_pos[0]-28, self._portal_pos[1]-28, 56, 56)

        self.hotbar_idx    = 0
        self.notif_text    = ""
        self.notif_timer   = 0.0
        self.phase2_shown  = False

        self._victory       = False
        self._victory_timer = 0.0
        self._death_screen  = False
        self._death_fade    = 0.0
        self._intro_timer   = 3.0

    def on_enter(self, prev_state=None):
        pd = self.game.player_data
        bdata = BossData.BOSS1 if self.boss_id == 1 else BossData.BOSS2

        # Build arena
        self.world_surf = pygame.Surface((self.arena_w, self.arena_h))
        self.world_surf.fill(bdata["arena_bg"])

        # Walls
        wc = bdata["wall_col"]
        for col in range(ARENA_W):
            for row in [0, ARENA_H-1]:
                pygame.draw.rect(self.world_surf, wc,
                                 (col*TILE_SIZE, row*TILE_SIZE, TILE_SIZE, TILE_SIZE))
        for row in range(ARENA_H):
            for col in [0, ARENA_W-1]:
                pygame.draw.rect(self.world_surf, wc,
                                 (col*TILE_SIZE, row*TILE_SIZE, TILE_SIZE, TILE_SIZE))

        # Grid lines
        gc = tuple(max(0, c-6) for c in bdata["arena_bg"])
        for col in range(0, self.arena_w, TILE_SIZE):
            pygame.draw.line(self.world_surf, gc, (col, 0), (col, self.arena_h), 1)
        for row in range(0, self.arena_h, TILE_SIZE):
            pygame.draw.line(self.world_surf, gc, (0, row), (self.arena_w, row), 1)

        # Spawn player at portal side
        spawn_x = self._portal_pos[0] + TILE_SIZE * 3
        spawn_y = self._portal_pos[1]
        self.player = Player(spawn_x, spawn_y, pd)

        # Spawn boss in center
        cx = self.arena_w // 2
        cy = self.arena_h // 2
        self.boss = BossEnemy(bdata, cx, cy)

        self.camera.set_world_size(ARENA_W, ARENA_H)
        self.camera.center_on(self.player.rect)

        self.minions     = []
        self.loot_drops  = []
        self.coin_drops  = []
        self._victory    = False
        self._death_screen = False
        self._intro_timer  = 3.0
        self.phase2_shown  = False
        self.hotbar_idx    = 0

    def handle_events(self, events):
        if self._death_screen:
            for e in events:
                if e.type == pygame.KEYDOWN and e.key == pygame.K_RETURN:
                    self.next = "tavern"
                    self.done = True
            return
        if self._victory and self._victory_timer > 2.0:
            for e in events:
                if e.type == pygame.KEYDOWN and e.key == pygame.K_RETURN:
                    self._on_victory_confirm()

        for event in events:
            inv_was_open = self.inv_ui.visible
            action = self.inv_ui.handle_event(event, self.game.player_data["inventory"])
            if action and action.get("action") == "eat":
                loc = action["loc"]
                if loc[0] == "hot":
                    self.player.eat(loc[1])
            if inv_was_open:
                continue

            if event.type == pygame.KEYDOWN:
                k = event.key
                if k == pygame.K_e:
                    self.inv_ui.toggle()
                elif k in (pygame.K_1,pygame.K_2,pygame.K_3,pygame.K_4,pygame.K_5):
                    self.hotbar_idx = k - pygame.K_1

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if not self.inv_ui.visible:
                    self.player.try_attack()

            if event.type == pygame.MOUSEWHEEL:
                self.hotbar_idx = (self.hotbar_idx - event.y) % 5

    def update(self, dt):
        if self.done: return
        if self._death_screen:
            self._death_fade = min(1.0, self._death_fade + dt * 0.8)
            return
        if self._victory:
            self._victory_timer += dt
            return
        if self._intro_timer > 0:
            self._intro_timer -= dt
            return

        pd = self.game.player_data
        world_rect = pygame.Rect(TILE_SIZE, TILE_SIZE,
                                  self.arena_w - 2*TILE_SIZE,
                                  self.arena_h - 2*TILE_SIZE)
        menu_open = self.inv_ui.visible

        # Mouse world coords
        mx_s, my_s = pygame.mouse.get_pos()
        mx_w, my_w = self.camera.world_pos(mx_s, my_s)

        keys = pygame.key.get_pressed()
        self.player.update(dt, keys, (mx_w, my_w), world_rect,
                           menu_open=menu_open)

        if self.player.dead:
            self._on_death()
            return

        self.camera.smooth_follow(self.player.rect, dt)

        # Boss
        if self.boss and self.boss.alive:
            self.boss.update(dt, self.player, world_rect)

            # Phase 2 message
            if self.boss.phase2 and not self.phase2_shown:
                self.phase2_shown = True
                self._notify(self.boss.bdata["phase2_msg"])

            # Player hits boss
            if self.player.check_hit(self.boss.rect, self.boss.uid):
                dmg     = self.player.deal_damage()
                killed  = self.boss.take_hit(dmg)
                self.player.hit_enemies.add(self.boss.uid)
                if killed:
                    self._on_boss_killed()

            # Minion spawning
            if self.boss.should_spawn_minion():
                self._spawn_minion()

        # Minions
        for m in self.minions:
            if not m.alive: continue
            m.update(dt, (self.player.pos.x, self.player.pos.y),
                     self.player, world_rect)
            if self.player.check_hit(m.rect, m.uid):
                dmg = self.player.deal_damage()
                m.take_hit(dmg)
                self.player.hit_enemies.add(m.uid)
        self.minions = [m for m in self.minions if m.alive]

        for ld in self.loot_drops: ld.update(dt)
        remaining_coins = []
        for cd in self.coin_drops:
            cd.update(dt)
            if math.hypot(cd.pos.x - self.player.pos.x,
                          cd.pos.y - self.player.pos.y) < 48:
                pd["coins"] += cd.amount
            else:
                remaining_coins.append(cd)
        self.coin_drops = remaining_coins

        self._portal_pulse += dt
        if self.notif_timer > 0:
            self.notif_timer -= dt

    def _spawn_minion(self):
        from src.data.enemies_data import ENEMY_TYPES
        mtype = "goblin" if self.boss_id == 1 else "imp"
        edata = ENEMY_TYPES[mtype]
        cx, cy = self.boss.pos.x, self.boss.pos.y
        ox = cx + random.choice([-1, 1]) * random.randint(60, 120)
        oy = cy + random.choice([-1, 1]) * random.randint(60, 120)
        m = Enemy(ox, oy, mtype, edata, tier=self.boss_id + 1)
        self.minions.append(m)

    def _on_boss_killed(self):
        self._victory = True
        pd = self.game.player_data

        # Drop loot
        items = make_boss_loot(self.boss_id)
        for item in items:
            ox = self.boss.pos.x + random.randint(-40, 40)
            oy = self.boss.pos.y + random.randint(-40, 40)
            self.loot_drops.append(LootDrop(ox, oy, item))
        coins = 100 + self.boss_id * 80
        self.coin_drops.append(CoinDrop(self.boss.pos.x, self.boss.pos.y - 20, coins))
        self._notify(f"{self.boss.name} defeated! Collect your rewards.")

    def _on_victory_confirm(self):
        pd = self.game.player_data
        # Grant boss kill
        if self.boss_id == 1 and pd.get("boss_kills", 0) < 1:
            pd["boss_kills"] = 1
            pd["storage"].update_size(1)
        elif self.boss_id == 2 and pd.get("boss_kills", 0) < 2:
            pd["boss_kills"] = 2
            pd["storage"].update_size(2)

        # Auto-collect remaining items
        inv = pd["inventory"]
        for ld in self.loot_drops:
            inv.add_item(ld.item)
        for cd in self.coin_drops:
            pd["coins"] += cd.amount

        save_player(pd)
        self.next = "tavern"
        self.done = True

    def _on_death(self):
        if self._death_screen: return
        self._death_screen = True
        pd = self.game.player_data
        pd["health"] = max(1, pd["max_health"] * 0.3)
        # No item drop in boss — fair recovery
        save_player(pd)

    def _notify(self, text):
        self.notif_text  = text
        self.notif_timer = 4.0

    def draw(self, surface):
        # World
        src_x = int(self.camera.offset.x)
        src_y = int(self.camera.offset.y)
        surface.blit(self.world_surf, (0, 0), (src_x, src_y, SCREEN_WIDTH, SCREEN_HEIGHT - HUD_H))

        # Portal
        px_s, py_s = self.camera.apply_pos(*self._portal_pos)
        pulse = abs(math.sin(self._portal_pulse * 1.5))
        pp = self._portal_spr.copy()
        pp.set_alpha(int(180 + 75 * pulse))
        surface.blit(pp, (px_s - 28, py_s - 28))

        for cd in self.coin_drops: cd.draw(surface, self.camera)
        for ld in self.loot_drops: ld.draw(surface, self.camera)
        for m in self.minions:     m.draw(surface, self.camera)
        if self.boss and self.boss.alive:
            self.boss.draw(surface, self.camera)
        self.player.draw(surface, self.camera)

        self.hud.draw(surface, self.player, self.hotbar_idx,
                      self.notif_text, self.notif_timer)

        # Intro
        if self._intro_timer > 0:
            alpha = min(255, int(self._intro_timer * 150))
            bdata = BossData.BOSS1 if self.boss_id == 1 else BossData.BOSS2
            ntl = self.font_xl.render(bdata["name"].upper(), True, (220, 60, 60))
            ntl.set_alpha(alpha)
            surface.blit(ntl, (SCREEN_WIDTH//2 - ntl.get_width()//2, SCREEN_HEIGHT//2 - 40))
            desc = self.font_md.render(bdata["description"], True, (180, 140, 140))
            desc.set_alpha(alpha)
            surface.blit(desc, (SCREEN_WIDTH//2 - desc.get_width()//2, SCREEN_HEIGHT//2 + 10))

        # Boss HP bar name
        if self.boss and self.boss.alive:
            bname = self.font_lg.render(self.boss.name, True, (220, 180, 100))
            surface.blit(bname, (SCREEN_WIDTH//2 - bname.get_width()//2, 15))

        # Victory screen
        if self._victory and self._victory_timer > 2.0:
            self._draw_victory(surface)

        # Death screen
        if self._death_screen:
            self._draw_death(surface)

        # Boss defeated — inv open to collect
        if self.inv_ui.visible:
            self.inv_ui.draw(surface, self.game.player_data["inventory"])

    def _draw_victory(self, surface):
        ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 140))
        surface.blit(ov, (0, 0))
        pw, ph = 480, 200
        px = SCREEN_WIDTH//2 - pw//2
        py = SCREEN_HEIGHT//2 - ph//2
        pygame.draw.rect(surface, (15, 40, 15), (px, py, pw, ph), 0, 10)
        pygame.draw.rect(surface, (50, 180, 50), (px, py, pw, ph), 2, 10)
        ttl = self.font_xl.render("VICTORY!", True, (80, 230, 80))
        surface.blit(ttl, (px + pw//2 - ttl.get_width()//2, py + 20))
        bdata = BossData.BOSS1 if self.boss_id == 1 else BossData.BOSS2
        sub = self.font_md.render(f"{bdata['name']} has fallen.", True, UI_TEXT)
        surface.blit(sub, (px + pw//2 - sub.get_width()//2, py + 80))
        cont = self.font_lg.render("Press ENTER to return", True, (220, 200, 100))
        surface.blit(cont, (px + pw//2 - cont.get_width()//2, py + 140))

    def _draw_death(self, surface):
        alpha = int(self._death_fade * 200)
        ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, alpha))
        surface.blit(ov, (0, 0))
        if self._death_fade > 0.5:
            pw, ph = 440, 180
            px = SCREEN_WIDTH//2 - pw//2
            py = SCREEN_HEIGHT//2 - ph//2
            pygame.draw.rect(surface, (30, 10, 10), (px, py, pw, ph), 0, 10)
            pygame.draw.rect(surface, (150, 30, 30), (px, py, pw, ph), 2, 10)
            ttl = self.font_xl.render("DEFEATED", True, (220, 50, 50))
            surface.blit(ttl, (px + pw//2 - ttl.get_width()//2, py + 20))
            sub = self.font_md.render("The boss resets. You keep your items.", True, (180, 140, 140))
            surface.blit(sub, (px + pw//2 - sub.get_width()//2, py + 80))
            cont = self.font_lg.render("Press ENTER to return to Tavern", True, (220, 200, 100))
            surface.blit(cont, (px + pw//2 - cont.get_width()//2, py + 125))
