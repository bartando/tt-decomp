#pragma once
#include <cstdint>

struct GameEventHeader {
    uint16_t id;
    uint8_t flags;
    uint8_t payloadWords;
};
static_assert(sizeof(GameEventHeader) == 4, "game event header size");

// The low byte of payloadWords selects how many four-byte words to copy.
// @ 0x8225E6E0
void PostGameMessage(uint32_t id, uint32_t flags, uint32_t payloadWords, const void* payload);

// @ 0x8225E7F8
void DispatchGameMessage(GameEventHeader* message);

// @ 0x8225E480. 'i' and 'f' consume raw 32-bit words (floats are bit patterns,
// not promoted doubles); 's' consumes a C string, copied including word padding.
void PostGameMessageFmt(uint32_t id, uint32_t flags, const char* format, ...);
