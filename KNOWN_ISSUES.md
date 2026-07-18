# Known Issues / Deferred Work

Things intentionally left unfinished or accepted as-is. Revisit before any public release.

## Rival's starter has no type matchup
The rival's starter species is rolled independently from the player's (see `RandomizeRivalTrainerMonSpecies`
in `src/battle_main.c`), rather than being counter-picked to have a type advantage the way vanilla
Emerald's Treecko/Torchic/Mudkip rival selection works. Dropped because the player's starter pool
covers every type, so there's no clean way to generalize "pick the type that counters the player"
the way the original 3-way Grass/Fire/Water triangle did. If revisited, this would need real
type-effectiveness lookup logic added to the rival roll in `new_game.c`.

## Abilities and move learnsets are build-time, not per-save
Unlike wild encounters/starters/rival (all per-save via a save-file seed), species abilities
(`tools/randomizer/randomize_abilities.py`) and move learnsets (`tools/randomizer/randomize_learnsets.py`)
are randomized once at build time and are identical across every save on a given ROM build. Making
these per-save would require a much more invasive runtime approach (abilities are read from many
call sites throughout battle logic, not a single choke point like wild encounters/trainer parties),
so this was deliberately scoped down. To get a different ability/learnset randomization, rerun the
scripts with a new `--seed` and rebuild.

## Starter's guaranteed damaging move isn't type-matchup-proofed against the rival
`randomize_learnsets.py`'s safety net guarantees every species has at least one real damaging move
early on (see `simulate_initial_moveset` / `CHECK_LEVEL` in the script), so no starter/early encounter
can have an all-status moveset. However, since the rival's species is *also* independently randomized,
there's a narrow edge case: if a starter's only guaranteed damaging move happens to be a type the
rival's rolled species is fully immune to (e.g. a Psychic-only attacker vs. a Dark-type rival), that
one guaranteed move could still be functionally useless in the first mandatory battle.

Accepted as-is for now (narrow intersection of unlucky rolls, not a guaranteed occurrence). If
revisited, the fix is to strengthen the safety net to guarantee at least two damaging moves of
*different* types within the early-level window, rather than just one -- no single type in the real
type chart is immune to two different attacking types at once, so this would close the gap entirely.
Would need move `.type` data added to the script (currently only tracks `.power` and `.effect`).
