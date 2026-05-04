# Assets

This folder is the one home for game art.

Rules:
- Every art file should exist only once.
- Store game-ready `.png` files only.
- Use lowercase `snake_case` names only.
- Organize by what the art is, not by who made it or where it came from.
- If teammates add new art, put it in the matching category folder here.

## Folder Layout

Animals:

```text
assets/animals/
  cows/
  deer/
  rabbits/
  sheep/
```

Items:

```text
assets/items/
  armor/
  food/
```

Weapons:

```text
assets/weapons/
  balanced/
    broadsword/
    hatchet/
    scimitar/
    sword/
    war_sword/
  light/
    dagger/
    mini_sword/
    rapier/
    sickle/
    twinblades/
  heavy/
    battle_axe/
    club/
    executioner_axe/
    greatsword/
    war_hammer/
  boss/
    hellborn_edge/
    warden_blade/
```

World:

```text
assets/world/
  decoration/
  frozen/
  hellscape/
  interactive/
  rocks/
  vegetation/
```

Environments:

```text
assets/environments/
  forest/
  tavern/
```

## Placement Examples

- Cow art goes in `assets/animals/cows/`
- Helmet art goes in `assets/items/armor/`
- Food art goes in `assets/items/food/`
- Hatchet art goes in `assets/weapons/balanced/hatchet/`
- Campfire art goes in `assets/world/interactive/`
- Forest background art goes in `assets/environments/forest/`

## Code Contract

The game now loads art directly from `assets/`.

If you rename or move a file that is already in use, update [src/sprite_factory.py](../src/sprite_factory.py) to match.
