# src/entities/death_pile.py
import pygame
import math
from src.sprite_factory import death_pile_sprite
from settings import DEATH_PILE_TTL


class DeathPile:
    """
    Spawned at the player's death location.
    Contains all carried items + coins.
    Timer only counts down while player is in the same world.
    """

    def __init__(self, x, y, items, coins):
        self.pos    = pygame.math.Vector2(x, y)
        self.items  = list(items)
        self.coins  = coins
        self.timer  = DEATH_PILE_TTL
        self.expired = False
        self.rect   = pygame.Rect(x - 14, y - 14, 28, 28)
        self._image = death_pile_sprite(28)
        self._pulse = 0.0

    def tick(self, dt):
        """Call only when player is actively in this world."""
        if self.expired:
            return
        self.timer -= dt
        self._pulse += dt * 3.0
        if self.timer <= 0:
            self.expired = True

    def loot(self):
        """Returns (items, coins) and empties the pile."""
        items = list(self.items)
        coins = self.coins
        self.items = []
        self.coins = 0
        self.expired = True
        return items, coins

    def draw(self, surface, camera):
        if self.expired:
            return
        scr = camera.apply(self.rect)

        # Pulse transparency based on time left
        alpha = 255
        if self.timer < 15:
            alpha = int(128 + 127 * math.sin(self._pulse))

        img = self._image.copy()
        img.set_alpha(alpha)
        surface.blit(img, scr)

        # Timer bar above pile
        bar_w = 36
        bar_x = scr.centerx - bar_w // 2
        bar_y = scr.top - 8
        pct   = self.timer / DEATH_PILE_TTL
        col   = (200, 60, 60) if pct < 0.3 else (220, 180, 40)
        pygame.draw.rect(surface, (50, 30, 20), (bar_x, bar_y, bar_w, 4))
        pygame.draw.rect(surface, col,          (bar_x, bar_y, int(bar_w * pct), 4))

    def to_dict(self):
        return {
            "x": self.pos.x, "y": self.pos.y,
            "items": [i.to_dict() for i in self.items],
            "coins": self.coins,
            "timer": self.timer,
        }

    @classmethod
    def from_dict(cls, d):
        from src.systems.item import Item
        items = [Item.from_dict(i) for i in d["items"] if i]
        items = [i for i in items if i]
        pile  = cls(d["x"], d["y"], items, d["coins"])
        pile.timer = d["timer"]
        return pile
