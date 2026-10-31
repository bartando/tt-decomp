#pragma once
#include <cstdint>

namespace rage {
uint32_t randomNext(uint32_t* seed); // @ 0x82568858
uint32_t randomRangeInclusive(void* owner, uint32_t low, uint32_t high); // @ 0x82447C78
int32_t randomRangeInclusiveSigned(void* owner, int32_t low, int32_t high); // @ 0x82447CE0
extern uint32_t g_randomShuffleTable[128]; // @ 0x825BD5B0
}
