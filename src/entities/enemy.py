# src/entities/enemy.py
import pygame
import math
import random
from src.sprite_factory import enemy_sprite, elite_sprite
from src.data.enemies_data import TIER_HP_MULT, TIER_DMG_MULT, TIER_SPEED_MULT, ELITE_MULT


class Enemy(pygame.sprite.Sprite):

    def __init__(self, x, y, etype, edata, tier=0, elite=False):
        super().__init__()
        self.etype  = etype
        self.elite  = elite
        self.tier   = tier

        # Scale stats by tier then apply difficulty config
        from src.config import get_config
        diff = get_config().get("difficulty", {})
        tmult = tier
        self.max_hp    = edata["hp"]        * (TIER_HP_MULT    ** tmult) * diff.get("enemy_hp_mult",    1.0)
        self.touch_dmg = edata["touch_dmg"] * (TIER_DMG_MULT   ** tmult) * diff.get("enemy_damage_mult", 1.0)
        self.speed     = edata["speed"]     * (TIER_SPEED_MULT ** tmult) * diff.get("enemy_speed_mult",  1.0)
        self.aggro     = edata["aggro"]
        self.size      = edata["size"]
        self.color     = edata["color"]
        self.loot_bonus = edata.get("loot_bonus", 0)
        self.name      = edata["name"]

        if elite:
            self.max_hp    *= ELITE_MULT["hp"]
            self.touch_dmg *= ELITE_MULT["touch_dmg"]
            self.speed     *= ELITE_MULT["speed"]
            self.size      += ELITE_MULT["size_add"]
            self.loot_bonus += 2

        self.hp = self.max_hp

        # Build sprite
        fn = elite_sprite if elite else enemy_sprite
        self.image = fn(self.color, self.size)
        self.rect  = self.image.get_rect(center=(x, y))
        self.pos   = pygame.math.Vector2(x, y)

        # AI state
        self.state        = "idle"
        self.wander_timer = random.uniform(0.5, 2.5)
        _wd = pygame.math.Vector2(random.uniform(-1, 1), random.uniform(-1, 1))
        self.wander_dir = _wd.normalize() if _wd.length() > 0 else pygame.math.Vector2(1, 0)

        # Touch damage cooldown
        self.dmg_cooldown = 0.0
        self.dmg_interval = 0.5   # seconds between damage ticks

        self.alive = True
        self._uid  = id(self)

    def update(self, dt, player_pos, player, world_rect, collision_rects=None):
        if not self.alive:
            return

        px, py = player_pos
        dx = px - self.pos.x
        dy = py - self.pos.y
        dist = math.hypot(dx, dy)

        # State transitions
        if dist <= self.aggro:
            self.state = "chase"
        elif self.state == "chase" and dist > self.aggro * 1.5:
            self.state = "idle"

        # Movement
        if self.state == "chase":
            if dist > 1:
                move = pygame.math.Vector2(dx, dy).normalize() * self.speed * dt
                self._try_move(move, world_rect, collision_rects or [])
        else:
            # Wander
            self.wander_timer -= dt
            if self.wander_timer <= 0:
                self.wander_timer = random.uniform(1.5, 3.5)
                angle = random.uniform(0, 2 * math.pi)
                self.wander_dir = pygame.math.Vector2(
                    math.cos(angle), math.sin(angle))
            move = self.wander_dir * self.speed * 0.3 * dt
            self._try_move(move, world_rect, collision_rects or [])

        # Touch damage
        if self.dmg_cooldown > 0:
            self.dmg_cooldown -= dt

        if self.dmg_cooldown <= 0:
            prect = pygame.Rect(player.rect.x, player.rect.y,
                                player.rect.w, player.rect.h)
            if self.rect.colliderect(prect):
                actual = player.take_damage(self.touch_dmg)
                if actual > 0:
                    self.dmg_cooldown = self.dmg_interval

    def _try_move(self, move, world_rect, collision_rects):
        half = self.size // 2

        new_x = self.pos.x + move.x
        new_y = self.pos.y + move.y
        new_x = max(world_rect.left  + half, min(new_x, world_rect.right  - half))
        new_y = max(world_rect.top   + half, min(new_y, world_rect.bottom - half))

        test = pygame.Rect(new_x - half, new_y - half, self.size, self.size)
        for cr in collision_rects:
            if test.colliderect(cr):
                # Try axes separately
                tx = pygame.Rect(new_x - half, self.pos.y - half, self.size, self.size)
                if tx.colliderect(cr):
                    new_x = self.pos.x
                ty = pygame.Rect(new_x - half, new_y - half, self.size, self.size)
                if ty.colliderect(cr):
                    new_y = self.pos.y

        self.pos.x = new_x
        self.pos.y = new_y
        self.rect.center = (round(self.pos.x), round(self.pos.y))

    def take_hit(self, damage):
        self.hp -= damage
        if self.hp <= 0:
            self.hp    = 0
            self.alive = False
        return not self.alive   # returns True if killed

    def draw(self, surface, camera):
        if not self.alive:
            return
        scr = camera.apply(self.rect)
        surface.blit(self.image, scr)

        # Health bar
        bar_w = self.size
        bar_h = 4
        bx = scr.x
        by = scr.y - 7
        pct = self.hp / self.max_hp
        pygame.draw.rect(surface, (80, 20, 20), (bx, by, bar_w, bar_h))
        pygame.draw.rect(surface, (200, 60, 60), (bx, by, int(bar_w * pct), bar_h))

        # Elite indicator
        if self.elite:
            pygame.draw.circle(surface, (255, 215, 0),
                               (scr.centerx, scr.top - 10), 4)

    @property
    def uid(self):
        return self._uid
