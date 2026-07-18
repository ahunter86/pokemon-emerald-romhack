#!/usr/bin/env python3
"""
Stage 1 (v5): Build a local cache of every SPECIES_ constant in the ROM,
cross-referenced against PokeAPI for legendary/mythical status AND
evolution data (evolves_from -- the api_name of its pre-evolution, or
null for base-stage species).

Run from the pokeemerald-expansion repo root:
    python3 tools/randomizer/fetch_species_data.py

Output: tools/randomizer/species_pool.json
"""
import json
import re
import sys
import time
import requests

SPECIES_H_PATH = "include/constants/species.h"
OUTPUT_PATH = "tools/randomizer/species_pool.json"
POKEAPI_SPECIES_URL = "https://pokeapi.co/api/v2/pokemon-species?limit=2000"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json",
}

SKIP_PATTERNS = [
    "SPECIES_NONE", "SPECIES_EGG", "SPECIES_OLD_UNOWN",
]

def normalize(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "", name).upper()

def parse_species_h(path):
    pattern = re.compile(r"^\s*(SPECIES_[A-Z0-9_]+)\s*=\s*(\d+)\s*,?")
    species = {}
    with open(path, "r") as f:
        for line in f:
            m = pattern.match(line)
            if not m:
                continue
            const_name, num = m.group(1), int(m.group(2))
            if any(const_name.startswith(p) or const_name == p for p in SKIP_PATTERNS):
                continue
            species[const_name] = num
    return species

def fetch_json(url, retries=3):
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            print(f"  fetch failed ({e}), retrying...", file=sys.stderr)
            time.sleep(2)
    raise RuntimeError(f"Failed to fetch {url} after {retries} attempts")

def find_form_fallback(bare_name, api_by_normalized):
    segments = bare_name.split("_")
    for i in range(len(segments) - 1, 0, -1):
        candidate = "_".join(segments[:i])
        norm = normalize(candidate)
        if norm in api_by_normalized:
            return api_by_normalized[norm]
    return None

def main():
    print("Parsing species.h ...")
    try:
        rom_species = parse_species_h(SPECIES_H_PATH)
    except FileNotFoundError:
        print(f"ERROR: couldn't find {SPECIES_H_PATH} -- run this from the repo root.")
        sys.exit(1)
    print(f"  found {len(rom_species)} candidate species constants")

    print("Fetching PokeAPI species list (this may take a minute)...")
    listing = fetch_json(POKEAPI_SPECIES_URL)
    api_species_urls = {entry["name"]: entry["url"] for entry in listing["results"]}
    print(f"  PokeAPI reports {len(api_species_urls)} species")

    api_by_normalized = {normalize(name): name for name in api_species_urls}

    matched = {}
    unmatched = []
    total = len(rom_species)
    for i, (const_name, dex_num) in enumerate(rom_species.items(), 1):
        bare = const_name[len("SPECIES_"):]
        norm = normalize(bare)
        api_name = api_by_normalized.get(norm)
        is_form = False
        if not api_name:
            api_name = find_form_fallback(bare, api_by_normalized)
            is_form = api_name is not None
        if not api_name:
            unmatched.append(const_name)
            continue
        matched[const_name] = {"api_name": api_name, "dex_num": dex_num, "is_form": is_form}
        if i % 200 == 0:
            print(f"  matched {i}/{total}...")

    form_count = sum(1 for v in matched.values() if v["is_form"])
    print(f"Matched {len(matched)} / {total} species constants "
          f"({form_count} via form-suffix fallback).")
    if unmatched:
        print(f"Still unmatched ({len(unmatched)}): {unmatched[:20]}")

    print("Fetching legendary/mythical/evolution flags (deduped by base species)...")
    detail_cache = {}
    pool = []
    unique_api_names = list({v["api_name"] for v in matched.values()})
    for i, api_name in enumerate(unique_api_names, 1):
        detail_url = api_species_urls[api_name]
        try:
            detail = fetch_json(detail_url)
        except RuntimeError as e:
            print(f"  WARNING: skipping {api_name}, {e}")
            continue
        evolves_from = detail.get("evolves_from_species")
        detail_cache[api_name] = {
            "legendary": detail.get("is_legendary", False),
            "mythical": detail.get("is_mythical", False),
            "evolves_from": evolves_from["name"] if evolves_from else None,
        }
        if i % 100 == 0:
            print(f"  fetched details for {i}/{len(unique_api_names)} unique species...")

    for const_name, info in matched.items():
        flags = detail_cache.get(info["api_name"])
        if flags is None:
            continue
        pool.append({
            "constant": const_name,
            "dex_num": info["dex_num"],
            "api_name": info["api_name"],
            "is_form": info["is_form"],
            "legendary": flags["legendary"],
            "mythical": flags["mythical"],
            "has_pre_evolution": flags["evolves_from"] is not None,
            "evolves_from": flags["evolves_from"],
        })

    legendary_count = sum(1 for p in pool if p["legendary"] or p["mythical"])
    base_stage_count = sum(1 for p in pool if not p["has_pre_evolution"])
    print(f"\nDone. {len(pool)} total species. "
          f"{legendary_count} legendary/mythical. "
          f"{base_stage_count} base-stage (no pre-evolution).")

    with open(OUTPUT_PATH, "w") as f:
        json.dump({"species": pool, "unmatched_constants": unmatched}, f, indent=2)
    print(f"Wrote {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
