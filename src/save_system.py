# src/save_system.py
import json, os

SAVE_DIR  = "saves"
SAVE_FILE = os.path.join(SAVE_DIR, "player.json")
WORLD_FILE = os.path.join(SAVE_DIR, "saved_world.json")


def ensure_save_dir():
    os.makedirs(SAVE_DIR, exist_ok=True)


def save_player(player_data):
    ensure_save_dir()
    # inventory & storage need serialization
    data = dict(player_data)
    if player_data.get("inventory"):
        data["inventory"] = player_data["inventory"].to_dict()
    if player_data.get("storage"):
        data["storage"] = player_data["storage"].to_dict()
    data.pop("saved_world", None)  # saved separately
    with open(SAVE_FILE, "w") as f:
        json.dump(data, f, indent=2)


def load_player():
    if not os.path.exists(SAVE_FILE):
        return None
    with open(SAVE_FILE) as f:
        data = json.load(f)
    from src.systems.inventory import Inventory, TavernStorage
    data["inventory"] = Inventory.from_dict(data["inventory"])
    data["storage"]   = TavernStorage.from_dict(
        data["storage"], boss_kills=data.get("boss_kills", 0))
    return data


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
    return {
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
