#include "rage/random_range.hpp"

namespace rage {
// @ 0x82568858 | size: 0x70
uint32_t randomNext(uint32_t* seed) {
    const uint32_t first = (*seed * 0x7FFFFFEDu + 0x7FFFFFC3u) % 0x7FFFFFFFu;
    const uint32_t second = (first * 0x7FFFFFEDu + 0x7FFFFFC3u) % 0x7FFFFFFFu;
    *seed = second;
    const uint32_t index = second & 0x7F;
    const uint32_t result = g_randomShuffleTable[index];
    g_randomShuffleTable[index] = first;
    return result;
}

// @ 0x82447C78 | size: 0x68
uint32_t randomRangeInclusive(void* owner, uint32_t low, uint32_t high) {
    if (low == high) return low;
    auto* seed = reinterpret_cast<uint32_t*>(static_cast<uint8_t*>(owner) + 0xAC);
    const uint32_t value = randomNext(seed);
    const uint32_t width = high - low + 1u;
    if (width == 0) __builtin_trap();
    return low + value % width;
}

// @ 0x82447CE0 | size: 0x68
int32_t randomRangeInclusiveSigned(void* owner, int32_t low, int32_t high) {
    if (low == high) return low;
    auto* seed = reinterpret_cast<uint32_t*>(static_cast<uint8_t*>(owner) + 0xAC);
    const uint32_t value = randomNext(seed);
    const uint32_t width = static_cast<uint32_t>(high) - static_cast<uint32_t>(low) + 1u;
    if (width == 0) __builtin_trap();
    return static_cast<int32_t>(static_cast<uint32_t>(low) + value % width);
}
}
