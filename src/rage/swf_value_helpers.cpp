#include "rage/swf_value.hpp"
#include "rage/ptr32.hpp"
#include <cstring>

extern "C" {
// The caller explicitly consumes the low byte, even with dirty upper bits.
uint32_t swfValueToBoolean(const SwfVmValue* value); // @ 0x823FA420
float swfValueToFloat(const SwfVmValue* value); // @ 0x823FA688
const char* util_A768_1(const void* value, void* buffer, int maxLen); // @ 0x823FA768
}

namespace {
struct TextChunk {
    char bytes[12];
    rage::ptr32<TextChunk> next;
};
static_assert(sizeof(TextChunk) == 16);

// Retail copies whole twelve-byte chunks, then appends a terminator. A null
// chain stays null, rather than becoming an empty string.
const char* flatten(const SwfVmValue* value, char* buffer) {
    const auto* chunk = rage::load_ptr32<TextChunk>(value, 0);
    if (!chunk) return nullptr;
    char* out = buffer;
    do {
        std::memcpy(out, chunk->bytes, 12);
        out += 12;
        chunk = chunk->next.get();
    } while (chunk);
    *out = '\0';
    return buffer;
}
}

// @ 0x823FA4C8
extern "C" uint8_t swfValueIsInteger(const SwfVmValue* value) {
    const char* text;
    char buffer[40];
    switch (value->tag) {
    case 0: text = flatten(value, buffer); break;
    case 1: text = rage::load_ptr32<const char>(value, 0); break;
    case 2: case 3: return 1;
    default: return 0;
    }
    if (!text) return 1;
    const char* point = std::strchr(text, '.');
    if (!point) return 1;
    do { ++point; } while (*point == '0');
    return *point == '\0';
}

// Equality dispatches on the left tag and converts only the right operand.
// @ 0x823FA928
extern "C" uint8_t swfValuesEqual(const SwfVmValue* a, const SwfVmValue* b) {
    switch (a->tag) {
    case 0: case 1: {
        char rightBuffer[1024];
        const char* right = util_A768_1(b, rightBuffer, sizeof(rightBuffer));
        char leftBuffer[1024];
        const char* left = a->tag == 0 ? flatten(a, leftBuffer)
                                     : rage::load_ptr32<const char>(a, 0);
        return std::strcmp(left, right) == 0;
    }
    case 2:
        return *reinterpret_cast<const uint8_t*>(a) == static_cast<uint8_t>(swfValueToBoolean(b));
    case 3:
        return static_cast<int32_t>(a->payload) == swfValueToInteger(b);
    case 4: {
        const float right = swfValueToFloat(b);
        float left;
        std::memcpy(&left, &a->payload, sizeof(left));
        return left == right;
    }
    case 5:
        return a->payload == (b->tag == 5 ? b->payload : 0);
    case 6:
        return a->payload == b->payload;
    default:
        return 0;
    }
}
