# src/config.py
# Loads setup.json once and caches it. Falls back to defaults if file is missing/invalid.
import json
import os

_cache = None


def get_config():
    global _cache
    if _cache is None:
        path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "setup.json",
        )
        try:
            with open(path) as f:
                _cache = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            _cache = _defaults()
    return _cache


def _defaults():
    return {
        "world": {
            "enemy_count_mult":        1.0,
            "animal_count_mult":       1.0,
            "loot_node_count_mult":    1.0,
            "loot_tier_bonus":         0,
            "ruin_count_min":          1,
            "ruin_count_max":          3,
            "enemy_camp_count_min":    1,
            "enemy_camp_count_max":    2,
            "poi_count":               1,
            "decorative_scatter_mult": 1.0,
        },
        "difficulty": {
            "enemy_damage_mult": 1.0,
            "enemy_hp_mult":     1.0,
            "enemy_speed_mult":  1.0,
            "hunger_drain_mult": 1.0,
        },
        "player": {
            "starting_coins":  25,
            "starting_health": 100,
            "starting_hunger": 100,
        },
    }
