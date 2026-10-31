#include "bound_copy.hpp"
#include <cstdint>
#include <cstring>

namespace rage {
// @ 0x8228DA50
void phBound_CopyProperties(void* destination, const void* source) {
    auto* out = static_cast<uint8_t*>(destination);
    const auto* in = static_cast<const uint8_t*>(source);
    // Preserve the vtable. Retain the scalar, vector and forward-byte ordering
    // for partially overlapping bounds; this is not a whole-record memmove.
    for (unsigned offset = 4; offset < 8; ++offset) out[offset] = in[offset];
    *reinterpret_cast<float*>(out + 8) = *reinterpret_cast<const float*>(in + 8);
    *reinterpret_cast<float*>(out + 12) = *reinterpret_cast<const float*>(in + 12);
    for (unsigned offset = 0x10; offset < 0x60; offset += 16) {
        alignas(16) uint8_t row[16];
        std::memcpy(row, in + offset, 16);
        std::memcpy(out + offset, row, 16);
    }
    *reinterpret_cast<uint16_t*>(out + 0x60) = *reinterpret_cast<const uint16_t*>(in + 0x60);
    for (unsigned offset = 0x62; offset < 0x70; ++offset) out[offset] = in[offset];
}
}
