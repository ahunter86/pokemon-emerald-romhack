#!/usr/bin/env python3
"""
Randomize move learnsets in src/data/pokemon/level_up_learnsets/gen_9.h
(the file actually compiled in, per P_LVL_UP_LEARNSETS == GEN_LATEST).

Levels are left untouched -- only which move is learned at each level is
randomized. Safety guarantee: simulates the game's actual initial-moveset
selection algorithm (GiveBoxMonInitialMoveset in pokemon.c -- a sliding
window that keeps the last 4 distinct moves learnable at or below a given
level) at a representative early level, and if the result would have zero
damaging moves, force-fixes one of the entries that's actually part of
that window. This is stricter than just checking "the first 4 entries",
since moves at higher levels can push early moves out of the window, or
vice versa a whole early cluster of status moves can fill the window
before any damaging move is reachable.

Usage (from repo root):
    python3 tools/randomizer/randomize_learnsets.py [--seed N]

A .bak backup is written the first time (never overwritten after that).
"""
import argparse
import random
import re
from pathlib import Path

MOVES_INFO_PATH = Path("src/data/moves_info.h")
MOVES_H_PATH = Path("include/constants/moves.h")
LEARNSET_PATH = Path("src/data/pokemon/level_up_learnsets/gen_9.h")

# Representative early-game level to guarantee a damaging move by. Starters
# begin at level 5; using 10 gives a bit of buffer for early wild catches too.
CHECK_LEVEL = 10

MOVE_BLOCK_START = re.compile(r'\[(MOVE_[A-Z0-9_]+)\]\s*=')
POWER_PATTERN = re.compile(r'\.power\s*=\s*(\d+)')
EFFECT_PATTERN = re.compile(r'\.effect\s*=\s*(EFFECT_[A-Z0-9_]+)')

# Moves with this effect can never knock out a target (they always leave
# at least 1 HP -- False Swipe, Hold Back). Fine as an ordinary move
# elsewhere, but must never be the ONLY damaging move guaranteed by our
# safety net, since a starter that can't finish off an opponent defeats
# the whole point of the guarantee.
NEVER_FAINTS_EFFECT = "EFFECT_FALSE_SWIPE"

# Pokémon: Let's Go, Pikachu!/Eevee! and Partner Power (Isle of Armor)
# signature moves -- don't make sense outside those specific event/partner
# mechanics.
EXTRA_EXCLUDED_MOVES = {
    "MOVE_PIKA_PAPOW", "MOVE_VEEVEE_VOLLEY",
    # Pikachu Partner Power moves
    "MOVE_ZIPPY_ZAP", "MOVE_FLOATY_FALL", "MOVE_SPLISHY_SPLASH",
    # Eevee Partner Power moves
    "MOVE_BOUNCY_BUBBLE", "MOVE_BUZZY_BUZZ", "MOVE_SIZZLY_SLIDE",
    "MOVE_GLITZY_GLOW", "MOVE_BADDY_BAD", "MOVE_SAPPY_SEED",
    "MOVE_FREEZY_FROST", "MOVE_SPARKLY_SWIRL",
}

LEARNSET_BLOCK = re.compile(
    r'(static const struct LevelUpMove \w+\[\] = \{)(.*?)(\};)', re.DOTALL
)
LEVEL_UP_MOVE = re.compile(r'LEVEL_UP_MOVE\(\s*(\d+)\s*,\s*(MOVE_[A-Z0-9_]+)\s*\)')


def load_gimmick_moves():
    """
    Z-moves, Max moves, and G-Max moves require special mechanics (Z-Crystal
    + trigger, or Dynamax) that don't make sense as an ordinary level-up
    move. They're grouped in one contiguous block at the tail of the
    MOVE_ enum in moves.h, starting at MOVE_CATASTROPIKA and running to
    the end of the file -- confirmed by the LAST_MAX_MOVE sentinel.
    """
    lines = MOVES_H_PATH.read_text().splitlines()
    move_pattern = re.compile(r'^\s*(MOVE_[A-Z0-9_]+)')
    gimmick = set()
    started = False
    for line in lines:
        if not started:
            if "FIRST_Z_MOVE" in line:
                started = True
            else:
                continue
        m = move_pattern.match(line)
        if m:
            gimmick.add(m.group(1))
    return gimmick


