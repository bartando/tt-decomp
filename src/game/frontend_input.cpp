#include "game/frontend_input.hpp"
#include <cstring>

extern "C" { rage::ptr32<void> g_frontendInputQueue; } // @ 0x8271A33C

// @ 0x822ECD68
uint8_t FrontendInput_FindHighestPriority(void* object, FrontendInputRecord* output,
                                        int32_t type, int32_t subtype) {
    auto* queue = static_cast<uint8_t*>(object);
    const int32_t count = *reinterpret_cast<const int32_t*>(queue + 0x9360);
    queue[8] = 0;
    const uint8_t* best = nullptr;
    for (int32_t i = 0; i < count; ++i) {
        const auto* record = queue + 0x360 + i * 0x480;
        const int32_t recordType = *reinterpret_cast<const int32_t*>(record + 8);
        bool acceptsType = recordType == type;
        if (type < 0) {
            acceptsType = false;
            const int32_t allowedCount = *reinterpret_cast<const int32_t*>(queue + 0x9398);
            for (int32_t j = 0; j < allowedCount; ++j) {
                if (*reinterpret_cast<const int32_t*>(queue + 0x9364 + j * 4) == recordType) {
                    acceptsType = true;
                    break;
                }
            }
        }
        if (!acceptsType || (subtype >= 0 &&
            *reinterpret_cast<const int32_t*>(record + 0x2C) != subtype)) continue;
        if (!best || *reinterpret_cast<const int32_t*>(record + 4) >
                     *reinterpret_cast<const int32_t*>(best + 4)) best = record;
    }
    if (!best) return 0;
    std::memcpy(output, best, sizeof(*output));
    return 1;
}
