#ifndef GUARD_ITEM_BALL_H
#define GUARD_ITEM_BALL_H

#include "constants/items.h"

void GetItemBallIdAndAmountFromTemplate(void);
enum Item RandomizeFieldItem(enum Item originalItem, u32 uniqueKey);
enum Item RandomizeGivenTM(enum Item originalItem, u32 uniqueKey);

#endif //GUARD_ITEM_BALL_H
