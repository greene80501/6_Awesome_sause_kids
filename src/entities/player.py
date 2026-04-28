# src/entities/player.py
import pygame
import math
from settings import (PLAYER_SPEED, PLAYER_MAX_HEALTH, PLAYER_MAX_HUNGER,
                       HUNGER_DRAIN_WORLD, HUNGER_DRAIN_TAVERN,
                       STARVATION_DMG, HEALTH_REGEN_RATE, HEALTH_REGEN_THRESHOLD,
                       ATTACK_ARC, ATTACK_RANGE, SLOW_WHILE_ATTACKING,
                       WEAPON_CLASSES, TILE_SIZE)
from src.sprite_factory import player_sprite, attack_arc_surface


class Player(pygame.sprite.Sprite):

    def __init__(self, x, y, player_data):
        super().__init__()
        self.data = player_data          # shared dict, persists across states
        self.size  = 24
        self.image = player_sprite(self.size)
        self.rect  = self.image.get_rect(center=(x, y))
        self.pos   = pygame.math.Vector2(x, y)

        # Combat state
        self.attacking     = False
        self.attack_timer  = 0.0
        self.attack_cooldown = 0.0
        self.attack_angle  = 0.0          # radians, facing direction
        self.hit_enemies   = set()        # ids hit this swing

        # Invincibility frames after taking damage
        self.iframe_timer  = 0.0
        self.iframe_dur    = 0.6

        # Visual flash
        self.flash_timer   = 0.0

        # Death flag
        self.dead = False

    # ── Properties from shared data ──
    @property
    def health(self): return self.data["health"]
    @health.setter
    def health(self, v): self.data["health"] = max(0.0, min(float(v), self.data["max_health"]))

    @property
    def hunger(self): return self.data["hunger"]
    @hunger.setter
    def hunger(self, v): self.data["hunger"] = max(0.0, min(float(v), self.data["max_hunger"]))

    @property
    def inventory(self): return self.data["inventory"]

    @property
    def equipped_weapon(self): return self.inventory.equip.get("weapon")

    @property
    def total_defense(self): return self.inventory.total_defense

    @property
    def speed(self):
        base = PLAYER_SPEED + self.inventory.speed_bonus
        if self.attacking:
            return base * SLOW_WHILE_ATTACKING
        return base

    # ── Update ──
    def update(self, dt, keys, mouse_pos, world_rect, in_tavern=False,
               menu_open=False, collision_rects=None):

        if self.dead:
            return

        # Aim direction
        wx = self.rect.centerx
        wy = self.rect.centery
        dx = mouse_pos[0] - wx
        dy = mouse_pos[1] - wy
        self.attack_angle = math.atan2(dy, dx)

        if not menu_open:
            self._move(dt, keys, world_rect, collision_rects or [])

        # Hunger
        if not menu_open:
            from src.config import get_config
            drain_mult = get_config().get("difficulty", {}).get("hunger_drain_mult", 1.0)
            drain = (HUNGER_DRAIN_TAVERN if in_tavern else HUNGER_DRAIN_WORLD) * drain_mult
            self.hunger -= drain * dt

        # Starvation / regen
        if self.hunger <= 0:
            self.hunger = 0
            self.health -= STARVATION_DMG * dt
        elif self.hunger >= HEALTH_REGEN_THRESHOLD:
            self.health = min(self.data["max_health"],
                              self.health + HEALTH_REGEN_RATE * dt)

        # Timers
        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt

        if self.attacking:
            self.attack_timer -= dt
            if self.attack_timer <= 0:
                self.attacking = False
                self.hit_enemies.clear()

        if self.iframe_timer > 0:
            self.iframe_timer -= dt

        if self.flash_timer > 0:
            self.flash_timer -= dt

        # Death check
        if self.health <= 0:
            self.dead = True

    def _move(self, dt, keys, world_rect, collision_rects):
        dx, dy = 0, 0
        if keys[pygame.K_w] or keys[pygame.K_UP]:    dy -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:  dy += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:  dx -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx += 1
        if dx and dy:
            dx *= 0.7071
            dy *= 0.7071

        spd = self.speed
        new_x = self.pos.x + dx * spd * dt
        new_y = self.pos.y + dy * spd * dt

        # Clamp to world
        half = self.size // 2
        new_x = max(world_rect.left + half, min(new_x, world_rect.right  - half))
        new_y = max(world_rect.top  + half, min(new_y, world_rect.bottom - half))

        # Tile collision (AABB)
        test_rect = pygame.Rect(new_x - half, new_y - half, self.size, self.size)
        for cr in collision_rects:
            if test_rect.colliderect(cr):
                # Try horizontal only
                hx_rect = pygame.Rect(new_x - half, self.pos.y - half, self.size, self.size)
                if hx_rect.colliderect(cr):
                    new_x = self.pos.x
                # Try vertical only
                vy_rect = pygame.Rect(new_x - half, new_y - half, self.size, self.size)
                if vy_rect.colliderect(cr):
                    new_y = self.pos.y
                break

        self.pos.x = new_x
        self.pos.y = new_y
        self.rect.center = (round(self.pos.x), round(self.pos.y))

    # ── Combat ──
    def try_attack(self):
        """Returns True if a new swing started."""
        if self.attack_cooldown > 0:
            return False
        weapon = self.equipped_weapon
        if weapon:
            cd   = weapon.cooldown
            dur_cost = 1
        else:
            cd   = WEAPON_CLASSES["balanced"]["cooldown"]
            dur_cost = 0

        self.attacking      = True
        self.attack_timer   = cd * 0.6
        self.attack_cooldown = cd
        self.hit_enemies.clear()

        if weapon and not weapon.stackable:
            weapon.take_durability(dur_cost)

        return True

    def check_hit(self, enemy_rect, enemy_id):
        """Returns True if enemy is within attack arc and hasn't been hit this swing."""
        if not self.attacking:
            return False
        if enemy_id in self.hit_enemies:
            return False

        weapon = self.equipped_weapon
        wc     = WEAPON_CLASSES.get(weapon.weapon_class if weapon else "balanced",
                                     WEAPON_CLASSES["balanced"])
        arc    = math.radians(ATTACK_ARC + wc.get("arc", 0))
        rng    = ATTACK_RANGE + wc.get("range", 0)

        ex, ey = enemy_rect.centerx, enemy_rect.centery
        dx = ex - self.rect.centerx
        dy = ey - self.rect.centery
        dist = math.hypot(dx, dy)
        if dist > rng + enemy_rect.width // 2:
            return False

        enemy_angle = math.atan2(dy, dx)
        diff = abs((enemy_angle - self.attack_angle + math.pi) % (2 * math.pi) - math.pi)
        return diff <= arc / 2

    def deal_damage(self):
        """Returns damage dealt by current weapon."""
        weapon = self.equipped_weapon
        if weapon and not weapon.broken:
            return weapon.damage
        return 8   # bare-hand fallback

    def take_damage(self, amount):
        if self.iframe_timer > 0:
            return 0
        defense = self.total_defense
        reduced = max(1, amount - defense // 4)
        self.health -= reduced
        self.iframe_timer = self.iframe_dur
        self.flash_timer  = 0.15
        # Damage armor durability
        inv = self.inventory
        for slot in ["head", "chest", "legs", "boots"]:
            piece = inv.equip.get(slot)
            if piece and not piece.broken:
                piece.take_durability(1)
                break  # only one piece takes dura per hit
        return reduced

    def eat(self, idx):
        """Eat food from hotbar slot idx. Returns amount restored."""
        restore = self.inventory.consume_hotbar(idx)
        if restore:
            self.hunger = min(self.data["max_hunger"], self.hunger + restore)
        return restore

    # ── Drawing ──
    def draw(self, surface, camera):
        if self.dead:
            return
        scr = camera.apply(self.rect)

        # Flash red when damaged
        if self.flash_timer > 0:
            flash = player_sprite(self.size).copy()
            flash.fill((255, 80, 80, 160), special_flags=pygame.BLEND_RGBA_MULT)
            surface.blit(flash, scr)
        else:
            surface.blit(self.image, scr)

        # Draw attack arc
        if self.attacking:
            weapon = self.equipped_weapon
            wc = WEAPON_CLASSES.get(weapon.weapon_class if weapon else "balanced",
                                     WEAPON_CLASSES["balanced"])
            arc_deg = ATTACK_ARC + wc.get("arc", 0)
            rng     = ATTACK_RANGE + wc.get("range", 0)
            arc_surf = attack_arc_surface(arc_deg, rng, (255, 220, 80, 80))
            arc_rect = arc_surf.get_rect(center=scr.center)
            # Rotate to face aim direction
            angle_deg = -math.degrees(self.attack_angle)
            rotated   = pygame.transform.rotate(arc_surf, angle_deg)
            rot_rect  = rotated.get_rect(center=scr.center)
            surface.blit(rotated, rot_rect)

        # Direction indicator (small dot)
        tip_x = scr.centerx + math.cos(self.attack_angle) * 16
        tip_y = scr.centery + math.sin(self.attack_angle) * 16
        pygame.draw.circle(surface, (255, 220, 80), (int(tip_x), int(tip_y)), 3)
