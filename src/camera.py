# src/camera.py
import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, HUD_H, TILE_SIZE, WORLD_W, WORLD_H


class Camera:
    """Translates world coordinates to screen coordinates."""

    def __init__(self):
        self.offset = pygame.math.Vector2(0, 0)
        self.view_w = SCREEN_WIDTH
        self.view_h = SCREEN_HEIGHT - HUD_H
        self.world_w = WORLD_W * TILE_SIZE
        self.world_h = WORLD_H * TILE_SIZE

    def center_on(self, entity_rect):
        """Snap camera to center on entity."""
        tx = entity_rect.centerx - self.view_w // 2
        ty = entity_rect.centery - self.view_h // 2
        self._clamp_and_set(tx, ty)

    def smooth_follow(self, entity_rect, dt, speed=8.0):
        tx = entity_rect.centerx - self.view_w // 2
        ty = entity_rect.centery - self.view_h // 2
        tx = max(0, min(tx, self.world_w - self.view_w))
        ty = max(0, min(ty, self.world_h - self.view_h))
        self.offset.x += (tx - self.offset.x) * min(speed * dt, 1.0)
        self.offset.y += (ty - self.offset.y) * min(speed * dt, 1.0)

    def _clamp_and_set(self, tx, ty):
        self.offset.x = max(0, min(tx, self.world_w - self.view_w))
        self.offset.y = max(0, min(ty, self.world_h - self.view_h))

    def apply(self, rect):
        """Return rect shifted by camera offset (for drawing)."""
        return pygame.Rect(rect.x - int(self.offset.x),
                           rect.y - int(self.offset.y),
                           rect.width, rect.height)

    def apply_pos(self, x, y):
        return (x - int(self.offset.x), y - int(self.offset.y))

    def world_pos(self, screen_x, screen_y):
        """Convert screen position to world position."""
        return (screen_x + int(self.offset.x), screen_y + int(self.offset.y))

    def visible_tiles(self):
        """Return (col_start, col_end, row_start, row_end) of visible tiles."""
        c0 = int(self.offset.x) // TILE_SIZE
        r0 = int(self.offset.y) // TILE_SIZE
        c1 = c0 + self.view_w // TILE_SIZE + 2
        r1 = r0 + self.view_h // TILE_SIZE + 2
        c0 = max(0, c0);  r0 = max(0, r0)
        c1 = min(WORLD_W, c1); r1 = min(WORLD_H, r1)
        return c0, c1, r0, r1

    def set_world_size(self, w_tiles, h_tiles):
        self.world_w = w_tiles * TILE_SIZE
        self.world_h = h_tiles * TILE_SIZE
