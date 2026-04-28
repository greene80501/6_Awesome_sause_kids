# Tavern Looter: Full Game Breakdown

This document explains the current game as it exists in this repository. It covers the player-facing design, the code architecture, the asset pipeline, and exact content counts pulled from the project files.

## 1. What the game is

**Tavern Looter** is a top-down dark-fantasy survival looter built in **Python** with **Pygame**.

The core loop is:

1. Start in the tavern hub.
2. Use the portal to enter a generated world or revisit your saved world.
3. Fight enemies, avoid starving, open chests, collect gear and food.
4. Return to the tavern to sell loot, repair gear, store items, and prepare again.
5. Beat boss fights to unlock better progression.

The code supports both a normal run structure and a persistent recovery loop:

- Dying in a normal world drops all carried items and coins into a timed death pile.
- Re-entering that same saved world lets you try to recover them.
- Dying in boss fights is more forgiving: the boss resets, but you keep your items.

## 2. Quick technical snapshot

| Area | Current implementation |
|---|---|
| Engine | Pygame |
| Language | Python |
| Window size | `1280 x 720` |
| Framerate target | `60 FPS` |
| Tile size | `32 px` |
| Main world size | `80 x 80` tiles |
| Tavern size | `25 x 18` tiles |
| Boss arena size | `40 x 30` tiles |
| Save format | JSON |
| Game structure | State machine |
| Rendering style | Mixed procedural art + imported PNG assets |

## 3. How the game is organized in code

### Entry and boot flow

- `main.py` is the entry point. It inserts the project root into `sys.path`, constructs `Game`, and runs it.
- `src/game.py` owns the main loop, the current state, the shared `player_data` dictionary, and state transitions.
- `settings.py` holds the game's constants: screen size, combat values, hunger rates, rarity tables, UI sizes, and progression thresholds.
- `src/config.py` loads `setup.json` once and uses defaults if the file is missing or invalid.

### The state machine

The game is split into major states:

- `menu` for the title screen.
- `tavern` for the hub.
- `world` for regular procedural runs.
- `boss1` for The Warden.
- `boss2` for The Hellborn.

`src/game.py` lazy-loads these states and switches between them by calling each state's `on_enter`, `update`, `draw`, and `on_exit`.

### Main directories and responsibilities

| Path | Responsibility |
|---|---|
| `src/states/` | Menu, tavern, world, and boss fight flow |
| `src/entities/` | Player, enemies, animals, loot drops, death pile |
| `src/systems/` | Item instances, inventory, economy, loot tables |
| `src/data/` | Static content definitions for items and enemies |
| `src/world_gen/` | Biomes, world generation, object placement |
| `src/ui/` | HUD, inventory, shop, storage, portal UI |
| `src/sprite_factory.py` | Procedural sprites, asset loading, cached image fitting |
| `src/save_system.py` | Save/load for player and world JSON |
| `assets/` | Runtime PNGs plus the original imported source pack |

### Codebase size

Based on the current repo snapshot:

- **37 Python files** total in the repo, excluding `.venv` and `__pycache__`
- **35 Python files** under `src/`

## 4. What happens in each major state

### Menu

`src/states/menu_state.py`

- Draws an animated title screen with a pulsing portal and star field.
- Supports `New Game` and `Continue`.
- Loads save existence through `has_save()`.

### Tavern

`src/states/tavern_state.py`

This is the safe hub.

Features:

- Fixed tavern map with a bar, walls, torches, bartender, chest, and portal.
- Bartender shop.
- Permanent storage chest.
- Portal menu for world selection and boss access.
- Inventory access.
- Light hunger drain, but no active enemy threat.

Important tavern interactions:

- `F` near bartender opens the shop.
- `F` near storage opens long-term storage.
- `F` near the portal opens world/boss selection.

### Regular world

`src/states/world_state.py`

This is the main gameplay state.

Features:

