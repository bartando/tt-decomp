#include "crt/host_format.h"
#include <cstdint>
#include <cstring>

extern "C" char g_networkTimestampLogBuffer[50]; // @ 0x8271A978

// @ 0x8239BF30 | size: 0x8C
char* FormatTimestampForLog(void* timestamp) {
    const auto* bytes = static_cast<const uint8_t*>(timestamp);
    int32_t whole;
    float fraction;
    std::memcpy(&whole, bytes, 4);
    std::memcpy(&fraction, bytes + 4, 4);
    const float scaled = fraction * 1000.0f;
    // fctidz saturates to signed 64 bits; stfiwx retains its low word.
    uint32_t milliseconds;
    if (scaled != scaled || scaled <= -0x1p63f) milliseconds = 0;
    else if (scaled >= 0x1p63f) milliseconds = UINT32_MAX;
    else milliseconds = static_cast<uint32_t>(static_cast<int64_t>(scaled));
    const int32_t minutes = whole / 60;
    const int32_t seconds = whole % 60;
    _snprintf(g_networkTimestampLogBuffer, 50, "%d:%2.2d:%3.3d", minutes, seconds,
              static_cast<int32_t>(milliseconds));
    return g_networkTimestampLogBuffer;
}
