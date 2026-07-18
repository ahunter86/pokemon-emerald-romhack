#!/usr/bin/env python3
"""
Randomize species abilities across all src/data/pokemon/species_info/gen_*_families.h files.

For each species, preserves the *shape* of its ability slots (i.e. if the
original had a primary + hidden ability but no secondary, the randomized
version keeps a primary + hidden but no secondary) while replacing which
specific abilities occupy the filled slots. Slots on the same species are
kept unique from each other where possible.

Usage (from repo root):
    python3 tools/randomizer/randomize_abilities.py [--seed N]

A .bak backup of each file is written the first time (never overwritten
after that, so you always keep your true original).
"""
import argparse
import random
import re
import shutil
from pathlib import Path

ABILITIES_H_PATH = Path("include/constants/abilities.h")
SPECIES_INFO_DIR = Path("src/data/pokemon/species_info")
TARGET_FILES = [
    "gen_1_families.h", "gen_2_families.h", "gen_3_families.h",
    "gen_4_families.h", "gen_5_families.h", "gen_6_families.h",
    "gen_7_families.h", "gen_8_families.h", "gen_9_families.h",
]

ABILITY_LINE_PATTERN = re.compile(
    r'\.abilities = \{ (ABILITY_[A-Z0-9_]+), (ABILITY_[A-Z0-9_]+), (ABILITY_[A-Z0-9_]+) \},'
)


def load_ability_pool():
    pattern = re.compile(r'^\s*(ABILITY_[A-Z0-9_]+)\s*=\s*\d+,?')
    pool = []
    with open(ABILITIES_H_PATH) as f:
        for line in f:
            m = pattern.match(line)
            if m and m.group(1) != "ABILITY_NONE":
                pool.append(m.group(1))
    return pool


def randomize_match(match, pool, rng):
    a, b, h = match.group(1), match.group(2), match.group(3)
    slots_present = [x != "ABILITY_NONE" for x in (a, b, h)]
    chosen = []
    used = set()
    for present in slots_present:
        if not present:
            chosen.append("ABILITY_NONE")
            continue
        pick = rng.choice(pool)
        tries = 0
        while pick in used and tries < 20:
            pick = rng.choice(pool)
            tries += 1
        used.add(pick)
        chosen.append(pick)
    return f".abilities = {{ {chosen[0]}, {chosen[1]}, {chosen[2]} }},"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducible output")
    args = parser.parse_args()
    rng = random.Random(args.seed)

    if not ABILITIES_H_PATH.exists():
        print(f"ERROR: {ABILITIES_H_PATH} not found -- run this from the repo root.")
        return

    pool = load_ability_pool()
    print(f"Ability pool: {len(pool)} candidates (ABILITY_NONE excluded).")

    total_species = 0
    for filename in TARGET_FILES:
        path = SPECIES_INFO_DIR / filename
        if not path.exists():
            print(f"  skip {filename} (not found)")
            continue
        backup = path.with_suffix(path.suffix + ".bak")
        content = path.read_text()

        count = [0]

        def repl(m):
            count[0] += 1
            return randomize_match(m, pool, rng)

        new_content = ABILITY_LINE_PATTERN.sub(repl, content)

        if not backup.exists():
            shutil.copy(path, backup)
        else:
            print(f"    (backup already exists for {filename}, not overwritten)")

        path.write_text(new_content)
        print(f"  {filename}: randomized {count[0]} species")
        total_species += count[0]

    print(f"Total species randomized: {total_species}")


if __name__ == "__main__":
    main()
