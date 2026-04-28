# Tavern Looter

A dark-fantasy top-down survival looter built in Python + Pygame.

## Requirements
- Python 3.9+
- pygame 2.1+

## Install & Run

```bash
pip install pygame
python main.py
```

## Controls

| Key / Button       | Action                         |
|--------------------|-------------------------------|
| WASD               | Move                          |
| Mouse              | Aim direction                 |
| Left Mouse Button  | Attack (sword arc)            |
| E                  | Open inventory                |
| F                  | Interact (portal / bartender / chest / pickup) |
| 1–5                | Select hotbar slot            |
| Mouse Wheel        | Cycle hotbar                  |
| ESC (in world)     | Return to tavern portal       |
| ENTER              | Confirm (death / victory screens) |

## Gameplay Loop

1. Start in the **Tavern** — safe hub with Bartender (F to interact), Storage chest (F), and Portal (F)
2. Use the **Portal** to enter a procedurally generated world or revisit your saved one
3. Explore, fight enemies, gather loot and food
4. Manage **hunger** (drains over time) and **gear durability** (use costs)
5. Return through the portal to sell, repair, and resupply
6. Defeat **Boss 1** (The Warden) and **Boss 2** (The Hellborn) for major upgrades
7. Push deeper into endless harder runs after both bosses fall

## Death

- Dying drops all carried items + coins at your death location
- The pile vanishes after 60 seconds **in-world time**
- Re-enter the same world to attempt recovery before time runs out

## Progression

| Milestone       | Reward                              |
|-----------------|-------------------------------------|
| Boss 1 defeated | Storage 20→40, better shop stock   |
| Boss 2 defeated | Storage 40→80, best shop stock     |
| Endless runs    | Rising tiers, rarer loot, harder enemies |

## File Structure

```
tavern_looter/
├── main.py              ← Entry point
├── settings.py          ← All constants
├── requirements.txt
├── saves/               ← Auto-generated save files
└── src/
    ├── game.py          ← State machine / main loop
    ├── camera.py        ← Smooth scroll camera
    ├── sprite_factory.py ← Procedural art generation
    ├── save_system.py   ← JSON save/load
    ├── data/
    │   ├── items_data.py    ← All item definitions
    │   └── enemies_data.py  ← All enemy definitions
    ├── systems/
    │   ├── item.py          ← Item class
    │   ├── inventory.py     ← Inventory + storage
    │   ├── loot_tables.py   ← Drop generation
    │   └── economy.py       ← Shop pricing
    ├── entities/
    │   ├── player.py        ← Player entity
    │   ├── enemy.py         ← Enemy AI
    │   ├── animal.py        ← Passive wildlife
    │   ├── loot_drop.py     ← Ground items
    │   └── death_pile.py    ← Death recovery pile
    ├── world_gen/
    │   ├── biomes.py        ← Biome definitions
    │   └── generator.py     ← Procedural world builder
    ├── ui/
    │   ├── hud.py           ← In-game HUD
    │   ├── inventory_ui.py  ← Inventory screen
    │   ├── shop_ui.py       ← Bartender shop
    │   ├── storage_ui.py    ← Tavern storage
    │   └── portal_ui.py     ← World selection
    └── states/
        ├── base_state.py    ← State base class
        ├── menu_state.py    ← Title screen
        ├── tavern_state.py  ← Hub world
        ├── world_state.py   ← Procedural run
        └── boss_state.py    ← Boss fights
```
