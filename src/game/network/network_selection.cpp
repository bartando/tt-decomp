#include "game/network_selection.hpp"
#include "rage/random_range.hpp"
#include "rage/ptr32.hpp"
#include "rage/memory.h"

extern "C" void* rage_Alloc(uint32_t bytes); // @ 0x820DEC88

// @ 0x8245AAC8 | size: 0x150
uint32_t pongNetMessageHolder_AAC8_w(pongNetMessageHolder* holder, uint32_t unused,
                                    uint16_t* outSlotId, uint32_t* outPayload, float value) {
    (void)unused;
    *outPayload = 0xFFFFFFFFu;
    *outSlotId = 0xFFFF;
    auto* inner = rage::load_ptr32<uint8_t>(holder, 8);
    const uint32_t count = *reinterpret_cast<uint32_t*>(inner) & 0xFFFF;
    auto* scratch = static_cast<uint16_t*>(rage_Alloc(count * 2));
    if (!scratch) return 0x8007000Eu;
    // The allocator can run callbacks; retail reloads the pool after it returns.
    auto* entries = rage::load_ptr32<uint8_t>(holder, 8) + 8;
    uint16_t matches = 0;
    for (uint32_t index = 0; index < count; ++index) {
        const auto* bounds = reinterpret_cast<const float*>(entries + index * 16 + 4);
        if (bounds[0] <= value && bounds[1] >= value)
            scratch[matches++] = static_cast<uint16_t>(index);
    }
    if (matches != 0) {
        void* randomOwner = rage::load_ptr32<void>(holder, 4);
        const uint16_t chosen = static_cast<uint16_t>(rage::randomRangeInclusiveSigned(randomOwner, 0, matches - 1));
        const uint16_t slot = scratch[chosen];
        *outPayload = *reinterpret_cast<uint32_t*>(entries + slot * 16);
        *outSlotId = slot;
    }
    rage_free(scratch);
    return 0;
}