- Loads or receives a `WorldData` object.
- Pre-renders the world terrain and static objects.
- Spawns enemies, animals, chests, portal, loot drops, and optional death pile.
- Tracks fog of war.
- Handles combat, hunger, item pickup, objective completion, and death recovery.

### Boss fights

`src/states/boss_state.py`

These are self-contained arenas with:

- A special boss entity.
- Phase transitions.
- Minion spawning in phase 2.
- Victory and defeat screens.
- Automatic progression rewards on success.

The two bosses are:

- **Boss 1:** The Warden
- **Boss 2:** The Hellborn

## 5. Core gameplay systems

### Movement and camera

- Player movement is WASD / arrow-key based.
- Diagonal movement is normalized.
- Collision is simple AABB collision against blocking world rectangles.
- `src/camera.py` provides smooth follow behavior and world-to-screen translation.

### Combat

Combat is melee arc-based, not projectile-based.

- Left-click starts a swing.
- The player attacks in a directional cone aimed at the mouse.
- Hit detection checks:
  - whether the target is inside attack range
  - whether the target falls inside the attack arc
  - whether the target has already been hit during this swing

Combat values from `settings.py`:

- Base attack arc: **85 degrees**
- Base attack range: **68 px**
- Attack movement slowdown: **35% of normal speed**

Weapon classes:

- `light`: fast, weaker, less durable
- `balanced`: standard middle ground
- `heavy`: slow, stronger, longer reach / wider arc bonuses

### Hunger, starvation, and regen

The survival layer is simple but always active.

- Hunger drains in the world at **0.55 per second**
- Hunger drains in the tavern at **0.12 per second**
- At `0 hunger`, the player takes **6 HP/sec** starvation damage
- At `90+ hunger`, the player regenerates **3.5 HP/sec**

### Durability

- Weapons lose durability when used.
- Armor loses durability when taking damage.
- Broken gear stays equipped but stops giving its normal benefit.
- The shop repair tab restores durability for coins.

### Death recovery

In regular worlds:

- Death drops all carried inventory, hotbar items, equipped gear, and coins.
- The death pile lasts **60 seconds of in-world time**.
- The timer only ticks while you are inside that world.

In boss states:

- Death does **not** create a death pile.
- You keep your items.
- The boss encounter resets.

## 6. Procedural world generation

`src/world_gen/generator.py` and `src/world_gen/biomes.py`

Each generated world has:

- a random world ID and seed
- one biome
- one world type
- a portal position and spawn position
- scattered terrain objects
- enemy spawns
- animal spawns
- loot chests
- optional points of interest
- optional objective data
- persistent fog data

### World types

There are **3 world types**:

- `resource`
- `combat`
- `objective`

The generator weights them at:

- 40% resource
- 40% combat
- 20% objective

### Biomes

There are **7 biomes**:

1. Plains
2. Forest
3. Desert
4. Caves
5. Hellscape
6. Frozen Land
7. Cloud Land

Each biome defines:

- floor tile style
- background color
- obstacle density
- scatter object types
- animal budget
- threat multiplier
- food density
- loot density
- danger label
- hint text

### Points of interest

There are **4 POI templates**:

1. Abandoned Watchtower
2. Overgrown Graveyard
3. Bandit Camp
4. Ruined Shrine

POIs add:

- themed structure layouts
- clustered enemies
- elite opportunities
- guaranteed loot nodes

### Objectives

The generator can assign **3 objective types**:

1. `kill_elite`
2. `clear_world`
3. `carry_item`

Important implementation note:

- `kill_elite` is implemented.
- `clear_world` is implemented.
- `carry_item` is generated and displayed, but the current code does not actually spawn or track a carried objective item, so this objective path is only partially wired.

## 7. Content counts

These counts come directly from the data files in this repo.

### Enemies and creatures

- **18 enemy archetypes**
- **5 passive animal archetypes**
- **2 bosses**

Enemy archetypes:

- Goblin
- Skeleton
- Zombie
- Wolf
- Forest Troll
- Scorpion
- Sand Wraith
- Bat
- Cave Spider
- Stone Golem
- Imp
- Demon
- Hell Knight
- Frost Wolf
- Ice Wraith
- Frost Giant
- Harpy
- Storm Elemental

