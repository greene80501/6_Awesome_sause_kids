# Asset Layout

`assets/imported/awesome_sauce_kids/`
- Unmodified copy of the pulled GitHub art pack.

`assets/game/`
- Normalized runtime filenames used by the code.
- Names are lowercase and underscore-separated so the game can address them reliably.

## Runtime Mappings

### Food
- The runtime now includes the full imported food icon set under `assets/game/items/food/`.
- The original six food items still exist, and additional food entries were added so the rest of the imported food art can appear in shops and loot.
- `berries` still reuses `items/food/apples.png` because the source pack has no berry icon.

### Armor
- `leather_hood` uses `items/armor/hood.png`.
- `iron_helm` uses `items/armor/iron_helmet.png`.
- `chain_coif` uses `items/armor/chainmail_coif.png`.
- `war_helm` reuses `items/armor/iron_helmet.png`.
- `dread_crown` and `infernal_crown` use `items/armor/dread_crown.png`.
- `leather_vest` uses `items/armor/leather_vest.png`.
- `warden_plate` reuses `items/armor/leather_vest.png`.

### Animals
- `cow`, `sheep`, `deer`, `snow_hare`, and `desert_rabbit` use imported art.
- Cows and snow hares now use the variant images from the pack.
- Animals without matching source art still fall back to generated sprites.

### World Objects
- Imported art is wired for chest, campfire, puddle, ice rock, bone pile, flaming rock, lava fissure, rocks, bush, cactus, and log.
- Objects without matching source art still fall back to generated world props.

### Missing Source Art
- The linked pack does not contain player, enemy, bartender, or portal sprites.
- Those game entities still use generated placeholder art until matching images are added.
