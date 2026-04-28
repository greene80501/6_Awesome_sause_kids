# src/entities/loot_drop.py
import pygame
import math
from src.sprite_factory import loot_drop_sprite
from settings import RARITY_COLORS


class LootDrop(pygame.sprite.Sprite):
    """An item sitting on the ground in the world."""

    _next_id = 0

    def __init__(self, x, y, item):
        super().__init__()
        self.item  = item
        self.pos   = pygame.math.Vector2(x, y)
        self.image = loot_drop_sprite(item, 20)
        self.rect  = self.image.get_rect(center=(x, y))
        self._id   = LootDrop._next_id
        LootDrop._next_id += 1

        # Bobbing animation
        self._bob_t  = 0.0
        self._bob_off = 0.0

    def update(self, dt):
        self._bob_t   += dt * 2.5
        self._bob_off  = math.sin(self._bob_t) * 2.5
        cy = round(self.pos.y + self._bob_off)
        self.rect.center = (round(self.pos.x), cy)

    def draw(self, surface, camera):
        scr = camera.apply(self.rect)
        surface.blit(self.image, scr)
        # Rarity glow
        r_col = RARITY_COLORS.get(self.item.rarity, (180, 180, 180))
        pygame.draw.circle(surface, r_col, scr.center, 12, 1)

    def to_dict(self):
        return {"x": self.pos.x, "y": self.pos.y, "item": self.item.to_dict()}

    @classmethod
    def from_dict(cls, d):
        from src.systems.item import Item
        item = Item.from_dict(d["item"])
        if item:
            return cls(d["x"], d["y"], item)
        return None

    @property
    def uid(self):
        return self._id


class CoinDrop:
    """A coin pile on the ground."""

    _next_id = 1_000_000

    def __init__(self, x, y, amount):
        self.pos    = pygame.math.Vector2(x, y)
        self.amount = amount
        self.rect   = pygame.Rect(x - 8, y - 8, 16, 16)
        self._id    = CoinDrop._next_id
        CoinDrop._next_id += 1
        self._bob_t = 0.0

    def update(self, dt):
        self._bob_t += dt * 3.0

    def draw(self, surface, camera):
        scr_pos = camera.apply_pos(self.pos.x, self.pos.y + math.sin(self._bob_t) * 2)
        pygame.draw.circle(surface, (255, 215, 0), (int(scr_pos[0]), int(scr_pos[1])), 7)
        pygame.draw.circle(surface, (200, 160, 0), (int(scr_pos[0]), int(scr_pos[1])), 7, 2)

    @property
    def uid(self):
        return self._id
