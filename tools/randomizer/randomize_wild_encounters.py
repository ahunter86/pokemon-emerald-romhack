#!/usr/bin/env python3
"""
Stage 2: Randomize wild encounters in wild_encounters.json.

Regular (non-legendary/mythical) slots are replaced with random regular
species. If any slot already contains a legendary/mythical (unusual for
this file, but handled just in case -- e.g. some hacks add roamers to
route tables), it's replaced with a different legendary/mythical instead,
per the "legendaries only replaced with legendaries" rule.

Mega Evolution / Gigantamax / Primal forms are excluded from the pool
entirely -- they require a held item + in-battle trigger and shouldn't
appear as ordinary wild encounters.

Usage (from repo root):
    python3 tools/randomizer/randomize_wild_encounters.py [--seed N] [--dry-run]

A backup of the original file is written to wild_encounters.json.bak
the first time you run this (it will NOT overwrite an existing .bak,
so you always keep your true original).
"""
import argparse
import json
import random
import shutil
from pathlib import Path

ENCOUNTERS_PATH = Path("src/data/wild_encounters.json")
BACKUP_PATH = Path("src/data/wild_encounters.json.bak")
SPECIES_POOL_PATH = Path("tools/randomizer/species_pool.json")

ENCOUNTER_FIELD_TYPES = ["land_mons", "water_mons", "rock_smash_mons", "fishing_mons"]

EXCLUDE_SUBSTRINGS = ["_MEGA", "_GMAX", "_PRIMAL", "_ETERNAMAX", "_TOTEM"]


def load_pools():
    data = json.loads(SPECIES_POOL_PATH.read_text())
    regular = []
    legendary = []
    by_constant = {}
    for entry in data["species"]:
        const = entry["constant"]
        by_constant[const] = entry
        if any(sub in const for sub in EXCLUDE_SUBSTRINGS):
            continue
        if entry["legendary"] or entry["mythical"]:
            legendary.append(const)
        else:
            regular.append(const)
    return regular, legendary, by_constant


def randomize_mons_list(mons, regular_pool, legendary_pool, by_constant, rng, counters):
    for mon in mons:
        current = mon.get("species")
        info = by_constant.get(current)
        is_legendary = bool(info and (info["legendary"] or info["mythical"]))
        pool = legendary_pool if is_legendary else regular_pool
        if not pool:
            continue
        mon["species"] = rng.choice(pool)
        counters["legendary" if is_legendary else "regular"] += 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=None,
                         help="Random seed for reproducible output")
    parser.add_argument("--dry-run", action="store_true",
                         help="Print what would change without writing the file")
    args = parser.parse_args()

    rng = random.Random(args.seed)

    if not ENCOUNTERS_PATH.exists():
        print(f"ERROR: {ENCOUNTERS_PATH} not found -- run this from the repo root.")
        return
    if not SPECIES_POOL_PATH.exists():
        print(f"ERROR: {SPECIES_POOL_PATH} not found -- run fetch_species_data.py first.")
        return

    regular_pool, legendary_pool, by_constant = load_pools()
    print(f"Regular pool: {len(regular_pool)} species. Legendary/mythical pool: {len(legendary_pool)} species.")

    data = json.loads(ENCOUNTERS_PATH.read_text())

    counters = {"regular": 0, "legendary": 0}
    for group in data.get("wild_encounter_groups", []):
        for encounter in group.get("encounters", []):
            for field_type in ENCOUNTER_FIELD_TYPES:
                field = encounter.get(field_type)
                if not field:
                    continue
                randomize_mons_list(field["mons"], regular_pool, legendary_pool,
                                     by_constant, rng, counters)

    total = counters["regular"] + counters["legendary"]
    print(f"Randomized {total} encounter slots ({counters['regular']} regular, "
          f"{counters['legendary']} legendary/mythical).")

    if args.dry_run:
        print("Dry run -- not writing any files.")
        return

    if not BACKUP_PATH.exists():
        shutil.copy(ENCOUNTERS_PATH, BACKUP_PATH)
        print(f"Backed up original to {BACKUP_PATH}")
    else:
        print(f"Backup already exists at {BACKUP_PATH} (not overwritten -- that's your true original).")

    ENCOUNTERS_PATH.write_text(json.dumps(data, indent=2) + "\n")
    print(f"Wrote randomized encounters to {ENCOUNTERS_PATH}")


if __name__ == "__main__":
    main()
