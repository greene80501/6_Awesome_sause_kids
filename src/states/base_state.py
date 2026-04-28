# src/states/base_state.py
import pygame


class BaseState:
    """All game states inherit from this."""

    def __init__(self, game):
        self.game = game
        self.next  = None    # set to state name to trigger transition
        self.done  = False

    def on_enter(self, prev_state=None):
        """Called when this state becomes active."""
        pass

    def on_exit(self):
        """Called when leaving this state."""
        pass

    def handle_events(self, events):
        pass

    def update(self, dt):
        pass

    def draw(self, surface):
        pass

    def _make_fonts(self):
        from settings import FONT_SM, FONT_MD, FONT_LG, FONT_XL
        return (
            pygame.font.SysFont("segoeui", FONT_SM),
            pygame.font.SysFont("segoeui", FONT_MD),
            pygame.font.SysFont("segoeui", FONT_LG),
            pygame.font.SysFont("segoeui", FONT_XL),
        )
