#!/usr/bin/env python3
"""
Randomize the player's 3 starter species in src/starter_choose.c.

Pulls from the FULL species pool (regular + legendary/mythical), since
starters are a one-time pick rather than a repeated encounter pool.
Mega Evolution / Gigantamax / Primal / Totem / Ultra forms are excluded
-- they require battle-only mechanics that don't make sense as a
starting species.

The name and front sprite shown on the starter-select screen are both
already pulled dynamically from species data (GetSpeciesName /
CreatePokemonFrontSprite), so no other code needs to change for those
to display correctly.

Usage (from repo root):
    python3 tools/randomizer/randomize_starters.py [--seed N]

A backup of the original file is written to starter_choose.c.bak the
first time you run this (never overwritten after that, so you keep
your true original).
"""
import argparse
import random
import re
import json
import shutil
from pathlib import Path

STARTER_CHOOSE_PATH = Path("src/starter_choose.c")
BACKUP_PATH = Path("src/starter_choose.c.bak")
SPECIES_POOL_PATH = Path("tools/randomizer/species_pool.json")

EXCLUDE_SUBSTRINGS = ["_MEGA", "_GMAX", "_PRIMAL", "_ETERNAMAX", "_TOTEM", "_ULTRA", "_COMPLETE"]

ARRAY_PATTERN = re.compile(
    r"static const u16 sStarterMon\[STARTER_MON_COUNT\] =\s*\{[^}]*\};"
)


def load_full_pool():
    data = json.loads(SPECIES_POOL_PATH.read_text())
    pool = []
    for entry in data["species"]:
        const = entry["constant"]
        if any(sub in const for sub in EXCLUDE_SUBSTRINGS):
            continue
        if entry.get("has_pre_evolution", False):
            continue  # only first-stage species are eligible as starters
        pool.append(const)
    return pool


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=None,
                         help="Random seed for reproducible output")
    args = parser.parse_args()

    rng = random.Random(args.seed)

    if not STARTER_CHOOSE_PATH.exists():
        print(f"ERROR: {STARTER_CHOOSE_PATH} not found -- run this from the repo root.")
        return
    if not SPECIES_POOL_PATH.exists():
        print(f"ERROR: {SPECIES_POOL_PATH} not found -- run fetch_species_data.py first.")
        return

    pool = load_full_pool()
    print(f"Full starter-eligible pool: {len(pool)} species (regular + legendary/mythical).")

    chosen = rng.sample(pool, 3)
    print("Chosen starters:")
    print(f"  Slot 0 (left,  was Grass-type slot): {chosen[0]}")
    print(f"  Slot 1 (mid,   was Fire-type slot):  {chosen[1]}")
    print(f"  Slot 2 (right, was Water-type slot): {chosen[2]}")

    content = STARTER_CHOOSE_PATH.read_text()
    new_block = (
        "static const u16 sStarterMon[STARTER_MON_COUNT] =\n"
        "{\n"
        f"    {chosen[0]},\n"
        f"    {chosen[1]},\n"
        f"    {chosen[2]},\n"
        "};"
    )

    if not ARRAY_PATTERN.search(content):
        print("ERROR: couldn't find the sStarterMon array in starter_choose.c -- "
              "the file may have changed structure. No changes made.")
        return

    new_content = ARRAY_PATTERN.sub(new_block, content, count=1)

    if not BACKUP_PATH.exists():
        shutil.copy(STARTER_CHOOSE_PATH, BACKUP_PATH)
        print(f"Backed up original to {BACKUP_PATH}")
    else:
        print(f"Backup already exists at {BACKUP_PATH} (not overwritten).")

    STARTER_CHOOSE_PATH.write_text(new_content)
    print(f"Wrote randomized starters to {STARTER_CHOOSE_PATH}")


if __name__ == "__main__":
    main()
