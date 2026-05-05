# src/save_system.py
import json, os

SAVE_DIR  = "saves"
SAVE_FILE = os.path.join(SAVE_DIR, "player.json")
WORLD_FILE = os.path.join(SAVE_DIR, "saved_world.json")


def ensure_save_dir():
    os.makedirs(SAVE_DIR, exist_ok=True)


def sanitize_player_data(player_data, allow_zero_health=False):
    """Clamp persisted player state and backfill missing save fields."""
    from src.config import get_config
    from src.systems.inventory import Inventory, TavernStorage

    pc = get_config().get("player", {})
    max_health = max(1.0, float(player_data.get("max_health", pc.get("starting_health", 100))))
    max_hunger = max(1.0, float(player_data.get("max_hunger", pc.get("starting_hunger", 100))))
    min_health = 0.0 if allow_zero_health else 1.0

    player_data["max_health"] = max_health
    player_data["max_hunger"] = max_hunger
    player_data["health"] = max(min_health, min(float(player_data.get("health", max_health)), max_health))
    player_data["hunger"] = max(0.0, min(float(player_data.get("hunger", max_hunger)), max_hunger))
    player_data["coins"] = max(0, int(player_data.get("coins", pc.get("starting_coins", 25))))
    player_data["boss_kills"] = max(0, int(player_data.get("boss_kills", 0)))
    player_data["highest_tier"] = max(0, int(player_data.get("highest_tier", 0)))
    player_data["worlds_cleared"] = max(0, int(player_data.get("worlds_cleared", 0)))
    player_data["death_world_id"] = player_data.get("death_world_id")
    player_data["saved_world"] = player_data.get("saved_world")

    if not isinstance(player_data.get("inventory"), Inventory):
        player_data["inventory"] = Inventory()
    if not isinstance(player_data.get("storage"), TavernStorage):
        player_data["storage"] = TavernStorage(boss_kills=player_data["boss_kills"])
    else:
        player_data["storage"].update_size(player_data["boss_kills"])
    return player_data


def save_player(player_data):
    ensure_save_dir()
    # inventory & storage need serialization
    data = sanitize_player_data(dict(player_data))
    if data.get("inventory"):
        data["inventory"] = data["inventory"].to_dict()
    if data.get("storage"):
        data["storage"] = data["storage"].to_dict()
    data.pop("saved_world", None)  # saved separately
    with open(SAVE_FILE, "w") as f:
        json.dump(data, f, indent=2)


def load_player():
    if not os.path.exists(SAVE_FILE):
        return None
    with open(SAVE_FILE) as f:
        data = json.load(f)
    from src.systems.inventory import Inventory, TavernStorage
    data["inventory"] = Inventory.from_dict(data.get("inventory", {})) \
        if data.get("inventory") else Inventory()
    data["storage"]   = TavernStorage.from_dict(
        data.get("storage", {}), boss_kills=data.get("boss_kills", 0))
    return sanitize_player_data(data)


def save_world(world_data):
    if world_data is None:
        if os.path.exists(WORLD_FILE):
            os.remove(WORLD_FILE)
        return
    ensure_save_dir()
    with open(WORLD_FILE, "w") as f:
        json.dump(world_data, f, indent=2)


def load_world():
    if not os.path.exists(WORLD_FILE):
        return None
    with open(WORLD_FILE) as f:
        return json.load(f)


def delete_world():
    if os.path.exists(WORLD_FILE):
        os.remove(WORLD_FILE)


def has_save():
    return os.path.exists(SAVE_FILE)


def new_player_data():
    from src.systems.inventory import Inventory, TavernStorage
    from src.config import get_config
    pc = get_config().get("player", {})
    data = {
        "health":      pc.get("starting_health", 100),
        "max_health":  pc.get("starting_health", 100),
        "hunger":      pc.get("starting_hunger", 100),
        "max_hunger":  pc.get("starting_hunger", 100),
        "coins":       pc.get("starting_coins",  25),
        "inventory":   Inventory(),
        "storage":     TavernStorage(boss_kills=0),
        "boss_kills":  0,
        "highest_tier": 0,
        "worlds_cleared": 0,
        "saved_world": None,
        "death_world_id": None,
    }
    return sanitize_player_data(data)
