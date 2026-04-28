# src/entities/animal.py
import pygame
import math
import random
from src.sprite_factory import animal_sprite
from src.systems.loot_tables import roll_animal_drop


class Animal(pygame.sprite.Sprite):

    def __init__(self, x, y, atype, adata):
        super().__init__()
        self.atype      = atype
        self.name       = adata["name"]
        self.hp         = adata["hp"]
        self.max_hp     = adata["hp"]
        self.speed      = adata["speed"]
        self.size       = adata["size"]
        self.color      = adata["color"]
        self.flee_range = adata["flee_range"]
        self._adata     = adata

        variant_seed = int(x + y + len(self.atype))
        self.image = animal_sprite(self.color, self.size, atype=self.atype, variant_seed=variant_seed)
        self.rect  = self.image.get_rect(center=(x, y))
        self.pos   = pygame.math.Vector2(x, y)

        self.state        = "wander"
        self.wander_timer = random.uniform(1.0, 3.0)
        self.wander_dir   = pygame.math.Vector2(
            random.uniform(-1, 1), random.uniform(-1, 1)
        ).normalize()

        self.alive = True
        self._uid  = id(self)

    def update(self, dt, player_pos, world_rect):
        if not self.alive:
            return
        px, py = player_pos
        dx = px - self.pos.x
        dy = py - self.pos.y
        dist = math.hypot(dx, dy)

        if dist < self.flee_range:
            self.state = "flee"
        elif self.state == "flee" and dist > self.flee_range * 1.8:
            self.state = "wander"

        if self.state == "flee":
            if dist > 1:
                flee_dir = pygame.math.Vector2(-dx, -dy).normalize()
                self._move(flee_dir * self.speed * dt, world_rect)
        else:
            self.wander_timer -= dt
            if self.wander_timer <= 0:
                self.wander_timer = random.uniform(1.5, 4.0)
                angle = random.uniform(0, 2 * math.pi)
                self.wander_dir = pygame.math.Vector2(
                    math.cos(angle), math.sin(angle))
            self._move(self.wander_dir * self.speed * 0.35 * dt, world_rect)

    def _move(self, move, world_rect):
        half = self.size // 2
        nx = max(world_rect.left + half, min(self.pos.x + move.x, world_rect.right  - half))
        ny = max(world_rect.top  + half, min(self.pos.y + move.y, world_rect.bottom - half))
        self.pos.x = nx
        self.pos.y = ny
        self.rect.center = (round(nx), round(ny))

    def take_hit(self, damage):
        self.hp -= damage
        if self.hp <= 0:
            self.hp    = 0
            self.alive = False
        return not self.alive

    def get_drop(self):
        return roll_animal_drop(self._adata)

    def draw(self, surface, camera):
        if not self.alive:
            return
        scr = camera.apply(self.rect)
        surface.blit(self.image, scr)

    @property
    def uid(self):
        return self._uid
