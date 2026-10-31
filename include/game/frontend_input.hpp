#pragma once
#include <cstdint>
#include "rage/ptr32.hpp"

// One frontend input notification, copied as a complete 0x480-byte record.
struct FrontendInputRecord { uint8_t bytes[0x480]; };
uint8_t FrontendInput_FindHighestPriority(void* queue, FrontendInputRecord* output,
                                        int32_t type, int32_t subtype); // @ 0x822ECD68
extern "C" rage::ptr32<void> g_frontendInputQueue; // @ 0x8271A33C
