#include "global.h"
#include "item_ball.h"
#include "event_data.h"
#include "item.h"
#include "constants/event_objects.h"
#include "constants/items.h"
#include "data/randomizer/item_pool.h"
#include "data/randomizer/tm_pool.h"

static u32 GetItemBallAmountFromTemplate(u32);
static u32 GetItemBallIdFromTemplate(u32);

// Deterministic integer hash (MurmurHash3 finalizer). Mirrors the one in
// wild_encounter.c -- pure function, same inputs always give the same
// output.
static u32 RandomizerHash(u32 x)
{
    x ^= x >> 16;
    x *= 0x7feb352dU;
    x ^= x >> 15;
    x *= 0x846ca68bU;
    x ^= x >> 16;
    return x;
}

// Substitutes an item-ball/hidden-item item based on this save's
// randomizer seed and a caller-supplied uniqueKey identifying THIS
// SPECIFIC location (not the original item) -- so every location is
// randomized independently, rather than every instance of e.g. an Ether
// always mapping to the same substitute. Only touches items already in
// a "safe" pocket (Items/Poké Balls/TM-HM). Key items and (non-Sitrus)
// berries pass through unchanged, and are never selected as a
// replacement either, since sRandomizerItemPool never contains them.
enum Item RandomizeFieldItem(enum Item originalItem, u32 uniqueKey)
{
    u32 hash;
    enum Pocket pocket = GetItemPocket(originalItem);

    if (pocket != POCKET_ITEMS && pocket != POCKET_POKE_BALLS && pocket != POCKET_TM_HM)
        return originalItem;

    hash = RandomizerHash(gSaveBlock2Ptr->pokedex.randomizerSeed ^ (uniqueKey * 0xB5297A4Du) ^ 0x49E1F4D2u);
    return sRandomizerItemPool[hash % RANDOMIZER_ITEM_POOL_COUNT];
}

// Substitutes a TM/HM given via a script (giveitem/finditem -- gym
// leader rewards, Trick House puzzles, any other NPC-given TM/HM) based
// on this save's randomizer seed and a caller-supplied uniqueKey
// identifying THIS SPECIFIC call site -- every giveitem/finditem in the
// game is randomized independently, not mapped by original item. Only
// touches TM/HM pocket items, so a TM slot always becomes another
// TM/HM. Everything else (regular NPC-given items, key items) passes
// through unchanged.
enum Item RandomizeGivenTM(enum Item originalItem, u32 uniqueKey)
{
    u32 hash;

    if (GetItemPocket(originalItem) != POCKET_TM_HM)
        return originalItem;

    hash = RandomizerHash(gSaveBlock2Ptr->pokedex.randomizerSeed ^ (uniqueKey * 0x2545F491u) ^ 0x27D4EB2Fu);
    return sRandomizerTMPool[hash % RANDOMIZER_TM_POOL_COUNT];
}

static u32 GetItemBallAmountFromTemplate(u32 itemBallId)
{
    u32 amount = gMapHeader.events->objectEvents[itemBallId].movementRangeX;

    if (amount > MAX_BAG_ITEM_CAPACITY)
        return MAX_BAG_ITEM_CAPACITY;

    return (amount == 0) ? 1 : amount;
}

static u32 GetItemBallIdFromTemplate(u32 itemBallId)
{
    enum Item itemId = gMapHeader.events->objectEvents[itemBallId].trainerRange_berryTreeId;
    u32 uniqueKey;

    if (itemId >= ITEMS_COUNT)
        return ITEM_NONE + 1;

    uniqueKey = ((u32)gMapHeader.mapLayoutId << 16) ^ itemBallId;
    return RandomizeFieldItem(itemId, uniqueKey);
}

void GetItemBallIdAndAmountFromTemplate(void)
{
    u32 itemBallId = (gSpecialVar_LastTalked - 1);
    gSpecialVar_Result = GetItemBallIdFromTemplate(itemBallId);
    gSpecialVar_0x8009 = GetItemBallAmountFromTemplate(itemBallId);
}
