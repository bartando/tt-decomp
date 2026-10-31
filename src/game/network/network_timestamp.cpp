#include "crt/host_format.h"
#include "game/network_timestamp.hpp"
#include "rage/ptr32.hpp"
#include <cstdint>
#include <cstring>

extern "C" char g_networkTimestampLogBuffer[50]; // @ 0x8271A978

extern "C" const float k_initRefreshRate; // @ 0x825C4948

namespace {
// fctidz saturates to signed 64 bits; stfiwx retains its low word.
uint32_t TruncateLowWord(float value) {
    if (value != value || value <= -0x1p63f) return 0;
    if (value >= 0x1p63f) return UINT32_MAX;
    return static_cast<uint32_t>(static_cast<int64_t>(value));
}
struct CachedClockTimestamp {
    rage::ptr32<void> vtable;
    int32_t whole;
    float fraction;
    float lastFormatted;
    char text[50];
};
}

// @ 0x8239BE30 | size: 0xFC
int networkFormatElapsedTime(char* destination, uint32_t /*unusedCapacity*/, float seconds) {
    const bool negative = seconds < 0.0f;
    const float magnitude = negative ? -seconds : seconds;
    const uint32_t minutes = TruncateLowWord(magnitude * (1.0f / 60.0f));
    // Retail zero-extends the low word before converting it back to float.
    const float minuteSeconds = static_cast<float>(minutes) * k_initRefreshRate;
    const float remainder = magnitude - minuteSeconds;
    const uint32_t wholeSeconds = TruncateLowWord(remainder);
    const float fraction = remainder - static_cast<float>(wholeSeconds);
    const uint32_t milliseconds = TruncateLowWord(fraction * 1000.0f);
    return _snprintf(destination, 50, "%s%d:%2.2d:%3.3d", negative ? "-" : "",
                     static_cast<int32_t>(minutes), static_cast<int32_t>(wholeSeconds),
                     static_cast<int32_t>(milliseconds));
}

// @ 0x82391480 | size: 0x90
const char* networkClockTimestamp(void* clock, int slot) {
    const uint32_t offset = (static_cast<uint32_t>(slot) + 3u) * 4u;
    auto* timestamp = rage::load_ptr32<CachedClockTimestamp>(clock, offset);
    const float value = timestamp->fraction + static_cast<float>(timestamp->whole);
    if (timestamp->lastFormatted != value) {
        timestamp->lastFormatted = value;
        networkFormatElapsedTime(timestamp->text, 50, value);
    }
    return timestamp->text;
}

// @ 0x8239BF30 | size: 0x8C
char* FormatTimestampForLog(void* timestamp) {
    const auto* bytes = static_cast<const uint8_t*>(timestamp);
    int32_t whole;
    float fraction;
    std::memcpy(&whole, bytes, 4);
    std::memcpy(&fraction, bytes + 4, 4);
    const float scaled = fraction * 1000.0f;
    const uint32_t milliseconds = TruncateLowWord(scaled);
    const int32_t minutes = whole / 60;
    const int32_t seconds = whole % 60;
    _snprintf(g_networkTimestampLogBuffer, 50, "%d:%2.2d:%3.3d", minutes, seconds,
              static_cast<int32_t>(milliseconds));
    return g_networkTimestampLogBuffer;
}