Animal archetypes:

- Cow
- Sheep
- Deer
- Snow Hare
- Desert Hare

### Items

- **15 weapon definitions**
- **20 armor definitions**
- **35 food definitions**
- **4 boss loot definitions**

That is **74 total item definitions** in the content tables.

#### Weapons

- 5 light weapons
- 5 balanced weapons
- 5 heavy weapons

#### Armor

Armor covers these slots:

- head
- chest
- legs
- boots

Each slot has 5 tiers of definitions.

#### Food

Food is stackable and mostly serves hunger recovery. The list ranges from basic survival foods like apples and bread to higher-tier items like hamburger, pizza, feast ration, and cherry pie.

### Rarities

There are **5 rarities**:

1. Common
2. Good
3. Rare
4. Epic
5. Legendary

Rarity affects:

- weapon damage
- armor defense
- sell value
- loot odds

## 8. Inventory, storage, and economy

### Inventory model

`src/systems/inventory.py`

The player carries:

- **24 main inventory slots**
- **5 hotbar slots**
- **5 equipment slots**

Equipment slots are:

- head
- chest
- legs
- boots
- weapon

### Storage

Tavern storage is persistent and expands with boss progression:

- **20 slots** at start
- **40 slots** after Boss 1
- **80 slots** after Boss 2

### Shop

`src/ui/shop_ui.py` and `src/systems/economy.py`

The bartender has three tabs:

1. Buy
2. Sell
3. Repair

Shop stock is rebuilt when entering the tavern and is gated by boss progression:

- 0 boss kills: basic shop
- 1 boss kill: mid-tier shop
- 2 boss kills: best shop

## 9. Boss progression

### The Warden

- HP: **600**
- Touch damage: **18**
- Speed: **85**
- Size: **52**
- Phase 2 threshold: **45% HP**

Rewards:

- sets `boss_kills` to 1 if not already earned
- expands storage to 40
- unlocks Boss 2
- grants boss loot and coins

### The Hellborn

- HP: **1100**
- Touch damage: **28**
- Speed: **95**
- Size: **60**
- Phase 2 threshold: **40% HP**

Rewards:

- sets `boss_kills` to 2 if not already earned
- expands storage to 80
- grants boss loot and coins

## 10. Save system and persistence

`src/save_system.py`

The game uses JSON files in `saves/`:

- `saves/player.json`
- `saves/saved_world.json`

What persists:

- health and hunger values
- coins
- inventory
- storage
- boss progression
- saved world data

World data persists separately from player data so a run can be revisited.

The world save includes:

- fog state
- object placements
- enemy kill history
- loot node opened state
- dropped items
- death pile data

## 11. Rendering and sprite pipeline

This game uses a **hybrid art pipeline**:

- some visuals are imported PNG sprite assets
- many others are generated procedurally in code

### Exact PNG counts

In the current repo:

- **61 PNG files** inside `assets/game/`
- **63 PNG files** inside `assets/imported/`
- **124 PNG files** total under `assets/`
- **60 unique runtime PNG files** are actually referenced by code
- **1 runtime PNG file is currently unused:** `assets/game/items/food/applles.png`

### Runtime PNG breakdown

Referenced runtime PNG files break down like this:

- **6 animal PNGs**
- **5 armor PNGs**
- **34 used food PNGs**
- **15 world / chest / prop PNGs**

### Imported art coverage

#### Animals

All 5 animal types are backed by imported art.

Details:

- Cows have 2 variants
- Snow hares have 2 variants
- Desert hare reuses the alternate snow hare sprite

#### World objects

There are **22 world object types** defined in biome/object data.

- **13 object types** have imported PNG art wired in
- **9 object types** fall back to procedural drawing

Object types with imported PNG art:

- campfire
- puddle
- ice_rock
- skull_pile
- fire_rock
- lava_crack
- rock_large
- rock_med
- rock_small
- stalagmite
- bush
- cactus
- log