def load_move_pools():
    gimmick_moves = load_gimmick_moves()
    content = MOVES_INFO_PATH.read_text()
    matches = list(MOVE_BLOCK_START.finditer(content))
    damaging = []
    all_moves = []
    for i, m in enumerate(matches):
        move_const = m.group(1)  # already the full "MOVE_X" constant
        if move_const == "MOVE_NONE" or move_const in gimmick_moves or move_const in EXTRA_EXCLUDED_MOVES:
            continue
        window_end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        window = content[m.end():window_end]
        power_match = POWER_PATTERN.search(window)
        power = int(power_match.group(1)) if power_match else 0
        effect_match = EFFECT_PATTERN.search(window)
        effect = effect_match.group(1) if effect_match else None
        all_moves.append(move_const)
        if power > 0 and effect != NEVER_FAINTS_EFFECT:
            damaging.append(move_const)
    return all_moves, damaging


def simulate_initial_moveset(levels, moves, check_level):
    """
    Mirrors GiveBoxMonInitialMoveset's exact algorithm: walk entries in
    array order (assumed ascending by level, matching the source file and
    the game's own assumption), stop once level exceeds check_level, skip
    duplicates, and keep only the last 4 distinct moves via a sliding
    window. Returns the list of SOURCE INDICES that ended up in the
    final window, so a fix can be applied to the exact entry involved.
    """
    window = []  # list of source indices, oldest first
    known_moves = []
    for idx, lvl in enumerate(levels):
        if lvl > check_level:
            break
        if lvl == 0:
            continue
        mv = moves[idx]
        if mv in known_moves:
            continue
        if len(window) < 4:
            window.append(idx)
            known_moves.append(mv)
        else:
            window.pop(0)
            known_moves.pop(0)
            window.append(idx)
            known_moves.append(mv)
    return window


def randomize_block(block_text, all_moves, damaging_moves, rng, stats):
    entries = list(LEVEL_UP_MOVE.finditer(block_text))
    if not entries:
        return block_text

    levels = [int(e.group(1)) for e in entries]
    new_moves = [rng.choice(all_moves) for _ in entries]
    damaging_set = set(damaging_moves)

    sim_indices = simulate_initial_moveset(levels, new_moves, CHECK_LEVEL)

    if sim_indices:
        if not any(new_moves[i] in damaging_set for i in sim_indices):
            # Force the entry that would actually appear in the simulated
            # initial moveset to a damaging move -- guarantees it's usable.
            fix_idx = sim_indices[0]
            new_moves[fix_idx] = rng.choice(damaging_moves)
            stats["safety_fixes"] += 1
    else:
        # No moves learnable by CHECK_LEVEL at all (rare for base-stage
        # species). Best-effort fallback: fix the lowest-level entry overall.
        lowest_idx = min(range(len(entries)), key=lambda i: levels[i])
        new_moves[lowest_idx] = rng.choice(damaging_moves)
        stats["safety_fixes"] += 1
        stats["no_early_moves_fallback"] += 1

    # Rebuild the block text, replacing each match's move name in place.
    result = []
    last_end = 0
    for entry, new_move in zip(entries, new_moves):
        result.append(block_text[last_end:entry.start(2)])
        result.append(new_move)
        last_end = entry.end(2)
    result.append(block_text[last_end:])
    stats["species"] += 1
    return "".join(result)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducible output")
    args = parser.parse_args()
    rng = random.Random(args.seed)

    if not MOVES_INFO_PATH.exists():
        print(f"ERROR: {MOVES_INFO_PATH} not found -- run this from the repo root.")
        return
    if not LEARNSET_PATH.exists():
        print(f"ERROR: {LEARNSET_PATH} not found -- run this from the repo root.")
        return

    all_moves, damaging_moves = load_move_pools()
    print(f"Move pool: {len(all_moves)} total moves, {len(damaging_moves)} damaging.")

    content = LEARNSET_PATH.read_text()
    stats = {"species": 0, "safety_fixes": 0, "no_early_moves_fallback": 0}

    def repl(m):
        prefix, body, suffix = m.group(1), m.group(2), m.group(3)
        new_body = randomize_block(body, all_moves, damaging_moves, rng, stats)
        return prefix + new_body + suffix

    new_content = LEARNSET_BLOCK.sub(repl, content)

    backup = LEARNSET_PATH.with_suffix(LEARNSET_PATH.suffix + ".bak")
    if not backup.exists():
        backup.write_text(content)
        print(f"Backed up original to {backup}")
    else:
        print(f"Backup already exists at {backup} (not overwritten).")

    LEARNSET_PATH.write_text(new_content)
    print(f"Randomized {stats['species']} species' learnsets.")
    print(f"Applied the no-damage-move safety fix to {stats['safety_fixes']} species.")
    print(f"  (of which {stats['no_early_moves_fallback']} used the rare no-early-moves fallback.)")


if __name__ == "__main__":
    main()
