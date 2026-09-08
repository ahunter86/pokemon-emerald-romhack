# Pokémon Emerald: Randomizer Hack

A personal randomizer ROM hack of Pokémon Emerald, built on [pokeemerald-expansion](https://github.com/rh-hideout/pokeemerald-expansion).

## Features

### Randomization (per-save -- rolled independently each time you start a new save)
- **Wild encounters**: every encounter (grass, water, rock smash, fishing) is a genuinely fresh random pull from the whole eligible species pool, not tied to a fixed slot -- two fishing attempts at the same spot can give totally different species
- **Starters**: yours and the rival's, rolled independently; the rival's starter-line stays consistent with yours across her many battles
- **Every trainer's team**: not just the rival -- every trainer in the game has their species randomized, with team size, levels, moves, and everything else about their data completely untouched. Each party slot is independently randomized, so e.g. a trainer with two of the same original species gets two different substitutes, not the same one twice
- **Item balls, hidden items, given/shop TMs**: each specific location is independently randomized (not mapped by original item), so e.g. every Ether in the game doesn't all become the same replacement
- **Abilities**: consistent across an entire evolution line (evolving never changes your ability)
- **Move learnsets**: per-save, with a safety net guaranteeing a real damaging move is knowable at any level a Pokémon could realistically start at
- **Legendary/mythical/Paradox/Ultra Beast encounters** (the Regis, etc.): only ever randomize into another legendary-category Pokémon, never a regular species -- and regular wild encounters/trainers never roll a legendary-category Pokémon either
- **Shiny odds increased** to 1/512 (from vanilla 1/8192)

### Quality of life
- **Level cap system**: badge/Elite-Four-member/Champion/postgame-gated progression caps, so you can't out-level the story
- **Start Menu Tools shortcut**: Fly, Repel toggle (persistent, no need to keep buying/using Repel items), and instant party Heal, all from one submenu
- **Fly usable from the start of the game**, no badge required (still only flies to previously-visited locations)
- **Hold R on a Pokémon's Skills page** to see its actual IVs (numeric values, not letter grades) instead of calculated stats
- **Every Pokémon can learn every TM/HM** (species compatibility check removed for TM teaching specifically)
- **Regi ruins streamlined**: no Relicanth/Wailord party requirement or dig-and-braille puzzle. All three ruin entrances are open from the start of a new save
- Unlimited Rare Candy, max starting money, HMs usable without teaching them to a Pokémon

See [`FEATURES.md`](FEATURES.md) for the full list of features inherited from the underlying `pokeemerald-expansion` engine.

## Playing this hack

See [`PLAYING.md`](PLAYING.md) for how to get a playable ROM (patch a copy of vanilla Emerald you already own) or build it from source yourself.

## Known issues

See [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md) for deferred/known limitations.

## Credits

This hack is built on [RHH's pokeemerald-expansion](https://github.com/rh-hideout/pokeemerald-expansion), itself built on [pret's pokeemerald](https://github.com/pret/pokeemerald) decompilation project. See [`HACK_CREDITS.md`](HACK_CREDITS.md) for full attribution.
