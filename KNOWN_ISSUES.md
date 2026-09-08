# Known Issues / Deferred Work

Things intentionally left unfinished or accepted as-is. Revisit before any public release.

## Rival's starter has no type matchup

The rival's starter species is rolled independently from the player's (see `RandomizeRivalTrainerMonSpecies`
in `src/battle_main.c`), rather than being counter-picked to have a type advantage the way vanilla
Emerald's Treecko/Torchic/Mudkip rival selection works. Dropped because the player's starter pool
covers every type, so there's no clean way to generalize "pick the type that counters the player"
the way the original 3-way Grass/Fire/Water triangle did. If revisited, this would need real
type-effectiveness lookup logic added to the rival roll in `new_game.c`.

## Starter's guaranteed damaging move isn't type-matchup-proofed against the rival

`GetSpeciesLevelUpLearnset`'s runtime safety net (`src/pokemon.c`, using `sMoveIsDamaging` /
`RANDOMIZER_LEARNSET_CHECK_LEVEL`) guarantees every species has at least one real damaging move
early on, so no starter/early encounter can have an all-status moveset. However, since the rival's
species is *also* independently randomized, there's a narrow edge case: if a starter's only
guaranteed damaging move happens to be a type the rival's rolled species is fully immune to (e.g. a
Psychic-only attacker vs. a Dark-type rival), that one guaranteed move could still be functionally
useless in the first mandatory battle.

Accepted as-is for now (narrow intersection of unlucky rolls, not a guaranteed occurrence). If
revisited, the fix is to strengthen the safety net to guarantee at least two damaging moves of
*different* types within the early-level window, rather than just one -- no single type in the real
type chart is immune to two different attacking types at once, so this would close the gap entirely.
Would need move `.type` data added to the runtime pool (`sRandomizerMovePool` currently only tracks
`.power` and `.effect` via `sMoveIsDamaging`).

## Fossil scientist only handles 0 or 1 fossil type cleanly
The Devon Corp fossil scientist (Rustboro City, `data/maps/RustboroCity_DevonCorp_2F/scripts.inc`)
now works without requiring the player to have any specific fossil item, and correctly uses/consumes
an actual fossil if the player has exactly one type (`CheckPlayerFossilItem` / `GetFossilBaseSpecies`
in `src/wild_encounter.c`), randomizing based on that fossil's real base species. However, if the
player has zero, or two or more DIFFERENT fossil types at once, it falls back to a generic two-option
choice labeled "Root Fossil"/"Claw Fossil" regardless of what's actually in the bag, and doesn't
consume anything in that case. Multiple copies of the SAME fossil type are fine (still treated as
"exactly one type").
Accepted as-is for now, since properly supporting 3+ different fossil types simultaneously would need
a dynamically-built choice menu (a new string/UI per possibility) rather than the existing fixed
two-option multichoice, and fossils aren't especially common randomizer loot. If revisited, this would
need either a dynamic multichoice built from whichever fossils the player is actually carrying, or a
simpler UI (e.g. a scrollable list) that doesn't require a fixed string per combination.

## Hidden items that randomize to a TM/HM can get double-randomized
`RandomizeFieldItem` runs once for the hidden item itself (`src/field_control_avatar.c`), and if the
result happens to be a TM, `ScrCmd_additem`'s separate TM-specific randomization (`src/scrcmd.c`) can
run a second time on top of it, since it doesn't distinguish "already-randomized TM" from "TM straight
from a script." Narrow edge case (~10% of hidden item pulls, only when the intermediate result happens
to land on a TM). Accepted as-is for now. If revisited, this would need `RandomizeFieldItem` to tag its
result somehow (or `ScrCmd_additem` to recognize it was called via the hidden-item path) so the TM
randomization step is skipped when the item was already substituted upstream.
