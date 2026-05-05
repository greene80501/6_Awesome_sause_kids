# src/game.py
import pygame
import sys
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE
from src.save_system import (load_player, new_player_data, load_world,
                               save_player, save_world, delete_world,
                               sanitize_player_data)
from src.world_gen.generator import generate_world, WorldData


class Game:
    """
    Central game manager.
    Owns the state machine, player_data, and the main loop.
    """

    def __init__(self):
        pygame.init()
        pygame.display.set_caption(TITLE)
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock  = pygame.time.Clock()

        # Shared mutable player state passed to all states
        self.player_data = new_player_data()

        # State registry (lazy-loaded)
        self._states = {}
        self._current_state_name = None
        self._current_state      = None

        # Boot into menu
        self._transition_to("menu")

    # ─────────────────────────────────────────────
    def _get_state(self, name):
        if name not in self._states:
            self._states[name] = self._build_state(name)
        return self._states[name]

    def _build_state(self, name):
        from src.states.menu_state   import MenuState
        from src.states.tavern_state import TavernState
        from src.states.world_state  import WorldState
        from src.states.boss_state   import BossState

        if name == "menu":
            return MenuState(self)
        if name == "tavern":
            return TavernState(self)
        if name == "world":
            return WorldState(self)
        if name == "boss1":
            return BossState(self, boss_id=1)
        if name == "boss2":
            return BossState(self, boss_id=2)
        raise ValueError(f"Unknown state: {name}")

    def _transition_to(self, name, prev_name=None):
        if self._current_state:
            self._current_state.on_exit()

        # Resolve special transition names
        actual_name = self._resolve_transition(name)

        state = self._get_state(actual_name)
        state.done = False
        state.next = None
        state.on_enter(prev_state=prev_name)

        self._current_state_name = actual_name
        self._current_state      = state

    def _resolve_transition(self, name):
        """Handle special names that require setup before entering a state."""

        if name == "tavern_new":
            self.player_data = new_player_data()
            return "tavern"

        if name == "load":
            loaded = load_player()
            if loaded:
                self.player_data = loaded
                # Restore saved world reference
                saved = load_world()
                if saved:
                    self.player_data["saved_world"] = saved
                sanitize_player_data(self.player_data)
            return "tavern"

        if name == "world_new":
            pd  = self.player_data
            wd  = generate_world(
                worlds_cleared=pd.get("worlds_cleared", 0),
                boss_kills=pd.get("boss_kills", 0),
            )
            pd["saved_world"] = wd.to_dict()
            save_world(wd.to_dict())
            # Inject world data into the world state
            ws = self._get_state("world")
            ws.world_data = wd
            ws.done = False
            return "world"

        if name == "world_revisit":
            pd   = self.player_data
            data = load_world() or pd.get("saved_world")
            if data:
                wd = WorldData.from_dict(data)
                ws = self._get_state("world")
                ws.world_data = wd
                ws.done = False
            return "world"

        if name == "death_return":
            # Player died — re-enter same world for recovery
            pd   = self.player_data
            data = load_world() or pd.get("saved_world")
            if data:
                wd = WorldData.from_dict(data)
                ws = self._get_state("world")
                ws.world_data = wd
                ws.done = False
            return "world"

        if name in ("boss1", "boss2"):
            # Reset boss state
            key = "boss1" if name == "boss1" else "boss2"
            if key in self._states:
                del self._states[key]
            return name

        return name

    # ─────────────────────────────────────────────
    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            dt = min(dt, 0.05)   # cap to prevent spiral

            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self._quit()

            state = self._current_state
            state.handle_events(events)
            state.update(dt)
            state.draw(self.screen)

            pygame.display.flip()

            # State transition
            if state.done and state.next:
                prev = self._current_state_name
                self._transition_to(state.next, prev_name=prev)

    def _quit(self):
        # Auto-save on quit
        try:
            save_player(self.player_data)
            if self.player_data.get("saved_world"):
                save_world(self.player_data["saved_world"])
        except Exception:
            pass
        pygame.quit()
        sys.exit()
