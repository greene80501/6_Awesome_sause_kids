# src/states/world_state.py
import pygame
import math
import random
from settings import (SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE, HUD_H,
                       FOG_VISION_RADIUS, WORLD_W, WORLD_H,
                       UI_TEXT, UI_TEXT_DIM, UI_BG, UI_PANEL, UI_BORDER,
                       RARITY_COLORS)
from src.states.base_state import BaseState
from src.entities.player import Player
from src.entities.enemy import Enemy
from src.entities.animal import Animal
from src.entities.loot_drop import LootDrop, CoinDrop
from src.entities.death_pile import DeathPile
from src.sprite_factory import portal_sprite, chest_sprite
from src.camera import Camera
from src.ui.hud import HUD
from src.ui.inventory_ui import InventoryUI
from src.ui.portal_ui import GroundPanel
from src.systems.loot_tables import (roll_enemy_drop, roll_enemy_coins,
                                       roll_loot_node, roll_objective_reward)
from src.data.enemies_data import ENEMY_TYPES, ANIMAL_TYPES
from src.world_gen.generator import get_collision_rects, draw_world_base
from src.world_gen.biomes import BIOMES
from src.save_system import save_player, save_world, delete_world


PICKUP_RANGE  = 48
INTERACT_RANGE = 72


class WorldState(BaseState):

    def __init__(self, game):
        super().__init__(game)
        self.font_sm, self.font_md, self.font_lg, self.font_xl = self._make_fonts()

        self.camera      = Camera()
        self.hud         = HUD(self.font_sm, self.font_md, self.font_lg)
        self.inv_ui      = InventoryUI(self.font_sm, self.font_md, self.font_lg)
        self.ground_panel = GroundPanel(self.font_sm, self.font_md)

        self.world_data   = None
        self.world_surf   = None
        self.collision_rects = []

        self.player   = None
        self.enemies  = []
        self.animals  = []
        self.loot_drops = []
        self.coin_drops = []
        self.death_pile = None

        self.loot_nodes = []   # [{"x","y","looted"}]
        self.chest_surfs = {"closed": chest_sprite(24), "opened": chest_sprite(24, opened=True)}

        self.portal_spr  = portal_sprite(56)
        self._portal_pulse = 0.0
        self._portal_rect  = None

        self.hotbar_idx  = 0
        self.notif_text  = ""
        self.notif_timer = 0.0

        self.fog_surf    = None
        self._fog_dirty  = True

        self.objective_done   = False
        self.obj_reward_shown = False

        self._death_screen   = False
        self._death_timer    = 0.0
        self._death_fade     = 0.0

        self._show_loot_pile = False   # recovery prompt

        self._world_complete = False   # all enemies dead (for clear objective)

    # ─────────────────────────────────────────────
    def on_enter(self, prev_state=None):
        pd = self.game.player_data
        wd = self.world_data
        if wd is None:
            self.next = "tavern"
            self.done = True
            return

        # Build world surface
        self.world_surf      = draw_world_base(wd)
        self.collision_rects = get_collision_rects(wd)

        # Spawn player
        # Check for recovery (re-entering after death)
        recovering = (pd.get("death_world_id") == wd.world_id)
        sx = wd.spawn_x
        sy = wd.spawn_y
        self.player = Player(sx, sy, pd)
        self.camera.set_world_size(wd.w, wd.h)
        self.camera.center_on(self.player.rect)

        # Spawn enemies
        self.enemies = []
        killed_ids = set(wd.important_kills)
        for sp in wd.enemy_spawns:
            sp_id = f'{sp["x"]}_{sp["y"]}'
            if sp_id in killed_ids:
                continue
            edata = ENEMY_TYPES.get(sp["etype"])
            if edata:
                e = Enemy(sp["x"], sp["y"], sp["etype"], edata,
                          tier=wd.tier, elite=sp.get("elite", False))
                e._spawn_id = sp_id
                self.enemies.append(e)

        # Spawn animals
        self.animals = []
        for sp in wd.animal_spawns:
            adata = ANIMAL_TYPES.get(sp["atype"])
            if adata:
                a = Animal(sp["x"], sp["y"], sp["atype"], adata)
                self.animals.append(a)

        # Restore loot drops from saved state
        self.loot_drops = []
        self.coin_drops = []
        for d in wd.dropped_items:
            drop = LootDrop.from_dict(d)
            if drop:
                self.loot_drops.append(drop)

        # Loot nodes
        self.loot_nodes = [dict(n) for n in wd.loot_nodes]

        # Death pile
        self.death_pile = None
        if wd.death_pile and recovering:
            self.death_pile = DeathPile.from_dict(wd.death_pile)
            self._show_loot_pile = True
            self._notify("Death pile recovered! Reach it before time runs out.")
        pd["death_world_id"] = None

        # Portal rect
        self._portal_rect = pygame.Rect(
            wd.portal_x - 28, wd.portal_y - 28, 56, 56)

        # Fog
        self.fog_surf  = pygame.Surface((wd.w * TILE_SIZE, wd.h * TILE_SIZE),
                                         pygame.SRCALPHA)
        self._fog_dirty = True
        self._update_fog()

        self._death_screen = False
        self._death_timer  = 0.0
        self._death_fade   = 0.0
        self.objective_done = wd.objective.get("done", False) if wd.objective else False

    def on_exit(self):
        self._save_world_state()

    # ─────────────────────────────────────────────
    def handle_events(self, events):
        if self._death_screen:
            for event in events:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    self._do_death_return()
            return

        for event in events:
            # Inventory
            inv_was_open = self.inv_ui.visible
            action = self.inv_ui.handle_event(event, self.game.player_data["inventory"])
            if action and action.get("action") == "eat":
                loc = action["loc"]
                ltype, idx = loc
                if ltype == "hot":
                    self.player.eat(idx)
            if inv_was_open:
                continue

            if event.type == pygame.KEYDOWN:
                k = event.key
                if k == pygame.K_e:
                    self.inv_ui.toggle()
                elif k in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5):
                    self.hotbar_idx = k - pygame.K_1
                elif k == pygame.K_f:
                    self._try_interact()
                elif k == pygame.K_ESCAPE:
                    # Escape to portal (soft retreat)
                    self._return_to_tavern()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and not self.inv_ui.visible:
                    self.player.try_attack()
                elif event.button in (4, 5):
                    self.hotbar_idx = (self.hotbar_idx + (1 if event.button == 5 else -1)) % 5

            if event.type == pygame.MOUSEWHEEL:
                self.hotbar_idx = (self.hotbar_idx - event.y) % 5

    # ─────────────────────────────────────────────
    def update(self, dt):
        if self.done:
            return

        if self._death_screen:
            self._death_fade = min(1.0, self._death_fade + dt * 0.8)
            return

        pd       = self.game.player_data
        wd       = self.world_data
        menu_open = self.inv_ui.visible

        # Mouse in world coords
        mx_scr, my_scr = pygame.mouse.get_pos()
        mx_w, my_w = self.camera.world_pos(mx_scr, my_scr)

        keys = pygame.key.get_pressed()
        world_rect = pygame.Rect(0, 0, wd.w * TILE_SIZE, wd.h * TILE_SIZE)

        # Player
        self.player.update(dt, keys, (mx_w, my_w), world_rect,
                           in_tavern=False, menu_open=menu_open,
                           collision_rects=self.collision_rects)

        if self.player.dead:
            self._on_player_death()
            return

        # Camera
        self.camera.smooth_follow(self.player.rect, dt)

        # Enemies
        for e in self.enemies:
            if not e.alive:
                continue
            e.update(dt, (self.player.pos.x, self.player.pos.y),
                     self.player, world_rect, self.collision_rects)

            # Check if player hit this enemy
            if self.player.check_hit(e.rect, e.uid):
                dmg   = self.player.deal_damage()
                killed = e.take_hit(dmg)
                self.player.hit_enemies.add(e.uid)
                if killed:
                    self._on_enemy_killed(e)

        # Remove dead
        self.enemies = [e for e in self.enemies if e.alive]

        # Animals
        for a in self.animals:
            if not a.alive:
                continue
            a.update(dt, (self.player.pos.x, self.player.pos.y), world_rect)
            if self.player.check_hit(a.rect, a.uid):
                dmg    = self.player.deal_damage()
                killed = a.take_hit(dmg)
                self.player.hit_enemies.add(a.uid)
                if killed:
                    drop = a.get_drop()
                    if drop:
                        self.loot_drops.append(
                            LootDrop(a.pos.x, a.pos.y + 10, drop))
        self.animals = [a for a in self.animals if a.alive]

        # Loot drops bobbing
        for ld in self.loot_drops:
            ld.update(dt)
        for cd in self.coin_drops:
            cd.update(dt)

        # Auto-collect coins
        pr = self.player.rect
        self.coin_drops = [cd for cd in self.coin_drops
                           if not self._try_collect_coin(cd, pd)]

        # Death pile timer
        if self.death_pile and not self.death_pile.expired:
            self.death_pile.tick(dt)

        # Portal pulse
        self._portal_pulse += dt

        # Fog
        self._update_fog()

        # Ground panel
        nearby = [ld for ld in self.loot_drops
                  if math.hypot(ld.pos.x - self.player.pos.x,
                                ld.pos.y - self.player.pos.y) < PICKUP_RANGE * 2]
        self.ground_panel.update(nearby)

        # Objective check
        self._check_objective()

        # Notification
        if self.notif_timer > 0:
            self.notif_timer -= dt

        # Loot node interaction range indicator
        self._near_node = None
        for node in self.loot_nodes:
            if not node["looted"]:
                dist = math.hypot(node["x"] - self.player.pos.x,
                                  node["y"] - self.player.pos.y)
                if dist < INTERACT_RANGE:
                    self._near_node = node
                    break

        # Near portal hint
        pp = (self.world_data.portal_x, self.world_data.portal_y)
        self._near_portal = (math.hypot(self.player.pos.x - pp[0],
                                         self.player.pos.y - pp[1]) < INTERACT_RANGE)

        # Near death pile
        self._near_death_pile = False
        if self.death_pile and not self.death_pile.expired:
            dp = self.death_pile.pos
            if math.hypot(self.player.pos.x - dp.x, self.player.pos.y - dp.y) < INTERACT_RANGE:
                self._near_death_pile = True

        # POI proximity — show name when within 160 px
        self._current_poi_name = None
        for poi in (wd.pois if hasattr(wd, "pois") else []):
            if math.hypot(self.player.pos.x - poi["x"],
                          self.player.pos.y - poi["y"]) < 160:
                self._current_poi_name = poi["name"]
                break

    # ─────────────────────────────────────────────
    def draw(self, surface):
        # World base
        c0, c1, r0, r1 = self.camera.visible_tiles()
        view_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT - HUD_H))
        src_x = int(self.camera.offset.x)
        src_y = int(self.camera.offset.y)
        view_surf.blit(self.world_surf, (0, 0), (src_x, src_y, SCREEN_WIDTH, SCREEN_HEIGHT - HUD_H))
        surface.blit(view_surf, (0, 0))

        # Loot nodes (chests)
        for node in self.loot_nodes:
            if not node["looted"]:
                sx, sy = self.camera.apply_pos(node["x"], node["y"])
                chest = self.chest_surfs["closed"]
                surface.blit(chest, (sx - chest.get_width() // 2, sy - chest.get_height() // 2))

        # Portal
        px_s, py_s = self.camera.apply_pos(self.world_data.portal_x,
                                            self.world_data.portal_y)
        pulse = abs(math.sin(self._portal_pulse * 1.5))
        pp = self.portal_spr.copy()
        pp.set_alpha(int(180 + 75 * pulse))
        surface.blit(pp, (px_s - 28, py_s - 28))
        pl = self.font_sm.render("EXIT", True, (160, 120, 255))
        surface.blit(pl, (px_s - pl.get_width()//2, py_s + 30))

        # Death pile
        if self.death_pile and not self.death_pile.expired:
            self.death_pile.draw(surface, self.camera)

        # Coin drops
        for cd in self.coin_drops:
            cd.draw(surface, self.camera)

        # Loot drops
        for ld in self.loot_drops:
            ld.draw(surface, self.camera)

        # Animals
        for a in self.animals:
            a.draw(surface, self.camera)

        # Enemies
        for e in self.enemies:
            e.draw(surface, self.camera)

        # Player
        self.player.draw(surface, self.camera)

        # Fog of war overlay
        if self.fog_surf:
            fog_view = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT - HUD_H), pygame.SRCALPHA)
            fog_view.blit(self.fog_surf, (-src_x, -src_y))
            surface.blit(fog_view, (0, 0))

        # HUD
        self.hud.draw(surface, self.player, self.hotbar_idx,
                      self.notif_text, self.notif_timer)

        # Interaction prompts
        self._draw_prompts(surface)

        # POI name banner
        if getattr(self, "_current_poi_name", None):
            pn = self.font_lg.render(
                f"★  {self._current_poi_name}  ★", True, (220, 200, 120))
            surface.blit(pn, (SCREEN_WIDTH//2 - pn.get_width()//2, 32))

        # Objective display
        self._draw_objective(surface)

        # Inventory UI
        if self.inv_ui.visible:
            self.inv_ui.draw(surface, self.game.player_data["inventory"])
            self.ground_panel.draw(surface)

        # Death screen
        if self._death_screen:
            self._draw_death_screen(surface)

    # ─────────────────────────────────────────────
    def _update_fog(self):
        wd  = self.world_data
        if not self.fog_surf:
            return
        px_t = int(self.player.pos.x) // TILE_SIZE
        py_t = int(self.player.pos.y) // TILE_SIZE
        r    = FOG_VISION_RADIUS

        revealed = False
        for dr in range(-r, r + 1):
            for dc in range(-r, r + 1):
                col = px_t + dc
                row = py_t + dr
                if 0 <= col < wd.w and 0 <= row < wd.h:
                    if wd.fog[col][row] == 0:
                        wd.fog[col][row] = 1
                        revealed = True
                    if dc*dc + dr*dr <= (r-1)*(r-1):
                        wd.fog[col][row] = 2   # fully visible

        # Rebuild fog surface (only tiles that changed)
        if revealed or self._fog_dirty:
            self._fog_dirty = False
            self.fog_surf.fill((0, 0, 0, 0))
            for col in range(wd.w):
                for row in range(wd.h):
                    state = wd.fog[col][row]
                    if state == 0:
                        pygame.draw.rect(self.fog_surf, (0, 0, 0, 255),
                                         (col*TILE_SIZE, row*TILE_SIZE, TILE_SIZE, TILE_SIZE))
                    elif state == 1:
                        pygame.draw.rect(self.fog_surf, (0, 0, 0, 160),
                                         (col*TILE_SIZE, row*TILE_SIZE, TILE_SIZE, TILE_SIZE))
                    # state == 2: transparent (fully visible)

    def _on_enemy_killed(self, e):
        wd  = self.world_data
        pd  = self.game.player_data

        # Mark kill
        wd.important_kills.append(e._spawn_id)

        # Drop coins
        coins = roll_enemy_coins(e.loot_bonus, wd.tier)
        self.coin_drops.append(CoinDrop(e.pos.x, e.pos.y - 10, coins))

        # Drop items
        items = roll_enemy_drop(e.loot_bonus, wd.tier)
        for item in items:
            ox = e.pos.x + random.randint(-20, 20)
            oy = e.pos.y + random.randint(-20, 20)
            self.loot_drops.append(LootDrop(ox, oy, item))

        # Objective check
        if wd.objective and wd.objective["type"] == "kill_elite":
            if e._spawn_id == wd.objective.get("target_id") or e.elite:
                wd.objective["done"] = True
                self.objective_done  = True
                self._notify("OBJECTIVE COMPLETE! Return to portal for reward.")

    def _try_collect_coin(self, cd, pd):
        dist = math.hypot(cd.pos.x - self.player.pos.x,
                          cd.pos.y - self.player.pos.y)
        if dist < PICKUP_RANGE:
            pd["coins"] += cd.amount
            return True
        return False

    def _try_interact(self):
        # Portal
        if self._near_portal:
            self._return_to_tavern()
            return

        # Death pile
        if self._near_death_pile and self.death_pile:
            items, coins = self.death_pile.loot()
            pd = self.game.player_data
            pd["coins"] += coins
            added = 0
            for item in items:
                if pd["inventory"].add_item(item):
                    added += 1
            self._notify(f"Recovered {added} items and {coins} coins!")
            self.death_pile = None
            return

        # Loot node (chest)
        for node in self.loot_nodes:
            if not node["looted"]:
                dist = math.hypot(node["x"] - self.player.pos.x,
                                  node["y"] - self.player.pos.y)
                if dist < INTERACT_RANGE:
                    items = roll_loot_node(self.world_data.tier)
                    node["looted"] = True
                    for item in items:
                        ox = node["x"] + random.randint(-24, 24)
                        oy = node["y"] + random.randint(-24, 24)
                        self.loot_drops.append(LootDrop(ox, oy, item))
                    self._notify("Chest opened!")
                    return

        # Pick up nearest loot drop
        best = None
        best_dist = PICKUP_RANGE
        for ld in self.loot_drops:
            d = math.hypot(ld.pos.x - self.player.pos.x,
                           ld.pos.y - self.player.pos.y)
            if d < best_dist:
                best_dist = d
                best = ld

        if best:
            inv = self.game.player_data["inventory"]
            if inv.add_item(best.item):
                self.loot_drops.remove(best)
                self._notify(f"Picked up: {best.item.display_name}")
            else:
                self._notify("Inventory full!")

    def _return_to_tavern(self):
        # Collect objective reward if done
        if self.objective_done and not self.obj_reward_shown:
            self._give_objective_reward()
        self._save_world_state()
        save_player(self.game.player_data)
        self.next = "tavern"
        self.done = True

    def _give_objective_reward(self):
        self.obj_reward_shown = True
        pd = self.game.player_data
        wd = self.world_data
        items, coins = roll_objective_reward(wd.tier)
        pd["coins"] += coins
        added = 0
        for item in items:
            if pd["inventory"].add_item(item):
                added += 1
            else:
                self.loot_drops.append(LootDrop(self.player.pos.x + random.randint(-40,40),
                                                  self.player.pos.y + random.randint(-40,40), item))
        self._notify(f"Objective reward: {coins}g + {added} items!")

    def _check_objective(self):
        wd = self.world_data
        if not wd.objective or wd.objective.get("done"):
            return
        if wd.objective["type"] == "clear_world":
            if len(self.enemies) == 0 and not self.objective_done:
                wd.objective["done"] = True
                self.objective_done  = True
                self._notify("World cleared! Return to portal for reward.")

    def _on_player_death(self):
        if self._death_screen:
            return
        self._death_screen = True
        pd = self.game.player_data
        wd = self.world_data

        # Drop all items at death location
        items = pd["inventory"].drop_all()
        coins = pd["coins"]
        pd["coins"] = 0

        if items or coins > 0:
            dp = DeathPile(self.player.pos.x, self.player.pos.y, items, coins)
            self.death_pile = dp
            wd.death_pile   = dp.to_dict()

        # Mark death world for recovery
        pd["death_world_id"] = wd.world_id
        pd["health"] = 1   # respawn with minimal health

        self._save_world_state()
        save_player(pd)

    def _do_death_return(self):
        pd = self.game.player_data
        pd["health"] = max(1, pd["max_health"] * 0.3)
        self.next = "death_return"
        self.done = True

    def _save_world_state(self):
        wd = self.world_data
        if not wd:
            return
        # Save dropped items
        wd.dropped_items = [ld.to_dict() for ld in self.loot_drops]
        if self.death_pile and not self.death_pile.expired:
            wd.death_pile = self.death_pile.to_dict()
        save_world(wd.to_dict())

    def _notify(self, text):
        self.notif_text  = text
        self.notif_timer = 3.5

    # ─────────────────────────────────────────────
    def _draw_prompts(self, surface):
        hints = []
        if self._near_portal:
            hints.append("F / E — Return to Tavern")
        if hasattr(self, "_near_node") and self._near_node:
            hints.append("F — Open chest")
        if self._near_death_pile:
            hints.append("F — Recover death pile!")
        # Near loot
        nearby_loot = [ld for ld in self.loot_drops
                       if math.hypot(ld.pos.x - self.player.pos.x,
                                     ld.pos.y - self.player.pos.y) < PICKUP_RANGE]
        if nearby_loot and not self._near_portal and not self._near_death_pile:
            hints.append("F — Pick up item")

        if hints:
            for i, h in enumerate(hints):
                ht = self.font_md.render(h, True, (255, 230, 100))
                surface.blit(ht, (SCREEN_WIDTH//2 - ht.get_width()//2,
                                  SCREEN_HEIGHT - HUD_H - 40 - i*24))

    def _draw_objective(self, surface):
        wd = self.world_data
        if not wd.objective:
            return
        obj = wd.objective
        type_labels = {
            "kill_elite": "OBJECTIVE: Kill the Elite",
            "clear_world": f"OBJECTIVE: Clear all enemies ({len(self.enemies)} remaining)",
            "carry_item":  "OBJECTIVE: Carry item to portal",
        }
        label = type_labels.get(obj["type"], "OBJECTIVE: Complete")
        col   = (80, 200, 80) if obj.get("done") else (255, 200, 60)
        if obj.get("done"):
            label = "✓ OBJECTIVE COMPLETE — Return to portal!"
        t = self.font_md.render(label, True, col)
        surface.blit(t, (SCREEN_WIDTH//2 - t.get_width()//2, 8))

        # Biome / world info strip
        bname = BIOMES[wd.biome]["display"]
        wtype = wd.world_type.title()
        danger = BIOMES[wd.biome]["danger"]
        info = self.font_sm.render(
            f"{bname}  |  {wtype} World  |  Tier {wd.tier}  |  Danger: {danger}",
            True, UI_TEXT_DIM)
        surface.blit(info, (8, 8))

    def _draw_death_screen(self, surface):
        alpha = int(self._death_fade * 200)
        ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, alpha))
        surface.blit(ov, (0, 0))

        if self._death_fade > 0.5:
            pw, ph = 460, 220
            px = SCREEN_WIDTH  // 2 - pw // 2
            py = SCREEN_HEIGHT // 2 - ph // 2
            pygame.draw.rect(surface, (30, 10, 10), (px, py, pw, ph), 0, 10)
            pygame.draw.rect(surface, (150, 30, 30), (px, py, pw, ph), 2, 10)

            ttl = self.font_xl.render("YOU DIED", True, (220, 50, 50))
            surface.blit(ttl, (px + pw//2 - ttl.get_width()//2, py + 20))

            sub = self.font_md.render("Your items dropped at death location.", True, (180, 140, 140))
            surface.blit(sub, (px + pw//2 - sub.get_width()//2, py + 75))

            sub2 = self.font_md.render("You can re-enter to recover them (60s timer).", True, (180, 140, 140))
            surface.blit(sub2, (px + pw//2 - sub2.get_width()//2, py + 100))

            cont = self.font_lg.render("Press ENTER to return to Tavern", True, (220, 200, 100))
            surface.blit(cont, (px + pw//2 - cont.get_width()//2, py + 155))
