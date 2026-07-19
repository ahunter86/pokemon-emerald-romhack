#include "global.h"
#include "item_ball.h"
#include "event_data.h"
#include "item.h"
#include "constants/event_objects.h"
#include "constants/items.h"
#include "data/randomizer/item_pool.h"

static u32 GetItemBallAmountFromTemplate(u32);
static u32 GetItemBallIdFromTemplate(u32);

// Deterministic integer hash (MurmurHash3 finalizer). Mirrors the one in
// wild_encounter.c -- pure function, same inputs always give the same
// output, so a given item-ball slot always substitutes to the same item
// within one save, but differs between saves (different seed).
static u32 RandomizerHash(u32 x)
{
    x ^= x >> 16;
    x *= 0x7feb352dU;
    x ^= x >> 15;
    x *= 0x846ca68bU;
    x ^= x >> 16;
    return x;
}

// Substitutes an item-ball item based on this save's randomizer seed.
// Only touches items already in a "safe" pocket (Items/Poké Balls/TM-HM).
// Key items and berries pass through unchanged, and are never selected as
// a replacement either, since sRandomizerItemPool never contains them.
static enum Item RandomizeItemBallItem(enum Item originalItem)
{
    u32 hash;
    enum Pocket pocket = GetItemPocket(originalItem);

    if (pocket != POCKET_ITEMS && pocket != POCKET_POKE_BALLS && pocket != POCKET_TM_HM)
        return originalItem;

    hash = RandomizerHash(gSaveBlock2Ptr->pokedex.randomizerSeed ^ ((u32)originalItem * 0xB5297A4Du) ^ 0x49E1F4D2u);
    return sRandomizerItemPool[hash % RANDOMIZER_ITEM_POOL_COUNT];
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

    if (itemId >= ITEMS_COUNT)
        return ITEM_NONE + 1;

    return RandomizeItemBallItem(itemId);
}

void GetItemBallIdAndAmountFromTemplate(void)
{
    u32 itemBallId = (gSpecialVar_LastTalked - 1);
    gSpecialVar_Result = GetItemBallIdFromTemplate(itemBallId);
    gSpecialVar_0x8009 = GetItemBallAmountFromTemplate(itemBallId);
}