World object types still drawn procedurally:

- flower
- tall_grass
- tree_large
- tree_med
- tree_small
- snow_drift
- frozen_tree
- cloud_puff
- wind_crystal

#### Items

There are **46 item IDs mapped to PNG icons**, but those mappings only use **39 unique item icon files** because several items reuse the same art.

Known icon reuse:

- `berries` uses the apples icon
- `stew` uses `bowl_of_rice.png`
- `feast_ration` uses `sandwich.png`
- `war_helm` reuses `iron_helmet.png`
- `infernal_crown` reuses `dread_crown.png`
- `chain_mail`, `plate_chest`, `war_plate`, and `warden_plate` all reuse `leather_vest.png`

#### What is still procedural instead of imported PNG art

These important visuals are currently generated in `src/sprite_factory.py`:

- player
- all normal enemies
- elite enemy crown overlay
- both bosses
- portal
- bartender
- terrain tiles for all biomes
- fallback weapon icons
- fallback armor icons
- fallback food icons

Practical result:

- the game has real imported icon/prop support
- but combat characters are still mostly placeholder-style procedural art

## 12. UI systems

### HUD

`src/ui/hud.py`

Shows:

- health bar
- hunger bar
- coin count
- current weapon and durability
- 5-slot hotbar
- minimap
- notifications

### Inventory UI

`src/ui/inventory_ui.py`

Supports:

- drag/swap style left-click movement
- right-click equip
- right-click food use
- equipment panel
- tooltips

### Shop UI

`src/ui/shop_ui.py`

Supports:

- item buying
- selling from inventory/hotbar/equipment
- gear repair
- hover tooltips with price info

### Storage UI

`src/ui/storage_ui.py`

Supports:

- moving items between inventory and permanent storage
- right-click quick transfer

### Portal UI

`src/ui/portal_ui.py`

Supports:

- re-entering the saved world
- generating a new world
- starting Boss 1
- starting Boss 2 after Boss 1 is cleared

## 13. Tuning and balancing hooks

The easiest place to tune the game without changing code is `setup.json`.

You can change:

- enemy count multiplier
- animal count multiplier
- loot node multiplier
- loot tier bonus
- ruin count
- enemy camp count
- POI count
- decorative scatter multiplier
- enemy damage / HP / speed multipliers
- hunger drain multiplier
- starting coins / health / hunger

This is a clean separation point between design tuning and engine code.

## 14. Important implementation notes

These are not guesses; they are based on the current code.

### Progression counters are only partly wired

The player data includes:

- `worlds_cleared`
- `highest_tier`

Those values are displayed or passed into systems, but in the current code they are not actually incremented during the main world return flow. That means long-term tier progression is currently driven more by:

- boss kills
- `setup.json` tuning

than by completed world count.

### Single saved-world model

The portal currently works around one saved world slot:

- generate new world replaces the saved slot
- revisit reopens that saved slot

### Some hooks exist but are not fully used

Examples:

- `carry_item` objective is not fully implemented
- `delete_world()` exists in the save system but is not currently part of the normal flow
- `revisitable` exists on `WorldData` but is not meaningfully enforced elsewhere

## 15. Summary

At its current stage, Tavern Looter is a solid small action-looter with:

- a functioning state-machine architecture
- procedural world generation
- persistent loot and save data
- hunger, durability, and death-recovery systems
- a tavern hub with shop, storage, and portal flow
- 7 biomes, 18 enemy types, 5 animals, 2 bosses, and 74 item definitions
- 60 runtime-used PNG sprite/image files plus procedural fallback rendering for major actors

The strongest technical choices in the current build are:

- clean state separation
- data-driven content tables
- JSON persistence
- a hybrid procedural/imported art pipeline
- a configurable tuning layer through `setup.json`

The biggest current gaps are:

- incomplete world-clear progression tracking
- incomplete `carry_item` objective support
- continued reliance on placeholder procedural sprites for player/enemy/boss character art
