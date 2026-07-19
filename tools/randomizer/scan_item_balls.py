#!/usr/bin/env python3
"""
Diagnostic: scan every data/maps/*/map.json for OBJ_EVENT_GFX_ITEM_BALL
objects, and cross-reference each item against its pocket in items.h.
Reports any item balls holding a POCKET_KEY_ITEMS item, to confirm or
refute the assumption that key items are never placed this way.
"""
import json
import re
from pathlib import Path
from collections import Counter

ITEMS_H_PATH = Path("src/data/items.h")
MAPS_DIR = Path("data/maps")

ITEM_BLOCK_START = re.compile(r'\[(ITEM_[A-Z0-9_]+)\]\s*=')
POCKET_PATTERN = re.compile(r'\.pocket\s*=\s*(POCKET_[A-Z0-9_]+)')


def load_item_pockets():
    content = ITEMS_H_PATH.read_text()
    matches = list(ITEM_BLOCK_START.finditer(content))
    pockets = {}
    for i, m in enumerate(matches):
        name = m.group(1)
        window_end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        window = content[m.end():window_end]
        pocket_match = POCKET_PATTERN.search(window)
        pockets[name] = pocket_match.group(1) if pocket_match else None
    return pockets


def main():
    pockets = load_item_pockets()
    print(f"Loaded pocket data for {len(pockets)} items.")

    pocket_counts = Counter()
    key_item_hits = []
    total_ball_count = 0

    for map_json in sorted(MAPS_DIR.glob("*/map.json")):
        try:
            data = json.loads(map_json.read_text())
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        for obj in data.get("object_events", []):
            if obj.get("graphics_id") != "OBJ_EVENT_GFX_ITEM_BALL":
                continue
            total_ball_count += 1
            item = obj.get("trainer_sight_or_berry_tree_id", "")
            pocket = pockets.get(item, "UNKNOWN")
            pocket_counts[pocket] += 1
            if pocket == "POCKET_KEY_ITEMS":
                key_item_hits.append((map_json.parent.name, item, obj.get("flag", "")))

    print(f"\nTotal item balls found: {total_ball_count}")
    print("Breakdown by pocket:")
    for pocket, count in pocket_counts.most_common():
        print(f"  {pocket}: {count}")

    print(f"\nKey item hits: {len(key_item_hits)}")
    for map_name, item, flag in key_item_hits:
        print(f"  {map_name}: {item} (flag: {flag})")


if __name__ == "__main__":
    main()
